#!/usr/bin/env python3

import json
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
import torch

from app.data.examples import load_few_shot_examples

examples = load_few_shot_examples()

records = []
instruction = "Parse IATA Type B messages into structured JSON according to the format in the examples."

import os

model_name = "./llama-2-7b-chat-safetensors"

tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    tokenizer_file=os.path.join(model_name, "tokenizer.json"),
    local_files_only=True,
    use_fast=True
)


if tokenizer.eos_token is None:
    tokenizer.add_special_tokens({'eos_token': '</s>'})

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

for ex in examples:
    prompt = f"{instruction}\nMessage:\n{ex['message']}\nJSON Output:"
    completion = json.dumps(ex['parsed_json'], indent=2)
    records.append({"prompt": prompt, "completion": completion + tokenizer.eos_token})

dataset = Dataset.from_list(records)

def tokenize_fn(example):
    text = example['prompt'] + example['completion']
    return tokenizer(
        text,
        truncation=True,
        max_length=1024,
    )

tokenized = dataset.map(tokenize_fn, batched=False)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
)

lora_config = LoraConfig(
    task_type="CAUSAL_LM",
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.05,
)

base_model = AutoModelForCausalLM.from_pretrained(
    "./llama-2-7b-chat-safetensors",
    local_files_only=True,
    trust_remote_code=True,
    torch_dtype=torch.float16,
    device_map="auto",
    low_cpu_mem_usage=True,
    use_safetensors=True,
)
model = get_peft_model(base_model, lora_config)

device_type = (
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)
use_fp16 = device_type == "cuda"
use_bf16 = device_type == "mps"
print(f"⚙️ Training on {device_type}, fp16={use_fp16}, bf16={use_bf16}")

training_args = TrainingArguments(
    output_dir="./lora_tuned",
    learning_rate=1e-4,
    per_device_train_batch_size=1,
    num_train_epochs=5,
    save_total_limit=2,
    logging_steps=10,
    fp16=use_fp16,
    bf16=use_bf16,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

if __name__ == "__main__":
    trainer.train()
    model.save_pretrained("./lora_tuned")
    state_dict = get_peft_model_state_dict(model)
    torch.save(state_dict, "./lora_tuned/adapter_state.pt")
    print("✅ Local LLaMA model tuned with LoRA. Few-shot logic baked into the adapter.")