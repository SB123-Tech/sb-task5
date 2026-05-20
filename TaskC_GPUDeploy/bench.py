import time, json
from openai import OpenAI

local_client = OpenAI(api_key="local", base_url="http://localhost:8000/v1")
cloud_client = OpenAI(api_key="sk-h9d8tMxaLmuysdwUAtgewbvtpTfjCVZKPTYDl6GrBpPm4QgV", base_url="https://api.agicto.cn/v1")

test_prompt = "请详细介绍番茄早疫病的发病原因、症状识别和防治方法，包括农业防治和化学防治的具体措施。"
results = {}

for name, client, model in [
    ("Local GPU (Qwen2.5-7B)", local_client, "Qwen/Qwen2.5-7B-Instruct"),
    ("Cloud API (gpt-4o-mini)", cloud_client, "gpt-4o-mini"),
]:
    times_list = []
    outputs = []
    print(f"Testing {name}...")
    for i in range(3):
        start = time.time()
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": test_prompt}],
                temperature=0.5,
                max_tokens=512
            )
            elapsed = time.time() - start
            content = resp.choices[0].message.content
            times_list.append(elapsed)
            outputs.append(content)
            print(f"  Trial {i+1}: {elapsed:.2f}s, {len(content)} chars")
        except Exception as e:
            print(f"  Trial {i+1}: ERROR - {e}")
            times_list.append(None)
            outputs.append("")

    valid_times = [t for t in times_list if t is not None]
    if valid_times:
        avg_time = sum(valid_times) / len(valid_times)
        avg_len = sum(len(o) for o in outputs) / len(outputs)
        results[name] = {"avg_time": avg_time, "avg_len": avg_len, "sample": outputs[0][:300] if outputs else ""}
        print(f"  Avg: {avg_time:.2f}s, {avg_len:.0f} chars")

print("\n=== RESULTS ===")
print(json.dumps(results, ensure_ascii=False, indent=2))
