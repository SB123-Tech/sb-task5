#!/usr/bin/env python3
"""Task B: RAG — NPG顶刊配色版 (使用 bge-small-zh-v1.5)"""

import os, glob, json
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# Font
for fname in ["Microsoft YaHei", "SimHei"]:
    try:
        fm.findfont(fname, fallback_to_default=False)
        plt.rcParams["font.family"] = fname
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False

# NPG Colors
NPG_RED = "#E64B35"; NPG_BLUE = "#4DBBD5"; NPG_GREEN = "#00A087"
NPG_NAVY = "#3C5488"; NPG_SALMON = "#F39B7F"; NPG_GRAY = "#8491B4"

plt.rcParams.update({
    "axes.titlesize":14,"axes.labelsize":12,"axes.edgecolor":"#333333","axes.linewidth":0.8,
    "xtick.labelsize":10,"ytick.labelsize":10,"legend.fontsize":10,
    "figure.dpi":150,"savefig.dpi":300,"savefig.bbox":"tight"
})

API_KEY = "sk-h9d8tMxaLmuysdwUAtgewbvtpTfjCVZKPTYDl6GrBpPm4QgV"
BASE_URL = "https://api.agicto.cn/v1"
MODEL = "gpt-4o-mini"
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

print("="*60)
print("  Task B: RAG System (bge-small-zh-v1.5 + NPG)")
print("="*60)

# Load docs
def load_documents(directory):
    docs = []
    for path in glob.glob(os.path.join(directory, "**/*.md"), recursive=True):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        rel = os.path.relpath(path, directory)
        docs.append({"source": rel, "content": content, "title": os.path.basename(path)})
    print(f"Loaded {len(docs)} documents")
    for d in docs:
        print(f"  - {d['source']} ({len(d['content'])} chars)")
    return docs

docs = load_documents("knowledge_base")

# Chunk
def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para: continue
        if len(current) + len(para) < chunk_size:
            current += "\n\n" + para if current else para
        else:
            if current: chunks.append(current)
            words = current.split()
            current = (" ".join(words[-overlap:]) if len(words) > overlap else current) + "\n\n" + para
    if current: chunks.append(current)
    return chunks

all_chunks = []
for doc in docs:
    chunks = chunk_text(doc["content"])
    for i, chunk in enumerate(chunks):
        all_chunks.append({"text": chunk, "source": doc["source"], "title": doc["title"], "chunk_id": f"{doc['source']}_{i}"})
print(f"Total chunks: {len(all_chunks)}")

# Build vector DB with bge-small-zh-v1.5
print(f"\nBuilding vector DB with {EMBED_MODEL}...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

try:
    chroma_client.delete_collection(name="agri_knowledge")
    print("Deleted old collection")
except Exception:
    pass

collection = chroma_client.create_collection(name="agri_knowledge", embedding_function=embedding_func, metadata={"description": "agriculture KB"})
print("Created new collection")
texts = [c["text"] for c in all_chunks]
ids = [c["chunk_id"] for c in all_chunks]
metadatas = [{"source": c["source"], "title": c["title"]} for c in all_chunks]

for i in range(0, len(texts), 100):
    batch_end = min(i+100, len(texts))
    collection.add(documents=texts[i:batch_end], ids=ids[i:batch_end], metadatas=metadatas[i:batch_end])
print(f"Stored {len(texts)} chunks in vector DB")

# RAG QA
rag_results = {}

def retrieve_and_answer(question, top_k=3):
    results = collection.query(query_texts=[question], n_results=top_k)
    print(f"\nQ: {question}")
    context_parts = []
    retrieved_info = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        rel = 1 - dist
        print(f"  [{meta['source']}] relevance: {rel:.3f}")
        context_parts.append(f"Source: {meta['source']}\nContent: {doc}")
        retrieved_info.append({"source": meta["source"], "relevance": float(rel), "snippet": doc[:200]})

    context = "\n\n---\n\n".join(context_parts)
    system_prompt = """You are an agricultural expert. Answer based on reference materials.
Rules: 1. Only use provided references 2. Admit if references insufficient 3. Be practical 4. Cite sources"""

    answer = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":system_prompt},
                  {"role":"user","content":f"References:\n{context}\n\nQuestion: {question}"}],
        temperature=0.3, max_tokens=1024
    ).choices[0].message.content

    print(f"Answer: {answer[:150]}...")
    rag_results[question] = {"answer": answer, "retrieved": retrieved_info}
    return answer, retrieved_info

