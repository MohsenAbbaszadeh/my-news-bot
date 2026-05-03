import feedparser
import requests
import os
import google.generativeai as genai

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENT_FILE = "sent_news.txt"
USERS_FILE = "users.txt"
SOURCES_FILE = "sources.txt"

# موقتا روی 1 گذاشتم تا قطعا پیام بیاید. بعد از تست موفق، این را به 7 تغییر دهید.
IMPORTANCE_THRESHOLD = 1 

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        ai_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
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

# این تابعی بود که جا مانده بود!
def update_users_list(users_set):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        res = requests.get(url).json()
        if res.get("ok"):
            for item in res["result"]:
                if "message" in item and "chat" in item["message"]:
                    users_set.add(str(item["message"]["chat"]["id"]))
    except Exception as e:
        print(f"User Update Error: {e}")
    return users_set

def broadcast_message(text, users_set):
    for chat_id in users_set:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, data=payload)

def run_bot():
    sent_links = get_saved_data(SENT_FILE)
    users = get_saved_data(USERS_FILE)
    
    # پیدا کردن آیدی تلگرام شما
    users = update_users_list(users)
    save_data(USERS_FILE, users)

    if not users:
        print("هنوز هیچ کاربری یافت نشده! لطفا در تلگرام به ربات پیام بدهید.")
        return

    sources_dict = load_sources()
    headers = {'User-Agent': 'Mozilla/5.0'}

    for name, url in sources_dict.items():
        try:
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:5]: 
                if entry.link not in sent_links:
                    score = 0
                    if ai_model:
                        try:
                            prompt = (
                                f"Translate this headline to Persian and rate its global economic/political importance from 1 to 10.\n"
                                f"Headline: {entry.title}\n"
                                f"Response format MUST BE EXACTLY:\n"
                                f"SCORE: [number]\n"
                                f"PERSIAN_TITLE: [translation]\n"
                                f"WHY_IMPORTANT: [one sentence explanation in Persian]"
                            )
                            res = ai_model.generate_content(prompt).text
                            
                            for line in res.split('\n'):
                                if "SCORE:" in line:
                                    try: score = int(''.join(filter(str.isdigit, line)))
                                    except: score = 0
                            
                            if score >= IMPORTANCE_THRESHOLD:
                                persian_title = res.split("PERSIAN_TITLE:")[1].split("\n")[0].strip() if "PERSIAN_TITLE:" in res else entry.title
                                why_important = res.split("WHY_IMPORTANT:")[1].strip() if "WHY_IMPORTANT:" in res else "بدون تحلیل"
                                
                                message = (
                                    f"🔥 **{name}**\n"
                                    f"امتیاز: {score}/10\n\n"
                                    f"📌 **{persian_title}**\n\n"
                                    f"💡 **تحلیل:** {why_important}\n\n"
                                    f"🔗 [لینک خبر]({entry.link})"
                                )
                                broadcast_message(message, users)
                        except Exception as e:
                            print(f"AI error: {e}")
                    
                    sent_links.add(entry.link)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

if __name__ == "__main__":
    run_bot()
