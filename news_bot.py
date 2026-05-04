import feedparser
import requests
import os
from groq import Groq

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SENT_FILE = "sent_news.txt"

def get_saved_links():
    if not os.path.exists(SENT_FILE): return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())

def save_link(link):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def broadcast_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False}
    requests.post(url, data=payload)

def run_bot():
    print("شروع رادار اخبار جهان...")
    sent_links = get_saved_links()
    
    feed_url = "https://news.google.com/rss/search?q=source:Reuters+when:1h&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(feed_url)
        if len(feed.entries) == 0:
            print("خبر جدیدی در یک ساعت گذشته یافت نشد.")
            return

        client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        if not client:
            print("❌ کلید Groq پیدا نشد!")
            return
            
        for entry in feed.entries[:3]:
            if entry.link in sent_links:
                continue 
                
            print(f"در حال بررسی تیتر: {entry.title}")
            
            # 🧠 پرامپت اصلاح‌شده: فقط تاکید روی الفبای فارسی (بدون اشاره به زبان‌های دیگر)
            prompt = (
                f"You are an expert Persian (Farsi) news editor and a top-tier translator. "
                f"Analyze this headline: '{entry.title}'\n\n"
                f"Task 1: Rate its GLOBAL IMPORTANCE from 1 to 10.\n"
                f"Task 2: IF the score is 5 or higher, write a professional Persian news report.\n\n"
                f"CRITICAL RULES FOR TRANSLATION:\n"
                f"1. Write EXACTLY and ONLY in the Persian language (Farsi).\n"
                f"2. Use ONLY the standard Persian alphabet. NEVER use any other scripts, letters, or foreign characters.\n"
                f"3. Ensure the text flows naturally, like a formal report from a major Iranian news agency (e.g., IRNA or ISNA).\n"
                f"4. Write 2 well-structured paragraphs without repeating sentences.\n\n"
                f"Reply EXACTLY in this format:\n"
                f"SCORE: [number from 1 to 10]\n"
                f"PERSIAN_TITLE: [Catchy Persian title]\n"
                f"SUMMARY: [Detailed, perfect Persian analysis]"
            )
            
            # 🚀 استفاده از مدل Gemma 2 گوگل که در فارسی شاهکار است
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="gemma2-9b-it", 
                temperature=0.3, 
            )
            
            res = chat_completion.choices[0].message.content
            
            score = 0
            for line in res.split('\n'):
                if "SCORE:" in line:
                    try: score = int(''.join(filter(str.isdigit, line)))
                    except: score = 0
                    
            print(f"نمره اهمیت این خبر: {score}/10")
            
            if score >= 5:
                persian_title = res.split("PERSIAN_TITLE:")[1].split("\n")[0].strip() if "PERSIAN_TITLE:" in res else entry.title
                summary = res.split("SUMMARY:")[1].strip() if "SUMMARY:" in res else "جزئیات بیشتر در لینک خبر..."
                
                icon = "🚨" if score >= 8 else "📰"
                urgency_text = "خبر فوری و بسیار مهم!" if score >= 8 else "خبر مهم جهانی"
                
                message = (
                    f"{icon} **{urgency_text}**\n"
                    f"🔹 میزان اهمیت: {score}/10\n\n"
                    f"**{persian_title}**\n\n"
                    f"📝 **شرح ماجرا:**\n{summary}\n\n"
                    f"🔗 [مشاهده منبع اصلی خبر]({entry.link})"
                )
                
                broadcast_message(message)
                print("✅ پیام به تلگرام ارسال شد!")
            else:
                print("❌ خبر معمولی بود. (رد شد)")
                
            save_link(entry.link)
            
    except Exception as e:
        print(f"❌ خطای سیستم: {e}")

if __name__ == "__main__":
    run_bot()
