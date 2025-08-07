from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_wallets_message(wallets):
    msg = "🔍 Tracked Wallets:\n"
    keyboard = InlineKeyboardMarkup()
    for wallet in wallets:
        msg += f"• {wallet[0]}\n"
        keyboard.add(InlineKeyboardButton(f"Edit {wallet[0][:5]}...", callback_data=f"edit_{wallet[0]}"))
    return msg, keyboard
