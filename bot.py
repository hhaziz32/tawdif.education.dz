import os
import requests
from bs4 import BeautifulSoup
import re
from telegram import Update, ParseMode, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import logging
from flask import Flask, request

# --- الإعدادات الأساسية ---
TOKEN = os.environ.get("TELEGRAM_TOKEN") # سنقرأ التوكن من متغيرات البيئة على السيرفر
PORT = int(os.environ.get('PORT', 8443))
APP_NAME = os.environ.get("APP_NAME") # اسم التطبيق على Render (مثل yourapp.onrender.com)

bot = Bot(token=TOKEN)
app = Flask(__name__)

# (دوال الفحص كما هي بدون تغيير)
def check_account(username, password):
    # ... نفس محتوى الدالة من الكود السابق بدون أي تغيير ...
    payload = {'user': username, 'password': password}
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'}
    try:
        with requests.Session() as session:
            session.post('https://tawdif.education.dz/login', data=payload, headers=headers).raise_for_status()
            response = session.get('https://tawdif.education.dz/results', headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            info_card_header = soup.find('h4', class_='text-white card-title', string=re.compile("معلومات المترشح"))
            if not info_card_header:
                return {"status": "failed", "message": "فشل تسجيل الدخول أو لا توجد بيانات."}
            def get_info_by_label(label_text):
                try: return soup.find('td', string=re.compile(label_text)).find_next('td').text.strip()
                except AttributeError: return "غير متوفر"
            data = {
                "first_name": get_info_by_label("الاسم"), "last_name": get_info_by_label("اللقب"),
                "residence": get_info_by_label("بلدية الإقامة"), "position": get_info_by_label("رتبة الترشح"),
                "subject": get_info_by_label("المادة"), "status_text": soup.find('h1', class_='card-title').text.strip()
            }
            return {"status": "success", "data": data}
    except requests.exceptions.RequestException:
        return {"status": "failed", "message": "حدث خطأ في الشبكة."}

# (دوال الأوامر كما هي بدون تغيير)
def start(update: Update, context: CallbackContext) -> None:
    # ... نفس محتوى الدالة من الكود السابق بدون أي تغيير ...
    welcome_message = "👋 *أهلاً بك في بوت فحص النتائج*\n\n` /check username:password`\n\n*مثال:*\n`/check aziz3232:aziz3232`"
    update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN_V2)

def check_single_account(update: Update, context: CallbackContext) -> None:
    # ... نفس محتوى الدالة من الكود السابق بدون أي تغيير ...
    try:
        credentials = context.args[0]
        username, password = credentials.split(':', 1)
        sent_message = update.message.reply_text(f"⏳ جارٍ فحص الحساب: `{username}`\nالرجاء الانتظار قليلاً...")
        result = check_account(username, password)
        if result["status"] == "success":
            data = result["data"]; status_text = data['status_text']; emoji = "❓"
            if "جاري دراسة" in status_text: emoji = "⏳"
            elif "مطابق" in status_text or "مقبول" in status_text: emoji = "✅"
            elif "مرفوض" in status_text: emoji = "❌"
            message = f"✅ *نتائج الحساب: `{username}`*\n\n*الاسم الكامل:* {data['first_name']} {data['last_name']}\n*الإقامة:* {data['residence']}\n*المنصب:* {data['position']} ({data['subject']})\n\n*{emoji} الحالة:* {status_text}"
        else:
            message = f"❌ *فشل فحص الحساب: `{username}`*\n\n*السبب:* {result['message']}"
        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=sent_message.message_id, text=message, parse_mode=ParseMode.MARKDOWN_V2)
    except (IndexError, ValueError):
        update.message.reply_text("⚠️ *خطأ في الصيغة*\n\nالرجاء إرسال الأمر بالتنسيق الصحيح:\n`/check username:password`", parse_mode=ParseMode.MARKDOWN_V2)

# --- الجزء الجديد الخاص بـ Webhook ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook_handler():
    update = Update.de_json(request.get_json(force=True), bot)
    updater.dispatcher.process_update(update)
    return 'ok'

if __name__ == "__main__":
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("check", check_single_account))

    # إعداد الـ webhook
    webhook_url = f"https://{APP_NAME}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    
    # تشغيل خادم الويب
    app.run(host="0.0.0.0", port=PORT)
