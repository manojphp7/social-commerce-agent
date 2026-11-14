import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.dialects.postgresql import insert

from agent.graph import graph
from config import VERIFY_TOKEN
from database import SessionLocal
from agent.nodes.messages import t
from instagram import (
    product_image_url,
    send_instagram_carousel,
    send_instagram_image,
    send_instagram_message,
    send_instagram_sender_action,
)
from models import ProcessedInstagramMessage, Shop
from ocr import extract_text_from_image


router = APIRouter()

# Temporary upload directory
TEMP_DIR = Path(__file__).resolve().parents[1] / "uploads" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024


@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


async def download_attachment(
    attachment_type: str,
    attachment_url: str | None,
):
    """Download a supported Instagram attachment to the temporary directory."""

    if not attachment_url:
        print("Attachment URL missing")
        return None

    parsed_url = urlparse(attachment_url)

    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "lookaside.fbsbx.com"
    ):
        print("Invalid attachment URL host:", parsed_url.hostname)
        return None

    extensions = {
        "image": ".jpg",
        "video": ".mp4",
    }

    extension = extensions.get(attachment_type)

    if not extension:
        print("Unsupported attachment type:", attachment_type)
        return None

    file_path = TEMP_DIR / f"{uuid4().hex}{extension}"

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=60,
        ) as client:
            async with client.stream("GET", attachment_url) as response:
                response.raise_for_status()

                # Do not follow a redirect to an unexpected host.
                if response.url.host != "lookaside.fbsbx.com":
                    raise ValueError("Unexpected attachment redirect host")

                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > MAX_FILE_SIZE:
                    raise ValueError("Attachment exceeds 50 MB")

                total_size = 0

                with file_path.open("wb") as file:
                    async for chunk in response.aiter_bytes():
                        total_size += len(chunk)

                        if total_size > MAX_FILE_SIZE:
                            raise ValueError("Attachment exceeds 50 MB")

                        file.write(chunk)

        print("Attachment downloaded:", file_path)
        print("Attachment size:", total_size, "bytes")
        return file_path

    except Exception as exc:
        file_path.unlink(missing_ok=True)
        print("Attachment download failed:", str(exc))
        return None


def extract_sku_candidates(ocr_results: list[str]) -> list[str]:
    """Extract SKU-like tokens from OCR text for the agent state."""

    candidates = []

    for detected_text in ocr_results:
        matches = re.findall(r"[A-Za-z0-9_-]{4,}", detected_text or "")

        for sku in matches:
            if sku not in candidates:
                candidates.append(sku)

    return candidates


def is_duplicate_message(
    db,
    message_id: str,
    shop_id: int,
    sender_id: str,
) -> bool:
    """Atomically register an Instagram message ID and detect duplicates."""

    stmt = (
        insert(ProcessedInstagramMessage)
        .values(
            message_id=message_id,
            shop_id=shop_id,
            sender_id=sender_id,
        )
        .on_conflict_do_nothing(index_elements=["message_id"])
    )

    result = db.execute(stmt)
    db.commit()

    return result.rowcount == 0


def release_message_for_retry(db, message_id: str) -> None:
    """Remove a failed message registration so a later webhook retry can process it."""

    try:
        db.query(ProcessedInstagramMessage).filter(
            ProcessedInstagramMessage.message_id == message_id
        ).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise


