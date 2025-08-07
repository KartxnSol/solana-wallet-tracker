from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Format /wallets list message
def format_wallets_message(wallets):
    if not wallets:
        return "🪙 You don't have any wallets yet.", InlineKeyboardMarkup()

    keyboard = InlineKeyboardMarkup()
    msg_lines = ["🧾 <b>Your Tracked Wallets:</b>"]

    for wallet in wallets:
        wallet_id, address, name, min_sol, max_sol, fresh_wallet = wallet
        label = f"{name or address[:6] + '...' + address[-4:]}"
        msg_lines.append(f"• {label}")
        keyboard.add(InlineKeyboardButton(label, callback_data=f"wallet_{wallet_id}"))

    return "\n".join(msg_lines), keyboard

# Wallet settings inline menu
def build_wallet_menu(wallet_id, current_name, min_sol, max_sol, fresh_wallet):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton("✏️ Rename", callback_data=f"rename_{wallet_id}")
    )
    keyboard.add(
        InlineKeyboardButton("💰 Set Min/Max", callback_data=f"threshold_{wallet_id}")
    )
    keyboard.add(
        InlineKeyboardButton(
            "🔄 Toggle Fresh Wallet",
            callback_data=f"toggle_fresh_{wallet_id}"
        )
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")
    )

    message = (
        f"⚙️ <b>Wallet Settings</b>\n\n"
        f"🆔 ID: <code>{wallet_id}</code>\n"
        f"🏷️ Name: {current_name or '(None)'}\n"
        f"💸 Min: {min_sol} | Max: {max_sol}\n"
        f"🧼 Fresh Wallet: {'Yes' if fresh_wallet else 'No'}"
    )

    return message, keyboard
