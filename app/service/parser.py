# app/service/parser.py
import openai
import re
import json
from app.service.prompt_builder import build_few_shot_prompt, build_zero_shot_prompt

def parse_tty_message(message: str, use_few_shots: bool = True) -> dict:
    prompt = build_few_shot_prompt(message) if use_few_shots else build_zero_shot_prompt(message)
    try:
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
    except openai.error.OpenAIError as e:
        # bubble up a RuntimeError with a clear message
        raise RuntimeError(f"OpenAI API error: {e}")
        # Parse each choice's content

    resp_dict = resp.to_dict()

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
    return resp_dict