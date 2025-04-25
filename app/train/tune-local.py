
#!/usr/bin/env python3
# app/train/tune-local.py

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

# Import your few-shot examples loader
from app.data.examples import load_few_shot_examples

# 1. Load few-shot examples
examples = load_few_shot_examples()

# 2. Build prompt-completion pairs
records = []
instruction = "Parse IATA Type B messages into structured JSON."
model_name = "meta-llama/Llama-2-7b-chat-hf"
# Load tokenizer and ensure eos_token exists
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
if tokenizer.eos_token is None:
    tokenizer.add_special_tokens({'eos_token': '</s>'})

for ex in examples:
    prompt = f"{instruction}\nMessage:\n{ex['message']}\nOutput:"
    completion = json.dumps(ex['parsed_json'])
    # Append end-of-text token for causal modeling
    records.append({"prompt": prompt, "completion": completion + tokenizer.eos_token})

# 3. Create a HuggingFace Dataset
dataset = Dataset.from_list(records)

def tokenize_fn(example):
    text = example['prompt'] + example['completion']
    return tokenizer(
        text,
        truncation=True,
        max_length=1024,
    )

# 5. Tokenize the dataset
tokenized = dataset.map(tokenize_fn, batched=False)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
)

# 6. Prepare LoRA config
lora_config = LoraConfig(
    task_type="CAUSAL_LM",
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.05,
)

# 7. Load base model and apply PEFT
base_model = AutoModelForCausalLM.from_pretrained(
    "./llama-2-7b-chat-safetensors",
    local_files_only=True,
    trust_remote_code=True,      # only if the model repo uses custom code
    torch_dtype=torch.float16,
    device_map="auto",
    low_cpu_mem_usage=True,
    use_safetensors=True,
)
model = get_peft_model(base_model, lora_config)

# 8. Training arguments
training_args = TrainingArguments(
    output_dir="./lora_tuned",
    learning_rate=1e-4,
    per_device_train_batch_size=1,
    num_train_epochs=3,
    save_total_limit=1,
    logging_steps=10,
    fp16=True,
)

# 9. Trainer setup
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

# 10. Fine-tune and save
if __name__ == "__main__":
    trainer.train()
    # Save full adapter
    model.save_pretrained("./lora_tuned")
    # Optionally save only the adapter weights
    state_dict = get_peft_model_state_dict(model)
    torch.save(state_dict, "./lora_tuned/adapter_state.pt")
    print("Local LLaMA model tuned with LoRA. Few-shot logic baked in.")
