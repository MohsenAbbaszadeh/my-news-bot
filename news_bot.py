import feedparser
import requests
import os
from groq import Groq

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def broadcast_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False}
    requests.post(url, data=payload)

def run_bot():
    print("شروع دریافت اخبار...")
    # لینک مستقیم گوگل نیوز برای اخبار رویترز
    feed_url = "https://news.google.com/rss/search?q=source:Reuters+when:1d&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(feed_url)
        
        if len(feed.entries) == 0:
            print("❌ هیچ خبری پیدا نشد!")
            return

        # گرفتن جدیدترین خبر
        entry = feed.entries[0] 
        
        if not GROQ_API_KEY:
            print("❌ کلید Groq API پیدا نشد!")
            return
            
        print("در حال ارتباط با هوش مصنوعی...")
        client = Groq(api_key=GROQ_API_KEY)
        
        # 🧠 دستور (پرامپت) حرفه‌ای به هوش مصنوعی
        prompt = (
            f"You are an expert international journalist and a highly skilled native Persian translator. "
            f"Read the following news headline: '{entry.title}'\n\n"
            f"Based on this news, write a comprehensive, flawless, and highly professional news report in Persian. "
            f"Reply EXACTLY in this format:\n"
            f"PERSIAN_TITLE: [Provide a catchy, accurate, and professional Persian translation of the headline]\n"
            f"SUMMARY: [Write a detailed explanation in 2 to 3 well-structured paragraphs. "
            f"Explain the context of the news, why it is important, and provide a clear analysis. "
            f"The tone MUST be strictly journalistic, neutral, and grammatically perfect in Persian. "
            f"Do not use robotic language; make it sound like a top-tier Persian news agency.]"
        )
        
        # استفاده از مدل فعال و تنظیم دمای هوش مصنوعی برای متن روان‌تر
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.3, 
        )
        
        res = chat_completion.choices[0].message.content
        print("✅ ترجمه هوش مصنوعی با موفقیت انجام شد.")
        
        # جداسازی تیتر و متن
        persian_title = res.split("PERSIAN_TITLE:")[1].split("\n")[0].strip() if "PERSIAN_TITLE:" in res else entry.title
        summary = res.split("SUMMARY:")[1].strip() if "SUMMARY:" in res else res
        
        # قالب‌بندی زیبای پیام برای تلگرام
        message = (
            f"📰 **{persian_title}**\n\n"
            f"📝 **شرح و تحلیل خبر:**\n{summary}\n\n"
            f"🔗 [مشاهده منبع اصلی خبر]({entry.link})"
        )
        
        broadcast_message(message)
        print("✅ پیام به تلگرام ارسال شد!")
        
    except Exception as e:
        print(f"❌ خطای سیستم: {e}")

if __name__ == "__main__":
    run_bot()
