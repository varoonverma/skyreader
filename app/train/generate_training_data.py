#!/usr/bin/env python3
import json

import tiktoken

from app.data.examples import load_few_shot_examples

# Configuration
OUTPUT_JSONL = "training.jsonl"
MAX_TOKENS = 4096           # model context limit

# 2) Initialize the tokenizer
try:
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
except KeyError:
    enc = tiktoken.get_encoding("cl100k_base")


# System instruction for zero-shot fine-tuning
SYSTEM_INSTRUCTION = (
    "Parse IATA Type B messages into structured JSON according to AHM specification."
)

# 5) Generate training records: one per example
records = []
for ex in load_few_shot_examples():
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user",   "content": ex["message"]},
        {"role": "assistant", "content": json.dumps(ex["parsed_json"])},
    ]

    # Optional sanity check
    total_tokens = sum(len(enc.encode(m["content"])) for m in messages)
    if total_tokens > MAX_TOKENS:
        print(f"⚠️ Warning: record token count {total_tokens} exceeds {MAX_TOKENS}")

    records.append({"messages": messages})

# 6) Write out the JSONL file
with open(OUTPUT_JSONL, "w") as out:
    for rec in records:
        out.write(json.dumps(rec) + "\n")

print(f"Wrote {len(records)} records to {OUTPUT_JSONL}")