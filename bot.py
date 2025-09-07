import os
import requests
from bs4 import BeautifulSoup
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext
import logging

# --- الإعدادات الأساسية ---
# سيتم قراءة هذه المتغيرات من إعدادات سيرفر Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get('PORT', 8443))
APP_NAME = os.environ.get("APP_NAME") # e.g., your-app-name.onrender.com

# إعداد تسجيل الدخول لتتبع الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# الجزء الأساسي: دالة فحص الحساب (لا تغيير هنا)
# -----------------------------------------------------------------------------
def check_account(username, password):
    payload = {'user': username, 'password': password}
    headers = {'User-Agent': 'Mozilla/5.0'}
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
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error for {username}: {e}")
        return {"status": "failed", "message": "حدث خطأ في الشبكة."}

# -----------------------------------------------------------------------------
# دوال الأوامر الخاصة بالبوت (تم تحديثها لتكون async)
# -----------------------------------------------------------------------------
async def start(update: Update, context: CallbackContext) -> None:
    """إرسال رسالة ترحيب عند إرسال الأمر /start."""
    welcome_message = (
        "👋 *أهلاً بك في بوت فحص النتائج*\n\n"
        "يمكنك استخدام هذا البوت لفحص حالة ملفك بسهولة\\.\n\n"
        "🔹 *الأوامر المتاحة:*\n"
        "`/check username:password`\n"
        "لفحص حالة حساب واحد\\.\n\n"
        "*مثال:*\n"
        "`/check aziz3232:aziz3232`"
    )
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN_V2)

async def check_single_account(update: Update, context: CallbackContext) -> None:
    """فحص حساب واحد يتم إرساله مع الأمر."""
    try:
        credentials = context.args[0]
        username, password = credentials.split(':', 1)
        
        # إرسال رسالة "جاري الفحص..."
        sent_message = await update.message.reply_text(f"⏳ جارٍ فحص الحساب: `{username}`\nالرجاء الانتظار قليلاً\\.\\.\\.")
        
        # استدعاء دالة الفحص
        result = check_account(username, password)
        
        # تنسيق الرسالة النهائية
        if result["status"] == "success":
            data = result["data"]
            status_text = data['status_text']
            
            emoji = "❓"
            if "جاري دراسة" in status_text: emoji = "⏳"
            elif "مطابق" in status_text or "مقبول" in status_text: emoji = "✅"
            elif "مرفوض" in status_text: emoji = "❌"

            # يجب تهريب الأحرف الخاصة في MarkdownV2
            message = (
                f"✅ *نتائج الحساب: `{username}`*\n\n"
                f"*الاسم الكامل:* {data['first_name']} {data['last_name']}\n"
                f"*الإقامة:* {data['residence']}\n"
                f"*المنصب:* {data['position']} \\({data['subject']}\\)\n\n"
                f"*{emoji} الحالة:* {status_text}"
            )
        else:
            message = f"❌ *فشل فحص الحساب: `{username}`*\n\n*السبب:* {result['message']}"

        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=sent_message.message_id, text=message, parse_mode=ParseMode.MARKDOWN_V2)

    except (IndexError, ValueError):
        await update.message.reply_text(
            "⚠️ *خطأ في الصيغة*\n\n"
            "الرجاء إرسال الأمر بالتنسيق الصحيح:\n"
            "`/check username:password`",
            parse_mode=ParseMode.MARKDOWN_V2
        )

# -----------------------------------------------------------------------------
# دالة التشغيل الرئيسية (محدثة بالكامل لـ v20+)
# -----------------------------------------------------------------------------
def main() -> None:
    """إنشاء وتشغيل البوت."""
    application = Application.builder().token(TOKEN).build()

    # تسجيل الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_single_account))

    # تشغيل البوت باستخدام Webhook (الطريقة الموصى بها للسيرفرات)
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://{APP_NAME}/{TOKEN}"
    )

if __name__ == '__main__':
    main()
