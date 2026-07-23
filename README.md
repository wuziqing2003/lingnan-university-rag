# 岭南师范学院教务 RAG 智能咨询系统

> 面向高校教务场景的检索增强生成（RAG）全栈项目：官方规章知识库检索 + 大模型流式问答 + FastAPI 工程化后端 + 前后端分离 Web 界面。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async%20API-009688.svg)](https://fastapi.tiangolo.com/)
[![RAG](https://img.shields.io/badge/RAG-Hybrid%20Search-orange.svg)](https://www.langchain.com/)
[![Status](https://img.shields.io/badge/Status-MVP%20v0.2-success.svg)](#)

---

## 项目简介

校园教务咨询高度依赖规章原文。直接使用大模型容易产生幻觉；本项目将学校官方 PDF 规章切块、向量化并持久化检索，再基于检索上下文生成回答，约束模型在资料不足时明确拒答。

系统按企业常见方式拆分：

- **后端**：业务 API、鉴权、缓存、RAG 推理
- **前端**：交互与流式展示，通过 HTTP 调用后端

适合作为后端 / AI 应用方向的工程实践作品，可完整演示从入库、检索到问答的闭环。

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **完整 RAG 闭环** | PDF 入库 → Recursive 切块 → BGE Embedding → Chroma 持久化 → Hybrid 检索 → Rerank 精排 → Prompt 约束 → DeepSeek 流式生成 |
| **混合检索** | Chroma 稠密向量 + `rank_bm25` 关键字检索，经 RRF 融合排序；中文分词采用 jieba |
| **二次精排** | Hybrid Top10 候选经 `bge-reranker-v2-m3` 重排后取 Top3，缓解「相关块在池中但排序靠后」 |
| **前后端分离** | Streamlit 经 `httpx` 流式请求 `POST /chat/stream`，前端不直连大模型 SDK |
| **工程化后端** | FastAPI 分层（`routers / schemas / crud / models / core`）、CORS、统一异常、健康检查 |
| **可落地用户体系** | MySQL + SQLAlchemy、JWT 登录、密码哈希、Redis Cache-Aside |
| **可验证实验** | 切块、混合检索与 Rerank 对照实验有完整记录，详见 [evaluation_report.md](./evaluation_report.md) |

### 运行效果

**Streamlit 教务问答界面**

![Streamlit 正常问答演示](./image/streamlit.png)

**FastAPI Swagger 文档（/docs）**

![Swagger API 文档](./image/Swagger.png)

---

## 系统架构

![请求生命周期 / 架构示意](./image/architecture.png)

**一次教务问答的数据流：**

```text
用户（Streamlit）
    │  httpx stream  POST /chat/stream
    ▼
FastAPI  chat router
    │  rag_chain.astream(question)
    ▼
Hybrid 检索（Chroma 向量 + BM25 + RRF）→ Top10 候选
    ▼
Rerank（bge-reranker-v2-m3）→ Top3 上下文
    ▼
Prompt（仅依据检索资料作答）→ DeepSeek 流式生成 → 前端输出
```

**用户 / 鉴权路径：**

```text
Client → CORS → Router → Pydantic 校验 → Depends(get_db)
      → Redis 缓存（读） / MySQL（写与未命中）
      → JWT 鉴权（受保护接口）→ 统一异常 JSON
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit、httpx |
| API | FastAPI、Uvicorn、Pydantic、CORS |
| RAG | ChromaDB、LangChain LCEL、Recursive 切块、BGE Embedding、rank_bm25、jieba、bge-reranker、DeepSeek |
| 数据 | MySQL、SQLAlchemy、Redis |
| 安全 | JWT（python-jose）、passlib |
| 工程 | python-dotenv、pytest、分层目录、Git 规范提交 |

---

## 目录结构

```text
lingnan-university-rag/
├── main.py                      # Streamlit 入口
├── frontend/                    # 前端（config / api / styles / components）
├── app/                         # FastAPI 后端
│   ├── main.py
│   ├── core/                    # 配置、数据库、安全、Redis、异常
│   ├── models/ schemas/ crud/
│   ├── routers/                 # users / auth / chat
│   └── rag/
│       ├── chain.py             # LCEL RAG 链路
│       ├── hybrid.py            # 混合检索
│       └── rerank.py            # Rerank 二次精排
├── scripts/                     # PDF 入库、检索探针
├── data/                        # 教务语料
├── playground/                  # 实验脚本
├── tests/                       # pytest
├── evaluation_report.md         # RAG 优化实验报告
├── image/                       # 架构图与演示截图
├── requirements.txt
├── .env.example
└── README.md
```

---

## 快速开始

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
```

复制环境变量模板并填写密钥（**不要提交 `.env`**）：

```bash
copy .env.example .env
```

需配置：`DEEPSEEK_API_KEY`、`SiliconFlow_API_KEY`、`DB_*`、`SECRET_KEY`、`REDIS_HOST`、`REDIS_PORT` 等。

请确保本机 **MySQL**、**Redis** 已启动；首次使用需将 PDF 入库生成 `chroma_db/`（见 `scripts/ingest_pdfs.py`）。

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

侧边栏显示「后端已连接」后即可提问，支持流式回答。

### 4. 测试

```bash
pytest -v
```

---

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/chat/stream` | RAG 流式问答 |
| POST | `/user` | 用户注册 |
| GET | `/user/{id}` | 按 id 查询（Redis 缓存） |
| GET | `/user` | 用户分页列表 |
| POST | `/login` | 登录，返回 JWT |
| GET | `/profile` | 当前用户信息（Bearer Token） |

**流式问答示例：**

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"研究生国家奖学金和国家助学金有什么区别？\"}"
```

---

## 实验与评估

本项目对 RAG 关键环节做了受控对照实验，完整数据与结论见：

**[RAG 优化实验报告（evaluation_report.md）](./evaluation_report.md)**

| 实验 | 内容 | 结论摘要 |
|------|------|----------|
| **实验一：切块策略** | 对比固定硬切、CharacterTextSplitter、RecursiveCharacterTextSplitter（128 / 256 / 512） | Recursive 更利于保留条款边界；生产采用 Recursive + chunk_size=256 + overlap=50 |
| **实验二：混合检索** | 对比纯向量 Dense 与 Hybrid（向量 + BM25 + RRF）；中文分词采用 jieba | 双通道检索已落地；Dense 在语义清晰问句上已较强，Hybrid 提升关键字通道稳定性；瓶颈转为「排不准」 |
| **实验三：Rerank 精排** | Hybrid Top10 → `bge-reranker-v2-m3` → Top3；探针对比 Hybrid / Rerank 金标位次 | 精排已接入生产 `retrieve`；针对候选内排序，不扩大召回；正式 Ragas 定量评估仍待补充 |

说明：README 仅保留实验结论摘要；方法细节、对照表与局限分析请阅读实验报告。

---

## 演示建议

1. 打开 Streamlit，展示前后端分离与流式输出  
2. 提问语料内规章问题，展示基于原文的回答  
3. 提问语料外问题，展示拒答与防幻觉约束  
4. 打开 `/docs`，展示 FastAPI 接口与用户鉴权能力  
5. 结合 [evaluation_report.md](./evaluation_report.md) 说明切块、Hybrid 与 Rerank 的实验依据 

---

## 当前进度与后续规划

**当前 MVP（v0.2）已具备：**

- 可演示的校园规章 RAG 问答与流式 API
- 分层后端、JWT / Redis / MySQL、模块化前端
- Recursive 切块入库、Hybrid 检索与 Rerank 精排接入
- 切块 / 混合检索 / Rerank 的正式实验报告

**规划中：**

- 提示词强化与负向拒答测试
- 基于固定问题集与 Ragas 的定量评估
- 知识库版本治理与场景化扩容

---

## 作者

如有问题可通过 Issues 交流。若本项目对你有帮助，欢迎 Star。
