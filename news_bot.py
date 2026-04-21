import feedparser
import requests
import os
from datetime import datetime
import google.generativeai as genai

# --- تنظیمات امنیتی ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENT_FILE = "sent_news.txt"
USERS_FILE = "users.txt"
SOURCES_FILE = "sources.txt"

# فعال‌سازی هوش مصنوعی گوگل
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        ai_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"AI Config Error: {e}")
        ai_model = None
else:
    ai_model = None

def load_sources():
    sources = {}
    if os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
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
        print("هیچ کاربری یافت نشد. لطفاً در تلگرام به ربات پیام /start بدهید.")
        return

    sources_dict = load_sources()
    headers = {'User-Agent': 'Mozilla/5.0'}

    for name, url in sources_dict.items():
        try:
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:3]:
                if entry.link not in sent_links:
                    summary = entry.get('summary', '') or entry.get('description', '')
                    summary = (summary[:350] + '...') if len(summary) > 350 else summary
                    
                    ai_analysis = ""
                    # فعال‌سازی تحلیل فقط برای منابع غیر ویدیویی
                    if ai_model and "youtube" not in entry.link:
                        try:
                            # دستور اختصاصی برای تحلیل دلار و بورس
                            prompt = (
                                f"به عنوان یک تحلیلگر ارشد سیاسی-اقتصادی ایران، این خبر را در حداکثر ۳ خط تحلیل کن. "
                                f"حتماً بگو این اتفاق چه تأثیر احتمالی بر 'قیمت دلار' یا 'شاخص بورس تهران' دارد:\n"
                                f"تیتر: {entry.title}\nمتن: {summary}"
                            )
                            response_ai = ai_model.generate_content(prompt)
                            ai_analysis = f"\n\n🧠 **تحلیل اختصاصی:**\n{response_ai.text.strip()}"
                        except Exception as e:
                            print(f"AI Error: {e}")

                    message = f"📰 **منبع: {name}**\n\n🔹 **{entry.title}**{ai_analysis}\n\n🔗 [لینک منبع]({entry.link})"
                    broadcast_message(message, users)
                    sent_links.add(entry.link)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

if __name__ == "__main__":
    run_bot()
