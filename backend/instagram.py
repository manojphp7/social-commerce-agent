import os
from urllib.parse import quote

import requests

from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID

GRAPH_URL = f"https://graph.facebook.com/v26.0/{INSTAGRAM_ACCOUNT_ID}/messages"

# Product photos are served from here: <base>/<file name>
PRODUCT_IMAGE_BASE_URL = os.getenv(
    "PRODUCT_IMAGE_BASE_URL", "https://api.bghs.in/uploads/products/"
)

CAROUSEL_MAX_ITEMS = 10   # Instagram generic template limit


def _headers() -> dict:
    return {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}


def test_instagram_connection():
    url = f"https://graph.facebook.com/v26.0/{INSTAGRAM_ACCOUNT_ID}"

    response = requests.get(
        url,
        params={"fields": "id,username", "access_token": INSTAGRAM_ACCESS_TOKEN},
        timeout=30,
    )

    print("Connection Status:", response.status_code)
    print("Connection Response:", response.text)

    response.raise_for_status()


def send_instagram_message(recipient_id: str, message: str) -> dict:
    response = requests.post(
        GRAPH_URL,
        headers=_headers(),
        json={"recipient": {"id": recipient_id}, "message": {"text": message}},
        timeout=30,
    )

    print("Instagram API Status:", response.status_code)
    print("Instagram API Response:", response.text)

    response.raise_for_status()
    return response.json()


def send_instagram_image(recipient_id: str, image_url: str) -> dict:
    response = requests.post(
        GRAPH_URL,
        headers=_headers(),
        json={
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {"type": "image", "payload": {"url": image_url}}
            },
        },
        timeout=30,
    )

    print("Image API Status:", response.status_code)
    print("Image API Response:", response.text)

    response.raise_for_status()
    return response.json()


def product_image_url(image_path: str | None) -> str | None:
    """DB value -> public https URL.

    Works for 'tshirt001.jpg', 'products/tshirt001.jpg',
    'uploads/products/tshirt001.jpg' and full URLs.
    """
    if not image_path:
        return None

    image_path = str(image_path).strip()

    if image_path.startswith("https://"):
        return image_path

    file_name = image_path.replace("\\", "/").rstrip("/").split("/")[-1]
    if not file_name:
        return None

    return PRODUCT_IMAGE_BASE_URL.rstrip("/") + "/" + quote(file_name)


def _clip(text: str, limit: int = 80) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_carousel_elements(products: list[dict]) -> list[dict]:
    """One card per product: image, '1. Name', 'Rs price | Sizes'."""
    elements = []

    for number, product in enumerate(products[:CAROUSEL_MAX_ITEMS], start=1):
        image_url = product_image_url(product.get("image_path"))
        if not image_url:
            continue

        price = float(product["price"])
        price_text = f"{price:,.0f}" if price.is_integer() else f"{price:,.2f}"
        subtitle = f"₹{price_text}"
        if product.get("sizes"):
            subtitle += " | Sizes: " + ", ".join(product["sizes"])

        elements.append(
            {
                "title": _clip(f"{number}. {product['name']}"),
                "subtitle": _clip(subtitle),
                "image_url": image_url,
            }
        )

    return elements


def send_instagram_carousel(recipient_id: str, products: list[dict]) -> dict | None:
    """Send up to 10 products as a swipeable carousel.

    Returns None when no product has an image (caller sends text instead).
    """
    elements = build_carousel_elements(products)
    if not elements:
        return None

    response = requests.post(
        GRAPH_URL,
        headers=_headers(),
        json={
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {"template_type": "generic", "elements": elements},
                }
            },
        },
        timeout=30,
    )

    print("Carousel API Status:", response.status_code)
    print("Carousel API Response:", response.text)

    response.raise_for_status()
    return response.json()


def send_instagram_product(
    recipient_id: str, product_name: str, price: str, image_url: str
):
    send_instagram_image(recipient_id, image_url)
    send_instagram_message(recipient_id, f"{product_name}\nPrice: ₹{price}")


def send_instagram_sender_action(recipient_id: str, action: str) -> dict:

    if action not in ("typing_on", "typing_off"):
        raise ValueError("Invalid Instagram sender action")

    response = requests.post(
        GRAPH_URL,
        headers=_headers(),
        json={"recipient": {"id": recipient_id}, "sender_action": action},
        timeout=30,
    )

    print(f"Instagram {action} Status:", response.status_code)
    print(f"Instagram {action} Response:", response.text)

    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    test_instagram_connection()
