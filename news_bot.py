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
        print(f"تعداد خبرهای پیدا شده: {len(feed.entries)}")
        
        if len(feed.entries) == 0:
            print("❌ هیچ خبری پیدا نشد! مشکل از دریافت اطلاعات است.")
            return

        # فقط اولین و جدیدترین خبر را برمی‌داریم
        entry = feed.entries[0] 
        print(f"تیتر خبر: {entry.title}")
        
        if not GROQ_API_KEY:
            print("❌ کلید Groq API در گیت‌هاب پیدا نشد!")
            return
            
        print("در حال ارتباط با هوش مصنوعی Groq...")
        client = Groq(api_key=GROQ_API_KEY)
        
        prompt = (
            f"You are a news translator. Read this:\n"
            f"Headline: '{entry.title}'\n\n"
            f"Reply EXACTLY in this format:\n"
            f"PERSIAN_TITLE: [translate headline to Persian]\n"
            f"SUMMARY: [write a 2-sentence factual summary in Persian]"
        )
        
        # استفاده از مدل فوق‌سریع و فعالِ Groq
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.1,
        )
        
        res = chat_completion.choices[0].message.content
        print("✅ ترجمه هوش مصنوعی با موفقیت انجام شد.")
        
        # مرتب‌سازی متن پیام
        persian_title = res.split("PERSIAN_TITLE:")[1].split("\n")[0].strip() if "PERSIAN_TITLE:" in res else entry.title
        summary = res.split("SUMMARY:")[1].strip() if "SUMMARY:" in res else "بدون خلاصه"
        
        message = (
            f"🔥 **اولین خبر ترجمه شده با هوش مصنوعی**\n\n"
            f"📌 **{persian_title}**\n\n"
            f"📝 **خلاصه:** {summary}\n\n"
            f"🔗 [لینک خبر]({entry.link})"
        )
        
        broadcast_message(message)
        print("✅ پیام به تلگرام ارسال شد!")
        
    except Exception as e:
        print(f"❌ خطای سیستم: {e}")

if __name__ == "__main__":
    run_bot()
