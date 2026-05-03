import feedparser
import requests
import os
from groq import Groq

# --- تنظیمات پایه ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SENT_FILE = "sent_news.txt"
SOURCES_FILE = "sources.txt"

# حد آستانه اهمیت خبر (از ۱ تا ۱۰)
IMPORTANCE_THRESHOLD = 7 

# راه‌اندازی کلاینت Groq
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"خطا در اتصال به Groq: {e}")
        client = None
else:
    client = None

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
            
            for entry in feed.entries[:5]: # بررسی ۵ خبر اول
                if entry.link not in sent_links:
                    score = 0
                    if client:
                        try:
                            # استخراج متن کوتاه خبر (اگر وجود داشت)
                            news_summary = entry.get('summary', '') or entry.get('description', '')
                            
                            # دستور جدید به هوش مصنوعی: بدون تحلیل، فقط ترجمه و چکیده واقعیت‌ها
                            prompt = (
                                f"You are a professional news translator. Read this news entry:\n"
                                f"Headline: '{entry.title}'\n"
                                f"Brief Context: '{news_summary}'\n\n"
                                f"Tasks:\n"
                                f"1. Rate the global economic/political importance of this news from 1 to 10.\n"
                                f"2. Translate the headline accurately to Persian.\n"
                                f"3. Write a concise factual summary (2-3 sentences max) in Persian based ONLY on the provided text. DO NOT add any AI analysis, opinions, or background info that isn't in the text. Just report the facts.\n\n"
                                f"Reply EXACTLY in this format:\n"
                                f"SCORE: [number]\n"
                                f"PERSIAN_TITLE: [translation]\n"
                                f"FACTUAL_SUMMARY: [factual summary in Persian]"
                            )
                            
                            chat_completion = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama3-70b-8192", 
                                temperature=0.1, # دما را کم کردیم تا فقط واقعیت را بگوید و خلاقیت به خرج ندهد
                            )
                            
                            res = chat_completion.choices[0].message.content
                            
                            for line in res.split('\n'):
                                if "SCORE:" in line:
                                    try: score = int(''.join(filter(str.isdigit, line)))
                                    except: score = 0
                            
                            if score >= IMPORTANCE_THRESHOLD:
                                persian_title = res.split("PERSIAN_TITLE:")[1].split("\n")[0].strip() if "PERSIAN_TITLE:" in res else entry.title
                                factual_summary = res.split("FACTUAL_SUMMARY:")[1].strip() if "FACTUAL_SUMMARY:" in res else "جزئیات بیشتری در دسترس نیست."
                                
                                message = (
                                    f"📰 **{name}**\n"
                                    f"امتیاز اهمیت: {score}/10\n\n"
                                    f"📌 **{persian_title}**\n\n"
                                    f"📝 **شرح خبر:**\n{factual_summary}\n\n"
                                    f"🔗 [مشاهده خبر کامل]({entry.link})"
                                )
                                broadcast_message(message)
                                print(f"ارسال شد: {persian_title} (Score: {score})")
                            else:
                                print(f"رد شد (کم‌اهمیت): {entry.title} (Score: {score})")
                                
                        except Exception as e:
                            print(f"AI error for {entry.title}: {e}")
                    
                    sent_links.add(entry.link)
        except Exception as e:
            print(f"Error in {name}: {e}")

    save_data(SENT_FILE, sent_links)

if __name__ == "__main__":
    run_bot()
