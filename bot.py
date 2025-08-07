import os
import logging
import asyncio
import requests

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from contextlib import asynccontextmanager

from config import TELEGRAM_BOT_TOKEN, create_tables
from database import (
    add_user, add_wallet, remove_wallet,
    get_user_wallets, get_wallet_by_address,
    update_wallet_name, update_wallet_thresholds,
    toggle_fresh_wallet_flag, is_tx_notified, log_notified_tx
)
from utils import format_wallets_message, build_wallet_menu

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://solana-wallet-tracker-production.up.railway.app/webhook"
HELIUS_PATH = "/helius"

# ========== Telegram Handlers ==========

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.reply("👋 Welcome! Use:\n/add <wallet>\n/remove <wallet>\n/menu to configure.\n/wallets to list wallets.")

@dp.message_handler(commands=["add"])
async def add_cmd(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.reply("Usage: /add <wallet_address>")
    add_wallet(message.from_user.id, parts[1])
    await message.reply("✅ Wallet added.")

@dp.message_handler(commands=["remove"])
async def remove_cmd(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.reply("Usage: /remove <wallet_address>")
    remove_wallet(message.from_user.id, parts[1])
    await message.reply("🗑️ Wallet removed.")

@dp.message_handler(commands=["wallets"])
async def wallets_cmd(message: types.Message):
    wallets = get_user_wallets(message.from_user.id)
    msg, keyboard = format_wallets_message(wallets)
    await message.reply(msg, reply_markup=keyboard)

@dp.message_handler(commands=["menu"])
async def menu_cmd(message: types.Message):
    wallets = get_user_wallets(message.from_user.id)
    if not wallets:
        return await message.reply("You don’t have any wallets yet.")
    await message.reply("⚙️ Choose a wallet to configure:", reply_markup=format_wallets_message(wallets)[1])

# ========== Inline Menu Callbacks ==========

@dp.callback_query_handler(lambda c: c.data.startswith("menu:"))
async def open_wallet_menu(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    user_wallets = get_user_wallets(callback.from_user.id)
    wallet_data = next((w for w in user_wallets if w[0] == wallet_id), None)
    if not wallet_data:
        return await callback.answer("Wallet not found.", show_alert=True)
    text, keyboard = build_wallet_menu(wallet_id, wallet_data)
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("setname:"))
async def set_name(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    await callback.message.answer("✏️ Send the new name:")
    dp.register_message_handler(lambda m: apply_name(m, wallet_id), content_types=types.ContentTypes.TEXT, state=None)

async def apply_name(message: types.Message, wallet_id: int):
    update_wallet_name(wallet_id, message.text.strip())
    await message.reply("✅ Name updated.")
    dp.unregister_message_handler(lambda m: apply_name(m, wallet_id))

@dp.callback_query_handler(lambda c: c.data.startswith("setthreshold:"))
async def set_threshold(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    await callback.message.answer("✏️ Send min and max SOL like this:\n<code>0.1 10</code>")
    dp.register_message_handler(lambda m: apply_threshold(m, wallet_id), content_types=types.ContentTypes.TEXT, state=None)

async def apply_threshold(message: types.Message, wallet_id: int):
    try:
        min_sol, max_sol = map(float, message.text.strip().split())
        update_wallet_thresholds(wallet_id, min_sol, max_sol)
        await message.reply("✅ Thresholds updated.")
    except Exception:
        await message.reply("❌ Invalid format. Use: <code>0.1 10</code>")
    dp.unregister_message_handler(lambda m: apply_threshold(m, wallet_id))

@dp.callback_query_handler(lambda c: c.data.startswith("togglefresh:"))
async def toggle_fresh(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    toggle_fresh_wallet_flag(wallet_id)
    await callback.answer("🔄 Fresh wallet setting toggled.")
    await open_wallet_menu(callback)

# ========== FastAPI Setup ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    for i in range(3):
        try:
            await bot.set_webhook(WEBHOOK_URL)
            logging.info("Webhook set successfully.")
            break
        except Exception as e:
            logging.error(f"Webhook setup failed (attempt {i+1}): {e}")
            await asyncio.sleep(2)
    yield
    try:
        await bot.delete_webhook()
        logging.info("Webhook deleted on shutdown.")
    except Exception as e:
        logging.error(f"Webhook delete failed: {e}")

app = FastAPI(lifespan=lifespan)

# ========== Telegram Webhook Endpoint ==========

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"Telegram update received: {data}")
        if isinstance(data, dict):
            await dp.process_update(types.Update(**data))
        elif isinstance(data, list):
            for d in data:
                await dp.process_update(types.Update(**d))
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Failed to process Telegram update: {e}")
        return {"status": "error", "detail": str(e)}

# ========== Helius Webhook for SOL + Token Tracking ==========

@app.post(HELIUS_PATH)
async def helius_webhook(request: Request):
    try:
        payload = await request.json()
        for tx in payload.get("transactions", []):
            sig = tx.get("signature")
            for ev in tx.get("events", {}).get("transfers", []):
                process_transfer_event(ev, sig, is_token=False)
            for ev in tx.get("events", {}).get("tokenTransfers", []):
                process_transfer_event(ev, sig, is_token=True)
        return {"ok": True}
    except Exception as e:
        logging.error(f"Helius error: {e}")
        return {"ok": False, "error": str(e)}

# ========== Helper ==========

def process_transfer_event(ev, sig, is_token):
    to_addr = ev.get("toUserAccount") or ev.get("to")
    amount = float(ev.get("amount", 0)) / (1e9 if not is_token else 10 ** ev.get("decimals", 0))
    wallet = get_wallet_by_address(to_addr)
    if not wallet: return
    wallet_id, user_id, addr, name, min_sol, max_sol, fresh, _ = wallet
    if not (min_sol <= amount <= max_sol): return
    if is_tx_notified(wallet_id, sig): return
    if fresh:
        hist = requests.get(
            f"https://api.helius.xyz/v0/addresses/{to_addr}/transactions?api-key={os.getenv('HELIUS_API_KEY')}&limit=2"
        ).json()
        if len(hist) > 1: return
    log_notified_tx(wallet_id, sig)
    token = "TOKEN" if is_token else "SOL"
    asyncio.ensure_future(bot.send_message(
        user_id,
        f"📥 <b>{token} Transfer Detected</b>\n"
        f"<b>Wallet:</b> {name or addr}\n"
        f"<b>To:</b> <code>{to_addr}</code>\n"
        f"<b>Amount:</b> {amount:.4f} {token}\n"
        f"🔗 <a href='https://solscan.io/tx/{sig}'>View Tx</a>"
    ))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=8000)
