import re
import json

class ParserService:
    def __init__(self, impl, compact=False):
        self.impl = impl
        self.compact = compact

    def parse_tty_message(self, message: str) -> dict:
        resp_dict = self.impl.parse_tty_message(message)

        content_text = resp_dict["choices"][0]["message"]["content"]

        if "JSON Output:" in content_text:
            match = re.search(r'(?s)JSON Output:\s*({.*})', content_text)
            if match:
                json_text = match.group(1)

                try:
                    content_json = json.loads(json_text)
                except json.JSONDecodeError:
                    # Auto-fix common JSON problems
                    fixed_text = self._fix_json(json_text)
                    try:
                        content_json = json.loads(fixed_text)
                    except json.JSONDecodeError as final_error:
                        raise ValueError(f"Failed to parse even after fixing: {final_error}")
            else:
                raise ValueError("JSON Output section found but no valid JSON extracted.")
        else:
            try:
                parsed_once = json.loads(content_text)
                content_json = json.loads(parsed_once) if isinstance(parsed_once, str) else parsed_once
            except json.JSONDecodeError:
                decoder = json.JSONDecoder()
                content_json, idx = decoder.raw_decode(content_text)

        resp_dict["choices"] = content_json
        return resp_dict

    def _fix_json(self, json_str: str) -> str:
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')

        # Add quotes around unquoted keys
        json_str = re.sub(r'(\s*)(\w+)\s*:', r'\1"\2":', json_str)

        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)

        # Auto-close unbalanced braces/brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        json_str += '}' * (open_braces - close_braces)

        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        json_str += ']' * (open_brackets - close_brackets)

        # Remove any extra content after the last closing brace or bracket
        last_brace = max(json_str.rfind('}'), json_str.rfind(']'))
        if last_brace != -1:
            json_str = json_str[:last_brace + 1]

        return json_str