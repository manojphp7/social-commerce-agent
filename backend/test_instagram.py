
import os
from pathlib import Path
from dotenv import load_dotenv

# Root folder ki .env file load karo
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
instagram_id = os.getenv("INSTAGRAM_ACCOUNT_ID")

print("Token loaded:", bool(token))
print("Instagram ID:", instagram_id)
