# 第五部分：LLM 与大模型应用 — 农业知识问答系统

## 实验环境

| 配置项 | 详情 |
|--------|------|
| 本地 Docker 环境 | dl-env (Python + Jupyter) |
| 云端 LLM API | agicto API (`gpt-4o-mini`) |
| 向量模型 | BAAI/bge-small-zh-v1.5 (512维) |
| 知识库 | ChromaDB 持久化存储 |
| GPU 服务器 | Tesla V100S 32GB, CUDA 13.0 |
| 本地部署模型 | Qwen2.5-7B-Instruct (FP16) |
| 可视化配色 | NPG (Nature Publishing Group) 顶刊风格 |

---

## 任务 A：LLM API 初体验与 Prompt Engineering

### 实验目的
调用 agicto API 进行对话，对比三种 Prompt 策略在农业场景下的效果。

### 实验设计

| 策略 | System Prompt | 特点 |
|------|---------------|------|
| 基础 Prompt | 无 | 直接提问，无额外引导 |
| 角色设定 + 结构化 | 20年农业植保专家 | 指定身份 + 要求结构化输出 |
| Few-shot + Chain-of-Thought | 专家 + 诊断示例 | 2个示例 + 逐步推理引导 |

### 实验结果

**测试问题**：番茄叶子发黄是什么原因？

| 策略 | 响应时间 | 回答长度 | 质量评分 |
|------|----------|----------|----------|
| 基础 Prompt | 6.2s | ~500 chars | 3/10 |
| 角色设定 + 结构化 | 7.3s | ~700 chars | 7/10 |
| Few-shot + CoT | 3.2s | ~350 chars | 9/10 |

### 可视化结果

![Prompt Engineering 对比](task_a_prompt_comparison.png)

*图1: 三种 Prompt 策略的质量评分对比。Few-shot + Chain-of-Thought 策略获得最高评分（9/10）。*

![响应时间与回答长度](task_a_response_time.png)

*图2: 各策略的响应时间与回答长度双轴对比。Few-shot 策略在保持高质量的同时响应速度最快。*

![多维雷达图](task_a_radar.png)

*图3: 多维评估雷达图。Few-shot 策略在专业性、结构性、准确性等维度全面领先。*

### 多轮对话测试
模拟农业咨询场景的三轮对话（病害诊断 → 用药咨询 → 施用频率），模型展现出良好的上下文理解能力。

### 结论
- **角色设定**显著提升回答的专业性和可操作性
- **Few-shot + CoT**策略在专业诊断场景中效果最佳
- 结构化输出要求对农业技术指导场景至关重要

---

## 任务 B：RAG 农业知识库问答系统

### 实验目的
构建基于检索增强生成（RAG）的农业知识问答系统，对比有/无知识库的回答质量。

### 系统架构

```
知识文档 → 文本分块(500字/块, 50字重叠) → BGE向量化(512维) → ChromaDB
                                                              ↓
用户提问 → 向量化 → 检索Top-K相关块 → 拼接Prompt → LLM生成回答
```

### 知识库构成

![知识库组成](task_b_kb_composition.png)

*图4: 知识库包含4篇文档（diseases/planting/pesticide），共18个文本块。*

### 检索效果

对三个典型问题的检索结果：

![检索相关度](task_b_retrieval_relevance.png)

*图5: 三个问题的检索相关度。Top-3 检索的平均相关度在 0.70-0.80 之间。同一文档的不同分块以 [chunkN] 区分。*

![检索热力图](task_b_heatmap.png)

*图6: 检索相关度热力图。同类文档（如病害问题→病害文档）检索效果最佳。*

### RAG vs Direct LLM 对比

![RAG对比](task_b_rag_comparison.png)

*图7: 有 RAG 的回答能提供具体药品名称、浓度和安全间隔期（基于知识库），而无 RAG 的回答较为笼统。*

### 关键发现
1. **减少幻觉**：RAG 将回答锚定在实际文档上，大幅减少编造信息
2. **专业深度**：知识库中的专业内容（农药浓度、安全间隔期）直接被引用
3. **可追溯性**：每个回答都能追溯到具体的参考文档

---

## 任务 C：GPU 服务器本地模型部署与性能对比

