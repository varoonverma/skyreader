# app/service/local_parser.py

import os
import uuid
import re
import json
import logging
import torch

from typing import Dict, Any
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import PeftModel

from app.service.base_parser import BaseParser
from app.service.prompt_builder import build_few_shot_prompt, build_zero_shot_prompt
from app.exception.exceptions import RemoteModelError

SYSTEM_INSTRUCTION = (
    "Parse IATA Type B messages into structured JSON according to AHM specification."
)


class LocalModelParser(BaseParser):
    """Parser that uses a local LLM (with optional LoRA adapter) to parse TTY messages."""

    _model_instance = None
    _tokenizer_instance = None

    @classmethod
    def initialize(
            cls,
            base_model_path: str,
            max_length: int = 8192,
    ):
        """
        Load and cache the base model (from LOCAL_BASE_MODEL_PATH or default),
        then apply a LoRA adapter if the provided path is an adapter folder.
        """
        try:
            # determine adapter folder
            adapter_model_path = os.getenv("LORA_ADAPTER_PATH")

            # 1) load & patch config
            config = AutoConfig.from_pretrained(base_model_path)
            config.max_position_embeddings = max_length
            for attr in ("n_positions", "n_ctx"):  # older HF names
                if hasattr(config, attr): setattr(config, attr, max_length)
            logging.info("Set model context length to %d", max_length)

            # 2) tokenizer
            cls._tokenizer_instance = AutoTokenizer.from_pretrained(
                base_model_path, use_fast=True,
                model_max_length=max_length,
                padding_side="right",
                truncation_side="right",
            )
            if cls._tokenizer_instance.eos_token is None:
                cls._tokenizer_instance.add_special_tokens({"eos_token": "</s>"})
            if cls._tokenizer_instance.pad_token is None:
                cls._tokenizer_instance.pad_token = cls._tokenizer_instance.eos_token

            # 3) model kwargs
            device_map = "auto"
            torch_dtype = torch.float16
            if os.getenv("LOW_MEMORY", "false").lower() == "true":
                device_map, torch_dtype = {"": 0}, torch.float32

            model_kwargs = {
                "config": config,
                "torch_dtype": torch_dtype,
                "device_map": device_map,
                "low_cpu_mem_usage": True,
                "use_safetensors": True,
            }

            # optional 4bit
            if os.getenv("USE_QUANTIZATION", "false").lower() == "true":
                try:
                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float32,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_cpu_offload=True,
                    )
                    logging.info("4-bit quantization enabled")
                except ImportError:
                    logging.warning("bitsandbytes missing, skipping quantization")


            # 4) load base
            base = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                **model_kwargs,
            )
            logging.info("Base model loaded from %s", base_model_path)

            # 5) apply LoRA if exists
            if os.path.isdir(adapter_model_path):
                cls._model_instance = PeftModel.from_pretrained(
                    base, adapter_model_path, torch_dtype=base.dtype
                )
                logging.info("Loaded LoRA adapter from %s", adapter_model_path)
            else:
                cls._model_instance = base
                logging.info("No LoRA adapter found, using base model only")

            logging.info("Local model initialization complete")

        except Exception as e:
            logging.error("Failed to initialize local model: %s", e, exc_info=True)
            raise

    def __init__(
            self,
            base_model_path: str = None,
            use_few_shots: bool = False,
    ):
        """
        :param base_model_path: HF ID or local path (falls back to env LOCAL_MODEL_PATH)
        :param use_few_shots:      Whether to prepend few-shot examples in each prompt.
        """
        if LocalModelParser._model_instance is None:
            LocalModelParser.initialize(base_model_path)

        self.model = LocalModelParser._model_instance
        self.tokenizer = LocalModelParser._tokenizer_instance
        self.use_few_shots = use_few_shots

        # device
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        logging.info("Inference device: %s", self.device)

    def parse_tty_message(self, tty_message: str) -> Dict[str, Any]:
        try:
            # Build the prompt
            prompt = (
                build_few_shot_prompt(tty_message)
                if self.use_few_shots
                else build_zero_shot_prompt(tty_message)
            )

            # Tokenize and move to device
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.tokenizer.model_max_length,
            ).to(self.device)

            # Generate without gradients
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=256,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Decode only new tokens
            gen_ids = outputs[0][ inputs.input_ids.shape[-1] : ]
            raw_response = self.tokenizer.decode(
                gen_ids, skip_special_tokens=True
            ).strip()

            # Extract JSON
            json_text = self._extract_json_from_text(raw_response)
            try:
                parsed = json.loads(json_text)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON from local model")

            # Build return structure
            response_id = str(uuid.uuid4())
            usage = {
                "prompt_tokens": inputs.input_ids.shape[-1],
                "completion_tokens": gen_ids.shape[-1],
                "total_tokens": outputs.shape[-1],
            }

            return {
                "message_id": response_id,
                "usage": usage,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": raw_response},
                        "finish_reason": "stop",
                        "parsed_json": parsed,
                    }
                ],
            }

        except Exception as e:
            logging.error("Error in LocalModelParser.parse_tty_message: %s", e, exc_info=True)
            raise RemoteModelError(f"Local model error: {e}")

    def _extract_json_from_text(self, text: str) -> str:
        # Try fenced JSON
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if m:
            return m.group(1)
        # Fallback to first {...}
        m = re.search(r'(\{.*\})', text, re.DOTALL)
        return m.group(1) if m else text