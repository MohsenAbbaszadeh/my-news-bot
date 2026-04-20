import feedparser
import requests
import os
from datetime import datetime

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SENT_FILE = "sent_news.txt"
USERS_FILE = "users.txt" # فایل جدید برای ذخیره کاربران

# لیست منابع
SOURCES = {
    "ایران اینترنشنال": "https://www.iranintl.com/rss",
    "بی‌بی‌سی فارسی": "https://www.bbc.com/persian/index.xml",
    "رادیو فردا": "https://www.radiofarda.com/rss/?count=20",
    "ویدیوهای ایران اینترنشنال": "https://www.youtube.com/feeds/videos.xml?channel_id=UC6P_fS0U40C_H_A_XUv9XAw",
    "ویدیوهای بی‌بی‌سی فارسی": "https://www.youtube.com/feeds/videos.xml?channel_id=UC7O7Y077X_hX-PZ_XmUshXg"
}

def get_saved_data(filename):
    if not os.path.exists(filename): return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())

def save_data(filename, data_set):
    with open(filename, "w", encoding="utf-8") as f:
        for item in data_set:
            f.write(str(item) + "\n")

# پیدا کردن کاربران جدیدی که Start زده‌اند
def update_users_list(users_set):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        res = requests.get(url).json()
        if res.get("ok"):
            for item in res["result"]:
                if "message" in item and "chat" in item["message"]:
                    chat_id = str(item["message"]["chat"]["id"])
                    users_set.add(chat_id)
    except Exception as e:
        print("خطا در دریافت کاربران:", e)
    return users_set

# ارسال پیام برای تمام کاربران لیست
def broadcast_message(text, users_set):
    for chat_id in users_set:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload)

def run_bot():
    sent_links = get_saved_data(SENT_FILE)
    users = get_saved_data(USERS_FILE)
    
    # به‌روزرسانی لیست کاربران
    users = update_users_list(users)
    save_data(USERS_FILE, users)

    if not users:
        print("هنوز هیچ کاربری ربات را استارت نکرده است.")
        return

    headers = {'User-Agent': 'Mozilla/5.0'}
    daily_headlines = []

    for name, url in SOURCES.items():
        try:
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:5]:
                if entry.link not in sent_links:
                    summary = entry.get('summary', '') or entry.get('description', '')
                    summary = (summary[:300] + '...') if len(summary) > 300 else summary
                    
                    if "youtube" in entry.link:
                        message = f"🎬 **ویدیو جدید: {name}**\n\n📌 {entry.title}\n\n🔗 {entry.link}"
                    else:
                        message = f"📰 **{name}**\n\n🔹 **{entry.title}**\n\n📖 {summary}\n\n🔗 [مطالعه کامل خبر]({entry.link})"
                    
                    # ارسال به همه کاربران
                    broadcast_message(message, users)
                    
                    sent_links.add(entry.link)
                    daily_headlines.append(entry.title)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

    # --- بخش گزارش روزانه برای تورنتو (ساعت 8 صبح) ---
    current_hour = datetime.now().hour
    if current_hour == 12: 
        if daily_headlines:
            summary_text = "☀️ **بررسی مطبوعات: صبح بخیر!**\n\nمهم‌ترین عناوین خبری:\n\n" + "\n\n".join([f"▫️ {h}" for h in daily_headlines[:12]])
            broadcast_message(summary_text, users)

if __name__ == "__main__":
    run_bot()
