from fastapi import FastAPI, Request
from config import TELEGRAM_BOT_TOKEN
import requests

app = FastAPI()

@app.post("/webhook")
async def helius_webhook(request: Request):
    data = await request.json()
    # Simplified handling
    print("Received webhook:", data)
    return {"status": "ok"}
