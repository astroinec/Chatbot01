import requests
from google import genai
from fastapi import FastAPI, Request
import logging
import os
import io
from dotenv import load_dotenv
from PIL import Image

# 加载系统环境变量
load_dotenv()
app = FastAPI()

# ==================== 【配置区】 ====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logging.error("❌ 环境变量未设置！请在云端后台配置 TELEGRAM_TOKEN 和 GEMINI_API_KEY")

# 视觉/多模态模型池（按 RPD 优先级排序）
VISION_POOL = [
    "gemini-3.1-flash-lite-preview",  # 500次/天，首选
    "gemini-3.1-flash-image-preview", # Nano Banana 2
    "gemini-1.5-flash"                # 备用
]

# 纯文字模型池
TEXT_POOL = [
    "gemini-3.1-flash-lite-preview",
    "gemma-3-27b-it",                 
    "gemma-3-12b-it"
]

SYSTEM_PROMPT = (
    "你是一个机智、幽默且博学的 AI 助手。你叫'俊宇的数字分身'。"
    "请用简洁有趣的语言回答用户，像老朋友聊天一样。"
)
# =============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("chat_history.log", encoding='utf-8'), logging.StreamHandler()]
)

client = genai.Client(api_key=GEMINI_API_KEY)

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_name = message.get("from", {}).get("first_name", "Unknown")
    
    # 初始化变量
    user_text = message.get("text", "")
    image_data = None
    prompt = user_text

    # ==================== 【2. 修改：增加图片处理逻辑】 ====================
    if "photo" in message:
        logging.info(f"📸 收到来自 {user_name} 的图片，准备下载...")
        file_id = message["photo"][-1]["file_id"] # 获取最高清图
        # 下载图片
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]
        image_data = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}").content
        # 如果发图时带了文字说明（Caption），就用它当提示词
        prompt = message.get("caption", "请描述一下这张图片")

    # ==================== 【3. 修改：多模型自动回退逻辑】 ====================
    # 根据是否有图片选择对应的池子
    current_pool = VISION_POOL if image_data else TEXT_POOL
    ai_reply = None
    for model_id in current_pool:
        try:
            logging.info(f"🚀 尝试使用模型: {model_id}")
            
            contents_call = [prompt]
            if image_data:
                # 🛠️ 【修改点】：将原始字节转为 PIL 图像对象
                # 这样 PIL 会自动检测并告知 SDK 这是一个 'image/jpeg'
                img = Image.open(io.BytesIO(image_data))
                contents_call.append(img)  # <-- 将 PIL 对象加入 contents

            response = client.models.generate_content(
                model=model_id,
                contents=contents_call,
                # system_instruction 使用你原来的人设（保持不变）
                config={'system_instruction': SYSTEM_PROMPT}
            )
            ai_reply = response.text
            logging.info(f"✅ 模型 {model_id} 调用成功！")
            break  # 成功了直接跳出模型池循环

        except Exception as e:
            if "429" in str(e):
                logging.warning(f"⚠️ 模型 {model_id} 额度已满，尝试下一个...")
                continue
            else:
                logging.error(f"❌ 模型 {model_id} 报错: {e}")
                continue

    # 如果所有模型都挂了的保底回复
    if not ai_reply:
        ai_reply = "🤖 哎呀，所有大脑都罢工了，俊宇快来救命！"

    # 回传消息给 Telegram
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": ai_reply})
    
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
