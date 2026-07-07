# telegram/bot.py
import telebot
from .config import TELEGRAM_BOT_TOKEN, DEFAULT_LIMIT, MAX_LIMIT
from .sender import get_top_jobs, format_jobs_message


# راه‌اندازی ربات
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, """
🤖 *MatchFlow Pipeline Bot*

📊 *دستورات موجود:*
/user [number]  ← تعداد آگهی‌های برتر (پیش‌فرض ۳۰)
/help           ← راهنما

📌 *مثال:*
/user 10        ← ۱۰ آگهی برتر
/user 50        ← ۵۰ آگهی برتر

📊 *حداکثر:* ۱۰۰ آگهی
""", parse_mode='Markdown')


@bot.message_handler(commands=['user'])
def handle_user_command(message):
    try:
        # استخراج عدد از دستور
        parts = message.text.split()
        limit = int(parts[1]) if len(parts) > 1 else DEFAULT_LIMIT
        limit = min(limit, MAX_LIMIT)
        
        # دریافت آگهی‌ها
        jobs = get_top_jobs(limit)
        if not jobs:
            bot.reply_to(message, "❌ هیچ آگهی با امتیاز پیدا نشد!")
            return
        
        # ارسال پیام
        msg = format_jobs_message(jobs)
        
        # تقسیم پیام به دلیل محدودیت ۴۰۹۶ کاراکتری
        chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
        for chunk in chunks:
            bot.send_message(message.chat.id, chunk, parse_mode='Markdown', disable_web_page_preview=True)
        
    except ValueError:
        bot.reply_to(message, "❌ لطفاً یک عدد معتبر وارد کن.\nمثال: /user 20")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)}")


def run_bot():
    """اجرای ربات"""
    print("🤖 Telegram Bot is running...")
    bot.infinity_polling()


if __name__ == "__main__":
    run_bot()