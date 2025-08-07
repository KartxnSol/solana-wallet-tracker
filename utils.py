from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_wallets_message(wallets):
    if not wallets:
        return "You have no wallets yet.", None

    msg = "Your Solana wallets:\n\n"
    keyboard = InlineKeyboardMarkup(row_width=1)

    for wallet in wallets:
        msg += f"• `{wallet}`\n"
        keyboard.add(InlineKeyboardButton(text=wallet, url=f"https://solscan.io/account/{wallet}"))

    return msg, keyboard