### 实验目的
在 GPU 服务器上部署开源模型，对比本地部署与云端 API 的性能差异。

### 部署配置

| 项目 | 配置 |
|------|------|
| GPU | Tesla V100S 32GB |
| 模型 | Qwen2.5-7B-Instruct (FP16, ~14GB 显存) |
| 推理框架 | Flask + HuggingFace Transformers |
| API 接口 | OpenAI 兼容 (`/v1/chat/completions`) |

### 性能对比

| 指标 | 本地 GPU (V100S) | 云端 API (gpt-4o-mini) |
|------|-------------------|------------------------|
| 平均响应时间 | 20.11s | 5.98s |
| 平均输出长度 | 817 chars | 659 chars |
| 字符生成速度 | 40.6 chars/s | 110.2 chars/s |
| 显存占用 | ~15 GB | N/A |

### 可视化结果

![响应时间对比](task_c_response_time.png)

*图8: 本地 GPU vs 云端 API 响应时间对比。云端 API 响应速度快 3.4 倍。*

![双轴对比](task_c_dual_comparison.png)

*图9: 响应时间与输出长度双轴对比。本地模型输出更详细（+24%），但速度较慢。*

![吞吐量对比](task_c_throughput.png)

*图10: 字符生成速度对比。云端 API 的吞吐量是本地 V100S 的 2.7 倍。*

### 讨论
1. **云端优势**：gpt-4o-mini 在速度上明显领先，得益于更强的基础设施
2. **本地优势**：无 API 费用、数据不出服务器、可完全控制模型行为
3. **V100S 局限性**：较老架构，FP16 推理速度有限；使用 vLLM 或 TensorRT-LLM 可显著提升

---

## 任务 D：农业 AI 助手 Web 应用

### 功能特性

- **Streamlit Web UI**：简洁的聊天界面
- **RAG 引擎**：BGE 向量检索 + ChromaDB 知识库
- **多模型支持**：可切换 gpt-4o-mini / qwen-plus
- **参考来源展示**：每次回答附带检索到的文档来源

### 运行方式

```bash
streamlit run task_d_challenge.py --server.address 0.0.0.0 --server.port 8501
```

应用地址：`http://localhost:8501`

### 系统截图

![Streamlit 应用主界面](task_d_streamlit_app.png)

*图11: Streamlit 农业 AI 助手 Web 应用。测试问题："番茄叶片出现褐色斑点，是什么病？怎么防治？"。系统通过 RAG 检索知识库，返回了包括晚疫病和早疫病的详细诊断及具体防治方案（含农药名称、浓度、安全间隔期），并附带可追溯的参考来源。*

---

## 总结

### 完成情况

| 任务 | 状态 | 关键产出 |
|------|------|----------|
| Task A: Prompt Engineering | ✅ | 3种策略对比 + 4张NPG图表 |
| Task B: RAG 系统 | ✅ | 向量知识库 + RAG vs no-RAG 对比 + 4张图表 |
| Task C: 本地部署 | ✅ | Flask + Qwen2.5-7B 部署 + 性能对比 + 3张图表 |
| Task D: Web 应用 | ✅ | Streamlit 农业 AI 助手 |

### 关键技术栈

- **LLM API**: agicto (兼容 OpenAI SDK)
- **向量模型**: BAAI/bge-small-zh-v1.5
- **向量数据库**: ChromaDB (持久化)
- **本地推理**: Flask + HuggingFace Transformers + PyTorch 2.6.0
- **可视化**: Matplotlib (NPG 顶刊配色)
- **Web 框架**: Streamlit

### 思考题回答

1. **角色设定提升回答质量的原因**：角色设定为模型提供了明确的"身份锚点"，激活了训练数据中与该角色相关的知识模式，使回答更具专业性和针对性。

2. **RAG 减少幻觉的机制**：RAG 将 LLM 的生成过程从"自由回忆"转变为"阅读理解"，模型基于实际文档内容生成回答，大大降低了编造信息的概率。

3. **本地部署 vs 云端 API 选择**：
   - 云端适合：快速原型、低延迟需求、不想维护基础设施
   - 本地适合：数据隐私敏感、高并发低成本推理、需要定制模型
