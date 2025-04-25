# app/service/local_parser.py

import torch
import re
import json
import logging
from typing import Dict, Any
import os

from app.service.base_parser import BaseParser
from app.service.prompt_builder import build_few_shot_prompt, build_zero_shot_prompt
from app.exception.exceptions import RemoteModelError

class LocalModelParser(BaseParser):
    """Parser that uses a local LLM to parse IATA Type B messages"""

    # Class variable to hold the loaded model instance
    _model_instance = None
    _tokenizer_instance = None

    @classmethod
    def initialize(cls, model_name_or_path="microsoft/phi-2"):
        """
        Initialize the model and tokenizer at application startup

        Args:
            model_name_or_path: Can be a HuggingFace model ID or local path
                                Default is microsoft/phi-2 which works well with tokenizers
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logging.info(f"Loading tokenizer from {model_name_or_path}")
            cls._tokenizer_instance = AutoTokenizer.from_pretrained(
                model_name_or_path,
                use_fast=True,  # Use fast tokenizer (based on tokenizers library)
            )

            # Set padding token if needed
            if cls._tokenizer_instance.pad_token is None:
                cls._tokenizer_instance.pad_token = cls._tokenizer_instance.eos_token

            logging.info(f"Loading model from {model_name_or_path}")
            # Configure device placement based on available hardware
            device_map = "auto"
            torch_dtype = torch.float16

            # For smaller or less capable devices, use more conservative settings
            if os.environ.get("LOW_MEMORY", "false").lower() == "true":
                device_map = {"": 0}  # Place on first GPU only
                torch_dtype = torch.float32  # Use regular precision if memory limited

            cls._model_instance = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                torch_dtype=torch_dtype,
                device_map=device_map,
                use_safetensors=True,
                low_cpu_mem_usage=True,
            )
            logging.info("Model loaded successfully")

        except Exception as e:
            logging.error(f"Failed to initialize local model: {str(e)}", exc_info=True)
            raise

    def __init__(self, model_name_or_path="microsoft/phi-2", use_few_shots: bool = False):
        """
        Initialize parser with reference to the shared model

        Args:
            model_name_or_path: HuggingFace model ID or path (used only if model isn't already loaded)
            use_few_shots: Whether to use few-shot examples in prompts
        """
        # If model not loaded yet, load it
        if LocalModelParser._model_instance is None or LocalModelParser._tokenizer_instance is None:
            logging.warning("Model not pre-loaded, loading now - this may cause delay")
            LocalModelParser.initialize(model_name_or_path)

        self.model = LocalModelParser._model_instance
        self.tokenizer = LocalModelParser._tokenizer_instance
        self.use_few_shots = use_few_shots

    def parse_tty_message(self, tty_message: str) -> Dict[str, Any]:
        """Parse a TTY message using the local model"""
        try:
            # Get appropriate prompt
            prompt = build_few_shot_prompt(tty_message) if self.use_few_shots else build_zero_shot_prompt(tty_message)

            # Create system message prefix for better instruction following
            system_msg = "Parse IATA Type B messages into structured JSON according to AHM specification."
            full_prompt = f"{system_msg}\n\n{prompt}"

            # Tokenize input
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    do_sample=False,
                    temperature=0.1,
                    repetition_penalty=1.1
                )

            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract model's reply (remove the prompt)
            response = response[len(full_prompt):].strip()

            # Generate a unique ID for this response
            import uuid
            response_id = str(uuid.uuid4())

            # Extract JSON from response
            try:
                json_text = self._extract_json_from_text(response)
                parsed_obj = json.loads(json_text)
            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"Failed to parse JSON from model response: {str(e)}")
                parsed_obj = {"error": "Failed to parse valid JSON", "raw_response": response}

            # Return in the same format as the OpenAI implementation
            return {
                "message_id": response_id,
                "usage": {
                    "prompt_tokens": inputs.input_ids.shape[1],
                    "completion_tokens": outputs.shape[1] - inputs.input_ids.shape[1],
                    "total_tokens": outputs.shape[1]
                },
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response
                        },
                        "finish_reason": "stop",
                        "parsed_json": parsed_obj
                    }
                ]
            }

        except Exception as e:
            logging.error(f"Error in local model parsing: {str(e)}", exc_info=True)
            raise RemoteModelError(f"Local model error: {str(e)}")

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from model response text"""
        # Try to extract JSON from markdown code block
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)

        # Try to find JSON object with curly braces
        json_object_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_object_match:
            return json_object_match.group(1)

        # If no JSON pattern found, return the raw text
        # (this will likely fail to parse as JSON)
        return text