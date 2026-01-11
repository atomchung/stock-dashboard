import os
from dotenv import load_dotenv

def verify():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if key and len(key) > 10:
        print("SUCCESS: API Key found in .env and looks valid.")
        masked = key[:4] + "*" * (len(key)-8) + key[-4:]
        print(f"Key: {masked}")
    else:
        print("FAILED: API Key not found or too short in .env.")

if __name__ == "__main__":
    verify()
