# 高校教务规章 RAG 问答系统

> 个人项目（独立完成）。用学校公开教务规章 PDF 做知识库，实现「检索 + 生成」的问答：Hybrid 检索、Cross-Encoder 精排，并用 Ragas 与拒答行为小金标做对照评估。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![RAG](https://img.shields.io/badge/RAG-Hybrid%20%2B%20Rerank-orange.svg)](https://www.langchain.com/)
[![Eval](https://img.shields.io/badge/Eval-Ragas-purple.svg)](https://github.com/explodinggradients/ragas)

**求职相关方向：** 大模型应用 / RAG 应用 / Python 后端（AI）实习

---

## 项目亮点

1. **检索链路完整**：PDF 按页入库 → Recursive 切块 → BGE Embedding → Chroma → Hybrid（向量 + BM25 + RRF）→ `bge-reranker-v2-m3` 精排 → Prompt 约束 → DeepSeek 流式生成，并回传来源页码  
2. **有对照实验，不只调通**：用 **50** 道自建题 + Ragas，对比有无 Rerank；四项指标均提升，Context Precision 约 **0.73 → 0.79**，Answer Relevancy 约 **0.65 → 0.83**  
3. **拒答行为有回归集**：另建 **30** 题（该答 10 / 部分答 10 / 该拒 10），人工记误拒与幻觉；当前 **误拒 3、幻觉 0**，不单凭感觉调 Prompt  
4. **前后端可演示**：Streamlit 通过 `httpx` 调用 FastAPI `POST /chat/stream`，流式返回答案并展示 PDF 来源 / 页码；资料不足时要求模型拒答，减轻幻觉

### Ragas 评估结果（50 题）

| 指标 | 无 Rerank | 有 Rerank | 差值 |
|------|----------:|----------:|-----:|
| Context Precision | 0.73 | **0.79** | +0.06 |
| Context Recall | 0.74 | **0.88** | +0.14 |
| Faithfulness | 0.86 | **0.89** | +0.03 |
| Answer Relevancy | 0.65 | **0.83** | +0.18 |

**怎么理解：** Rerank 改善进入生成的 Top3 质量（Precision / Relevancy 上升）；Recall 也会因最终 Top3 置换而变化，但**不能**捞到 Hybrid Top10 以外的块——两边仍 Recall=0 的题要回到切块 / 初筛上查。

### 拒答 / 幻觉行为回归（30 题）

| 指标 | 结果 |
|------|------|
| 题型 | 该答 10 / 部分答 10 / 该拒 10 |
| 行为准确 | **27/30** |
| 误拒 | **3/30**（心理电话、转专业名额、宿舍房型等「有制度缺精确字段」时整句拒答） |
| 幻觉 | **0/30**（该拒题未编造价格 / 时刻 / 网址等） |

金标与跑分：`evaluation/refusal_gold.json`、`evaluation/eval_refusal.py`。完整过程与逐题分析见 [docs/evaluation_report.md](./docs/evaluation_report.md)。

---

## 项目简介

直接问大模型教务规定，容易答错或编造。本项目把规章 PDF 切块并写入向量库，回答时先检索再生成，并在 Prompt 里要求：只根据检索到的内容作答，资料不够就明确说明。

这是一个可本地运行的 MVP：后端负责检索与流式生成，前端负责对话展示。仓库中的完整规章 PDF **未公开收录**（体积与版权考虑）；若要本地复现，可自备同类 PDF，按下方入库脚本处理。

---

## 系统架构

主路径是一次问答的完整生成周期（前端 → FastAPI → Hybrid / Rerank → 流式生成）。离线入库与用户鉴权不在主图展开，见下方文字与[附录](#附录用户接口请求生命周期)。

**在线问答：用户请求完整生成周期**

![RAG 问答请求完整生成周期](./image/rag_qa_lifecycle.png)

**一次问答的数据流：**

```text
用户（Streamlit）
    │  httpx stream  POST /chat/stream
    ▼
FastAPI  chat router
    │  同一批 hits：生成答案 + 附加来源元数据
    ▼
Hybrid 检索（Chroma 向量 + BM25 + RRF）→ Top10 候选（含 source / page）
    ▼
Rerank（bge-reranker-v2-m3）→ Top3 hit
    ▼
Prompt（仅依据检索资料作答）→ DeepSeek 流式生成
    ▼
前端：流式展示答案 → 解析来源 JSON → 显示 PDF 名与页码
```

**离线入库（一次构建知识库）：**

```text
data/pdfs → 按页抽文本 → Recursive 切块(256/50) → BGE Embedding
         → chroma_db（metadata: source, page）
```

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **RAG 闭环** | 入库 → 切块 → Embedding → 检索 → 精排 → 生成 |
| **混合检索** | 稠密向量 + `rank_bm25`，RRF 融合；中文分词用 jieba |
| **二次精排** | Hybrid Top10 → `bge-reranker-v2-m3` → Top3，改善「相关块在池中但排得偏后」 |
| **流式接口** | `POST /chat/stream`，答案流式输出后附带来源 JSON（PDF 名 / 页码 / 片段） |
| **可溯源展示** | 前端解析同一批检索 hit，在回答下方展示出处，避免模型自行编造来源 |
| **对照实验** | 切块 / Hybrid / Rerank / Ragas / 拒答小金标，见 `docs/` 与 `evaluation/` |
| **附带能力** | FastAPI 分层、JWT 登录、MySQL、Redis 缓存（非 RAG 主线，见[附录](#附录用户接口请求生命周期)） |

### 运行截图

**Streamlit 问答界面（答案 + PDF 来源 / 页码）**

![Streamlit 问答演示：流式回答并展示规章来源](./image/streamlit.png)

**FastAPI Swagger（/docs）**

![Swagger API 文档](./image/Swagger.png)

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit、httpx |
| API | FastAPI、Uvicorn、Pydantic |
| RAG | ChromaDB、LangChain LCEL、Recursive 切块、BGE Embedding、rank_bm25、jieba、bge-reranker、DeepSeek |
| 评估 | Ragas、自建 `ground_truth.json`（50 题）、拒答行为集 `refusal_gold.json`（30 题） |
| 数据 / 安全 | MySQL、SQLAlchemy、Redis、JWT（附录能力） |
| 工程 | python-dotenv、pytest |

---

## 实验与评估（摘要）

完整数据、设置与局限说明：[docs/evaluation_report.md](./docs/evaluation_report.md)  
评估脚本与结果：`evaluation/eval_with_ragas.py`、`evaluation/eval_refusal.py`、`evaluation/results_*.json`、`evaluation/refusal_run.json`

| 实验 | 做了什么 | 结论（简） |
|------|----------|------------|
| **切块** | Naive / Character / Recursive，以及 128 / 256 / 512 | Recursive 更利于保留条款边界；当前采用 chunk_size=256、overlap=50 |
| **混合检索** | Dense vs Hybrid（向量 + BM25 + RRF） | Hybrid 稳住关键字侧；问题逐渐变成「候选对了但排序不理想」 |
| **Rerank** | Hybrid Top10 → 精排 Top3，探针看位次变化 | 精排接进生产检索链路，职责是重排，不扩大召回 |
| **Ragas** | 50 题，有无 Rerank 四指标对照 | 四项均提升；Precision +0.06，Recall +0.14，Relevancy +0.18 |
| **拒答小金标** | 30 题：该答 10 / 部分答 10 / 该拒 10，人工记误拒与幻觉 | 行为准确 27/30；误拒 3、幻觉 0；短板是缺细节时过拒 |

---

## 目录结构

```text
lingnan-university-rag/
├── main.py                 # Streamlit 入口
├── frontend/               # 前端
├── app/                    # FastAPI 后端
│   ├── routers/            # users / auth / chat
│   └── rag/
│       ├── chain.py        # LCEL RAG 链路
│       ├── hybrid.py       # 混合检索
│       └── rerank.py       # Rerank
├── scripts/                # PDF 入库、检索探针
├── evaluation/             # Ragas / 拒答回归评估与结果
├── docs/
│   └── evaluation_report.md
├── data/                   # 本地语料目录（完整 PDF 未纳入本仓库）
├── playground/             # 实验脚本
├── tests/
├── image/
│   ├── rag_qa_lifecycle.png      # 主图：问答生成周期
│   └── user_api_lifecycle.png    # 附录：用户接口请求生命周期
├── requirements.txt
├── .env.example
└── README.md
```

---

## 快速开始

> 阅读本 README 即可了解设计与实验结果。若要本地跑通，需要自备 API Key、MySQL、Redis，以及若干规章类 PDF。

### 1. 环境

```bash
git clone https://github.com/wuziqing2003/lingnan-university-rag.git
cd lingnan-university-rag
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

在 `.env` 中填写 `DEEPSEEK_API_KEY`、`SiliconFlow_API_KEY`、`DB_*`、`SECRET_KEY`、`REDIS_*` 等（**不要提交 `.env`**）。

将 PDF 放到 `data/pdfs/` 后执行入库（生成 `chroma_db/`，该目录默认不提交）：

```bash
python scripts/ingest_pdfs.py
```

### 2. 启动后端

```bash
python -m app.main
```

- API 文档：http://127.0.0.1:8000/docs  
- 健康检查：http://127.0.0.1:8000/health  

### 3. 启动前端

```bash
streamlit run main.py
```

侧边栏显示「后端已连接」后即可提问。

### 4. 测试与评估（可选）

```bash
pytest -v
python evaluation/eval_with_ragas.py --mode rerank
python evaluation/eval_refusal.py
```
### 流式问答示例

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"研究生国家奖学金和国家助学金有什么区别？\"}"
```

---

## 当前不足

- 评估集现为 Ragas 50 题 / 拒答 30 题，结论仍不宜外推到全部规章问答  
- 仍有题目两边 Context Recall 为 0：所需段落可能未进入 Hybrid Top10，Rerank 帮不上，需要回头查切块、分词或初筛  
- 拒答回归里仍有 3 题误拒：有相关制度但缺精确字段（电话 / 名额 / 宿舍房型）时，模型会整句拒答，偏「过拒」  
- Rerank 依赖外部 API，会增加延迟与对密钥/网络的依赖  



---

## 附录：主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/chat/stream` | RAG 流式问答（主接口；答案后附带来源 JSON） |
| POST | `/user` | 用户注册 |
| GET | `/user/{id}` | 按 id 查询（Redis 缓存） |
| GET | `/user` | 用户分页列表 |
| POST | `/login` | 登录，返回 JWT |
| GET | `/profile` | 当前用户信息（Bearer Token） |

## 附录：用户接口请求生命周期

> 非 RAG 主路径。对应注册 / 登录 / 按 id 查用户等接口，体现 FastAPI 分层、Schema 校验、Redis Cache-Aside 与全局异常处理。

![用户接口请求生命周期（CORS → 校验 → Redis/MySQL → 异常）](./image/user_api_lifecycle.png)
