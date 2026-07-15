# 岭南师范学院教务 RAG 智能咨询系统

基于 **Streamlit** 与 **DeepSeek** 的校园教务智能咨询前端，以及 **FastAPI** 后端用户/鉴权服务（后端骨架 **v0.1**）。目标是通过检索增强生成（RAG）为师生提供忠于官方源文件的业务咨询，并配套可扩展的工程化 API。

---

## 项目组成

| 部分 | 入口 | 说明 |
|------|------|------|
| RAG 对话 UI | 根目录 `main.py` | Streamlit + DeepSeek 流式对话 |
| 后端 API | `app/main.py` | 用户注册/登录、JWT、Redis 缓存、统一异常、CORS、pytest |

---

## 核心特性

- **AI 流式响应**：基于 DeepSeek 模型，打字机式流式输出
- **防幻觉 Prompt**：无检索依据不作答的兜底机制
- **分层后端骨架（v0.1）**：`routers / schemas / crud / models / core` 分层，CORS、统一异常、JWT、Redis Cache-Aside
- **(Coming Soon) 知识库 RAG**：ChromaDB + 文档解析的混合检索

---

## 后端架构：用户请求完整生命周期

![后端核心架构：用户请求完整生命周期流转图](./image/architecture.png)

请求大致路径：

1. 客户端发起 HTTP → `CORSMiddleware` 校验跨域
2. 匹配 `router`，经 `schema` 校验（非法自动 **422**）
3. 依赖注入（如 `get_db`）后进入业务逻辑
4. 读接口可走 **Redis** 缓存分支；未命中再查 **MySQL**，命中则回填缓存
5. 业务异常由全局异常处理器拦截，统一输出 JSON（如 `{"detail": "..."}`）

### 分层目录

```text
app/
  main.py           # 应用入口、CORS、异常处理、/health
  core/             # config、database、security、redis、exceptions
  models/           # SQLAlchemy 模型
  schemas/          # Pydantic 入参/出参
  crud/             # 数据库操作
  routers/          # users、auth 路由
tests/              # pytest 自动化测试
image/              # 架构流程图等静态资源
```

---

## 技术栈

- **UI**: Streamlit
- **API**: FastAPI + Uvicorn
- **DB**: MySQL + SQLAlchemy
- **Cache**: Redis
- **Auth**: JWT（python-jose）+ passlib
- **Test**: pytest + httpx / TestClient
- **LLM**: DeepSeek（OpenAI SDK）
- **Language**: Python 3.11+

---

## 快速开始

### 1. 克隆与环境

```bash
git clone https://github.com/wuziqing2003/lingnan-university-rag.git
cd lingnan-university-rag
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv passlib python-jose redis pytest httpx streamlit openai
```

配置项目根目录 `.env`（数据库、`SECRET_KEY`、`REDIS_HOST` / `REDIS_PORT`、`DEEPSEEK_API_KEY` 等），并确保 **MySQL**、**Redis** 已启动。

### 2. 启动后端 API

```bash
python -m app.main
```

- Swagger 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

### 3. 启动 Streamlit（RAG）

```bash
streamlit run main.py
```

### 4. 跑测试

```bash
pytest -v
```

---

## 主要接口（后端 v0.1）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/user` | 注册用户 |
| GET | `/user/{id}` | 按 id 查用户（Redis 缓存 5 分钟） |
| GET | `/user` | 用户列表分页 |
| POST | `/login` | 登录（form），返回 JWT |
| GET | `/profile` | 当前用户信息（需 Bearer Token） |
