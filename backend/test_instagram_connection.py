
import os
import requests
from dotenv import load_dotenv

load_dotenv("../.env")

access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")

if not access_token or not account_id:
    print("Missing Instagram credentials in .env")
    raise SystemExit(1)

url = f"https://graph.instagram.com/{account_id}"

try:
    response = requests.get(
        url,
        params={
            "fields": "id,username",
            "access_token": access_token,
        },
        timeout=20,
    )

    data = response.json()

    if response.ok:
        print("Instagram API connection successful!")
        print("Account ID:", data.get("id"))
        print("Username:", data.get("username", "Not returned"))
    else:
        error = data.get("error", {})
        print("Instagram API connection failed.")
        print("Error:", error.get("message", "Unknown API error"))
        print("Error code:", error.get("code", "Unknown"))

except requests.RequestException as exc:
    print("Network request failed:", type(exc).__name__)
