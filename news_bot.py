import feedparser
import requests
import os

# --- تنظیمات پایه ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENT_FILE = "sent_news.txt"
SOURCES_FILE = "sources.txt"

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

def broadcast_message(text):
    if not CHAT_ID:
        print("خطا: CHAT_ID پیدا نشد!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False}
    requests.post(url, data=payload)

def run_bot():
    sent_links = get_saved_data(SENT_FILE)
    sources_dict = load_sources()
    headers = {'User-Agent': 'Mozilla/5.0'}

    for name, url in sources_dict.items():
        try:
            print(f"در حال بررسی {name}...")
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            # دریافت ۲ خبر اول از هر منبع
            for entry in feed.entries[:2]: 
                if entry.link not in sent_links:
                    message = f"🚨 **{name}**\n\n📌 **{entry.title}**\n\n🔗 [لینک خبر]({entry.link})"
                    broadcast_message(message)
                    sent_links.add(entry.link)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

if __name__ == "__main__":
    run_bot()
