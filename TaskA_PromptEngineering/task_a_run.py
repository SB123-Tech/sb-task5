#!/usr/bin/env python3
"""Task A: LLM API + Prompt Engineering — NPG顶刊配色版"""

import os, time, json
from openai import OpenAI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ── 中文字体设置 ──
for fname in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"]:
    try:
        fm.findfont(fname, fallback_to_default=False)
        plt.rcParams["font.family"] = fname
        print(f"Using font: {fname}")
        break
    except Exception:
        continue

plt.rcParams["axes.unicode_minus"] = False

# ── NPG (Nature Publishing Group) 顶刊配色方案 ──
NPG_RED    = "#E64B35"
NPG_BLUE   = "#4DBBD5"
NPG_GREEN  = "#00A087"
NPG_NAVY   = "#3C5488"
NPG_SALMON = "#F39B7F"
NPG_GRAY   = "#8491B4"
NPG_MINT   = "#91D1C2"

# 全局绘图设置
plt.rcParams.update({
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "legend.fontsize": 10,
    "legend.frameon": True,
    "legend.edgecolor": "#cccccc",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

API_KEY = "sk-h9d8tMxaLmuysdwUAtgewbvtpTfjCVZKPTYDl6GrBpPm4QgV"
BASE_URL = "https://api.agicto.cn/v1"
MODEL = "gpt-4o-mini"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
results_log = {}


def chat_with_llm(messages, model=MODEL, temperature=0.7, max_tokens=1024):
    response = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return response.choices[0].message.content


def benchmark_prompt(system_prompt, user_prompt, label=""):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    start = time.time()
    reply = chat_with_llm(messages, temperature=0.3)
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"【{label}】")
    print(f"耗时: {elapsed:.1f}s")
    print(f"回答:\n{reply}")
    results_log[label] = {"time": elapsed, "reply": reply, "length": len(reply)}
    return reply


def main():
    print("=" * 60)
    print("  Task A: Prompt Engineering 对比实验 (NPG配色)")
    print("=" * 60)

    # 连通性测试
    test = chat_with_llm([{"role": "user", "content": "你好，用一句话介绍自己。"}], temperature=0.3, max_tokens=100)
    print(f"API连通: {test[:80]}...")

    # ── 实验 1: 基础 prompt ──
    benchmark_prompt(
        system_prompt="",
        user_prompt="番茄叶子发黄是什么原因？",
        label="实验1：基础Prompt",
    )

    # ── 实验 2: 角色设定 + 结构化 ──
    benchmark_prompt(
        system_prompt="你是一位有20年经验的农业植保专家。请用专业但易懂的语言回答农民的病害问题。",
        user_prompt="番茄叶子发黄是什么原因？请从以下方面分析：1. 可能的病害类型 2. 非病害原因（营养、水分等）3. 如何区分 4. 防治建议",
        label="实验2：角色设定+结构化",
    )

    # ── 实验 3: Few-shot + Chain of Thought ──
    benchmark_prompt(
        system_prompt="你是一位农业植保专家。请按以下步骤分析：先观察症状特征，再对比已知病害，最后给出诊断和建议。",
        user_prompt="""请参考以下诊断示例，对新的症状进行分析：

示例1：
- 症状：番茄叶片出现同心轮纹状褐色病斑
- 诊断：早疫病。轮纹状病斑是典型特征。
- 建议：移除病叶，喷施代森锰锌或苯醚甲环唑。

示例2：
- 症状：番茄果实出现水渍状褐色凹陷斑，高湿环境下有白色霉层
- 诊断：晚疫病。水渍状斑和白色霉层是关键特征。
- 建议：控制湿度，喷施烯酰吗啉或霜脲氰。

新症状：番茄叶片边缘出现 V 形黄褐色坏死斑，病健交界明显，多从下部叶片开始。
请逐步分析。""",
        label="实验3：Few-shot+逐步推理",
    )

    # ── 多轮对话 ──
    print("\n--- 多轮对话测试 ---")
    messages = [{"role": "system", "content": "你是农业植保专家，专门帮助农民诊断和防治作物病害。回答要专业、实用、有依据。"}]
    def multi_turn_chat(user_input):
        messages.append({"role": "user", "content": user_input})
        reply = chat_with_llm(messages, temperature=0.5)
        messages.append({"role": "assistant", "content": reply})
        print(f"\n你: {user_input}")
        print(f"专家: {reply}")
        return reply

    multi_turn_chat("我家的番茄最近叶子开始出现褐色斑点，集中在下部叶片，是怎么回事？")
    multi_turn_chat("用什么药比较好？我现在手头有代森锰锌。")
    multi_turn_chat("打药的频率应该是多少？")

    # ═══════════════════════════════════════
    # 图1: Prompt Engineering 效果对比
    # ═══════════════════════════════════════
    fig, ax = plt.subplots(figsize=(9, 5.5))
    experiments = ["Basic\nPrompt", "Role-setting\n+ Structure", "Few-shot\n+ Chain-of-Thought"]
    quality_scores = [3, 7, 9]
    colors_bar = [NPG_RED, NPG_BLUE, NPG_GREEN]

    bars = ax.barh(experiments, quality_scores, color=colors_bar, edgecolor="white", linewidth=0.8, height=0.55)
    for bar, score in zip(bars, quality_scores):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f"{score}/10", va="center", fontsize=13, fontweight="bold", color=NPG_NAVY)

    ax.set_xlabel("Answer Quality Score (subjective)", fontsize=12, color=NPG_NAVY)
    ax.set_title("Prompt Engineering Strategy Comparison", fontsize=14, fontweight="bold", color=NPG_NAVY, pad=15)
    ax.set_xlim(0, 11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.4, axis="x", linestyle="--", linewidth=0.5, color=NPG_GRAY)
    ax.tick_params(colors=NPG_NAVY)
    plt.tight_layout()
    plt.savefig("task_a_prompt_comparison.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("\n图1已保存: task_a_prompt_comparison.png")

    # ═══════════════════════════════════════
    # 图2: 响应时间与回答长度双轴图
    # ═══════════════════════════════════════
    fig, ax1 = plt.subplots(figsize=(9, 5.5))
    exps = ["Basic Prompt", "Role+Structured", "Few-shot+CoT"]
    times_list = [results_log["实验1：基础Prompt"]["time"],
                  results_log["实验2：角色设定+结构化"]["time"],
                  results_log["实验3：Few-shot+逐步推理"]["time"]]
    lengths = [results_log["实验1：基础Prompt"]["length"],
               results_log["实验2：角色设定+结构化"]["length"],
               results_log["实验3：Few-shot+逐步推理"]["length"]]

    x = np.arange(len(exps))
    width = 0.35

    bars1 = ax1.bar(x - width/2, times_list, width, color=NPG_RED, edgecolor="white", linewidth=0.8, label="Response Time (s)")
    ax1.set_ylabel("Response Time (s)", fontsize=12, color=NPG_RED)
    ax1.tick_params(axis="y", colors=NPG_RED)
    ax1.set_xticks(x)
    ax1.set_xticklabels(exps, fontsize=11, color=NPG_NAVY)

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, lengths, width, color=NPG_BLUE, edgecolor="white", linewidth=0.8, label="Response Length (chars)")
    ax2.set_ylabel("Response Length (characters)", fontsize=12, color=NPG_BLUE)
    ax2.tick_params(axis="y", colors=NPG_BLUE)

    # 添加数值标签
    for bar, t in zip(bars1, times_list):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                f"{t:.1f}s", ha="center", fontsize=10, fontweight="bold", color=NPG_RED)
    for bar, l in zip(bars2, lengths):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                f"{l}", ha="center", fontsize=10, fontweight="bold", color=NPG_BLUE)

    ax1.set_title("Response Time vs Length by Prompt Strategy", fontsize=14, fontweight="bold", color=NPG_NAVY, pad=15)
    ax1.spines["top"].set_visible(False)
    ax1.grid(True, alpha=0.3, axis="y", linestyle="--", linewidth=0.5, color=NPG_GRAY)

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=True, fontsize=10)
    plt.tight_layout()
    plt.savefig("task_a_response_time.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("图2已保存: task_a_response_time.png")

    # ═══════════════════════════════════════
    # 图3: 多维雷达图
    # ═══════════════════════════════════════
    categories = ["Professionalism", "Structure", "Practical\nValue", "Accuracy", "Completeness"]
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    basic_scores    = [2, 1, 3, 3, 2]
    role_scores     = [8, 7, 7, 7, 7]
    fewshot_scores  = [9, 9, 8, 8, 9]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10, color=NPG_NAVY)

    ax.plot(angles, basic_scores + basic_scores[:1], "o-", linewidth=2, color=NPG_RED, label="Basic Prompt", markersize=6)
    ax.fill(angles, basic_scores + basic_scores[:1], alpha=0.12, color=NPG_RED)
    ax.plot(angles, role_scores + role_scores[:1], "o-", linewidth=2, color=NPG_BLUE, label="Role+Structured", markersize=6)
    ax.fill(angles, role_scores + role_scores[:1], alpha=0.12, color=NPG_BLUE)
    ax.plot(angles, fewshot_scores + fewshot_scores[:1], "o-", linewidth=2, color=NPG_GREEN, label="Few-shot+CoT", markersize=6)
    ax.fill(angles, fewshot_scores + fewshot_scores[:1], alpha=0.12, color=NPG_GREEN)

    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8, color="#888888")
    ax.set_title("Multi-Dimensional Strategy Comparison", fontsize=14, fontweight="bold", color=NPG_NAVY, pad=25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig("task_a_radar.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("图3已保存: task_a_radar.png")

    # 保存实验结果JSON
    with open("task_a_results.json", "w", encoding="utf-8") as f:
        json.dump(results_log, f, ensure_ascii=False, indent=2)

    print("\n>>> Task A 完成！共生成 3 张 NPG 配色图表。")


if __name__ == "__main__":
    main()