questions = [
    "番茄早疫病的症状和防治方法是什么？",
    "番茄叶片出现褐色斑点可能是什么病？",
    "代森锰锌的使用方法和注意事项是什么？",
]
for q in questions:
    retrieve_and_answer(q)
    print("="*60)

# RAG vs no-RAG
print("\n--- RAG vs No-RAG Comparison ---")
test_q = "番茄早疫病用什么药治疗？推荐剂量是多少？"

answer_no_rag = client.chat.completions.create(
    model=MODEL, messages=[{"role":"system","content":"You are an agricultural expert."},
                            {"role":"user","content":test_q}],
    temperature=0.5, max_tokens=512
).choices[0].message.content

answer_with_rag, rag_info = retrieve_and_answer(test_q)

print(f"\n[No RAG]: {answer_no_rag[:200]}...")
print(f"\n[With RAG]: {answer_with_rag[:200]}...")

# ═══════════ CHARTS ═══════════

# Fig 1: Knowledge base composition
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
cats = {}
for d in docs:
    cat = d["source"].split("/")[0] if "/" in d["source"] else "root"
    cats[cat] = cats.get(cat, 0) + 1

pie_colors = [NPG_RED, NPG_BLUE, NPG_GREEN, NPG_NAVY, NPG_SALMON]
wedges, texts, autotexts = ax1.pie(list(cats.values()), labels=list(cats.keys()), autopct="%1.1f%%",
    colors=pie_colors[:len(cats)], startangle=90, wedgeprops={"edgecolor":"white","linewidth":1.5})
for at in autotexts:
    at.set_fontweight("bold"); at.set_fontsize(11)
ax1.set_title("Knowledge Base Composition", fontsize=14, fontweight="bold", color=NPG_NAVY)

chunk_cats = {}
for c in all_chunks:
    cat = c["source"].split("/")[0] if "/" in c["source"] else "root"
    chunk_cats[cat] = chunk_cats.get(cat, 0) + 1
srcs = list(chunk_cats.keys())
cnts = list(chunk_cats.values())
bars = ax2.bar(srcs, cnts, color=pie_colors[:len(srcs)], edgecolor="white", linewidth=0.8, width=0.5)
for b, c in zip(bars, cnts):
    ax2.text(b.get_x()+b.get_width()/2, b.get_height()+0.2, str(c), ha="center", fontsize=12, fontweight="bold", color=NPG_NAVY)
ax2.set_ylabel("Number of Chunks", color=NPG_NAVY)
ax2.set_title("Chunk Distribution", fontsize=14, fontweight="bold", color=NPG_NAVY)
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
ax2.grid(True, alpha=0.3, axis="y", linestyle="--", linewidth=0.5, color=NPG_GRAY)
plt.tight_layout()
plt.savefig("task_b_kb_composition.png", dpi=300, facecolor="white")
plt.close()
print("Fig1: task_b_kb_composition.png")

# Fig 2: Retrieval relevance (vertical layout to avoid label overlap)
def short_label(src, idx):
    s = src.replace("knowledge_base/","").replace("\\","/")
    parts = s.split("/")
    base = f"{parts[0]}/{parts[-1].replace('.md','')}" if len(parts)>=2 else s
    return f"{base} [chunk{idx+1}]"

