#!/usr/bin/env python3
"""Task C: vLLM/Flask 本地部署 vs 云端 API 性能对比 — NPG顶刊配色"""

import json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Font setup
for fname in ["Microsoft YaHei", "SimHei", "DejaVu Sans"]:
    try:
        fm.findfont(fname, fallback_to_default=False)
        plt.rcParams["font.family"] = fname
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False

# NPG Colors
NPG_RED    = "#E64B35"
NPG_BLUE   = "#4DBBD5"
NPG_GREEN  = "#00A087"
NPG_NAVY   = "#3C5488"
NPG_SALMON = "#F39B7F"
NPG_GRAY   = "#8491B4"

plt.rcParams.update({
    "axes.titlesize": 14, "axes.labelsize": 12,
    "axes.edgecolor": "#333333", "axes.linewidth": 0.8,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "figure.dpi": 150, "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Load benchmark results
with open("task_c_benchmark_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

local_key = [k for k in results if "Local" in k][0]
cloud_key = [k for k in results if "Cloud" in k][0]

local_time = results[local_key]["avg_time"]
cloud_time = results[cloud_key]["avg_time"]
local_len  = results[local_key]["avg_len"]
cloud_len  = results[cloud_key]["avg_len"]

print(f"Local GPU: {local_time:.2f}s, {local_len:.0f} chars")
print(f"Cloud API: {cloud_time:.2f}s, {cloud_len:.0f} chars")

# ═══════════════════════════════════════
# Fig 1: Response Time Comparison
# ═══════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
labels = ["Local GPU\n(Qwen2.5-7B, V100S)", "Cloud API\n(gpt-4o-mini)"]
times = [local_time, cloud_time]
colors_bar = [NPG_BLUE, NPG_GREEN]

bars = ax.bar(labels, times, color=colors_bar, edgecolor="white", linewidth=0.8, width=0.45)
for bar, t in zip(bars, times):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"{t:.1f}s", ha="center", fontsize=14, fontweight="bold", color=NPG_NAVY)

ax.set_ylabel("Average Response Time (s)", fontsize=12, color=NPG_NAVY)
ax.set_title("LLM Inference Speed: Local GPU vs Cloud API", fontsize=14, fontweight="bold", color=NPG_NAVY, pad=15)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.3, axis="y", linestyle="--", linewidth=0.5, color=NPG_GRAY)
ax.tick_params(colors=NPG_NAVY)
plt.tight_layout()
plt.savefig("task_c_response_time.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("Fig 1 saved: task_c_response_time.png")

# ═══════════════════════════════════════
# Fig 2: Dual-axis: Time + Output Length
# ═══════════════════════════════════════
fig, ax1 = plt.subplots(figsize=(8, 5))
x = np.arange(2)
width = 0.4

bars1 = ax1.bar(x - width/2, times, width, color=NPG_RED, edgecolor="white", linewidth=0.8, label="Response Time (s)")
ax1.set_ylabel("Response Time (s)", fontsize=12, color=NPG_RED)
ax1.tick_params(axis="y", colors=NPG_RED)
ax1.set_xticks(x)
ax1.set_xticklabels(["Local GPU", "Cloud API"], fontsize=11, color=NPG_NAVY)

for bar, t in zip(bars1, times):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"{t:.1f}s", ha="center", fontsize=12, fontweight="bold", color=NPG_RED)

ax2 = ax1.twinx()
lens = [local_len, cloud_len]
bars2 = ax2.bar(x + width/2, lens, width, color=NPG_BLUE, edgecolor="white", linewidth=0.8, label="Output Length (chars)")
ax2.set_ylabel("Output Length (characters)", fontsize=12, color=NPG_BLUE)
ax2.tick_params(axis="y", colors=NPG_BLUE)

for bar, l in zip(bars2, lens):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
            f"{l:.0f}", ha="center", fontsize=12, fontweight="bold", color=NPG_BLUE)

ax1.set_title("Local GPU vs Cloud API: Speed & Quality Trade-off", fontsize=14, fontweight="bold", color=NPG_NAVY, pad=15)
ax1.spines["top"].set_visible(False)
ax1.grid(True, alpha=0.3, axis="y", linestyle="--", linewidth=0.5, color=NPG_GRAY)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=True, fontsize=10)
plt.tight_layout()
plt.savefig("task_c_dual_comparison.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("Fig 2 saved: task_c_dual_comparison.png")

# ═══════════════════════════════════════
# Fig 3: Tokens-per-second comparison
# ═══════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
# Rough estimate: chars * 0.5 = tokens for Chinese
local_tps = local_len / local_time
cloud_tps = cloud_len / cloud_time

tps = [local_tps, cloud_tps]
bars = ax.bar(labels, tps, color=[NPG_BLUE, NPG_GREEN], edgecolor="white", linewidth=0.8, width=0.45)
for bar, t in zip(bars, tps):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{t:.1f}", ha="center", fontsize=14, fontweight="bold", color=NPG_NAVY)

ax.set_ylabel("Characters per Second", fontsize=12, color=NPG_NAVY)
ax.set_title("Throughput Comparison: Local vs Cloud", fontsize=14, fontweight="bold", color=NPG_NAVY, pad=15)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.3, axis="y", linestyle="--", linewidth=0.5, color=NPG_GRAY)
ax.tick_params(colors=NPG_NAVY)
plt.tight_layout()
plt.savefig("task_c_throughput.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("Fig 3 saved: task_c_throughput.png")

print("\n>>> Task C visualization complete! 3 NPG charts generated.")
