import feedparser
import requests
import os

# --- تنظیمات (این‌ها را در GitHub Secrets ست می‌کنیم) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("@MohsenAbbaszadeh08") # آیدی عددی چت خصوصی خودتان
SENT_FILE = "sent_news.txt"

SOURCES = {
    "ایران اینترنشنال": "https://www.iranintl.com/rss",
    "بی‌بی‌سی فارسی": "https://www.bbc.com/persian/index.xml",
    "رادیو فردا": "https://www.radiofarda.com/rss/?count=20",
    "صدای آمریکا": "https://ir.voanews.com/api/z-qv_eimvt",
    "دویچه وله": "https://rss.dw.com/xml/rss-far-all",
    "ایندیپندنت": "https://www.independentpersian.com/rss.xml"
}

def get_sent_links():
    if not os.path.exists(SENT_FILE): return set()
    with open(SENT_FILE, "r") as f:
        return set(f.read().splitlines())

def save_sent_link(link):
    with open(SENT_FILE, "a") as f:
        f.write(link + "\n")

def run_bot():
    sent_links = get_sent_links()
    headers = {'User-Agent': 'Mozilla/5.0'}

    for name, url in SOURCES.items():
        try:
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:3]: # بررسی ۳ خبر آخر هر سایت
                if entry.link not in sent_links:
                    message = f"🚨 **{entry.title}**\n\nمنبع: {name}\n\n🔗 [لینک خبر]({entry.link})"
                    
                    # ارسال به چت خصوصی شما برای تایید
                    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown"}
                    requests.post(tg_url, data=payload)
                    
                    save_sent_link(entry.link)
        except Exception as e:
            print(f"Error in {name}: {e}")

if __name__ == "__main__":
    run_bot()