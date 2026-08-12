$pyScript = @"
# -*- coding: utf-8 -*-
import os, json, time, re, traceback
import gspread
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from groq import Groq

TELEGRAM_TOKEN = "8669976589:AAGNJ4jaDIJpHwm_m7T9q97a_D5DqfXLeGA"
DEEPSEEK_API_KEY = "sk-fb624f61e71447869482eb55c1f9179f"
GROQ_API_KEY = "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"
ADMIN_ID = 686359645

google_credentials_dict = {
  "type": "service_account",
  "project_id": "emerald-vent-505112-h4",
  "private_key_id": "4c05f5f0b53ca5decf3389867c636c8c21f9b27e",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCnhOfrVZ7rDUSF\nbVfVXNGg/IYF7CD1ndKpVapGTXFPVdr4R4B3qOlimsSxyU8uB1fIoQeacZAtK1Gq\nUhqc+5G0Vctkf4wIMHTKN9QRbxJqrQtpxDO7ZJ0xcKyZiu+l+PjT6/K+nkQWSFZu\n6I1RXxPhC9i6EfHOAH0gWxOtFkrnTkY2+iD37M7BrY2+jNR3yoqlkRo7Em5Bh+Im\nUYisgWNHsiDVVnL3NF/4corfLpAs94EC9nAe4PfyvwpiDrn5RfHfIKeGUpOTfxLH\nxUr7niSPV+v7+0YcZcwWKMBuHXb9Lxz+qPDChwrg5ALzUyqDEM5llA/CkKK+QmKg\nweHA+FOFAgMBAAECggEAIrmBHZ489/pjFsloqJi594YA/h9JYcCaV3Gjfzk0YL6q\nSkcAEU3ZOxBb74KMQD1TbAo9Oj2KJmLRZd3pGFtpg5k5NRbfXx80Rmq2Mfr1NVmz\ngPQjyRd9Ii96B8XuEVh/s+Y4Bl1mPbw29nyMNq7fvwmmnkNz/UDKrzdR59I0KqgQ\nHxNOAgS9vH8lumoucapc8eS2V/ROkz3kRp3HUmB+yuLN3Gus3OuEfhHyoKRF5VGr\nFkt/I9Ug2upkB1OEXwfo4MzQS3MV1vAJb5N1ahe/WOh1OOcEy4K9WQ4hf5qhzBLV\nPSg2nhhu0RlszM/JHAzRgVy282YY31G7s7DBWY3eQQKBgQDZc0xhmWgIXO0b+NrZ\nvFe/mz5IR5naVRrsjmuYEl5R83Rm3SY6UI+3DUbB/xjAy9175bRjjIt0enkCLuZh\nUVyATkdxjT4nwvKd4mQxB9DjyOzS75kZoliYGqF2iMyoAS16Krik3HBP+u6G1VNi\njXOB2mftueSj3o/cjx7hxJupdQKBgQDFN4ta53I3y03/qMotnWBjuyCYdp173iun\nb7iaAnGWuITxoaBW8P7lwX96W9tE/o3ZK4fvOY2s7S3WRIpmI1sOxUKkmlxwTJWR\n+ubIel2vt9FTZwUlIufH6gz/Wkekg840OxV7BciyikuuPRTLQqHsmpU4xt3aQGBJ\nZqwoU1yv0QKBgBwo4UBWZHGIzy/rJzRBPr/Sc9taYmMy2DzAKNDVuB82vuE/TF8K\n5cGX14zx4xu8it8rnROzNLAN2DPfLPh3V9pJyNi8qMrvZQnrMnxi/bsx3vFmE9aM\n/pocAMLf7ljnZiNG+whmf6jr3w3Y/GZr2QR86y6O/zv1a33tjts/4cStAoGAAV2/\nI2QTEHviEHFU5Tf/4PD86tF3idIiL0jA2KBHtSmWEi5yc+e7fE/42BomzLWOugBp\nMqkNaDNEbAWRh9+a0+Fd8tH27fg52QcJ7j2axIrbcl52VKmHPYVLjcFMWcFn/kii\nf3WszD/VAmH98OKHSKJRglEuXEKx6BBEBQt+yuECgYAoA4I24qQzTDx/sugD+n0b\n09j05QlCl6PCMg7+Eky8c+JzvALiy+iMrb3d42gQluHz+1IFTDGRyyQlqxhLmK6z\nvqFZWg4sOBJbZCu77xXRowWhc3Gsfd84tE0ish6WyydnzW7huNBamhhlODENcUO8\nNUlqK31ijd0BLHkMOrue4w==\n-----END PRIVATE KEY-----\n",
  "client_email": "kotiba-bot@emerald-vent-505112-h4.iam.gserviceaccount.com",
  "client_id": "102442671461446325892",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/kotiba-bot%40emerald-vent-505112-h4.iam.gserviceaccount.com"
}

