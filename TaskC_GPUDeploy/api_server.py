import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import time

app = Flask(__name__)

print("Loading model Qwen/Qwen3-8B...", flush=True)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-8B",
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
model.eval()
print("Model loaded successfully!", flush=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/v1/models", methods=["GET"])
def list_models():
    return jsonify({"data": [{"id": "Qwen/Qwen3-8B", "object": "model"}], "object": "list"})


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    data = request.json
    messages = data.get("messages", [])
    temperature = data.get("temperature", 0.5)
    max_tokens = data.get("max_tokens", 512)

    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt += f"<|system|>\n{content}<|end|>\n"
        elif role == "user":
            prompt += f"<|user|>\n{content}<|end|>\n"
        elif role == "assistant":
            prompt += f"<|assistant|>\n{content}<|end|>\n"
    prompt += "<|assistant|>\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id
        )
    generated = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    elapsed = time.time() - start
    print(f"Generated {len(generated)} chars in {elapsed:.1f}s", flush=True)

    return jsonify({
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "Qwen/Qwen3-8B",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": generated},
            "finish_reason": "stop"
        }],
        "usage": {"completion_tokens": len(generated.split()), "total_tokens": 0}
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
