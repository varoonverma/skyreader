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
from app.service.base_parser import BaseParser
from app.service.prompt_builder import build_few_shot_prompt, build_zero_shot_prompt
from app.exception.exceptions import RemoteModelError

SYSTEM_INSTRUCTION = (
    "Parse IATA Type B messages into structured JSON according to AHM specification."
)


class LocalModelParser(BaseParser):
    """Parser that uses a local LLM to parse IATA Type B messages."""

    _model_instance = None
    _tokenizer_instance = None

    @classmethod
    def initialize(
            cls,
            model_name_or_path: str,
            max_length: int = 8192,
    ):
        """
        Load (and cache) the model and tokenizer with extended context length.
        """
        try:
            # 1) Load and patch config for longer context
            config = AutoConfig.from_pretrained(model_name_or_path)
            config.max_position_embeddings = max_length
            if hasattr(config, "n_positions"):
                config.n_positions = max_length
            if hasattr(config, "n_ctx"):
                config.n_ctx = max_length
            logging.info("Set model context length to %d", max_length)

            # 2) Load tokenizer
            cls._tokenizer_instance = AutoTokenizer.from_pretrained(
                model_name_or_path,
                use_fast=True,
                model_max_length=max_length,
                padding_side="right",
                truncation_side="right",
            )
            # ensure pad token
            if cls._tokenizer_instance.pad_token is None:
                cls._tokenizer_instance.pad_token = cls._tokenizer_instance.eos_token

            logging.info("Loading model from %s", model_name_or_path)

            # 3) Prepare model kwargs
            device_map = "auto"
            torch_dtype = torch.float16
            if os.environ.get("LOW_MEMORY", "false").lower() == "true":
                device_map = {"": 0}
                torch_dtype = torch.float32

            model_kwargs: Dict[str, Any] = {
                "config": config,
                "torch_dtype": torch_dtype,
                "device_map": device_map,
                "low_cpu_mem_usage": True,
                "use_safetensors": True,
            }

            # 4) Optional 4-bit quantization
            if os.environ.get("USE_QUANTIZATION", "false").lower() == "true":
                try:
                    logging.info("Enabling 4-bit quantization")
                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float32,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_cpu_offload=True,
                    )
                except ImportError:
                    logging.warning("bitsandbytes not installed, skipping quantization")

            cls._model_instance = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                **model_kwargs,
            )
            logging.info("Local model loaded successfully")

        except Exception as e:
            logging.error("Failed to initialize local model: %s", e, exc_info=True)
            raise

    def __init__(
            self,
            model_name_or_path: str = None,
            use_few_shots: bool = False,
    ):
        """
        :param model_name_or_path: HuggingFace ID or local path. If omitted, env var LOCAL_MODEL_PATH is used.
        :param use_few_shots:      Whether to include few-shot examples in the prompt.
        """
        path = model_name_or_path or os.environ.get("LOCAL_MODEL_PATH")
        if LocalModelParser._model_instance is None or LocalModelParser._tokenizer_instance is None:
            logging.warning("Local model not yet initialized; loading now...")
            LocalModelParser.initialize(path)

        self.model = LocalModelParser._model_instance
        self.tokenizer = LocalModelParser._tokenizer_instance
        self.use_few_shots = use_few_shots
        # choose device
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

    def parse_tty_message(self, tty_message: str) -> Dict[str, Any]:
        """
        Tokenizes the prompt, generates with the local model, extracts JSON, and returns
        in the same structure as the remote parser (with choices + parsed_json).
        """
        try:
            # 1) Build prompt (includes SYSTEM_INSTRUCTION internally)
            prompt = (
                build_few_shot_prompt(tty_message)
                if self.use_few_shots
                else build_zero_shot_prompt(tty_message)
            )

            # 2) Tokenize and move to device
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.tokenizer.model_max_length,
            ).to(self.device)

            # 3) Generate output (no grad, greedy, fixed-length)
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=256,       # cap to a few hundred tokens
                    do_sample=False,          # greedy
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # 4) Decode only the newly generated tokens
            gen_ids = outputs[0][ inputs.input_ids.shape[-1] : ]
            raw_response = self.tokenizer.decode(gen_ids, skip_special_tokens=True).strip()

            # 5) Extract JSON block
            json_text = self._extract_json_from_text(raw_response)
            try:
                parsed = json.loads(json_text)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON received from local model")

            # 6) Wrap into choices structure
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
            logging.error("Error in local_parser: %s", e, exc_info=True)
            raise RemoteModelError(f"Local model error: {e}")

    def _extract_json_from_text(self, text: str) -> str:
        # try fenced code block
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if m:
            return m.group(1)
        # try first {...}
        m = re.search(r'(\{.*\})', text, re.DOTALL)
        return m.group(1) if m else text