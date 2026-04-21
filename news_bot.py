import feedparser
import requests
import os
from datetime import datetime
import google.generativeai as genai

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENT_FILE = "sent_news.txt"
USERS_FILE = "users.txt"
SOURCES_FILE = "sources.txt"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

def load_sources():
    sources = {}
    if not os.path.exists(SOURCES_FILE):
        print("فایل sources.txt پیدا نشد!")
        return sources
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # نادیده گرفتن خطوط خالی و کامنت‌ها
            if line and "," in line and not line.startswith("#"):
                name, url = line.split(",", 1)
                sources[name.strip()] = url.strip()
    return sources

def get_saved_data(filename):
    if not os.path.exists(filename): return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())

def save_data(filename, data_set):
    with open(filename, "w", encoding="utf-8") as f:
        for item in data_set:
            f.write(str(item) + "\n")

def update_users_list(users_set):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        res = requests.get(url).json()
        if res.get("ok"):
            for item in res["result"]:
                if "message" in item and "chat" in item["message"]:
                    users_set.add(str(item["message"]["chat"]["id"]))
    except Exception as e:
        pass
    return users_set

def broadcast_message(text, users_set):
    for chat_id in users_set:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload)

def run_bot():
    sent_links = get_saved_data(SENT_FILE)
    users = get_saved_data(USERS_FILE)
    users = update_users_list(users)
    save_data(USERS_FILE, users)

    if not users:
        return

    sources_dict = load_sources()
    headers = {'User-Agent': 'Mozilla/5.0'}
    daily_headlines = []

    for name, url in sources_dict.items():
        try:
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:3]: 
                if entry.link not in sent_links:
                    summary = entry.get('summary', '') or entry.get('description', '')
                    summary = (summary[:300] + '...') if len(summary) > 300 else summary
                    
                    ai_analysis = ""
                    # تحلیل اختصاصی سیاسی و اقتصادی با هوش مصنوعی
                    if ai_model and "youtube" not in entry.link and "reddit" not in entry.link:
                        try:
                            prompt = f"به عنوان یک تحلیلگر ارشد مسائل سیاسی و اقتصادی ایران، این خبر را در ۲ الی ۳ خط به زبان فارسی بررسی کن. بگو این اتفاق چه تاثیری دارد:\nتیتر: {entry.title}\nمتن: {summary}"
                            response_ai = ai_model.generate_content(prompt)
                            ai_analysis = f"\n\n🧠 **تحلیل استراتژیک:**\n{response_ai.text.strip()}"
                        except Exception as e:
                            print(f"AI Error: {e}")

                    message = f"📰 **{name}**\n\n🔹 **{entry.title}**{ai_analysis}\n\n🔗 [لینک منبع]({entry.link})"
                    broadcast_message(message, users)
                    sent_links.add(entry.link)
                    daily_headlines.append(entry.title)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

    # گزارش روزانه ساعت 8 صبح تورنتو (12 UTC)
    current_hour = datetime.now().hour
    if current_hour == 12 and daily_headlines: 
        summary_text = "☀️ **داشبورد صبحگاهی: تورنتو**\n\nمهم‌ترین رویدادهای ایران:\n\n" + "\n\n".join([f"▫️ {h}" for h in daily_headlines[:12]])
        broadcast_message(summary_text, users)

if __name__ == "__main__":
    run_bot()