gc = gspread.service_account_from_dict(google_credentials_dict)
sh = gc.open("Kotiba_Baza")

def get_or_create_sheet(title, headers):
    try:
        ws = sh.worksheet(title)
        if not ws.get_all_values():
            ws.append_row(headers)
        return ws
    except:
        ws = sh.add_worksheet(title=title, rows="100", cols="10")
        ws.append_row(headers)
        return ws

sheet_staff = get_or_create_sheet("Xodimlar", ["Username", "Chat_ID", "Ism", "Lavozim", "Vazifalari", "Hisobot_Vaqti"])
sheet_tasks = get_or_create_sheet("Topshiriqlar", ["ID", "Xodim", "Topshiriq", "Berilgan_Vaqt", "Status", "Javob"])
sheet_debts = get_or_create_sheet("Qarzlar", ["Sana", "Shaxs/Muassasa", "Mablağ", "Tur", "Izoh"])
sheet_expenses = get_or_create_sheet("Xarajatlar", ["Sana", "Kategoriya", "Mablağ", "Izoh"])

deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
groq_client = Groq(api_key=GROQ_API_KEY)
chat_history = {}

SYSTEM_PROMPT_HRD = """Siz HR Direktori (HRD) uchun O'rinbosar, Strategik Ustoz, Moliyaviy Tahlilchi va Boshqaruv Assistentisiz.
Sizning vazifangiz:
1. Rahbarga HR tizimi, moliyaviy tahlillar (qarz va xarajatlar), Forex hamda shaxsiy rivojlanishda professional yordam berish.
2. Google Sheets'dan kelgan xarajat va qarz ma'lumotlarini aniq va tushunarli tartibda umumlashtirib xulosa berish."""

MAIN_MENU = ReplyKeyboardMarkup([
    ["💼 HRD va Vazifalar", "📈 Forex va Investitsiya"],
    ["💰 Qarzlar Hisoboti", "📉 Xarajatlar Hisoboti"],
    ["🌱 Shaxsiylik / Rivojlanish", "⚙️ Admin Panel"]
], resize_keyboard=True)

def fetch_staff_data():
    rows = sheet_staff.get_all_values()
    if not rows or len(rows) <= 1:
        return []
    staff_data = []
    for idx, row in enumerate(rows[1:], start=2):
        if len(row) >= 1 and row[0]:
            staff_data.append({
                "row_idx": idx,
                "Username": str(row[0]).replace("@", "").strip(),
                "Chat_ID": str(row[1]) if len(row) > 1 else "",
                "Ism": str(row[2]) if len(row) > 2 else "",
                "Lavozim": str(row[3]) if len(row) > 3 else ""
            })
    return staff_data

def get_sheet_summary(sheet_obj):
    rows = sheet_obj.get_all_values()
    if not rows or len(rows) <= 1:
        return "Hozircha hech qanday ma'lumot yozilmagan."
    
    # Oxirgi 15 ta yozuvni olish
    headers = rows[0]
    data_str = " | ".join(headers) + "\n" + "-"*30 + "\n"
    for r in rows[-15:]:
        data_str += " | ".join(r) + "\n"
    return data_str

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "Assalomu alaykum, Xo'jayin! Boshqaruv Markazi hamda HRD Virtual O'rinbosaringiz xizmatingizda.\n\n"
            "• Menyu tugmalari orqali xarajat, qarz va vazifalar tahlilini olishingiz mumkin.",
            reply_markup=MAIN_MENU
        )
        return

