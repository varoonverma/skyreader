import tiktoken
from PyPDF2 import PdfReader
from app.data.examples import load_few_shot_examples
import json

# 1) Extract all text from the PDF
reader = PdfReader("app/data/OAG-MVT-MVA-DIV-Message-Types-and-Examples.pdf")
full_text = ""
for page in reader.pages:
    txt = page.extract_text()
    if txt:
        full_text += txt + "\n\n"

# 2) Choose the right encoding for GPT-3.5-Turbo
try:
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
except KeyError:
    enc = tiktoken.get_encoding("cl100k_base")

# 3) Count tokens
tokens = enc.encode(full_text)
print(f"Extracted {len(full_text)} characters.")
print(f"GPT-3.5-Turbo token count: {len(tokens)}")


# 4) Count tokens for few-shot examples
examples = load_few_shot_examples()
total_example_tokens = 0
print("\nFew-shot examples token counts:")
for i, ex in enumerate(examples, start=1):
    # count tokens for prompt (message) and completion (parsed_json)
    prompt_tokens = len(enc.encode(ex["message"]))
    completion_text = json.dumps(ex["parsed_json"])
    completion_tokens = len(enc.encode(completion_text))
    example_tokens = prompt_tokens + completion_tokens
    total_example_tokens += example_tokens
    print(f" Example {i}: prompt={prompt_tokens}, completion={completion_tokens}, total={example_tokens}")
print(f"Total tokens for all {len(examples)} examples: {total_example_tokens}")

# Load tokenizer
enc = tiktoken.encoding_for_model("gpt-3.5-turbo")