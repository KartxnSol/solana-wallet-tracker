import logging
import os
import requests
import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from config import TELEGRAM_BOT_TOKEN, create_tables
from database import (
    add_user, add_wallet, remove_wallet,
    get_user_wallets, get_wallet_by_address,
    update_wallet_name, update_wallet_thresholds,
    toggle_fresh_wallet_flag, is_tx_notified, log_notified_tx
)
from utils import format_wallets_message, build_wallet_menu
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
bot.set_current(bot)
dp = Dispatcher(bot)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://solana-wallet-tracker-production.up.railway.app{WEBHOOK_PATH}"
HELIUS_PATH = "/helius"

# (Your existing /start, /add, /wallets, /menu handlers go here...)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    for i in range(3):
        try:
            await bot.set_webhook(WEBHOOK_URL)
            logging.info("Webhook set successfully.")
            break
        except Exception as e:
            logging.error(f"Webhook setup attempt {i+1} failed: {e}")
            import asyncio; await asyncio.sleep(2)
    yield
    try:
        await bot.delete_webhook()
        logging.info("Webhook deleted on shutdown.")
    except Exception as e:
        logging.error(f"Failed to delete webhook: {e}")

app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        if isinstance(data, dict):
            await dp.process_update(types.Update(**data))
        elif isinstance(data, list):
            for d in data:
                await dp.process_update(types.Update(**d))
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Failed to process update: {e}")
        return {"status": "error", "detail": str(e)}

@app.post(HELIUS_PATH)
async def helius_webhook(request: Request):
    try:
        payload = await request.json()
        for tx in payload.get("transactions", []):
            signature = tx.get("signature")
            # SOL transfers
            for ev in tx.get("events", {}).get("transfers", []):
                process_transfer_event(ev, signature, is_token=False)
            # Token transfers
            for ev in tx.get("events", {}).get("tokenTransfers", []):
                process_transfer_event(ev, signature, is_token=True)
        return {"ok": True}
    except Exception as e:
        logging.error(f"Error in Helius webhook: {e}")
        return {"ok": False, "error": str(e)}

def process_transfer_event(ev, signature, is_token: bool):
    to_addr = ev.get("toUserAccount") or ev.get("to")
    amount = float(ev.get("amount", 0)) / (1e9 if not is_token else 10**ev.get("decimals", 0))
    wallet = get_wallet_by_address(to_addr)
    if not wallet:
        return
    wallet_id, user_id, address, name, min_sol, max_sol, fresh, _ = wallet
    if not (min_sol <= amount <= max_sol):
        return
    if is_tx_notified(wallet_id, signature):
        return
    if fresh:
        history = requests.get(
            f"https://api.helius.xyz/v0/addresses/{to_addr}/transactions?api-key={os.getenv('HELIUS_API_KEY')}&limit=2"
        ).json()
        if len(history) > 1:
            return
    log_notified_tx(wallet_id, signature)
    currency = "SOL" if not is_token else "TOKEN"
    asyncio.ensure_future(bot.send_message(
        user_id,
        f"📥 <b>{currency} Transfer Detected</b>\n"
        f"<b>Wallet:</b> {name or address}\n"
        f"<b>To:</b> <code>{to_addr}</code>\n"
        f"<b>Amount:</b> {amount:.4f} {currency}\n"
        f"🔗 <a href='https://solscan.io/tx/{signature}'>View Tx</a>"
    ))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=8000)
