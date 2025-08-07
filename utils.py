from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_wallets_message(wallets):
    if not wallets:
        return "🔍 You don’t have any wallets yet.", None

    keyboard = InlineKeyboardMarkup()
    for wallet in wallets:
        wid, address, name, min_sol, max_sol, fresh = wallet
        label = f"{name or address[:6]}...{address[-4:]}"
        keyboard.add(InlineKeyboardButton(label, callback_data=f"menu:{wid}"))
    return "🧾 Your wallets:", keyboard

def build_wallet_menu(wallet_id, wallet_data):
    _, address, name, min_sol, max_sol, fresh = wallet_data
    text = f"""⚙️ <b>Wallet Settings</b>

<b>Name:</b> {name}
<b>Address:</b> {address}
<b>Min SOL:</b> {min_sol}
<b>Max SOL:</b> {max_sol}
<b>Fresh Wallet Only:</b> {"✅" if fresh else "❌"}"""

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✏️ Set Name", callback_data=f"setname:{wallet_id}"))
    keyboard.add(InlineKeyboardButton("💰 Set Min/Max SOL", callback_data=f"setthreshold:{wallet_id}"))
    keyboard.add(InlineKeyboardButton(f"{'🔴 Disable' if fresh else '🟢 Enable'} Fresh Wallet Only", callback_data=f"togglefresh:{wallet_id}"))
    return text, keyboard
