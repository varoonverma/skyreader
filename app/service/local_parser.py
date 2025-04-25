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

        config = AutoConfig.from_pretrained(base_model_path)
        config.max_position_embeddings = max_length
        for a in ("n_positions", "n_ctx"):
            if hasattr(config, a):
                setattr(config, a, max_length)
        logging.info("Context length set to %d", max_length)

        cls._tokenizer_instance = AutoTokenizer.from_pretrained(
            base_model_path, use_fast=True, model_max_length=max_length
        )
        if cls._tokenizer_instance.eos_token is None:
            cls._tokenizer_instance.add_special_tokens({"eos_token": "</s>"})
        if cls._tokenizer_instance.pad_token is None:
            cls._tokenizer_instance.pad_token = cls._tokenizer_instance.eos_token

        model_kwargs: Dict[str, Any] = {
            "config": config,
            "torch_dtype": torch.float16,
            "device_map": "auto",
            "low_cpu_mem_usage": True,
            "use_safetensors": True,
        }

        base = AutoModelForCausalLM.from_pretrained(base_model_path, **model_kwargs)
        logging.info("Base model loaded from %s", base_model_path)

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

        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        logging.info("Inference device: %s", self.device)

    def parse_tty_message(self, message: str) -> Dict[str, Any]:
        prompt = (
            build_few_shot_prompt(message)
            if self.use_few_shots
            else build_zero_shot_prompt(message)
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)

        outputs = self.model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=400,  # Increase the maximum number of tokens
            do_sample=False,
            early_stopping=True,
        )
        raw = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract JSON from the raw output
        json_matches = re.findall(r'\{.*\}', raw, re.DOTALL)
        if json_matches:
            json_txt = max(json_matches, key=len)  # Get the longest JSON match
            try:
                obj = json.loads(json_txt)
                pretty = json.dumps(obj, indent=2)
            except json.JSONDecodeError:
                logging.warning("Invalid JSON found; attempting to fix")
                json_txt = self._fix_json(json_txt)
                try:
                    obj = json.loads(json_txt)
                    pretty = json.dumps(obj, indent=2)
                except json.JSONDecodeError:
                    logging.warning("Could not fix JSON; returning raw output")
                    pretty = raw
        else:
            logging.warning("No JSON found in the output; returning raw output")
            pretty = raw

        return {"choices": [{"message": {"content": pretty}}]}

    @staticmethod
    def _fix_json(json_str: str) -> str:
        # Attempt to fix common JSON errors
        json_str = json_str.replace("'", '"')  # Replace single quotes with double quotes
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Add quotes around keys
        json_str = re.sub(r',\s*\}', '}', json_str)  # Remove trailing commas
        return json_str

    @staticmethod
    def _extract_json(text: str) -> str:
        m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return m.group(1)
        m2 = re.search(r"(\{.*?\})", text, re.DOTALL)
        return m2.group(1) if m2 else ""