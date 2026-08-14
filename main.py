import os
import json
import asyncio
from datetime import datetime
from flask import Flask
from threading import Thread

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from google.oauth2.service_account import Credentials
import openai

# 1. ENVIRONMENT VARIABLES
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# 2. CLIENTS SETUP
groq_client = None
if GROQ_API_KEY:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)

deepseek_client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
    timeout=15.0
)

# 3. GOOGLE SHEETS SETUP
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    if os.path.exists("credentials.json"):
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    else:
        creds_json = os.getenv("GOOGLE_CREDENTIALS")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    gc = gspread.authorize(creds)
    sh = gc.open("KOTIBA_DATABASE")
    sheet_expenses = sh.worksheet("Xarajatlar")
    sheet_debts = sh.worksheet("Qarzlar")
    sheet_tasks = sh.worksheet("Vazifalar")
    sheet_staff = sh.worksheet("Xodimlar")
except Exception as e:
    print(f"Google Sheets ulanishda xato: {e}")

# 4. SYSTEM PROMPT
SYSTEM_PROMPT_HRD = """
Siz Xo'jayinning (Boshqaruvchi / HRD) eng aqlli va sadoqatli Virtual O'rinbosarisiz.
Sizning vazifangiz:
1. Xarajatlar va qarzlarni tahlil qilish.
2. Xodimlarga topshiriqlarni aniq va tartibli ravishda yo'naltirish.
3. HRD boshqaruvi, audit va biznes jarayonlarida professional maslahat berish.
Javoblarni xushfomala, aniq va ixcham formatda bering.
"""

chat_history = {}

# 5. MENUS
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📉 Xarajatlar Hisoboti", "💰 Qarzlar Hisoboti"],
        ["💼 HRD va Vazifalar", "📈 Forex va Investitsiya"],
        ["🌱 Shaxsiylik / Rivojlanish", "⚙️ Admin Panel"]
    ],
    resize_keyboard=True
)

# 6. HELPER FUNCTIONS
def get_sheet_summary(worksheet):
    try:
        data = worksheet.get_all_values()
        if not data or len(data) <= 1:
            return "Ma'lumot topilmadi."
        headers = data[0]
        rows = data[1:]
        summary = f"Ustunlar: {', '.join(headers)}\n"
        for row in rows[-15:]:
            summary += f"- {', '.join(row)}\n"
        return summary
    except Exception as e:
        return f"Xato: {e}"

def fetch_staff_data():
    try:
        data = sheet_staff.get_all_records()
        return data
    except Exception as e:
        print(f"Xodimlarni olishda xato: {e}")
        return []

# 7. BOT HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum, Xo'jayin! Boshqaruv Markazi va HRD Virtual O'rinbosaringiz xizmatingizda.\n\n"
        "Kerakli bo'limni menyudan tanlang yoki menga matn/ovozli xabar yuboring.",
        reply_markup=MAIN_MENU
    )

