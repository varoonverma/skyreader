# app/service/remote_parser.py
import logging

import openai
from app.exception.exceptions import RemoteModelError

from app.service.base_parser import BaseParser
from app.service.prompt_builder import build_zero_shot_prompt

SYSTEM_INSTRUCTION = "Parse IATA Type B messages into structured JSON according to AHM specification."

class RemoteModelParser(BaseParser):
    """Parser that uses a remote LLM to parse IATA Type B messages"""

    def __init__(self, client=None, model: str = "openai"):
        self.client = client or openai
        if model == "openai":
            self.model_id = "gpt-3.5-turbo-16k"
        else:
            self.model_id = "ft:gpt-3.5-turbo-0125:myndful::BPq90znR"

    def parse_tty_message(self, tty_message: str) -> dict:
        prompt = build_zero_shot_prompt(tty_message)
        messages = [
            {"role": "system",  "content": SYSTEM_INSTRUCTION},
            {"role": "user",    "content": prompt}
        ]
        logging.info("Calling fine-tuned model %s with TTY message", self.model_id)
        try:
            resp = openai.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=0
            )
        except openai.OpenAIError as e:
            logging.error("OpenAI API error", exc_info=True)
            raise RemoteModelError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logging.error("Unexpected error calling OpenAI API", exc_info=True)
            raise RemoteModelError(f"Unexpected error: {str(e)}")

        # Pull out the assistant's reply
        assistant_msg = resp.choices[0].message.content

        # Return everything so the caller can post-process
        return {
            "message_id": resp.id,
            "usage": resp.usage.to_dict() if hasattr(resp, "usage") else {},
            "choices": [
                {
                    "index": resp.choices[0].index,
                    "message": {
                        "role": "assistant",
                        "content": assistant_msg
                    },
                    "finish_reason": resp.choices[0].finish_reason
                }
            ]
        }