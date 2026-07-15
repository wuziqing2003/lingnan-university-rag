# 📚 岭南师范学院教务 RAG 智能咨询系统

基于 **Streamlit** 与 **DeepSeek-V4** 大模型构建的工业级校园教务智能体系统。旨在通过检索增强生成（RAG）技术，为校内师生提供 100% 忠于官方源文件的权威、合规业务咨询。

---

## 🌟 核心特性
- **AI 流式响应**：基于 `deepseek-v4-pro` 模型，实现高能丝滑的打字机流式对话输出。
- **工业级 Prompt 严防幻觉**：内嵌高强度系统提示词，严守“无检索依据不作答”的兜底机制。
- **现代工程架构**：解耦式虚拟环境设计，代码结构纯净，配备完善的 `.gitignore` 策略。
- **(Coming Soon) 知识库 RAG**：基于本地向量数据库（ChromaDB）与智能文档解析（pdfplumber）的混合检索架构。

## 🛠️ 技术栈
- **Frontend / UI**: Streamlit v1.x
- **LLM API**: OpenAI SDK (DeepSeek-V4-Pro)
- **Language**: Python 3.11+
- **Version Control**: Git / GitHub

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone [https://github.com/你的GitHub用户名/lingnan-university-rag.git](https://github.com/你的GitHub用户名/lingnan-university-rag.git)
cd lingnan-university-rag


![Swagger API Docs](./swagger-docs.png)
## 🛠️ 后端核心架构：用户请求完整生命周期流转图

![后端核心架构图](image/architecture.png)