from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_wallets_message(wallets):
    if not wallets:
        return "🪙 You don’t have any wallets yet.", None

    msg = "🧾 <b>Your Wallets</b>:\n"
    keyboard = InlineKeyboardMarkup(row_width=1)

    for w in wallets:
        wallet_id, address, name, min_sol, max_sol, fresh_wallet = w
        display_name = f"{name} - " if name else ""
        msg += f"• <code>{address}</code>\n"
        msg += f"  └ {display_name}min: {min_sol} SOL, max: {max_sol} SOL, fresh: {'✅' if fresh_wallet else '❌'}\n\n"

        keyboard.add(InlineKeyboardButton(
            text=f"⚙️ Manage {name or address[:6]}...", 
            callback_data=f"wallet_{wallet_id}"
        ))

    return msg, keyboard

def build_wallet_menu(wallet_id: int):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ Set Name", callback_data=f"setname_{wallet_id}"),
        InlineKeyboardButton("🔁 Toggle Fresh", callback_data=f"togglefresh_{wallet_id}"),
        # You can add more options here:
        # InlineKeyboardButton("⚙️ Set Thresholds", callback_data=f"setthresholds_{wallet_id}")
    )
    return keyboard
