# app/service/local_parser.py

import torch
import re
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from app.service.prompt_builder import build_few_shot_prompt, build_zero_shot_prompt

class LocalModelParser:
    """Parser that uses a local LLM to parse TTY messages"""

    def __init__(self, model_path="./llama-2-7b-chat-safetensors"):
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Initialize model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            use_safetensors=True
        )

    def parse_tty_message(self, message: str, use_few_shots: bool = False) -> dict:
        """Parse a TTY message using the local model"""
        # Get appropriate prompt
        prompt = build_few_shot_prompt(message) if use_few_shots else build_zero_shot_prompt(message)

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=False,
                repetition_penalty=1.1
            )

        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract JSON from response
        match = re.search(r'```json\s*(\{.*\})\s*```', response, re.DOTALL)
        json_text = match.group(1) if match else response

        try:
            parsed_obj = json.loads(json_text)
        except json.JSONDecodeError:
            parsed_obj = {"raw_content": response}

        # Return in the same format as the OpenAI implementation
        return {
            "choices": [
                {
                    "message": {"content": response},
                    "parsed_json": parsed_obj
                }
            ]
        }