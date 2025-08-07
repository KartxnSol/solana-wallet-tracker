from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_wallets_message(wallets):
    if not wallets:
        return "❌ You don’t have any wallets yet.", None

    message = "📄 <b>Your Wallets:</b>\n\n"
    keyboard = InlineKeyboardMarkup()

    for wallet in wallets:
        wallet_id, address, name, min_sol, max_sol, fresh_wallet = wallet

        name_display = name if name else "(Unnamed)"
        min_sol = min_sol if min_sol is not None else 0
        max_sol = max_sol if max_sol is not None else 0
        fresh_status = "🟢 Fresh" if fresh_wallet else "🔴 Not Fresh"

        message += (
            f"📌 <b>{name_display}</b>\n"
            f"🔗 <code>{address}</code>\n"
            f"💰 Min: {min_sol} | Max: {max_sol} | {fresh_status}\n\n"
        )

        # Add button for menu
        keyboard.add(
            InlineKeyboardButton(text=name_display, callback_data=f"wallet_{wallet_id}")
        )

    return message, keyboard
