import os
import sqlite3
import logging
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
NAGAD_NUMBER = os.environ.get("NAGAD_NUMBER", "")
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", "6907180282"))
SUPPORT_ID = "@Ahsanvai10"
DB_FILE = "topup_bot.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

BOT_APP = None
BOT_LOOP = None

PACKAGES = {
    "lu6": ("🎫 Level Up-6", 50),
    "lu10": ("🎫 Level Up-10", 80),
    "lu15": ("🎫 Level Up-15", 80),
    "lu20": ("🎫 Level Up-20", 80),
    "lu25": ("🎫 Level Up-25", 80),
    "lu30": ("🎫 Level Up-30", 130),
    "wlite": ("🎁 Weekly Lite", 50),
    "weekly": ("🎁 Weekly Membership", 170),
    "monthly": ("🎁 Monthly Membership", 800),
    "d25": ("💎 25 Diamonds", 25),
    "d50": ("💎 50 Diamonds", 40),
    "d115": ("💎 115 Diamonds", 85),
    "d240": ("💎 240 Diamonds", 165),
    "d610": ("💎 610 Diamonds", 410),
    "d1240": ("💎 1240 Diamonds", 800),
    "d2530": ("💎 2530 Diamonds", 1600),
}


def db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            player_id TEXT NOT NULL,
            package_key TEXT NOT NULL,
            package_name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            txn_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'payment_pending',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )""")
        try:
            con.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT")
        except sqlite3.OperationalError:
            pass


def new_order(user_id, username, player_id, package_key, txn_id):
    name, amount = PACKAGES[package_key]
    with db() as con:
        cur = con.execute("INSERT INTO orders(user_id,username,player_id,package_key,package_name,amount,txn_id,status,created_at,payment_method) VALUES(?,?,?,?,?,?,?,?,?,?)",
                          (user_id, username, player_id, package_key, name, amount, txn_id, "payment_pending", datetime.now().isoformat(timespec="seconds"), "Nagad"))
        return cur.lastrowid


def get_order(order_id):
    with db() as con:
        return con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()


def set_status(order_id, status):
    with db() as con:
        if status == "completed":
            con.execute("UPDATE orders SET status=?, completed_at=? WHERE id=?", (status, datetime.now().isoformat(timespec="seconds"), order_id))
        else:
            con.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))


def status_bn(status):
    return {
        "payment_pending": "⏳ পেমেন্ট যাচাই বাকি",
        "payment_verified": "✅ পেমেন্ট যাচাই হয়েছে — Top-up বাকি",
        "completed": "🎉 Top-up সম্পন্ন",
        "rejected": "❌ বাতিল",
    }.get(status, status)


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Game Top Up", callback_data="game")],
        [InlineKeyboardButton("📋 My Orders", callback_data="orders"), InlineKeyboardButton("🆘 Support", callback_data="support")],
    ])


def game_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Free Fire", callback_data="ff")],
        [InlineKeyboardButton("🔙 Back", callback_data="home")],
    ])


def package_menu():
    rows = [
        [InlineKeyboardButton("🎫 Level Up Pass", callback_data="cat_level")],
        [InlineKeyboardButton("🎁 Membership", callback_data="cat_member")],
        [InlineKeyboardButton("💎 Diamonds", callback_data="cat_diamond")],
        [InlineKeyboardButton("🔙 Back", callback_data="game")],
    ]
    return InlineKeyboardMarkup(rows)


def category_menu(cat):
    if cat == "level": keys = ["lu6", "lu10", "lu15", "lu20", "lu25", "lu30"]
    elif cat == "member": keys = ["wlite", "weekly", "monthly"]
    else: keys = ["d25", "d50", "d115", "d240", "d610", "d1240", "d2530"]
    rows = []
    for k in keys:
        n, p = PACKAGES[k]
        rows.append([InlineKeyboardButton(f"{n} — ৳{p}", callback_data=f"pkg:{k}")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="ff")])
    return InlineKeyboardMarkup(rows)


def admin_keyboard(order_id, status):
    rows = []
    if status == "payment_pending":
        rows.append([InlineKeyboardButton("✅ PAYMENT VERIFIED", callback_data=f"admin:verify:{order_id}")])
        rows.append([InlineKeyboardButton("❌ REJECT", callback_data=f"admin:reject:{order_id}")])
    elif status == "payment_verified":
        rows.append([InlineKeyboardButton("🎮 TOP-UP DONE", callback_data=f"admin:done:{order_id}")])
        rows.append([InlineKeyboardButton("❌ REJECT", callback_data=f"admin:reject:{order_id}")])
    return InlineKeyboardMarkup(rows) if rows else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🎮 *Game TopUp BD*-এ স্বাগতম!\n\nযে Game Top-up করতে চান নির্বাচন করুন।", parse_mode="Markdown", reply_markup=main_menu())


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 *অর্ডার করার নিয়ম*\n1. Game Top Up → Free Fire\n2. Free Fire UID দিন\n3. Package নির্বাচন করুন\n4. Nagad-এ পেমেন্ট করুন\n5. Transaction ID দিন\n6. Admin payment verify করে manual top-up করবেন।\n\n🆘 Support: " + SUPPORT_ID, parse_mode="Markdown")


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "home":
        context.user_data.clear()
        await q.edit_message_text("🏠 Main Menu", reply_markup=main_menu())
        return
    if data == "game":
        await q.edit_message_text("🎮 Game নির্বাচন করুন:", reply_markup=game_menu())
        return
    if data == "ff":
        await q.edit_message_text("🔥 Free Fire\n\nআপনার *Free Fire UID* পাঠান:", parse_mode="Markdown")
        context.user_data["state"] = "player_id"
        return
    if data == "cat_level":
        await q.edit_message_text("🎫 *Level Up Pass* নির্বাচন করুন:", parse_mode="Markdown", reply_markup=category_menu("level"))
        return
    if data == "cat_member":
        await q.edit_message_text("🎁 *Membership* নির্বাচন করুন:", parse_mode="Markdown", reply_markup=category_menu("member"))
        return
    if data == "cat_diamond":
        await q.edit_message_text("💎 *Diamonds* নির্বাচন করুন:", parse_mode="Markdown", reply_markup=category_menu("diamond"))
        return
    if data.startswith("pkg:"):
        key = data.split(":", 1)[1]
        context.user_data["package_key"] = key
        name, amount = PACKAGES[key]
        player_id = context.user_data.get("player_id", "")
        text = (f"🧾 *Order Summary*\n\n🎮 Free Fire\n🆔 Free Fire UID: `{player_id}`\n📦 Package: {name}\n💰 Price: *৳{amount}*\n\n"
                f"💳 Nagad: `{NAGAD_NUMBER or 'Admin will provide number'}`\n\nপেমেন্ট করার পর নিচের বাটনে চাপুন।")
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💸 I Paid — Send Txn ID", callback_data="paid")],
            [InlineKeyboardButton("❌ Cancel", callback_data="home")],
        ]))
        return
    if data == "paid":
        context.user_data["state"] = "txn_id"
        await q.edit_message_text("🧾 আপনার Nagad *Transaction ID (TxnID)* পাঠান:\n\nউদাহরণ: `8A1B2C3D4E`", parse_mode="Markdown")
        return
    if data == "orders":
        with db() as con:
            rows = con.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (q.from_user.id,)).fetchall()
        if not rows:
            await q.edit_message_text("📋 আপনার কোনো অর্ডার নেই।", reply_markup=main_menu())
            return
        lines = ["📋 *Your Orders*\n"]
        for r in rows:
            lines.append(f"🆔 #{r['id']} | {r['package_name']} | ৳{r['amount']}\n🆔 Player: {r['player_id']}\n{status_bn(r['status'])}\n")
        await q.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_menu())
        return
    if data == "support":
        await q.edit_message_text(f"🆘 Support: {SUPPORT_ID}", reply_markup=main_menu())
        return

    if data.startswith("admin:"):
        if q.from_user.id != ADMIN_USER_ID:
            await q.answer("❌ আপনি admin নন।", show_alert=True)
            return
        _, action, oid_s = data.split(":")
        oid = int(oid_s)
        order = get_order(oid)
        if not order:
            await q.edit_message_text("❌ Order পাওয়া যায়নি।")
            return
        if action == "verify":
            if order["status"] != "payment_pending":
                await q.answer("এই order-এর payment already processed.", show_alert=True)
                return
            set_status(oid, "payment_verified")
            await q.edit_message_reply_markup(reply_markup=admin_keyboard(oid, "payment_verified"))
            await context.bot.send_message(order["user_id"], f"✅ *Payment Verified*\n\nOrder #{oid}\n📦 {order['package_name']}\n🆔 Free Fire UID: `{order['player_id']}`\n\n🎮 এখন আপনার Top-up processing হচ্ছে।", parse_mode="Markdown")
            return
        if action == "done":
            if order["status"] != "payment_verified":
                await q.answer("আগে PAYMENT VERIFIED করুন।", show_alert=True)
                return
            set_status(oid, "completed")
            await q.edit_message_reply_markup(reply_markup=None)
            await context.bot.send_message(order["user_id"], f"🎉 *Top-up Completed!*\n\nOrder #{oid}\n📦 {order['package_name']}\n🆔 Free Fire UID: `{order['player_id']}`\n💰 ৳{order['amount']}\n\nধন্যবাদ! ❤️", parse_mode="Markdown")
            return
        if action == "reject":
            if order["status"] in ("completed", "rejected"):
                await q.answer("এই order already closed.", show_alert=True)
                return
            set_status(oid, "rejected")
            await q.edit_message_reply_markup(reply_markup=None)
            await context.bot.send_message(order["user_id"], f"❌ *Order Rejected*\n\nOrder #{oid}\n📦 {order['package_name']}\n\nপ্রয়োজনে Support: {SUPPORT_ID}", parse_mode="Markdown")
            return


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    text = update.message.text.strip()
    if state == "player_id":
        context.user_data["player_id"] = text
        context.user_data["state"] = None
        await update.message.reply_text("📦 এখন package category নির্বাচন করুন:", reply_markup=package_menu())
        return
    if state == "txn_id":
        key = context.user_data.get("package_key")
        player_id = context.user_data.get("player_id")
        if not key or not player_id:
            context.user_data.clear()
            await update.message.reply_text("⚠️ Order session শেষ হয়ে গেছে। আবার /start দিন।")
            return
        if len(text) < 4:
            await update.message.reply_text("⚠️ সঠিক Transaction ID দিন।")
            return
        oid = new_order(update.effective_user.id, update.effective_user.username, player_id, key, text)
        name, amount = PACKAGES[key]
        context.user_data.clear()
        await update.message.reply_text(f"✅ *Order Submitted!*\n\n🆔 Order ID: `#{oid}`\n🎮 Free Fire\n🆔 Free Fire UID: `{player_id}`\n📦 {name}\n💰 ৳{amount}\n🧾 TxnID: `{text}`\n\n⏳ Admin payment verify করবেন, তারপর manual top-up হবে।", parse_mode="Markdown", reply_markup=main_menu())
        user = update.effective_user
        admin_text = (f"🔔 *NEW MANUAL ORDER*\n\n🆔 Order: `#{oid}`\n👤 User: `{user.id}` @{user.username or '-'}\n🆔 Free Fire UID: `{player_id}`\n📦 Package: {name}\n💰 Amount: *৳{amount}*\n🧾 TxnID: `{text}`\n\n⚠️ Nagad payment manually verify করুন। তারপর Payment Verified চাপুন এবং top-up করে Top-Up Done চাপুন.")
        await context.bot.send_message(ADMIN_USER_ID, admin_text, parse_mode="Markdown", reply_markup=admin_keyboard(oid, "payment_pending"))
        return
    await update.message.reply_text("/start চাপুন এবং menu থেকে শুরু করুন।")


def build_app():
    global BOT_APP
    BOT_APP = ApplicationBuilder().token(BOT_TOKEN).build()
    BOT_APP.add_handler(CommandHandler("start", start))
    BOT_APP.add_handler(CommandHandler("help", help_cmd))
    BOT_APP.add_handler(CallbackQueryHandler(buttons))
    BOT_APP.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    return BOT_APP


def run_bot_forever():
    global BOT_APP, BOT_LOOP
    init_db()
    BOT_APP = build_app()
    BOT_LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(BOT_LOOP)
    log.info("Game TopUp BD — manual mode started")
    BOT_APP.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


def main():
    run_bot_forever()


if __name__ == "__main__":
    main()