async def process_boss_message(text, update: Update, context: ContextTypes.DEFAULT_TYPE):
    staff_data = fetch_staff_data()
    staff_info = [f"{s['Ism']} (@{s['Username']})" for s in staff_data if s['Username']]
    
    parse_prompt = f"""
    Mavjud xodimlar ro'yxati: {', '.join(staff_info)}
    Rahbar xabari: "{text}"
    
    Vazifa: Ushbu xabarda aniq bir xodimga topshiriq berilganmi?
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
            matched = next((s for s in staff_data if target_user in s['Username'].lower() or target_user in s['Ism'].lower()), None)
            
            if matched and matched.get('Chat_ID'):
                await context.bot.send_message(chat_id=matched['Chat_ID'], text=f"📋 RAHBARIYAT TOPSHIRIĞI:\n\n{task_text}")
                sheet_tasks.append_row([datetime.now().strftime("%Y%m%d%H%M%S"), matched['Ism'] or matched['Username'], task_text, datetime.now().strftime("%Y-%m-%d %H:%M"), "Bajarilmoqda", ""])
                await update.message.reply_text(f"🚀 Topshiriq {matched['Ism'] or matched['Username']}ga yetkazildi.")
                return
    except Exception as e:
        print(f"Routing error: {e}")

    if ADMIN_ID not in chat_history:
        chat_history[ADMIN_ID] = [{"role": "system", "content": SYSTEM_PROMPT_HRD}]
    
    chat_history[ADMIN_ID].append({"role": "user", "content": text})
    
    ai_res = deepseek_client.chat.completions.create(
        messages=chat_history[ADMIN_ID],
        model="deepseek-chat"
    ).choices[0].message.content

    chat_history[ADMIN_ID].append({"role": "assistant", "content": ai_res})
    await update.message.reply_text(ai_res)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id == ADMIN_ID:
        if text == "📉 Xarajatlar Hisoboti":
            await update.message.reply_text("📊 Google Sheets'dan xarajatlar ma'lumoti olinmoqda...")
            summary_data = get_sheet_summary(sheet_expenses)
            prompt = f"Mana Google Sheets'dagi xarajatlar jadvali:\n\n{summary_data}\n\nUshbu ma'lumotlar bo'yicha menga xarajatlar tahlili, umumiy summa va qisqa xulosa ber."
            await process_boss_message(prompt, update, context)
            return

        elif text == "💰 Qarzlar Hisoboti":
            await update.message.reply_text("📊 Google Sheets'dan qarzlar ma'lumoti olinmoqda...")
            summary_data = get_sheet_summary(sheet_debts)
            prompt = f"Mana Google Sheets'dagi qarzlar jadvali:\n\n{summary_data}\n\nUshbu ma'lumotlar bo'yicha menga kimdan qancha qarzimiz borligi yoki berilgan qarzlarning umumiy tahlilini ber."
            await process_boss_message(prompt, update, context)
            return

        elif text == "💼 HRD va Vazifalar":
            summary_data = get_sheet_summary(sheet_tasks)
            prompt = f"Mana xodimlarning topshiriqlari va hisobotlari jadvali:\n\n{summary_data}\n\nHRD sifatida vazifalar ijrosi va holati bo'yicha qisqa hisobot ber."
            await process_boss_message(prompt, update, context)
            return

        elif text in ["📈 Forex va Investitsiya", "🌱 Shaxsiylik / Rivojlanish", "⚙️ Admin Panel"]:
            await process_boss_message(f"Siz '{text}' bo'limini tanladingiz. Ushbu bo'lim bo'yicha oxirgi holat va maslahatni bering.", update, context)
            return

        await process_boss_message(text, update, context)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file_path = f"voice_{user_id}.ogg"
    
    try:
        v_file = await context.bot.get_file(update.message.voice.file_id)
        await v_file.download_to_drive(file_path)
        
        with open(file_path, "rb") as af:
            tx = groq_client.audio.transcriptions.create(
                file=(file_path, af.read()), 
                model="whisper-large-v3",
                prompt="Ushbu ovozli xabar o'zbek tilida aytilgan. Iltimos, uni faqat o'zbek alifbosida matnga o'giring.",
                response_format="text"
            )
        rec_text = str(tx).strip()
        await update.message.reply_text(f"🗣 Ovoz: \"{rec_text}\"")

        if user_id == ADMIN_ID:
            await process_boss_message(rec_text, update, context)

    except Exception as e:
        await update.message.reply_text(f"Ovoz processing xatosi: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("Avtonom HRD Ustoz va Kotiba Bot ishga tushdi...")
    app.run_polling()
"@

$bytes = [System.Text.Encoding]::UTF8.GetBytes($pyScript)
$base64 = [Convert]::ToBase64String($bytes)
python -c "import base64; exec(base64.b64decode('$base64').decode('utf-8'))"