import re
import json

class ParserService:
    def __init__(self, impl, compact=False):
        self.impl = impl
        self.compact = compact

    def parse_tty_message(self, message: str) -> dict:
        resp_dict = self.impl.parse_tty_message(message)

        content_text = resp_dict["choices"][0]["message"]["content"]

        try:
            # Try normal load first
            parsed_once = json.loads(content_text)
            content_json = json.loads(parsed_once) if isinstance(parsed_once, str) else parsed_once

        except json.JSONDecodeError as e:
            # Handle double-JSON with multiple top-level objects
            try:
                decoder = json.JSONDecoder()
                content_json, idx = decoder.raw_decode(content_text)
            except Exception as inner_e:
                raise ValueError(f"Failed to parse content: {inner_e}") from e

        resp_dict["choices"] = content_json
        return resp_dict