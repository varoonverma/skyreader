# app/service/local_parser.py

import os
import re
import json
import logging
import torch

from typing import Any, Dict
from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

from app.service.base_parser import BaseParser
from app.service.prompt_builder import build_zero_shot_prompt, build_few_shot_prompt

class LocalModelParser(BaseParser):
    _model_instance = None
    _tokenizer_instance = None

    @classmethod
    def initialize(cls, base_model_path: str, max_length: int = 8192):
        adapter_path = os.getenv("LORA_ADAPTER_PATH", "")

        # 1) config
        config = AutoConfig.from_pretrained(base_model_path)
        config.max_position_embeddings = max_length
        for a in ("n_positions", "n_ctx"):
            if hasattr(config, a):
                setattr(config, a, max_length)
        logging.info("Context length set to %d", max_length)

        # 2) tokenizer
        cls._tokenizer_instance = AutoTokenizer.from_pretrained(
            base_model_path, use_fast=True, model_max_length=max_length
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

        model_kwargs: Dict[str, Any] = {
            "config": config,
            "torch_dtype": torch_dtype,
            "device_map": device_map,
            "low_cpu_mem_usage": True,
            "use_safetensors": True,
        }

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
                logging.warning("bitsandbytes not installed; skipping quant")

        # 4) load base
        base = AutoModelForCausalLM.from_pretrained(base_model_path, **model_kwargs)
        logging.info("Base model loaded from %s", base_model_path)

        # 5) apply LoRA if present
        if os.path.isdir(adapter_path):
            cls._model_instance = PeftModel.from_pretrained(base, adapter_path, torch_dtype=base.dtype)
            logging.info("Loaded LoRA adapter from %s", adapter_path)
        else:
            cls._model_instance = base
            logging.info("No LoRA adapter found; using base model only")

        logging.info("Local model initialization complete")

    def __init__(self, base_model_path: str = None, use_few_shots: bool = False):
        if LocalModelParser._model_instance is None:
            LocalModelParser.initialize(base_model_path or os.getenv("LOCAL_BASE_MODEL_PATH"))

        self.model = LocalModelParser._model_instance
        self.tokenizer = LocalModelParser._tokenizer_instance
        self.use_few_shots = use_few_shots

        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        logging.info("Inference device: %s", self.device)

    def parse_tty_message(self, message: str) -> Dict[str, Any]:
        # 1) build prompt
        prompt = (
            build_few_shot_prompt(message)
            if self.use_few_shots
            else build_zero_shot_prompt(message)
        )

        # 2) tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)

        # 3) generate
        outputs = self.model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=200,
            do_sample=False,
            early_stopping=True,
        )
        raw = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 4) extract the JSON blob
        json_txt = self._extract_json(raw)

        if not json_txt:
            logging.warning("no JSON found; returning raw text")
            pretty = raw
        else:
            try:
                obj = json.loads(json_txt)
                pretty = json.dumps(obj, indent=2)
            except json.JSONDecodeError:
                logging.warning("invalid JSON; returning raw text")
                pretty = raw

        # 5) wrap in the same shape your routes expect
        return {"choices": [{"message": {"content": pretty}}]}

    @staticmethod
    def _extract_json(text: str) -> str:
        # first look for ```json ... ```
        m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return m.group(1)
        # otherwise the first {...}
        m2 = re.search(r"(\{.*?\})", text, re.DOTALL)
        return m2.group(1) if m2 else ""