def run_social_agent(
    *,
    shop_id: int,
    sender_id: str,
    message_text: str | None = None,
    image_path: str | None = None,
    ocr_results: list[str] | None = None,
    sku_candidates: list[str] | None = None,
) -> dict | None:
    thread_id = f"shop_{shop_id}_customer_{sender_id}"

    # Only send fields received in the current message.
    state = {
        "shop_id": shop_id,
        "sender_id": sender_id,
        "message_text": message_text,
        "image_path": image_path,
        "ocr_results": ocr_results or [],
        "sku_candidates": sku_candidates or [],
        # Prevent a reply from the previous checkpoint from leaking into this turn.
        "reply": None,
    }

    result = graph.invoke(
        state,
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    reply = result.get("reply")

    if isinstance(reply, str) and reply.strip():
        return {
            "reply": reply.strip(),
            "intent": result.get("intent"),
            "language": result.get("language"),
            "product": result.get("product"),
            "products": result.get("products") or [],
            "search_exact": result.get("search_exact"),
        }

    return None


async def send_agent_reply(
    sender_id: str,
    reply: str,
    message_id: str | None = None,
):
    """Send the graph's final reply to the Instagram customer."""

    print(
        "SEND_AGENT_REPLY CALLED | "
        f"message_id={message_id} | sender_id={sender_id} | reply={reply!r}"
    )
    print("INSTAGRAM SEND FUNCTION START")

    response = await asyncio.to_thread(
        send_instagram_message,
        sender_id,
        reply,
    )

    print(
        "INSTAGRAM SEND FUNCTION FINISHED | "
        f"message_id={message_id} | response={response}"
    )
    print("Instagram Reply Sent:", response)
    return response


async def send_agent_output(
    sender_id: str,
    result: dict,
    message_id: str | None = None,
):
    """Send product photos first (carousel / single image), then the text.

    Any failure while sending photos falls back to the plain text reply,
    so the customer always gets an answer.
    """
    intent = result.get("intent")
    product = result.get("product")
    products = result.get("products") or []
    language = result.get("language")

    try:
        if intent in ("product_lookup", "product_select", "product_image"):

            if product:
                image_url = product_image_url(product.get("image_path"))
                if image_url:
                    await asyncio.to_thread(
                        send_instagram_image, sender_id, image_url
                    )

            elif products and intent == "product_lookup":
                sent = await asyncio.to_thread(
                    send_instagram_carousel, sender_id, products
                )
                if sent:
                    key = (
                        "pick_prompt"
                        if result.get("search_exact")
                        else "pick_prompt_closest"
                    )
                    return await send_agent_reply(
                        sender_id, t(language, key), message_id=message_id
                    )

    except Exception as exc:
        print("Product image sending failed, falling back to text:", str(exc))

    return await send_agent_reply(sender_id, result["reply"], message_id=message_id)


async def send_agent_typing(sender_id: str, action: str):
    try:
        response = await asyncio.to_thread(
            send_instagram_sender_action,
            sender_id,
            action,
        )
        print(f"Typing action completed: {action}", response)

    except Exception as exc:
        print(f"Typing action failed ({action}):", str(exc))


@router.post("/webhook")
async def receive_webhook(request: Request):
    print("========== WEBHOOK REQUEST RECEIVED ==========")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    if payload.get("object") not in (None, "instagram"):
        print("Ignoring unsupported webhook object:", payload.get("object"))
        return {"status": "ignored"}

    for entry in payload.get("entry", []):
        instagram_account_id = str(entry.get("id", ""))

        # Instagram messaging events normally arrive in `messaging`.
        events = list(entry.get("messaging", []) or [])

        # Keep support for the subscribed `changes` message field.
        for change in entry.get("changes", []) or []:
            if change.get("field") == "messages":
                value = change.get("value", {})
                if isinstance(value, dict):
                    events.append(value)

        if not events:
            print("Webhook entry contains no messaging events.")
            continue

        db = SessionLocal()

        try:
            shop = db.query(Shop).filter(
                Shop.instagram_user_id == instagram_account_id
            ).first()

            if not shop:
                print(f"\nShop Not Found: {instagram_account_id}")
                continue

            print(f"\nShop Found: {shop.shop_name}")
            print(f"Shop ID: {shop.id}")

            print("WEBHOOK EVENTS IN THIS ENTRY:", len(events))

            for event_index, event in enumerate(events, start=1):
                print(f"PROCESSING WEBHOOK EVENT #{event_index}")

                # Ignore read receipts and delivery notifications.
                if "read" in event or "delivery" in event:
                    continue

                message = event.get("message")

                if not isinstance(message, dict):
                    continue

                # Ignore messages echoed from the shop's own Instagram account.
                if message.get("is_echo"):
                    print(f"[SENT by {instagram_account_id}]")
                    continue

                sender_id = str(event.get("sender", {}).get("id", ""))

                print(
                    f"\n[RECEIVED on {instagram_account_id}] "
                    f"from {sender_id}"
                )

                if not sender_id:
                    print("Customer sender ID missing. Skipping event.")
                    continue

                # Meta supplies `mid` as the unique ID of an Instagram message.
                # Register it before typing, OCR, graph execution, or sending a reply.
                message_id = message.get("mid")
                message_registered = False

                if message_id:
                    message_id = str(message_id)
                    print("Instagram Message ID:", message_id)

                    try:
                        if is_duplicate_message(
                            db=db,
                            message_id=message_id,
                            shop_id=shop.id,
                            sender_id=sender_id,
                        ):
                            print(
                                "Duplicate Instagram message ignored:",
                                message_id,
                            )
                            continue

                        message_registered = True

                    except Exception as exc:
                        db.rollback()
                        print("Message deduplication failed:", str(exc))
                        # Fail closed: do not risk sending a duplicate reply.
                        continue
                else:
                    # Process the event, but it cannot be deduplicated without `mid`.
                    print(
                        "Warning: Instagram message ID (mid) missing; "
                        "duplicate protection unavailable for this event."
                    )

                message_text = (message.get("text") or "").strip()
                attachments = message.get("attachments") or []

                if message_text:
                    print("Customer Message:", message_text)

                downloaded_files = []
                ocr_results = []
                sku_candidates = []
                processing_succeeded = False

                try:
                    await send_agent_typing(sender_id, "typing_on")

                    # Download and OCR image attachments before invoking the graph.
                    for attachment in attachments:
                        attachment_type = attachment.get("type")
                        attachment_url = (
                            attachment.get("payload", {}).get("url")
                        )

                        print("Attachment Type:", attachment_type)

                        if attachment_type != "image":
                            print(
                                "Unsupported attachment type:",
                                attachment_type,
                            )
                            continue

                        file_path = await download_attachment(
                            attachment_type,
                            attachment_url,
                        )

                        if not file_path:
                            continue

                        downloaded_files.append(file_path)

                        image_ocr = await asyncio.to_thread(
                            extract_text_from_image,
                            file_path,
                        )

                        if isinstance(image_ocr, str):
                            image_ocr = [image_ocr]

                        ocr_results.extend(image_ocr or [])

                    sku_candidates = extract_sku_candidates(ocr_results)

                    print("OCR Results:", ocr_results)
                    print("SKU Candidates:", sku_candidates)

                    # Do not invoke the agent for an event with no usable content.
                    if not message_text and not downloaded_files:
                        print("No text or supported image found. Skipping.")
                        processing_succeeded = True
                        continue

                    # Include OCR text so the existing product node can search image SKUs.
                    graph_message_text = message_text or ""

                    if ocr_results:
                        ocr_text = " ".join(
                            str(item) for item in ocr_results if item
                        )
                        graph_message_text = (
                            f"{graph_message_text} {ocr_text}".strip()
                        )

                    first_image_path = (
                        str(downloaded_files[0])
                        if downloaded_files
                        else None
                    )

                    print("Invoking LangGraph...")

                    agent_result = await asyncio.to_thread(
                        run_social_agent,
                        shop_id=shop.id,
                        sender_id=sender_id,
                        message_text=graph_message_text or None,
                        image_path=first_image_path,
                        ocr_results=ocr_results,
                        sku_candidates=sku_candidates,
                    )

                    reply = agent_result["reply"] if agent_result else None
                    print("LangGraph Reply:", reply)

                    if not reply:
                        print("LangGraph returned no reply.")
                        processing_succeeded = True
                        continue

                    print(
                        "FINAL REPLY SENDING | "
                        f"message_id={message_id} | sender_id={sender_id}"
                    )
                    await send_agent_output(
                        sender_id,
                        agent_result,
                        message_id=message_id,
                    )
                    processing_succeeded = True

                except Exception as exc:
                    print("Message processing failed:", str(exc))

                finally:
                    await send_agent_typing(sender_id, "typing_off")

                    # Remove temporary files after OCR and graph processing.
                    for file_path in downloaded_files:
                        file_path.unlink(missing_ok=True)
                        print("Temporary image deleted:", file_path)

                    # Allow Meta's later retry if this attempt failed.
                    if message_registered and not processing_succeeded:
                        try:
                            release_message_for_retry(db, message_id)
                            print(
                                "Failed message registration released for retry:",
                                message_id,
                            )
                        except Exception as exc:
                            print(
                                "Could not release failed message registration:",
                                str(exc),
                            )

        finally:
            db.close()

    return {"status": "received"}
