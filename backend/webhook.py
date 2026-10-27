
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from config import VERIFY_TOKEN
from instagram import send_instagram_message

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


@router.post("/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            message = event.get("message", {}).get("text")

            if sender_id and message:
                print("Sender ID:", sender_id)
                print("Message:", message)

                try:
                    result = send_instagram_message(
                        sender_id,
                        f"Thanks for your message: {message}",
                    )
                    print("Reply sent:", result)
                except Exception as error:
                    print("Reply failed:", str(error))

    return {"status": "received"}