async def process_boss_message(text, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Task routing (Xodimlarga topshiriq ajratish)
    staff_data = fetch_staff_data()
    staff_info = [f"{s.get('Ism', '')} (@{s.get('Username', '')})" for s in staff_data if s.get('Username')]
    
    parse_prompt = f"""
    Mavjud xodimlar: {', '.join(staff_info)}
    Xabar: "{text}"
    
    Ushbu xabarda aniq bir xodimga topshiriq berilganmi?
    FAQAT JSON formatida javob bering:
    {{
        "is_task": true/false,
        "target_username": "xodim_username_yoki_ismi",
        "task_details": "topshiriq matni"
    }}
    """
    try:
        res = deepseek_client.chat.completions.create(
            messages=[{"role": "user", "content": parse_prompt}],
            model="deepseek-chat",
            temperature=0.0
        ).choices[0].message.content.strip()

        data = json.loads(res[res.find("{"):res.rfind("}")+1])
        
        if data.get("is_task"):
            target_user = str(data.get("target_username", "")).replace("@", "").lower().strip()
            task_text = data.get("task_details")
            matched = next((s for s in staff_data if target_user in str(s.get('Username', '')).lower() or target_user in str(s.get('Ism', '')).lower()), None)
            
            if matched and matched.get('Chat_ID'):
                await context.bot.send_message(chat_id=matched['Chat_ID'], text=f"📋 RAHBARIYAT TOPSHIRIĞI:\n\n{task_text}")
                sheet_tasks.append_row([datetime.now().strftime("%Y%m%d%H%M%S"), matched.get('Ism') or matched.get('Username'), task_text, datetime.now().strftime("%Y-%m-%d %H:%M"), "Bajarilmoqda", ""])
                await update.message.reply_text(f"🚀 Topshiriq {matched.get('Ism') or matched.get('Username')}ga yetkazildi va Sheets'ga yozildi.")
                return
    except Exception as e:
        print(f"Routing xatosi: {e}")

    # DeepSeek AI Chat
    if user_id not in chat_history:
        chat_history[user_id] = [{"role": "system", "content": SYSTEM_PROMPT_HRD}]
    
    chat_history[user_id].append({"role": "user", "content": text})
    
    try:
        ai_res = deepseek_client.chat.completions.create(
            messages=chat_history[user_id],
            model="deepseek-chat"
        ).choices[0].message.content

        chat_history[user_id].append({"role": "assistant", "content": ai_res})
        await update.message.reply_text(ai_res)
    except Exception as e:
        await update.message.reply_text(f"⚠️ DeepSeek AI javob berishda xatolik yuz berdi: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📉 Xarajatlar Hisoboti":
        await update.message.reply_text("📊 Google Sheets'dan xarajatlar ma'lumoti olinmoqda...")
        summary_data = get_sheet_summary(sheet_expenses)
        prompt = f"Mana xarajatlar jadvali:\n\n{summary_data}\n\nUshbu ma'lumotlar bo'yicha menga xarajatlar tahlili va umumiy xulosa ber."
        await process_boss_message(prompt, update, context)
        return

    elif text == "💰 Qarzlar Hisoboti":
        await update.message.reply_text("📊 Google Sheets'dan qarzlar ma'lumoti olinmoqda...")
        summary_data = get_sheet_summary(sheet_debts)
        prompt = f"Mana qarzlar jadvali:\n\n{summary_data}\n\nUshbu ma'lumotlar bo'yicha menga qarzlar tahlilini ber."
        await process_boss_message(prompt, update, context)
        return

    elif text == "💼 HRD va Vazifalar":
        summary_data = get_sheet_summary(sheet_tasks)
        prompt = f"Mana xodimlarning topshiriqlari jadvali:\n\n{summary_data}\n\nHRD sifatida vazifalar ijrosi bo'yicha qisqa hisobot ber."
        await process_boss_message(prompt, update, context)
        return

    elif text in ["📈 Forex va Investitsiya", "🌱 Shaxsiylik / Rivojlanish", "⚙️ Admin Panel"]:
        await process_boss_message(f"Siz '{text}' bo'limini tanladingiz. Ushbu bo'lim bo'yicha qisqa maslahat ber.", update, context)
        return

    await process_boss_message(text, update, context)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file_path = f"voice_{user_id}.ogg"
    
    try:
        await update.message.reply_text("🎙 Ovozli xabar qabul qilindi, eshitilmoqda...")
        v_file = await context.bot.get_file(update.message.voice.file_id)
        await v_file.download_to_drive(file_path)
        
        if groq_client:
            with open(file_path, "rb") as af:
                tx = groq_client.audio.transcriptions.create(
                    file=(file_path, af.read()), 
                    model="whisper-large-v3",
                    prompt="O'zbek tilidagi ovozli xabar.",
                    response_format="text"
                )
            rec_text = str(tx).strip()
            await update.message.reply_text(f"🗣 Matn: \"{rec_text}\"")
            await process_boss_message(rec_text, update, context)
        else:
            await update.message.reply_text("⚠️ Groq API kaliti o'rnatilmagan.")

    except Exception as e:
        print(f"Voice Error: {e}")
        await update.message.reply_text(f"⚠️ Ovozni tushunishda xatolik bo'ldi: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# 8. FLASK SERVER FOR RENDER
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Kotiba Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# 9. MAIN EXECUTION
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()
