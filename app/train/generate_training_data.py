#!/usr/bin/env python3
import os
import json
import tiktoken
import pdfplumber
from app.data.examples import load_few_shot_examples

# Configuration
PDF_PATH = os.path.join("app", "data", "OAG-MVT-MVA-DIV-Message-Types-and-Examples.pdf")
OUTPUT_JSONL = "training.jsonl"
CHUNK_TOKEN_SIZE = 1500     # chunk size in tokens
MAX_TOKENS = 4096           # model context limit

# 1) Extract the full PDF text
with pdfplumber.open(PDF_PATH) as pdf:
    full_text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)

# 2) Initialize the tokenizer
try:
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
except KeyError:
    enc = tiktoken.get_encoding("cl100k_base")

# 3) Chunk PDF into token-bounded spans
tokens = enc.encode(full_text)
chunks = [
    enc.decode(tokens[i : i + CHUNK_TOKEN_SIZE])
    for i in range(0, len(tokens), CHUNK_TOKEN_SIZE)
]

# 4) Build the few-shot examples section once
examples = load_few_shot_examples()
examples_section = ""
for ex in examples:
    examples_section += (
            "Input:\n```\n" + ex["message"] + "\n```\n"
                                              "Output:\n```json\n" + json.dumps(ex["parsed_json"], indent=2) + "\n```\n\n"
    )

# 5) Generate training records: one per chunk and per example
records = []
for chunk in chunks:
    for ex in examples:
        prompt = (
                "### INSTRUCTION\n"
                + chunk + "\n\n"
                          "### EXAMPLES\n"
                + examples_section
                + "### NOW PARSE THIS MESSAGE\n"
                "```" + ex["message"] + "```\n"
                "Respond with only the JSON payload."
        )
        completion = json.dumps(ex["parsed_json"])

        # Optional sanity check
        total_tokens = len(enc.encode(prompt)) + len(enc.encode(completion))
        if total_tokens > MAX_TOKENS:
            print(f"⚠️ Warning: record token count {total_tokens} exceeds {MAX_TOKENS}")

        records.append({
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": completion}
            ],
        })

# 6) Write out the JSONL file
with open(OUTPUT_JSONL, "w") as out:
    for rec in records:
        out.write(json.dumps(rec) + "\n")

print(f"Wrote {len(records)} records to {OUTPUT_JSONL}")