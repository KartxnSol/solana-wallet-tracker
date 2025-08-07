import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from config import TELEGRAM_BOT_TOKEN, create_tables
from database import (
    add_user, add_wallet, remove_wallet,
    get_user_wallets, update_wallet_name,
    update_wallet_thresholds, toggle_fresh_wallet_flag
)
from utils import format_wallets_message, build_wallet_menu
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

# Telegram Bot setup
bot = Bot(token=TELEGRAM_BOT_TOKEN)
bot.set_current(bot)  # Fix context issues
dp = Dispatcher(bot)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://solana-wallet-tracker-production.up.railway.app{WEBHOOK_PATH}"

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

@dp.message_handler(commands=["add"])
async def add_wallet_cmd(message: types.Message):
    try:
        address = message.text.split(" ", 1)[1].strip()
        add_wallet(message.from_user.id, address)
        await message.reply(f"✅ Wallet `{address}` added.", parse_mode="Markdown")
    except IndexError:
        await message.reply("❌ Please provide a wallet address: `/add <address>`", parse_mode="Markdown")

@dp.message_handler(commands=["remove"])
async def remove_wallet_cmd(message: types.Message):
    try:
        address = message.text.split(" ", 1)[1].strip()
        remove_wallet(message.from_user.id, address)
        await message.reply(f"🗑️ Wallet `{address}` removed.", parse_mode="Markdown")
    except IndexError:
        await message.reply("❌ Please provide a wallet address: `/remove <address>`", parse_mode="Markdown")

@dp.message_handler(commands=["menu"])
async def menu_cmd(message: types.Message):
    wallets = get_user_wallets(message.from_user.id)
    if not wallets:
        await message.reply("You don’t have any wallets yet.")
        return

    keyboard = types.InlineKeyboardMarkup()
    for w in wallets:
        keyboard.add(types.InlineKeyboardButton(text=w["address"], callback_data=f"menu:{w['id']}"))
    await message.reply("📋 Select a wallet to manage:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("menu:"))
async def wallet_menu_callback(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    keyboard = build_wallet_menu(wallet_id)
    await callback.message.edit_text("⚙️ Wallet settings:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("name:"))
async def rename_wallet_callback(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    await callback.message.answer(f"✍️ Send me the new name for wallet ID {wallet_id}:")
    dp.register_message_handler(lambda msg: save_name(msg, wallet_id), content_types=types.ContentTypes.TEXT)

async def save_name(message: types.Message, wallet_id: int):
    update_wallet_name(wallet_id, message.text.strip())
    await message.reply("✅ Name updated.")
    dp.unregister_message_handler(save_name)

@dp.callback_query_handler(lambda c: c.data.startswith("threshold:"))
async def threshold_wallet_callback(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    await callback.message.answer("🔢 Send min,max SOL amount (e.g. `0.1,5`):")
    dp.register_message_handler(lambda msg: save_thresholds(msg, wallet_id), content_types=types.ContentTypes.TEXT)

async def save_thresholds(message: types.Message, wallet_id: int):
    try:
        min_str, max_str = message.text.strip().split(",")
        update_wallet_thresholds(wallet_id, float(min_str), float(max_str))
        await message.reply("✅ Thresholds updated.")
    except Exception:
        await message.reply("❌ Invalid format. Use: `0.1,5`")
    dp.unregister_message_handler(save_thresholds)

@dp.callback_query_handler(lambda c: c.data.startswith("toggle_fresh:"))
async def toggle_fresh_callback(callback: types.CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    toggle_fresh_wallet_flag(wallet_id)
    await callback.answer("🔄 Fresh wallet logic toggled.")
    await wallet_menu_callback(callback)

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
