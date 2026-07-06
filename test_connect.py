import logging
import sys
from openai import OpenAI
from config import DEEPSEEK_API_KEY 
####hasattr(sys.stdout, "reconfigure") 是用来检查 sys.stdout 对象是否支持 reconfigure 方法。
####如果支持，则使用 sys.stdout.reconfigure(encoding="utf-8") 方法来设置输出编码为 utf-8。
####这样就可以在控制台输出中文了。

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 注意：这里不需要再写 basicConfig，它会自动继承 config.py 里的时间戳和中文格式

logging.info(" 正在初始化 OpenAI 客户端...")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

try:
    logging.info("⏳ 正在向 DeepSeek 服务器发送握手请求...")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "你好！请用一句话证明我们的 Python 脚本已经和你直连成功了。"}
        ]
    )
except Exception as e:
    logging.error(f"❌ [连接失败] 握手失败，快检查网络或密钥！错误详情: {e}")
else:
    logging.info("🎉 [连接成功] 对方已安全回应，内容如下：")
    print(f"\n🤖 大模型回复：{response.choices[0].message.content}\n")
