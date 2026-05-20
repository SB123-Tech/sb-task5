#!/usr/bin/env python3
"""
任务 A：LLM API 初体验与 Prompt Engineering
- 调用 agicto API 进行对话
- 对比三种 prompt 策略的效果
- 农业场景实践
"""

import os
import time
from openai import OpenAI
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── 配置 ──
API_KEY = os.environ.get("AGICTO_API_KEY", "替换为你的API Key")
BASE_URL = "https://api.agicto.cn/v1"
MODEL = "qwen-plus"  # 或 gpt-4o-mini 等

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def chat_with_llm(messages, model=MODEL, temperature=0.7, max_tokens=1024):
    """发送消息给 LLM 并获取回复"""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def benchmark_prompt(system_prompt, user_prompt, label=""):
    """发送单次请求并记录耗时和回答"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    start = time.time()
    reply = chat_with_llm(messages, temperature=0.3)
    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"【{label}】")
    print(f"耗时: {elapsed:.1f}s")
    print(f"回答:\n{reply}")
    return reply


def main():
    print("=" * 60)
    print("  任务 A：LLM API 初体验与 Prompt Engineering")
    print("=" * 60)

    # ── 基础连通性测试 ──
    print("\n--- 连通性测试 ---")
    try:
        test_reply = chat_with_llm(
            [{"role": "user", "content": "你好，用一句话介绍自己。"}],
            temperature=0.3,
            max_tokens=100,
        )
        print(f"测试回复: {test_reply}")
        print("API 连接成功！")
    except Exception as e:
        print(f"API 连接失败: {e}")
        print("请检查 API Key 和网络连接。")
        return

    # ── 实验 1：基础 prompt（无角色设定） ──
    benchmark_prompt(
        system_prompt="",
        user_prompt="番茄叶子发黄是什么原因？",
        label="实验1：基础 Prompt",
    )

    # ── 实验 2：角色设定 + 结构化要求 ──
    benchmark_prompt(
        system_prompt="你是一位有20年经验的农业植保专家。请用专业但易懂的语言回答农民的病害问题。",
        user_prompt="番茄叶子发黄是什么原因？请从以下方面分析：1. 可能的病害类型 2. 非病害原因（营养、水分等）3. 如何区分 4. 防治建议",
        label="实验2：角色设定+结构化",
    )

    # ── 实验 3：Few-shot + Chain of Thought ──
    benchmark_prompt(
        system_prompt="你是一位农业植保专家。请按以下步骤分析：先观察症状特征，再对比已知病害，最后给出诊断和建议。",
        user_prompt="""请参考以下诊断示例，对新的症状进行分析：

示例1：
- 症状：番茄叶片出现同心轮纹状褐色病斑
- 诊断：早疫病（Alternaria solani）。轮纹状病斑是典型特征。
- 建议：移除病叶，喷施代森锰锌或苯醚甲环唑。

示例2：
- 症状：番茄果实出现水渍状褐色凹陷斑，高湿环境下有白色霉层
- 诊断：晚疫病（Phytophthora infestans）。水渍状斑和白色霉层是关键特征。
- 建议：控制湿度，喷施烯酰吗啉或霜脲氰。

新症状：番茄叶片边缘出现 V 形黄褐色坏死斑，病健交界明显，多从下部叶片开始。
请逐步分析。""",
        label="实验3：Few-shot+逐步推理",
    )

    # ── 多轮对话 ──
    print("\n--- 多轮对话测试 ---")
    messages = [
        {
            "role": "system",
            "content": "你是农业植保专家，专门帮助农民诊断和防治作物病害。回答要专业、实用、有依据。",
        }
    ]

    def multi_turn_chat(user_input):
        messages.append({"role": "user", "content": user_input})
        reply = chat_with_llm(messages, temperature=0.5)
        messages.append({"role": "assistant", "content": reply})
        print(f"\n你: {user_input}")
        print(f"专家: {reply}")
        return reply

    multi_turn_chat(
        "我家的番茄最近叶子开始出现褐色斑点，集中在下部叶片，是怎么回事？"
    )
    multi_turn_chat("用什么药比较好？我现在手头有代森锰锌。")
    multi_turn_chat("打药的频率应该是多少？")

    # ── 可视化对比 ──
    print("\n--- 生成对比图 ---")
    experiments = ["基础 Prompt", "角色+结构化", "Few-shot+推理"]
    quality_scores = [3, 7, 9]  # 主观评分 1-10

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(
        experiments, quality_scores, color=["#4e79a7", "#f28e2b", "#e15759"], edgecolor="black"
    )
    for bar, score in zip(bars, quality_scores):
        ax.text(
            score + 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{score}/10",
            va="center",
            fontsize=12,
            fontweight="bold",
        )
    ax.set_xlabel("回答质量评分 (主观)")
    ax.set_title("Prompt Engineering 效果对比")
    ax.set_xlim(0, 11)
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    plt.savefig("task_a_prompt_comparison.png", dpi=150, bbox_inches="tight")
    print("对比图已保存到 task_a_prompt_comparison.png")

    print("\n--- 任务 A 完成！---")
    print("思考题:")
    print("1. 为什么角色设定能显著提升 LLM 的回答质量？")
    print("2. Few-shot learning 中，示例的数量和质量哪个更重要？")
    print("3. 在农业场景下，结构化输出为什么特别重要？")


if __name__ == "__main__":
    main()
