import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
API_KEY = os.environ.get("RECHARGEGAME_API_KEY", "")
API = "https://api.rechargegame.games"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

PACKAGES = {
    "ff_115": ("115 Diamonds", "Free Fire 115 Diamonds", "$0.61"),
    "ff_240": ("240 Diamonds", "Free Fire 240 Diamonds", "$1.22"),
    "ff_610": ("610 Diamonds", "Free Fire 610 Diamonds", "$3.07"),
    "ff_1240": ("1240 Diamonds", "Free Fire 1240 Diamonds", "$6.11"),
    "ff_2830": ("2830 Diamonds", "Free Fire 2830 Diamonds", "$19.25"),
    "ff_wlite": ("Weekly Lite", "Free Fire Weekly Lite", "$0.34"),
    "ff_weekly": ("Weekly Membership", "Free Fire Weekly Membership", "$1.22"),
    "ff_monthly": ("Monthly Membership", "Free Fire Monthly Membership", "$6.10"),
}

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Game Top Up", callback_data="games")],
        [InlineKeyboardButton("💰 My Balance", callback_data="balance"),
         InlineKeyboardButton("📋 My Orders", callback_data="orders")],
        [InlineKeyboardButton("🎁 Referral", callback_data="referral"),
         InlineKeyboardButton("🆘 Support", callback_data="support")],
    ])

def games_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Free Fire", callback_data="freefire")],
        [InlineKeyboardButton("⚔️ Mobile Legends", callback_data="ml"),
         InlineKeyboardButton("🎯 PUBG Mobile", callback_data="pubg")],
        [InlineKeyboardButton("🔙 Back", callback_data="home")],
    ])

def package_menu():
    rows = []
    for key, (name, _, price) in PACKAGES.items():
        rows.append([InlineKeyboardButton(f"{name} — {price}", callback_data=key)])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="games")])
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🎮 Game TopUp BD\n\nস্বাগতম! একটি অপশন বেছে নিন 👇", reply_markup=main_menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start — Main menu\n/ping — Telegram + RechargeGames API test\n/help — Help")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not API_KEY:
        await update.message.reply_text("❌ RECHARGEGAME_API_KEY Railway Variables-এ নেই।")
        return
    try:
        r = requests.get(f"{API}/v1/ping", headers={"X-API-Key": API_KEY}, timeout=20)
        data = r.json()
        if r.ok and data.get("ok"):
            await update.message.reply_text(f"✅ Bot online\n✅ RechargeGames connected\nBuyer: {data.get('buyer','unknown')}")
        else:
            await update.message.reply_text(f"⚠️ API response: {data}")
    except Exception as e:
        log.exception("ping failed")
        await update.message.reply_text(f"❌ API connection failed: {e}")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data

    if d == "home":
        context.user_data.clear()
        await q.edit_message_text("🏠 Main menu", reply_markup=main_menu())
    elif d == "games":
        await q.edit_message_text("🎮 Select a game:", reply_markup=games_menu())
    elif d == "freefire":
        context.user_data.clear()
        context.user_data["state"] = "player"
        await q.edit_message_text("🔥 Free Fire\n\nআপনার Player ID পাঠান:\nউদাহরণ: 51234567")
    elif d in ("ml", "pubg"):
        await q.edit_message_text("⏳ এই game এখনো configure করা হয়নি। আগে Free Fire চালু করছি।", reply_markup=games_menu())
    elif d in PACKAGES:
        if context.user_data.get("state") != "package":
            await q.edit_message_text("আগে Player ID দিন।", reply_markup=games_menu())
            return
        context.user_data["package"] = d
        name, product, price = PACKAGES[d]
        pid = context.user_data["player_id"]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])
        await q.edit_message_text(
            f"📋 Order Summary\n\n🎮 Free Fire\n🆔 Player ID: {pid}\n💎 {name}\n💵 Supplier cost: {price}\n\n"
            "⚠️ Payment এখনো চালু হয়নি। Confirm করলে real supplier order পাঠানো হবে না।",
            reply_markup=kb)
    elif d == "confirm":
        await q.edit_message_text(
            "⚠️ Payment gateway এখনো যুক্ত হয়নি, তাই real top-up order পাঠানো হয়নি।\n\n"
            "পরের ধাপে bKash/Nagad payment verification যোগ করব।", reply_markup=main_menu())
    elif d == "cancel":
        context.user_data.clear()
        await q.edit_message_text("❌ Order cancelled.", reply_markup=main_menu())
    elif d == "balance":
        await q.edit_message_text("💰 Balance system পরে যোগ হবে।", reply_markup=main_menu())
    elif d == "orders":
        await q.edit_message_text("📋 Order history পরে যোগ হবে।", reply_markup=main_menu())
    elif d == "referral":
        await q.edit_message_text("🎁 Referral system পরে যোগ হবে।", reply_markup=main_menu())
    elif d == "support":
        await q.edit_message_text("🆘 Support contact পরে সেট হবে।", reply_markup=main_menu())

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") == "player":
        pid = update.message.text.strip()
        if not pid.isdigit() or not 5 <= len(pid) <= 20:
            await update.message.reply_text("❌ শুধু সঠিক সংখ্যার Player ID দিন।")
            return
        context.user_data["player_id"] = pid
        context.user_data["state"] = "package"
        await update.message.reply_text(f"✅ Player ID: {pid}\n\nPackage নির্বাচন করুন:", reply_markup=package_menu())
    else:
        await update.message.reply_text("নিচের menu ব্যবহার করুন 👇", reply_markup=main_menu())

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
