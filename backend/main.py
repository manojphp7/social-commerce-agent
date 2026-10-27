
from fastapi import FastAPI

from webhook import router as webhook_router

app = FastAPI(
    title="Instagram Social Commerce Agent",
    description="AI-powered Instagram DM automation",
    version="1.0.0",
)


@app.get("/")
async def home():
    return {
        "status": "running",
        "message": "Instagram Social Commerce Agent is running!",
    }


app.include_router(webhook_router)
