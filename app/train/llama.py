import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import snapshot_download

# 0) Download *only* the safetensors files
repo_id = "meta-llama/Llama-2-7b-chat-hf"
local_dir = "./llama-2-7b-chat-safetensors"

snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    # only grab the .safetensors weight files (plus config & tokenizer)
    allow_patterns=["*.safetensors", "*.json", "tokenizer.model"],
    # avoid pulling down .bin shards
    ignore_patterns=["*.bin"]
)

# 1) tokenizer
tokenizer = AutoTokenizer.from_pretrained(local_dir)

# 2) model — float16 + automatic device map (will pick 'mps' on your Mac)
model = AutoModelForCausalLM.from_pretrained(
    local_dir,
    torch_dtype=torch.float16,
    device_map="auto",
    low_cpu_mem_usage=True,
    use_safetensors=True      # ensure we load the safetensors files
)

# 3) quick test
inputs = tokenizer("Hello, how are you?", return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))