fig, axes = plt.subplots(3, 1, figsize=(12, 8))
plot_results = dict(list(rag_results.items())[:3])
q_labels_short = ["Q1: Early Blight Symptoms", "Q2: Brown Spots Diagnosis", "Q3: Pesticide Usage"]
for idx, ((q, res), qlbl) in enumerate(zip(plot_results.items(), q_labels_short)):
    ax = axes[idx]
    sources = [short_label(r["source"], i) for i, r in enumerate(res["retrieved"])]
    scores = [r["relevance"] for r in res["retrieved"]]
    colors_grad = [NPG_GREEN, NPG_BLUE, NPG_RED][:len(scores)]
    bars = ax.barh(sources, scores, color=colors_grad, edgecolor="white", linewidth=0.8, height=0.55)
    for b, s in zip(bars, scores):
        ax.text(s - 0.012, b.get_y()+b.get_height()/2, f"{s:.3f}", va="center", ha="right", fontsize=10, fontweight="bold", color="white")
    ax.set_title(qlbl, fontsize=12, fontweight="bold", color=NPG_NAVY, loc="left")
    ax.set_xlim(0, 0.92)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3, axis="x", linestyle="--", linewidth=0.5, color=NPG_GRAY)
fig.suptitle("Retrieval Relevance Scores", fontsize=14, fontweight="bold", color=NPG_NAVY, y=1.01)
plt.tight_layout()
plt.savefig("task_b_retrieval_relevance.png", dpi=300, facecolor="white")
plt.close()
print("Fig2: task_b_retrieval_relevance.png")

# Fig 3: RAG vs No-RAG answer comparison
fig, ax = plt.subplots(figsize=(10, 5))
ax.axis("off")
text = f"Question: {test_q}\n\n{'='*60}\n"
text += f"[Without RAG - Direct LLM]\n{answer_no_rag[:400]}...\n\n{'='*60}\n"
text += f"[With RAG - Knowledge-Based]\n{answer_with_rag[:400]}..."
ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=9, verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="#F7F7F7", edgecolor=NPG_GRAY, alpha=0.9))
ax.set_title("RAG vs Direct LLM Answer Comparison", fontsize=14, fontweight="bold", color=NPG_NAVY, pad=15)
plt.tight_layout()
plt.savefig("task_b_rag_comparison.png", dpi=300, facecolor="white")
plt.close()
print("Fig3: task_b_rag_comparison.png")

# Fig 4: Retrieval heatmap
all_qs_short = ["Early Blight", "Brown Spots", "Pesticide Usage"]
plot_results = dict(list(rag_results.items())[:3])
all_srcs = sorted(set(r["source"].replace("knowledge_base/","") for res in plot_results.values() for r in res["retrieved"]))
heatmap_data = np.zeros((len(plot_results), len(all_srcs)))
for i, (q, res) in enumerate(plot_results.items()):
    for r in res["retrieved"]:
        j = all_srcs.index(r["source"].replace("knowledge_base/",""))
        heatmap_data[i, j] = r["relevance"]

fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(heatmap_data, cmap=plt.cm.YlOrRd, aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(all_srcs))); ax.set_xticklabels(all_srcs, fontsize=9, rotation=30, ha="right", color=NPG_NAVY)
ax.set_yticks(range(len(all_qs_short))); ax.set_yticklabels(all_qs_short, fontsize=10, color=NPG_NAVY)
for i in range(len(plot_results)):
    for j in range(len(all_srcs)):
        if heatmap_data[i,j] > 0:
            ax.text(j, i, f"{heatmap_data[i,j]:.2f}", ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white" if heatmap_data[i,j] > 0.5 else NPG_NAVY)
ax.set_title("Retrieval Relevance Heatmap", fontsize=14, fontweight="bold", color=NPG_NAVY)
cbar = plt.colorbar(im, ax=ax, shrink=0.8); cbar.set_label("Relevance", color=NPG_NAVY)
plt.tight_layout()
plt.savefig("task_b_heatmap.png", dpi=300, facecolor="white")
plt.close()
print("Fig4: task_b_heatmap.png")

# Save results
with open("task_b_results.json", "w", encoding="utf-8") as f:
    json.dump({q: {"answer": v["answer"][:500], "retrieved": v["retrieved"]} for q, v in rag_results.items()},
              f, ensure_ascii=False, indent=2)

print("\n>>> Task B complete! 4 NPG charts generated with bge-small-zh-v1.5")
