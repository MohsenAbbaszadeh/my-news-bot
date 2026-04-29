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

# حد آستانه اهمیت (از ۱ تا ۱۰). عدد بالاتر یعنی سخت‌گیری بیشتر و پیام کمتر.
IMPORTANCE_THRESHOLD = 7 

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

def broadcast_message(text, users_set):
    for chat_id in users_set:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload)

def run_bot():
    sent_links = get_saved_data(SENT_FILE)
    users = get_saved_data(USERS_FILE)
    sources_dict = load_sources()
    headers = {'User-Agent': 'Mozilla/5.0'}

    if not users: return

    for name, url in sources_dict.items():
        try:
            response = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:5]: # بررسی ۵ خبر آخر هر منبع
                if entry.link not in sent_links:
                    summary = entry.get('summary', '') or entry.get('description', '')
                    summary = summary[:400]
                    
                    # --- مرحله فیلتر هوشمند ---
                    is_important = True
                    ai_analysis = ""

                    if ai_model:
                        try:
                            # از هوش مصنوعی می‌خواهیم اهمیت را بسنجد
                            prompt = (
                                f"به عنوان یک سردبیر خبر خبره، این متن را بخوان:\n"
                                f"تیتر: {entry.title}\nمتن: {summary}\n\n"
                                f"۱. به این خبر از نظر اهمیت سیاسی یا اقتصادی برای ایران از ۱ تا ۱۰ نمره بده.\n"
                                f"۲. اگر نمره بالای {IMPORTANCE_THRESHOLD} است، یک تحلیل ۳ خطی درباره تاثیر آن بر دلار و بورس بنویس.\n"
                                f"۳. پاسخ را دقیقاً با این فرمت بده:\n"
                                f"SCORE: [نمره]\n"
                                f"ANALYSIS: [تحلیل شما]"
                            )
                            res = ai_model.generate_content(prompt).text
                            
                            # استخراج نمره از پاسخ AI
                            try:
                                score_part = res.split("SCORE:")[1].split("\n")[0].strip()
                                score = int(''.join(filter(str.isdigit, score_part)))
                            except:
                                score = 5 # در صورت خطا، نمره متوسط

                            if score < IMPORTANCE_THRESHOLD:
                                is_important = False # خبر کم‌اهمیت است، ارسال نشود
                            else:
                                ai_analysis = res.split("ANALYSIS:")[1].strip() if "ANALYSIS:" in res else ""
                        except Exception as e:
                            print(f"AI Filter Error: {e}")

                    # فقط اگر خبر مهم بود ارسال شود
                    if is_important:
                        message = f"🚨 **خبر مهم: {name}**\n\n🔹 **{entry.title}**\n\n🧠 **تحلیل:**\n{ai_analysis}\n\n🔗 [لینک منبع]({entry.link})"
                        broadcast_message(message, users)
                    
                    sent_links.add(entry.link)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

if __name__ == "__main__":
    run_bot()
