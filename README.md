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

---

## 项目亮点

| 亮点 | 说明 |
|------|------|
| **完整 RAG 闭环** | 文档切块 → Embedding（BGE 中文向量）→ Chroma 持久化 → Hybrid 检索（向量 + BM25 + RRF）→ Prompt 约束 → DeepSeek 生成 |
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
retrieve：Hybrid（Chroma 向量 + rank_bm25 + RRF）→ Top-K
    │  （亦可回退为纯向量检索，见实验 2）
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
│   └── rag/
│       ├── chain.py        # LCEL RAG 链路
│       └── hybrid.py       # 混合检索（BM25 + 向量 + RRF）
├── scripts/                # 入库 / 检索探针等
├── data/                   # 教务语料（PDF / 文本样本）
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

## 演示建议

1. 打开 Streamlit，展示前后端分离与流式输出  
2. 问一个语料内问题 → 应基于规章作答  
3. 问一个语料外问题 → 应拒绝编造（防幻觉约束）  
4. 打开 `/docs`，展示 FastAPI 工程化接口与用户/鉴权能力  
5. （可选）结合 `image/architecture.png` 讲解请求链路  

---

## 实验记录

### 实验 1：Chunk 切分对比

**目的**：同一段校规文本，比较硬切 / Character / Recursive，看哪种更适合入库。  
**样本**：学籍管理规定第 1–9 条（约 1563 字）  
**参数**：size = 128 / 256 / 512，overlap = 0  

**结果**：

| 方法 | 结论 |
|------|------|
| 硬切 | 差：大量句中腰斩（半截话） |
| Character（空 separator） | 与硬切几乎一样，无额外价值 |
| Recursive | 相对最好：更常在句号处切开 |

**额外发现**：

- 只加大 size 治不好腰斩；512 仍腰斩，还可能一块混多条
- Recursive 会出现很短残块（几十个字）
- 金标准「复查…」未命中：PDF 抽成了 `复\n查`（评估坑，不是切丢了）
- 「绩点」未命中：样本里没有该词

**对项目的含义**：入库不应再用按字硬切；应采用 Recursive + 清洗断行 + 适量 overlap（见 `scripts/ingest_pdfs.py`），再用固定问句做检索对比。

**复现**：`python playground/chunk_test.py`

### 实验 2：混合检索（Hybrid Search）

**目的**：Chroma 无原生 BM25。用 `rank_bm25` 做关键字通道，与稠密向量通道并用，经 RRF（互惠倒数排名）融合，观察是否优于纯向量检索。  
**实现**：`app/rag/hybrid.py`（tokenize → BM25 索引 → dense_rank / bm25_rank → rrf_fuse → hybrid_search）  
**对照脚本**：`scripts/retrieve_probe.py`（同一问题先 `[DENSE]` 再 `[HYBRID]`）  
**语料**：`lingnan_rag_pdfs`（约 1453 chunks，校规章 PDF）

**验收问句**：

| 角色 | 问句 |
|------|------|
| 精确词 / 专名 | 研究生三助一辅岗位怎么申请？ |
| 语义理解 | 研究生国家奖学金和国家助学金有什么区别？ |

**流程**：

```text
问题
  ├─ Chroma 向量 Top-N     → 排名列表 A
  ├─ rank_bm25 关键字 Top-N → 排名列表 B
  └─ RRF(A, B)（k=60）→ 最终 Top-K
```

**结果（探针实测）**：

| 问句 | DENSE（纯向量） | HYBRID（向量+BM25+RRF） |
|------|-----------------|-------------------------|
| 三助一辅怎么申请 | Top3 均来自《三助一辅岗位管理办法》，含条件与聘用程序，已很准 | Top1 仍相关，但 Top2 出现《专业实践教学》等噪声块 |
| 奖/助学金区别 | Top3 落在国家奖助学金办法，首条即两者定义，很贴 | 好结果仍在，同样可能被宽词相关文档挤进 Top3 |

**结论**：

1. **工程上已跑通**：不魔改 Chroma，外包 BM25 + 手写 RRF 即可做混合检索。
2. **对本批规章 + 上述问句**：纯向量已经很强；Hybrid **会改变排序**，但不保证全面优于 DENSE，宽词（如「研究生」）可能引入噪声。
3. **Hybrid 的价值**在于补齐精确词通道，适合「课代码 / 专名 / 条款号」等易语义飘的场景；需问句落在语料内才能测出差异。
4. **踩坑**：`collection.get(include=...)` 不能写 `"ids"`（ids 默认返回）；RRF 调用需传 `k`；脚本需在项目根设 `PYTHONPATH=.`。

**对项目的含义**：检索层已具备双通道能力（`hybrid_search`），`app/rag/chain.py` 的 `retrieve` 已接入 Hybrid。入库切块升级为 Recursive 后需重建 Chroma，并重启服务以刷新 BM25 缓存。

**复现**：

```bash
# 项目根目录（Windows PowerShell）
$env:PYTHONPATH = "."
python scripts/retrieve_probe.py
```

**相关 commit 信息**：`feat: implement hybrid search blending rank_bm25 with dense vector`

---

## 版本与后续规划

**当前 MVP（v0.2）已具备：** 可演示的校园 RAG 问答、流式 API、分层后端、JWT/Redis/MySQL、模块化 Streamlit 前端；实验 2 混合检索已实现并接入对话 `retrieve`；入库支持 Recursive 切块。

**规划中（持续迭代）：** 重建向量库后的全量回归评估、BM25 分词降噪、Rerank、检索/问答评估指标、更多语料与问句集等。

---

## 作者

欢迎通过 Issues 交流。若本项目对你有帮助，欢迎 Star。
