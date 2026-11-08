
import requests

from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID


def test_instagram_connection():
    url = f"https://graph.facebook.com/v26.0/{INSTAGRAM_ACCOUNT_ID}"

    response = requests.get(
        url,
        params={
            "fields": "id,username",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        },
        timeout=30
    )

    print("Connection Status:", response.status_code)
    print("Connection Response:", response.text)

    response.raise_for_status()


def send_instagram_message(recipient_id: str, message: str) -> dict:
    url = f"https://graph.facebook.com/v26.0/{INSTAGRAM_ACCOUNT_ID}/messages"

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"
        },
        json={
            "recipient": {"id": recipient_id},
            "message": {"text": message}
        },
        timeout=30
    )

    print("Instagram API Status:", response.status_code)
    print("Instagram API Response:", response.text)

    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    test_instagram_connection()

    # Replace with the customer's sender.id from webhook logs.
    recipient_id = "1855309905672399"

    send_instagram_message(
        recipient_id,
        "Hello! Your Instagram shop is working."
    )


def send_instagram_product(
    recipient_id: str,
    product_name: str,
    price: str,
    image_url: str
):
    # Send product image
    send_instagram_image(recipient_id, image_url)

    # Send product details
    message = f"{product_name}\nPrice: ₹{price}"

    send_instagram_message(recipient_id, message)



def send_instagram_image(recipient_id: str, image_url: str) -> dict:
    url = f"https://graph.facebook.com/v26.0/{INSTAGRAM_ACCOUNT_ID}/messages"

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"
        },
        json={
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url
                    }
                }
            }
        },
        timeout=30
    )

    print("Image API Status:", response.status_code)
    print("Image API Response:", response.text)

    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    send_instagram_product(
        recipient_id="1855309905672399",
        product_name="Cotton T-Shirt",
        price="499",
        image_url="https://api.bghs.in/uploads/products/tshirt001.jpg"
    )