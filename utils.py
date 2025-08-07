from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_wallets_message(wallets):
    if not wallets:
        return "📭 You don't have any wallets yet.", None

    msg = "📄 <b>Your Wallets:</b>\n\n"
    keyboard = InlineKeyboardMarkup(row_width=1)

    for wallet in wallets:
        wallet_id, address, name, min_sol, max_sol, fresh_wallet = wallet
        label = f"{name or address[:6]}...{address[-4:]}"
        msg += f"• <b>{label}</b>\n"
        keyboard.add(InlineKeyboardButton(text=label, callback_data=f"menu:{wallet_id}"))

    return msg, keyboard

def build_wallet_menu(wallet_id, wallet_data):
    _, address, name, min_sol, max_sol, fresh_wallet = wallet_data
    name_display = name if name else "Not set"
    fresh_status = "✅ ON" if fresh_wallet else "❌ OFF"

    msg = (
        f"⚙️ <b>Wallet Settings</b>\n"
        f"<b>Address:</b> <code>{address}</code>\n"
        f"<b>Name:</b> {name_display}\n"
        f"<b>Min SOL:</b> {min_sol}\n"
        f"<b>Max SOL:</b> {max_sol}\n"
        f"<b>Fresh Wallet:</b> {fresh_status}"
    )

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ Name", callback_data=f"setname:{wallet_id}"),
        InlineKeyboardButton("💰 Threshold", callback_data=f"setthreshold:{wallet_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🧪 Toggle Fresh", callback_data=f"togglefresh:{wallet_id}")
    )

    return msg, keyboard
