from aiogram import types

def format_wallets_message(wallets):
    if not wallets:
        return "You don’t have any wallets yet.", None

    text = "📄 *Your Wallets:*\n\n"
    for wallet in wallets:
        name = wallet.get("name") or wallet["address"]
        text += f"• `{name}`\n"
    return text, None

def build_wallet_menu(wallet_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✏️ Set Name", callback_data=f"name:{wallet_id}"))
    keyboard.add(types.InlineKeyboardButton("🔢 Set Min/Max", callback_data=f"threshold:{wallet_id}"))
    keyboard.add(types.InlineKeyboardButton("🔄 Toggle Fresh Wallet Logic", callback_data=f"toggle_fresh:{wallet_id}"))
    return keyboard
