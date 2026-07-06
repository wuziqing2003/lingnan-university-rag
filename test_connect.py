import logging
from openai import OpenAI
from config import DEEPSEEK_API_KEY  # 导入 Day 3 的中央配置

# 注意：这里不需要再写 basicConfig 了，因为它会自动继承 config.py 里的中文格式

logging.info("正在初始化 OpenAI 客户端...")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

try:
    logging.info("⏳ 正在向 DeepSeek 服务器发送握手暗号...")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "你好，请用一句话证明你对接成功了。"}
        ]
    )

    logging.info("🎉 [连接成功] 对方已安全回应，内容如下：")
    print(response.choices[0].message.content)  # 具体的聊天回复可以直接打印

except Exception as e:
    logging.error(f"❌ [连接失败] 踩到雷了，快检查代理或密钥！错误详情: {e}")