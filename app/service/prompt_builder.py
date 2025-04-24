import json

from app.data.examples import load_few_shot_examples

def build_few_shot_prompt(tty_message: str) -> str:
    examples = load_few_shot_examples()
    examples_text = ""
    for ex in examples:
        examples_text += (
            f"Input:\n```\n{ex['message']}\n```\n"
            f"Output:\n```json\n{json.dumps(ex['parsed_json'])}\n```\n\n"
        )
    prompt = (
            "You are SkyReader, a parser for aviation TTY messages.\n"
            "Parse the following message into JSON according to the examples.\n\n"
            f"{examples_text}"
            "Now parse this message:\n"
            "```\n" + tty_message + "\n```\n"
                                    "Respond with only valid JSON."
    )
    return prompt


def build_zero_shot_prompt(tty_message: str) -> str:
    return (
        f"Here is the raw message:\n```\n{tty_message}\n```\n\n"
        "Respond with valid JSON only, no additional text."
    )