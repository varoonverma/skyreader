# app/service/prompt_builder.py

from typing import List, Dict
import json

# This is the same text you already have in LocalModelParser.SYSTEM_INSTRUCTION
SYSTEM_INSTRUCTION = (
    "Parse IATA Type B messages into structured JSON according to AHM specification."
)

# Load your five-shot examples (adjust path if needed)
# examples.py should export a list called `EXAMPLES`
# where each entry is: {"message": "...", "parsed_json": { ... }}
from app.data.examples import load_few_shot_examples  # e.g. [{"message": "...", "parsed_json": {...}}, ...]

def build_zero_shot_prompt(msg: str) -> str:
    """
    Zero-shot: just instruction + the new message.
    """
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"### NOW PARSE THIS MESSAGE\n"
        f"{msg}\n\n"
        f"Respond with only valid JSON."
    )

def build_few_shot_prompt(msg: str) -> str:
    """
    Few-shot: instruction + all your examples + the new message.
    """
    # Build the examples section:
    #    for each example, show the raw message and then the JSON.
    parts: List[str] = [SYSTEM_INSTRUCTION, "\n### EXAMPLES"]
    for ex in load_few_shot_examples():
        # raw input
        parts.append(f"\n```\n{ex['message']}\n```")
        # expected JSON
        pretty = json.dumps(ex["parsed_json"], indent=2)
        parts.append(f"\n```json\n{pretty}\n```")
    # now the new message
    parts.append("\n### NOW PARSE THIS MESSAGE")
    parts.append(f"\n{msg}\n\nRespond with only valid JSON.")
    return "\n".join(parts)


# import json
#
# from app.data.examples import load_few_shot_examples
#
# def build_few_shot_prompt(tty_message: str) -> str:
#     examples = load_few_shot_examples()
#     examples_text = ""
#     for ex in examples:
#         examples_text += (
#             f"Input:\n```\n{ex['message']}\n```\n"
#             f"Output:\n```json\n{json.dumps(ex['parsed_json'])}\n```\n\n"
#         )
#     prompt = (
#             "You are SkyReader, a parser for aviation TTY messages.\n"
#             "Parse the following message into JSON according to the examples.\n\n"
#             f"{examples_text}"
#             "Now parse this message:\n"
#             "```\n" + tty_message + "\n```\n"
#                                     "Respond with only valid JSON."
#     )
#     return prompt
#
#
# def build_zero_shot_prompt(tty_message: str) -> str:
#     return (
#         f"Here is the raw message:\n```\n{tty_message}\n```\n\n"
#         "Respond with valid JSON only, no additional text."
#     )