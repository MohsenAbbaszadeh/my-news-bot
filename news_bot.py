import feedparser
import requests
import os
from datetime import datetime

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
SENT_FILE = "sent_news.txt"

# لیست منابع شامل یوتیوب برای ویدیوها
SOURCES = {
    "ایران اینترنشنال (متنی)": "https://www.iranintl.com/rss",
    "بی‌بی‌سی فارسی (متنی)": "https://www.bbc.com/persian/index.xml",
    "رادیو فردا": "https://www.radiofarda.com/rss/?count=20",
    "ویدیوهای ایران اینترنشنال": "https://www.youtube.com/feeds/videos.xml?channel_id=UC6P_fS0U40C_H_A_XUv9XAw",
    "ویدیوهای بی‌بی‌سی فارسی": "https://www.youtube.com/feeds/videos.xml?channel_id=UC7O7Y077X_hX-PZ_XmUshXg"
}

def get_sent_links():
    if not os.path.exists(SENT_FILE): return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())

def save_sent_link(link):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    return requests.post(url, data=payload)

def run_bot():
    sent_links = get_sent_links()
    headers = {'User-Agent': 'Mozilla/5.0'}
    daily_headlines = []

    for name, url in SOURCES.items():
        try:
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:5]: # بررسی ۵ خبر آخر
                if entry.link not in sent_links:
                    # استخراج خلاصه خبر (اگر وجود داشت)
                    summary = entry.get('summary', '') or entry.get('description', '')
                    # پاک کردن تگ‌های HTML احتمالی از خلاصه
                    summary = (summary[:300] + '...') if len(summary) > 300 else summary
                    
                    if "youtube" in entry.link:
                        message = f"🎬 **ویدیو جدید: {name}**\n\n📌 {entry.title}\n\n🔗 {entry.link}"
                    else:
                        message = f"📰 **{name}**\n\n🔹 **{entry.title}**\n\n📖 {summary}\n\n🔗 [مطالعه کامل خبر]({entry.link})"
                    
                    send_telegram(message)
                    save_sent_link(entry.link)
                    daily_headlines.append(entry.title)
        except Exception as e:
            print(f"Error in {name}: {e}")

    # --- بخش گزارش روزانه ---
    # اگر ساعت به وقت سرور بین ۲۰ تا ۲۱ بود، یک خلاصه بفرست (تقریبا آخر شب ایران)
    current_hour = datetime.now().hour
    if current_hour == 12: 
        summary_text = "🌙 **خلاصه اتفاقات مهم امروز:**\n\n" + "\n\n".join([f"▫️ {h}" for h in daily_headlines[:10]])
        send_telegram(summary_text)

if __name__ == "__main__":
    run_bot()
