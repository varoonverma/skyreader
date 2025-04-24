# app/service/parser.py
import json
import re

from app.service.base_parser import BaseParser


class ParserService:
    def __init__(
            self,
            impl: BaseParser,
            compact: bool = True
    ):
        self.impl = impl
        self.compact = compact

    def parse_tty_message(self, message: str) -> dict:
        resp_dict = self.impl.parse_tty_message(message)

        # Enhance each choice with parsed JSON content
        parsed_choices = []
        for choice in resp_dict["choices"]:
            raw = choice["message"]["content"]
            match = re.search(r'```json\s*(\{.*\})\s*```', raw, re.DOTALL)
            json_text = match.group(1) if match else raw
            try:
                parsed_obj = json.loads(json_text)
            except json.JSONDecodeError:
                parsed_obj = {"raw_content": raw}
                # attach parsed JSON to this choice
            choice["parsed_json"] = parsed_obj
            parsed_choices.append(choice)
        # Replace the original choices with enriched ones
        resp_dict["choices"] = parsed_choices
        resp_dict_compact = resp_dict["choices"][0]["parsed_json"]

        return resp_dict_compact if self.compact else resp_dict