
import os
import requests
import dotenv
from openai import OpenAI
import asyncio

# Load .env explicitly
dotenv.load_dotenv("/Users/apple/NeuroSupply/.env")

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def test_telegram():
    token = os.getenv("BOT_TOKEN")
    if not token or token == "your_telegram_bot_token":
        print(f"{RED}[FAIL] Telegram: BOT_TOKEN is missing or default{RESET}")
        return False
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            print(f"{GREEN}[OK] Telegram: Connected as {resp.json().get('result', {}).get('username')}{RESET}")
            return True
        else:
            print(f"{RED}[FAIL] Telegram: Error {resp.status_code} - {resp.text}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}[FAIL] Telegram: Connection error - {e}{RESET}")
        return False

def test_proxyapi():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("AI_MODEL", "gpt-4o")

    if not api_key or api_key == "your_proxyapi_key":
        print(f"{RED}[FAIL] ProxyAPI: OPENAI_API_KEY is missing or default{RESET}")
        return False
    
    print(f"Testing ProxyAPI with model: {model}...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello! Say verify."}],
            max_tokens=10
        )
        msg = response.choices[0].message.content
        print(f"{GREEN}[OK] ProxyAPI: Success! Response: {msg}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}[FAIL] ProxyAPI: Error - {e}{RESET}")
        return False

if __name__ == "__main__":
    print("--- Starting Connection Verification ---")
    tg_ok = test_telegram()
    ai_ok = test_proxyapi()
    print("--- Verification Complete ---")
