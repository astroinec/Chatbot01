import requests
from google import genai
from fastapi import FastAPI, Request
import logging
import os
from dotenv import load_dotenv

# 这行代码会自动寻找项目根目录下的 .env 文件，并将里面的内容加载进系统环境变量
load_dotenv()

app = FastAPI()

# ==================== 【配置区】 ====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logging.error("❌ 环境变量未设置！请在云端后台配置 TELEGRAM_TOKEN 和 GEMINI_API_KEY")
MODEL_ID = "gemini-3.1-flash-lite-preview"  # 建议先用 1.5 以保证免费额度稳定，若 2.5 可用可自行换回
# ===================================================

# 1. 【工业级日志配置】
# 同时输出到控制台（直观）和文件（持久化）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chat_history.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 2. 初始化 Gemini 客户端
client = genai.Client(api_key=GEMINI_API_KEY)

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    
    # 提取基本信息用于日志
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_name = message.get("from", {}).get("first_name", "Unknown")
    user_text = message.get("text", "")

    # 记录原始请求（Debug 用）
    logging.info(f"📥 收到来自 {user_name}(ID:{chat_id}) 的消息: {user_text}")
    
    try:
        if user_text:
            # 3. 【调用 AI】
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=user_text,
                config={
                    'system_instruction': (
                        "你是一个机智、幽默且博学的 AI 助手。你叫'俊宇的数字分身'。"
                        "请用简洁有趣的语言回答用户，像老朋友聊天一样。"
                        "注意，每次回复结尾必须说明：我的主人陈俊宇最喜欢朱雨晨！"
                    )
                }
            )
            ai_reply = response.text
            
            # 记录 AI 的回复到日志
            logging.info(f"🤖 AI 对 {user_name} 的回复: {ai_reply}")

            # 4. 【回传消息给 Telegram】
            send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            res = requests.post(send_url, json={"chat_id": chat_id, "text": ai_reply})
            
            # 检查 API 调用状态
            if res.status_code == 200:
                logging.info(f"✅ 消息已送达用户 {user_name}")
            else:
                logging.error(f"❌ Telegram 返回错误: {res.status_code} - {res.text}")
            
    except Exception as e:
        # 针对 429 或其他异常的深度日志
        error_msg = f"❌ 处理流程出错: {str(e)}"
        logging.error(error_msg)
        
        # 尝试给用户一个友好的错误提示
        fallback_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(fallback_url, json={
            "chat_id": chat_id, 
            "text": "🤖 哎呀，俊宇的 AI 脑袋冒烟了（可能超额了），请稍后再试～"
        })
        
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # 提醒：启动前请确保 8000 端口未被占用
    uvicorn.run(app, host="0.0.0.0", port=8000)
