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

# حد آستانه اهمیت (از ۱ تا ۱۰). نمره ۷ برای اخبار مهم جهانی عالی است.
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
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
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
            
            for entry in feed.entries[:5]: 
                if entry.link not in sent_links:
                    summary = entry.get('summary', '') or entry.get('description', '')
                    summary = summary[:500]
                    
                    is_important = False
                    ai_summary = ""
                    ai_analysis = ""

                    if ai_model:
                        try:
                            # دستور جدید برای اخبار انگلیسی و ترجمه فارسی
                            prompt = (
                                f"Act as a Senior International News Editor. Read this news:\n"
                                f"Title: {entry.title}\nText: {summary}\n\n"
                                f"۱. به اهمیت جهانی این خبر (فوری بودن) از ۱ تا ۱۰ نمره بده.\n"
                                f"۲. اگر نمره مساوی یا بالای {IMPORTANCE_THRESHOLD} است، تیتر و متن را در ۲ خط به زبان «فارسی» ترجمه و خلاصه کن.\n"
                                f"۳. در یک خط به زبان فارسی بگو این خبر چه تاثیری روی بازارهای جهانی (طلا، نفت، کریپتو یا اقتصاد) دارد.\n"
                                f"دقیقاً با این فرمت جواب بده:\n"
                                f"SCORE: [نمره]\n"
                                f"SUMMARY: [خلاصه فارسی]\n"
                                f"ANALYSIS: [تحلیل فارسی]"
                            )
                            res = ai_model.generate_content(prompt).text
                            
                            try:
                                score_part = res.split("SCORE:")[1].split("\n")[0].strip()
                                score = int(''.join(filter(str.isdigit, score_part)))
                            except:
                                score = 5 

                            if score >= IMPORTANCE_THRESHOLD:
                                is_important = True
                                try:
                                    ai_summary = res.split("SUMMARY:")[1].split("ANALYSIS:")[0].strip()
                                    ai_analysis = res.split("ANALYSIS:")[1].strip()
                                except:
                                    ai_summary = "خلاصه‌سازی انجام نشد."
                                    ai_analysis = "تحلیلی در دسترس نیست."
                        except Exception as e:
                            print(f"AI Filter Error: {e}")

                    # ارسال پیام فقط در صورت اهمیت بالا
                    if is_important:
                        message = f"🚨 **{name}**\n\n🔹 **{ai_summary}**\n\n🧠 **تحلیل بازار:**\n{ai_analysis}\n\n🔗 [لینک خبر انگلیسی]({entry.link})"
                        broadcast_message(message, users)
                    
                    sent_links.add(entry.link)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

if __name__ == "__main__":
    run_bot()
