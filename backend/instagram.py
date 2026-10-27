
import requests

from config import INSTAGRAM_ACCESS_TOKEN


def send_instagram_message(recipient_id: str, message: str) -> dict:
    url = "https://graph.instagram.com/v26.0/me/messages"

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"
        },
        json={
            "recipient": {"id": recipient_id},
            "message": {"text": message},
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()
