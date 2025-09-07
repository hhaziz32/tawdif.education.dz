import os
import requests
from bs4 import BeautifulSoup
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext
import logging

# --- الإعدادات الأساسية ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get('PORT', 8443))
APP_NAME = os.environ.get("APP_NAME")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- دالة جديدة لتهريب الحروف الخاصة ---
def escape_markdown_v2(text: str) -> str:
    """تهريب الحروف الخاصة لتنسيق MarkdownV2 في تليجرام."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# -----------------------------------------------------------------------------
# دالة فحص الحساب (تم إضافة timeout)
# -----------------------------------------------------------------------------
def check_account(username, password):
    payload = {'user': username, 'password': password}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with requests.Session() as session:
            # تم إضافة timeout=20 لمنع التعليق
            session.post('https://tawdif.education.dz/login', data=payload, headers=headers, timeout=20).raise_for_status()
            response = session.get('https://tawdif.education.dz/results', headers=headers, timeout=20)
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
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error for {username}")
        return {"status": "failed", "message": "انتهت مهلة الاتصال بالموقع. (قد يكون الموقع بطيئًا أو يحظر السيرفر)"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error for {username}: {e}")
        return {"status": "failed", "message": "حدث خطأ عام في الشبكة."}

# -----------------------------------------------------------------------------
# دوال الأوامر الخاصة بالبوت
# -----------------------------------------------------------------------------
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "👋 *أهلاً بك في بوت فحص النتائج*\n\n"
        "يمكنك استخدام هذا البوت لفحص حالة ملفك بسهولة\\.\n\n"
        "🔹 *الأوامر المتاحة:*\n"
        "`/check username:password`\n"
        "لفحص حالة حساب واحد\\.\n\n"
        "*مثال:*\n"
        "`/check aziz3232:aziz3232`"
    )
    await update.message.reply_text(escape_markdown_v2(welcome_message), parse_mode=ParseMode.MARKDOWN_V2)

async def check_single_account(update: Update, context: CallbackContext) -> None:
    try:
        credentials = context.args[0]
        username, password = credentials.split(':', 1)
        
        # إرسال رسالة "جاري الفحص..."
        progress_message = f"⏳ جارٍ فحص الحساب: `{username}`\nالرجاء الانتظار قليلاً..."
        sent_message = await update.message.reply_text(escape_markdown_v2(progress_message), parse_mode=ParseMode.MARKDOWN_V2)
        
        result = check_account(username, password)
        
        if result["status"] == "success":
            data = result["data"]
            status_text = data['status_text']; emoji = "❓"
            if "جاري دراسة" in status_text: emoji = "⏳"
            elif "مطابق" in status_text or "مقبول" in status_text: emoji = "✅"
            elif "مرفوض" in status_text: emoji = "❌"
            message = (
                f"✅ *نتائج الحساب: `{username}`*\n\n"
                f"*الاسم الكامل:* {data['first_name']} {data['last_name']}\n"
                f"*الإقامة:* {data['residence']}\n"
                f"*المنصب:* {data['position']} ({data['subject']})\n\n"
                f"*{emoji} الحالة:* {status_text}"
            )
        else:
            message = f"❌ *فشل فحص الحساب: `{username}`*\n\n*السبب:* {result['message']}"

        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=sent_message.message_id, text=escape_markdown_v2(message), parse_mode=ParseMode.MARKDOWN_V2)

    except (IndexError, ValueError):
        await update.message.reply_text(
            escape_markdown_v2("⚠️ *خطأ في الصيغة*\n\nالرجاء إرسال الأمر بالتنسيق الصحيح:\n`/check username:password`"),
            parse_mode=ParseMode.MARKDOWN_V2
        )

# -----------------------------------------------------------------------------
# دالة التشغيل الرئيسية
# -----------------------------------------------------------------------------
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_single_account))
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://{APP_NAME}/{TOKEN}"
    )

if __name__ == '__main__':
    main()
