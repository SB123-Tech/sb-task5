#!/usr/bin/env python3
"""
任务 B：RAG 农业知识库问答系统
- 加载知识库文档
- 文档分块与向量化
- 构建 ChromaDB 向量数据库
- 检索与问答
- 对比有/无 RAG 的效果
"""

import os
import glob
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── 配置 ──
API_KEY = os.environ.get("AGICTO_API_KEY", "替换为你的API Key")
BASE_URL = "https://api.agicto.cn/v1"
MODEL = "qwen-plus"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 加载 BGE-M3 向量模型（支持 CPU 运行）
print("=" * 60)
print("  任务 B：RAG 农业知识库问答系统")
print("=" * 60)
print("\n加载 BGE-M3 向量模型（首次下载约 2GB，请耐心等待）...")
embedder_model_path = "BAAI/bge-m3"

# ── 1. 加载知识库文档 ──
print("\n--- 步骤1：加载知识库文档 ---")


def load_documents(directory):
    """加载指定目录下的所有 .md / .txt 文件"""
    documents = []
    file_paths = glob.glob(os.path.join(directory, "**/*.md"), recursive=True)
    file_paths += glob.glob(os.path.join(directory, "**/*.txt"), recursive=True)

    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        rel_path = os.path.relpath(path, directory)
        documents.append({"source": rel_path, "content": content, "title": os.path.basename(path)})

    print(f"加载了 {len(documents)} 篇文档")
    for doc in documents:
        print(f"  - {doc['source']} ({len(doc['content'])} 字符)")
    return documents


kb_dir = "knowledge_base"
if not os.path.isdir(kb_dir):
    print(f"\n知识库目录 '{kb_dir}' 不存在！")
    print("请先创建 knowledge_base 目录并放入农业知识文档。")
    print("参考 任务指导书.md 中的知识库构建指南。")
else:
    docs = load_documents(kb_dir)

    # ── 2. 文档分块 ──
    print("\n--- 步骤2：文档分块 ---")

    def chunk_text(text, chunk_size=500, overlap=50):
        """将长文本分成重叠的块"""
        chunks = []
        paragraphs = text.split("\n\n")

        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                words = current_chunk.split()
                overlap_text = (
                    " ".join(words[-overlap:]) if len(words) > overlap else current_chunk
                )
                current_chunk = overlap_text + "\n\n" + para

        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc["content"], chunk_size=500, overlap=50)
        for i, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk,
                    "source": doc["source"],
                    "title": doc["title"],
                    "chunk_id": f"{doc['source']}_{i}",
                }
            )

    print(f"共分成 {len(all_chunks)} 个文本块")

    # ── 3. 构建向量数据库 ──
    print("\n--- 步骤3：构建向量数据库 ---")

    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedder_model_path
    )

    collection_name = "agri_knowledge"
    try:
        collection = chroma_client.get_collection(
            name=collection_name, embedding_function=embedding_func
        )
        print(f"使用已有集合: {collection_name}")
    except Exception:
        collection = chroma_client.create_collection(
            name=collection_name,
            embedding_function=embedding_func,
            metadata={"description": "农业知识库"},
        )
        print(f"创建新集合: {collection_name}")

    # 清空并添加数据
    collection.delete(where={})

    texts = [chunk["text"] for chunk in all_chunks]
    ids = [chunk["chunk_id"] for chunk in all_chunks]
    metadatas = [
        {"source": chunk["source"], "title": chunk["title"]} for chunk in all_chunks
    ]

    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_end = min(i + batch_size, len(texts))
        collection.add(
            documents=texts[i:batch_end],
            ids=ids[i:batch_end],
            metadatas=metadatas[i:batch_end],
        )

    print(f"已向量化并存储 {len(texts)} 个文本块")

    # ── 4. 检索与问答 ──
    print("\n--- 步骤4：检索与问答 ---")

    def retrieve_and_answer(question, top_k=3):
        """检索相关知识并生成回答"""
        results = collection.query(query_texts=[question], n_results=top_k)

        print(f"\n问题: {question}")
        print(f"\n检索到的相关知识:")
        print("-" * 50)

        context_parts = []
        for doc, metadata, distance in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            print(f"\n[来源: {metadata['source']}] (相关度: {1 - distance:.2f})")
            print(f"内容: {doc[:200]}...")
            context_parts.append(f"来源: {metadata['source']}\n内容: {doc}")

        context = "\n\n---\n\n".join(context_parts)

        system_prompt = """你是农业植保专家。请基于以下参考资料回答用户的问题。
要求：
1. 回答必须基于参考资料，不要编造信息
2. 如果参考资料不足以回答问题，请如实告知
3. 回答要实用、有针对性
4. 在回答末尾注明参考来源"""

        user_prompt = (
            f"参考资料：\n{context}\n\n用户问题：{question}\n\n"
            f"请基于以上资料，给出专业、实用的回答。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        answer = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.3, max_tokens=1024
        ).choices[0].message.content

        print(f"\n{'=' * 50}")
        print(f"AI 回答:")
        print("-" * 50)
        print(answer)
        return answer

    questions = [
        "番茄早疫病的症状和防治方法是什么？",
        "番茄叶片出现褐色斑点可能是什么病？",
        "代森锰锌的使用方法和注意事项是什么？",
    ]

    for q in questions:
        retrieve_and_answer(q, top_k=3)
        print("\n" + "=" * 60)

    # ── 5. RAG vs 无 RAG 对比 ──
    print("\n--- 步骤5：RAG vs 无 RAG 对比 ---")

    test_question = "番茄早疫病用什么药治疗？推荐剂量是多少？"

    # 无 RAG
    messages_no_rag = [
        {"role": "system", "content": "你是农业专家。"},
        {"role": "user", "content": test_question},
    ]
    answer_no_rag = client.chat.completions.create(
        model=MODEL, messages=messages_no_rag, temperature=0.5, max_tokens=512
    ).choices[0].message.content

    # 有 RAG
    answer_with_rag = retrieve_and_answer(test_question)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")

    text = f"问题: {test_question}\n\n"
    text += f"{'─' * 60}\n"
    text += f"【无 RAG（凭记忆回答）】\n{answer_no_rag[:500]}...\n\n"
    text += f"{'─' * 60}\n"
    text += f"【有 RAG（基于知识库）】\n{answer_with_rag[:500]}..."

    ax.text(
        0.02,
        0.98,
        text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        family="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    plt.tight_layout()
    plt.savefig("task_b_rag_comparison.png", dpi=150, bbox_inches="tight")
    print("对比图已保存到 task_b_rag_comparison.png")

    print("\n--- 任务 B 完成！---")
    print("思考题:")
    print("1. RAG 系统为什么能减少 LLM 的'幻觉'问题？")
    print("2. 文本分块的大小（chunk_size）对检索效果有什么影响？")
    print("3. 如果知识库中没有相关内容，系统应该如何处理？")
    print("4. 尝试不同的分块策略（按标题分块 vs 固定大小），哪种效果更好？")
    print("5. 如何用查询改写提升检索准确率？")
