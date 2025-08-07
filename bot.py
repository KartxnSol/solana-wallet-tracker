import logging
import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TELEGRAM_BOT_TOKEN, create_tables
from database import (
    add_user, add_wallet, remove_wallet, get_user_wallets,
    update_wallet_name, update_wallet_thresholds, toggle_fresh_wallet_flag
)
from utils import format_wallets_message, build_wallet_menu
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

# Setup
bot = Bot(token=TELEGRAM_BOT_TOKEN)
bot.set_current(bot)
dp = Dispatcher(bot)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://solana-wallet-tracker-production.up.railway.app{WEBHOOK_PATH}"

# Handlers
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.reply("👋 Welcome! Use /wallets or /menu to manage your tracked Solana wallets.")

@dp.message_handler(commands=["add"])
async def add_wallet_cmd(message: types.Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return await message.reply("❌ Usage: /add <wallet_address>")
    address = parts[1].strip()
    add_wallet(message.from_user.id, address)
    await message.reply(f"✅ Wallet added:\n<code>{address}</code>", parse_mode="HTML")

@dp.message_handler(commands=["remove"])
async def remove_wallet_cmd(message: types.Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return await message.reply("❌ Usage: /remove <wallet_address>")
    address = parts[1].strip()
    remove_wallet(message.from_user.id, address)
    await message.reply(f"🗑️ Wallet removed:\n<code>{address}</code>", parse_mode="HTML")

@dp.message_handler(commands=["wallets"])
async def wallets_cmd(message: types.Message):
    wallets = get_user_wallets(message.from_user.id)
    msg, keyboard = format_wallets_message(wallets)
    await message.reply(msg, reply_markup=keyboard, parse_mode="HTML")

@dp.message_handler(commands=["menu"])
async def menu_cmd(message: types.Message):
    wallets = get_user_wallets(message.from_user.id)
    if not wallets:
        await message.reply("🪙 You don’t have any wallets yet.")
        return
    msg, keyboard = format_wallets_message(wallets)
    await message.reply("📋 Select a wallet to manage:", reply_markup=keyboard, parse_mode="HTML")

# Callback handler for buttons
@dp.callback_query_handler(lambda c: c.data.startswith("wallet_"))
async def wallet_menu_callback(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split("_")[1])
    keyboard = build_wallet_menu(wallet_id)
    await callback.message.edit_text(f"⚙️ Manage wallet ID {wallet_id}:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("setname_"))
async def set_name_callback(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(f"✏️ Send me the new name for wallet {wallet_id}")
    dp.register_message_handler(
        lambda msg: handle_name_input(msg, wallet_id),
        content_types=types.ContentTypes.TEXT,
        state=None
    )

async def handle_name_input(message: types.Message, wallet_id: int):
    update_wallet_name(wallet_id, message.text.strip())
    await message.reply("✅ Name updated.")

@dp.callback_query_handler(lambda c: c.data.startswith("togglefresh_"))
async def toggle_fresh_callback(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split("_")[1])
    toggle_fresh_wallet_flag(wallet_id)
    await callback.answer("🔁 Fresh wallet status toggled.")
    await callback.message.delete()

# FastAPI lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(WEBHOOK_URL)
    create_tables()
    yield
    await bot.delete_webhook()

app = FastAPI(lifespan=lifespan)

# Webhook route
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        if isinstance(data, dict):
            update = types.Update(**data)
            await dp.process_update(update)
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
