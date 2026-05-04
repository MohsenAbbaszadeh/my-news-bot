import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def test_connection():
    if not BOT_TOKEN or not CHAT_ID:
        print("🚨 خطا: توکن ربات یا CHAT_ID در تنظیمات گیت‌هاب پیدا نشد!")
        return

    print("در حال ارسال پیام تست به تلگرام...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": "✅ سلام! من زنده هستم! ارتباط گیت‌هاب و تلگرام کاملاً سالم است."
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print("✅ پیام با موفقیت به تلگرام ارسال شد!")
    else:
        print(f"❌ خطای تلگرام: {response.text}")

if __name__ == "__main__":
    test_connection()
