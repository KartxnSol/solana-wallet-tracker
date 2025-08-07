import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from config import TELEGRAM_BOT_TOKEN
from database import add_user, get_user_wallets
from utils import format_wallets_message

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.reply("👋 Welcome! Use /wallets to manage your tracked Solana wallets.")

@dp.message_handler(commands=["wallets"])
async def wallets_cmd(message: types.Message):
    wallets = get_user_wallets(message.from_user.id)
    msg, keyboard = format_wallets_message(wallets)
    await message.reply(msg, reply_markup=keyboard)

if __name__ == "__main__":
    from config import create_tables
    create_tables()
    executor.start_polling(dp, skip_updates=True)
