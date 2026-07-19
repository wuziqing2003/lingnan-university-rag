# 岭南师范学院教务 RAG 智能咨询系统

> 面向高校教务场景的 **检索增强生成（RAG）** 全栈项目：知识库语义检索 + 大模型流式问答 + 工程化 FastAPI 后端 + 前后端分离 Web 界面。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async%20API-009688.svg)](https://fastapi.tiangolo.com/)
[![RAG](https://img.shields.io/badge/RAG-Chroma%20%2B%20LCEL-orange.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/Status-MVP%20v0.2-success.svg)](#)

---

## 为什么做这个项目

校园教务咨询高度依赖规章条文。直接把大模型「裸聊」容易幻觉；本项目把官方教务文本切块向量化后检索，再生成回答，并约束：**资料没有的内容明确说不知道**。

同时按企业常见方式拆分：

- **后端**：业务 API、鉴权、缓存、RAG 推理
- **前端**：只负责交互，通过 HTTP 流式调用后端

适合作为 Python / AI 应用 / 后端实习的作品集主项目。

---

## 项目亮点（简历可直接摘用）

| 亮点 | 说明 |
|------|------|
| **完整 RAG 闭环** | 文档切块 → Embedding（BGE 中文向量）→ Chroma 持久化检索 → Prompt 约束 → DeepSeek 生成 |
| **前后端分离 + 流式传输** | Streamlit 经 `httpx` 流式请求 `POST /chat/stream`，不再直连大模型 SDK |
| **工程化后端分层** | `routers / schemas / crud / models / core`，CORS、统一异常、健康检查 |
| **用户体系可落地** | MySQL + SQLAlchemy ORM、JWT 登录、密码哈希、Redis Cache-Aside |
| **前端模块化** | `frontend/` 分包：`config` / `api` / `styles` / `components`，入口极简 |
| **可演示、可联调** | Swagger 文档 + Streamlit 聊天页 + pytest 基础用例 |

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
retrieve：问题 Embedding → Chroma Top-K
    │
    ▼
Prompt（仅依据检索上下文作答）→ DeepSeek 流式生成 → 前端打字机输出
```

**用户 / 鉴权相关路径（独立模块）：**

```text
Client → CORS → Router → Pydantic 校验 → Depends(get_db)
      → Redis 缓存（读） / MySQL（写与未命中）
      → JWT 鉴权（受保护接口）→ 统一异常 JSON
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit、httpx（流式客户端） |
| API | FastAPI、Uvicorn、Pydantic、CORS |
| RAG | ChromaDB、LangChain LCEL、SiliconFlow Embedding（`BAAI/bge-large-zh-v1.5`）、DeepSeek |
| 数据 | MySQL、SQLAlchemy、Redis |
| 安全 | JWT（python-jose）、passlib |
| 工程 | python-dotenv、pytest、分层目录、Git 规范提交 |

---

## 目录结构

```text
lingnan-university-rag/
├── main.py                 # Streamlit 入口（瘦启动）
├── frontend/               # 前端包
│   ├── config.py           # API 地址、示例问题等
│   ├── api/client.py       # 唯一 HTTP 调用层
│   ├── styles/theme.py     # 页面主题
│   └── components/         # sidebar / chat
├── app/                    # FastAPI 后端
│   ├── main.py             # 应用入口、中间件、异常处理
│   ├── core/               # config / database / security / redis / exceptions
│   ├── models/ schemas/ crud/
│   ├── routers/            # users / auth / chat
│   └── rag/chain.py        # LCEL RAG 链路
├── data/                   # 教务语料（如 lingnan_docs.txt）
├── playground/             # 实验与原生 RAG 流水线脚本
├── tests/                  # pytest
├── image/                  # 架构图、演示截图
├── requirements.txt        # 依赖清单
├── .env.example            # 环境变量模板（无密钥）
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

复制环境变量模板并填写真实密钥（**不要把 `.env` 提交到 Git**）：

```bash
copy .env.example .env
```

按 `.env.example` 中的变量名补全：`DEEPSEEK_API_KEY`、`SiliconFlow_API_KEY`、`DB_*`、`SECRET_KEY`、`REDIS_HOST`、`REDIS_PORT` 等。

并确保本机 **MySQL**、**Redis** 已启动；向量库目录 `chroma_db/` 需已完成入库（可用 `playground/test/rag_pipeline.py` 等脚本基于 `data/` 语料构建）。

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

浏览器打开后，侧边栏显示「后端已连接」即可开始提问（支持示例问题与流式回答）。

### 4. 测试

```bash
pytest -v
```

---

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/chat/stream` | RAG 流式问答（`{"question":"..."}`，`text/plain` 流） |
| POST | `/user` | 用户注册 |
| GET | `/user/{id}` | 按 id 查询（Redis 缓存约 5 分钟） |
| GET | `/user` | 用户分页列表 |
| POST | `/login` | 登录，返回 JWT |
| GET | `/profile` | 当前用户信息（Bearer Token） |

**流式问答示例：**

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"国家奖学金和国家助学金能不能兼得？\"}"
```

---

## 演示建议（面试官 / HR）

1. 打开 Streamlit，展示前后端分离与流式输出  
2. 问一个语料内问题 → 应基于规章作答  
3. 问一个语料外问题 → 应拒绝编造（防幻觉约束）  
4. 打开 `/docs`，展示 FastAPI 工程化接口与用户/鉴权能力  
5. （可选）结合 `image/architecture.png` 讲解请求链路  

---

## 版本与后续规划

**当前 MVP（v0.2）已具备：** 可演示的校园 RAG 问答、流式 API、分层后端、JWT/Redis/MySQL、模块化 Streamlit 前端。

**规划中（持续迭代）：** 更细切块策略、混合检索、Rerank、量化评估报告、多 PDF 批量入库等。

---

## 作者

个人学习与求职作品集项目。欢迎通过 Issues 交流。

若本项目对你有帮助，欢迎 Star。
