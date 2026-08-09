# ===== 阶段 1：builder（专门装依赖）=====
# 目的：在“厨房”里 pip install，安装垃圾不必全进最终镜像
FROM python:3.11-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir -U pip \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    --prefix=/install

# ===== 阶段 2：runtime（真正拿去跑服务）=====
# 目的：只保留运行需要的 Python 依赖 + 代码
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 从 builder 拷贝已安装的包
COPY --from=builder /install /usr/local

# 只拷贝后端代码（不要把 .venv、.env、大数据目录打进镜像）
COPY app ./app

EXPOSE 8000

# 目的：容器外可访问；为什么不能 127.0.0.1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]