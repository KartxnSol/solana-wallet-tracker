import logging
import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from config import TELEGRAM_BOT_TOKEN, create_tables
from database import add_user, get_user_wallets
from utils import format_wallets_message

API_TOKEN = TELEGRAM_BOT_TOKEN
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://solana-wallet-tracker-production.up.railway.app{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

app = FastAPI()

# Handlers
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.reply("👋 Welcome! Use /wallets to manage your tracked Solana wallets.")

@dp.message_handler(commands=["wallets"])
async def wallets_cmd(message: types.Message):
    wallets = get_user_wallets(message.from_user.id)
    msg, keyboard = format_wallets_message(wallets)
    await message.reply(msg, reply_markup=keyboard)

# FastAPI startup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(WEBHOOK_URL)
    create_tables()
    yield
    await bot.delete_webhook()

app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()

        # If Telegram sent a single update
        if isinstance(data, dict):
            update = types.Update(**data)
            await dp.process_update(update)

        # If Telegram sent a list of updates (rare but possible)
        elif isinstance(data, list):
            for item in data:
                update = types.Update(**item)
                await dp.process_update(update)

        return {"status": "ok"}

    except Exception as e:
        logging.error(f"Failed to process update: {e}")
        return {"status": "error", "detail": str(e)}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=8000)
