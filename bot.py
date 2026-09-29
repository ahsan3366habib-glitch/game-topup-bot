import os
import time
import sqlite3
import logging
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# SETTINGS
# =========================================================
BOT_TOKEN = os.environ["BOT_TOKEN"]
API_KEY = os.environ.get("RECHARGEGAME_API_KEY", "")
NAGAD_NUMBER = os.environ.get("NAGAD_NUMBER", "")
# Your Telegram numeric ID. Can still be overridden in Render.
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "6907180282")
SUPPORT_USERNAME = "@Ahsanvai10"

API = "https://api.rechargegame.games"
DB_FILE = "topup_bot.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# =========================================================
# FREE FIRE PACKAGES
# =========================================================
PACKAGES = {
    "ff_115": {"name": "115 Diamonds", "supplier_product": "Free Fire 115 Diamonds", "selling_price": 80},
    "ff_240": {"name": "240 Diamonds", "supplier_product": "Free Fire 240 Diamonds", "selling_price": 160},
    "ff_610": {"name": "610 Diamonds", "supplier_product": "Free Fire 610 Diamonds", "selling_price": 400},
    "ff_1240": {"name": "1240 Diamonds", "supplier_product": "Free Fire 1240 Diamonds", "selling_price": 800},
    "ff_2830": {"name": "2830 Diamonds", "supplier_product": "Free Fire 2830 Diamonds", "selling_price": 2500},
    "ff_wlite": {"name": "Weekly Lite", "supplier_product": "Free Fire Weekly Lite", "selling_price": 50},
    "ff_weekly": {"name": "Weekly Membership", "supplier_product": "Free Fire Weekly Membership", "selling_price": 170},
    "ff_monthly": {"name": "Monthly Membership", "supplier_product": "Free Fire Monthly Membership", "selling_price": 850},
}

# =========================================================
# DATABASE
# =========================================================
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            referral_code TEXT,
            referred_by INTEGER,
            created_at INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            player_id TEXT,
            package_key TEXT,
            package_name TEXT,
            selling_price REAL,
            payment_status TEXT,
            transaction_id TEXT,
            supplier_order_id TEXT,
            supplier_status TEXT,
            buyer_ref TEXT UNIQUE,
            created_at INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            player_id TEXT,
            package_key TEXT,
            package_name TEXT,
            amount REAL,
            transaction_id TEXT,
            status TEXT,
            created_at INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallet_recharges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            transaction_id TEXT,
            status TEXT,
            created_at INTEGER
        )
    """)

    conn.commit()
    conn.close()


def ensure_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO users (user_id, balance, referral_code, created_at) VALUES (?, ?, ?, ?)",
            (user_id, 0, f"REF{user_id}", int(time.time())),
        )
        conn.commit()
    conn.close()


def get_balance(user_id):
    ensure_user(user_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return float(row["balance"]) if row else 0.0


def add_balance(user_id, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def deduct_balance(user_id, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
        (amount, user_id, amount),
    )
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed == 1


def create_payment(user_id, player_id, package_key, package_name, amount, transaction_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO payments
        (user_id, player_id, package_key, package_name, amount, transaction_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, player_id, package_key, package_name, amount, transaction_id, "pending", int(time.time())))
    conn.commit()
    payment_id = cur.lastrowid
    conn.close()
    return payment_id


def get_payment(payment_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_payment_status(payment_id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE payments SET status = ? WHERE id = ?", (status, payment_id))
    conn.commit()
    conn.close()


def create_wallet_recharge(user_id, amount, transaction_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO wallet_recharges
        (user_id, amount, transaction_id, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, transaction_id, "pending", int(time.time())))
    conn.commit()
    recharge_id = cur.lastrowid
    conn.close()
    return recharge_id


def get_wallet_recharge(recharge_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM wallet_recharges WHERE id = ?", (recharge_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_wallet_recharge_status(recharge_id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE wallet_recharges SET status = ? WHERE id = ?", (status, recharge_id))
    conn.commit()
    conn.close()


def save_order(user_id, player_id, package_key, package_name, selling_price,
               payment_status, transaction_id, supplier_order_id, supplier_status, buyer_ref):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders
        (user_id, player_id, package_key, package_name, selling_price, payment_status,
         transaction_id, supplier_order_id, supplier_status, buyer_ref, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, player_id, package_key, package_name, selling_price, payment_status,
          transaction_id, supplier_order_id, supplier_status, buyer_ref, int(time.time())))
    conn.commit()
    order_id = cur.lastrowid
    conn.close()
    return order_id


def get_user_orders(user_id, limit=10):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

# =========================================================
# MENUS
# =========================================================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Game Top Up", callback_data="games")],
        [InlineKeyboardButton("💰 My Balance", callback_data="balance"),
         InlineKeyboardButton("➕ Wallet Recharge", callback_data="wallet")],
        [InlineKeyboardButton("📋 My Orders", callback_data="orders"),
         InlineKeyboardButton("🎁 Referral", callback_data="referral")],
        [InlineKeyboardButton("🆘 Support", callback_data="support")],
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
    for key, package in PACKAGES.items():
        rows.append([InlineKeyboardButton(
            f"💎 {package['name']} — ৳{package['selling_price']}",
            callback_data=key,
        )])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="games")])
    return InlineKeyboardMarkup(rows)

# =========================================================
# COMMANDS
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text(
        "🎮 Game TopUp BD\n\nস্বাগতম! একটি অপশন বেছে নিন 👇",
        reply_markup=main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — Main menu\n"
        "/ping — RechargeGames API test\n"
        "/myid — আপনার Telegram User ID\n"
        "/help — Help"
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 আপনার Telegram User ID:\n\n`{update.effective_user.id}`",
        parse_mode="Markdown",
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not API_KEY:
        await update.message.reply_text("❌ RechargeGames API key পাওয়া যাচ্ছে না।")
        return
    try:
        response = requests.get(f"{API}/v1/ping", headers={"X-API-Key": API_KEY}, timeout=20)
        data = response.json()
        if response.ok and data.get("ok"):
            await update.message.reply_text(
                "✅ Bot online\n✅ RechargeGames connected\n\n"
                f"Buyer: {data.get('buyer', 'unknown')}"
            )
        else:
            await update.message.reply_text(f"⚠️ API response:\n\n{data}")
    except Exception as e:
        log.exception("Ping failed")
        await update.message.reply_text(f"❌ API connection failed.\n\n{e}")

# =========================================================
# BUTTON HANDLER
# =========================================================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    ensure_user(user_id)

    if data == "home":
        context.user_data.clear()
        await query.edit_message_text("🏠 Main menu", reply_markup=main_menu())
        return

    if data == "games":
        await query.edit_message_text("🎮 Select a game:", reply_markup=games_menu())
        return

    if data == "freefire":
        context.user_data.clear()
        context.user_data["state"] = "player"
        await query.edit_message_text("🔥 Free Fire\n\nআপনার Player ID পাঠান:\n\nউদাহরণ: 51234567")
        return

    if data in ("ml", "pubg"):
        await query.edit_message_text(
            "⏳ এই game এখনো configure করা হয়নি।\n\nআগে Free Fire চালু করছি।",
            reply_markup=games_menu(),
        )
        return

    if data in PACKAGES:
        if context.user_data.get("state") != "package":
            await query.edit_message_text("❌ আগে Player ID দিন।", reply_markup=games_menu())
            return
        context.user_data["package"] = data
        package = PACKAGES[data]
        player_id = context.user_data.get("player_id")
        await query.edit_message_text(
            "📋 Order Summary\n\n"
            "🎮 Free Fire\n"
            f"🆔 Player ID: {player_id}\n"
            f"💎 Package: {package['name']}\n"
            f"💵 Price: ৳{package['selling_price']}\n\n"
            "Payment method বেছে নিন 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Pay with Nagad", callback_data="pay_nagad")],
                [InlineKeyboardButton("💰 Pay from Wallet", callback_data="pay_wallet")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ]),
        )
        return

    # -------------------------
    # DIRECT NAGAD PAYMENT
    # -------------------------
    if data == "pay_nagad":
        package_key = context.user_data.get("package")
        player_id = context.user_data.get("player_id")
        if not package_key or not player_id:
            await query.edit_message_text("❌ Order information পাওয়া যায়নি।", reply_markup=main_menu())
            return
        if not NAGAD_NUMBER:
            await query.edit_message_text("❌ Nagad number configure করা হয়নি।", reply_markup=main_menu())
            return
        package = PACKAGES[package_key]
        amount = package["selling_price"]
        await query.edit_message_text(
            "💳 Nagad Payment\n\n"
            f"📱 Nagad Number:\n`{NAGAD_NUMBER}`\n\n"
            f"💵 Amount: ৳{amount}\n\n"
            "১️⃣ উপরের Nagad নম্বরে টাকা পাঠান।\n"
            "২️⃣ টাকা পাঠানোর পর I Paid চাপুন।\n"
            "৩️⃣ তারপর Transaction ID দিন।",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ I Paid", callback_data="i_paid")],
                [InlineKeyboardButton("🔙 Back", callback_data=package_key)],
            ]),
        )
        return

    if data == "i_paid":
        package_key = context.user_data.get("package")
        player_id = context.user_data.get("player_id")
        if not package_key or not player_id:
            await query.edit_message_text("❌ Order information পাওয়া যায়নি।", reply_markup=main_menu())
            return
        context.user_data["state"] = "transaction_id"
        await query.edit_message_text(
            "🧾 Transaction ID দিন:\n\n"
            "উদাহরণ:\n`8A7B6C5D9E`\n\nশুধু Transaction ID পাঠান।",
            parse_mode="Markdown",
        )
        return

    # -------------------------
    # WALLET RECHARGE
    # -------------------------
    if data == "wallet":
        if not NAGAD_NUMBER:
            await query.edit_message_text("❌ Nagad number configure করা হয়নি।", reply_markup=main_menu())
            return
        context.user_data.clear()
        context.user_data["state"] = "wallet_amount"
        await query.edit_message_text(
            "➕ Wallet Recharge\n\n"
            "কত টাকা wallet-এ add করতে চান?\n\n"
            "উদাহরণ: 500\n\n"
            "শুধু amount পাঠান।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Main Menu", callback_data="home")]
            ]),
        )
        return

    if data == "wallet_paid":
        amount = context.user_data.get("wallet_amount")
        if not amount:
            await query.edit_message_text("❌ Recharge information পাওয়া যায়নি।", reply_markup=main_menu())
            return
        context.user_data["state"] = "wallet_transaction_id"
        await query.edit_message_text(
            "🧾 Wallet Recharge Transaction ID দিন:\n\n"
            "শুধু Transaction ID পাঠান।",
            parse_mode="Markdown",
        )
        return

    if data == "pay_wallet":
        package_key = context.user_data.get("package")
        player_id = context.user_data.get("player_id")
        if not package_key or not player_id:
            await query.edit_message_text("❌ Order information পাওয়া যায়নি।", reply_markup=main_menu())
            return
        package = PACKAGES[package_key]
        amount = float(package["selling_price"])
        balance = get_balance(user_id)
        if balance < amount:
            await query.edit_message_text(
                "❌ Wallet balance কম।\n\n"
                f"💰 আপনার balance: ৳{balance:.2f}\n"
                f"💵 প্রয়োজন: ৳{amount:.2f}\n\n"
                "আগে Wallet Recharge করুন।",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Wallet Recharge", callback_data="wallet")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="home")],
                ]),
            )
            return
        if not API_KEY:
            await query.edit_message_text("❌ RechargeGames API key পাওয়া যাচ্ছে না।", reply_markup=main_menu())
            return

        buyer_ref = f"WALLET-{user_id}-{int(time.time())}"
        payload = {
            "product": package["supplier_product"],
            "region": "Bangladesh",
            "quantity": 1,
            "player_id": player_id,
            "buyer_ref": buyer_ref,
        }
        try:
            response = requests.post(
                f"{API}/v1/orders",
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            result = response.json() if response.content else {}
            if response.status_code in (200, 201):
                if not deduct_balance(user_id, amount):
                    await query.edit_message_text("❌ Order হয়েছে, কিন্তু wallet deduction করা যায়নি। Admin-এর সাথে যোগাযোগ করুন।", reply_markup=main_menu())
                    return
                supplier_order_id = result.get("order_id") or result.get("id") or "unknown"
                supplier_status = result.get("status", "pending")
                local_order_id = save_order(
                    user_id, player_id, package_key, package["name"], amount,
                    "wallet_paid", "WALLET", supplier_order_id, supplier_status, buyer_ref,
                )
                context.user_data.clear()
                await query.edit_message_text(
                    "✅ Wallet payment successful!\n\n"
                    f"📋 Order: #{local_order_id}\n"
                    f"💎 {package['name']}\n"
                    f"🆔 Player ID: {player_id}\n"
                    f"💵 ৳{amount:.2f}\n\n"
                    f"📦 Supplier: {supplier_status}\n"
                    f"🆔 Supplier ID: {supplier_order_id}\n\n"
                    "🚀 LIVE top-up order sent.",
                    reply_markup=main_menu(),
                )
                try:
                    await context.bot.send_message(
                        chat_id=int(ADMIN_USER_ID),
                        text=(
                            "💰 WALLET ORDER\n\n"
                            f"👤 User ID: {user_id}\n"
                            f"💎 {package['name']}\n"
                            f"💵 ৳{amount:.2f}\n"
                            f"🆔 Player ID: {player_id}\n"
                            f"📦 Supplier: {supplier_status}\n"
                            f"🆔 Supplier ID: {supplier_order_id}"
                        ),
                    )
                except Exception:
                    log.exception("Failed to notify admin about wallet order")
            else:
                await query.edit_message_text(
                    "❌ RechargeGames order failed।\n\n"
                    "Wallet থেকে টাকা কাটা হয়নি।\n\n"
                    f"HTTP: {response.status_code}\n{result}",
                    reply_markup=main_menu(),
                )
        except Exception as e:
            log.exception("Wallet supplier order failed")
            await query.edit_message_text(
                "❌ RechargeGames connection failed।\n\nWallet থেকে টাকা কাটা হয়নি।",
                reply_markup=main_menu(),
            )
        return

    if data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Order cancelled.", reply_markup=main_menu())
        return

    if data == "balance":
        balance = get_balance(user_id)
        await query.edit_message_text(
            "💰 My Balance\n\n"
            f"💵 Balance: ৳{balance:.2f}\n\n"
            "Wallet Recharge করে balance add করতে পারবেন।",
            reply_markup=main_menu(),
        )
        return

    if data == "orders":
        orders = get_user_orders(user_id, 10)
        if not orders:
            await query.edit_message_text("📋 My Orders\n\nএখনো কোনো order নেই।", reply_markup=main_menu())
            return
        text = "📋 My Orders\n\n"
        for order in orders:
            text += (
                f"🆔 Order: #{order['id']}\n"
                f"💎 {order['package_name']}\n"
                f"🆔 Player ID: {order['player_id']}\n"
                f"💵 ৳{order['selling_price']}\n"
                f"💳 Payment: {order['payment_status']}\n"
                f"📦 Top-up: {order['supplier_status']}\n\n"
            )
        await query.edit_message_text(text, reply_markup=main_menu())
        return

    if data == "referral":
        await query.edit_message_text(
            "🎁 Referral\n\n"
            f"Your referral code:\n`REF{user_id}`\n\n"
            "Referral reward system পরে চালু হবে.",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )
        return

    if data == "support":
        await query.edit_message_text(
            "🆘 Support\n\n"
            "কোনো সমস্যা হলে Admin-এর সাথে যোগাযোগ করুন।\n\n"
            f"👤 Support: `{SUPPORT_USERNAME}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Contact Support", url="https://t.me/Ahsanvai10")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="home")],
            ]),
        )
        return

    # =====================================================
    # ADMIN: LIVE DIRECT NAGAD ORDER APPROVE
    # =====================================================
    if data.startswith("approve:"):
        if str(user_id) != str(ADMIN_USER_ID):
            await query.answer("❌ আপনি Admin নন।", show_alert=True)
            return

        payment_id = int(data.split(":", 1)[1])
        payment = get_payment(payment_id)
        if not payment:
            await query.edit_message_text("❌ Payment request পাওয়া যায়নি।")
            return
        if payment["status"] != "pending":
            await query.answer("এই payment already processed.", show_alert=True)
            return
        if not API_KEY:
            await query.edit_message_text("❌ RechargeGames API key পাওয়া যাচ্ছে না।")
            return

        package = PACKAGES[payment["package_key"]]
        buyer_ref = f"SHOP-{payment_id}"
        payload = {
            "product": package["supplier_product"],
            "region": "Bangladesh",
            "quantity": 1,
            "player_id": payment["player_id"],
            "buyer_ref": buyer_ref,
        }

        try:
            response = requests.post(
                f"{API}/v1/orders",
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            result = response.json() if response.content else {}
            if response.status_code in (200, 201):
                supplier_order_id = result.get("order_id") or result.get("id") or "unknown"
                supplier_status = result.get("status", "pending")
                update_payment_status(payment_id, "approved")
                local_order_id = save_order(
                    payment["user_id"], payment["player_id"], payment["package_key"],
                    payment["package_name"], payment["amount"], "approved",
                    payment["transaction_id"], supplier_order_id, supplier_status, buyer_ref,
                )
                await query.edit_message_text(
                    "✅ PAYMENT APPROVED + LIVE ORDER SENT\n\n"
                    f"📋 Order: #{local_order_id}\n"
                    f"👤 User ID: {payment['user_id']}\n"
                    f"🆔 Player ID: {payment['player_id']}\n"
                    f"💎 {payment['package_name']}\n"
                    f"💵 ৳{payment['amount']}\n"
                    f"🧾 Txn ID: {payment['transaction_id']}\n\n"
                    f"📦 Supplier: {supplier_status}\n"
                    f"🆔 Supplier ID: {supplier_order_id}\n\n"
                    "🚀 LIVE RechargeGames order sent."
                )
                try:
                    await context.bot.send_message(
                        chat_id=payment["user_id"],
                        text=(
                            "✅ Payment approved!\n\n"
                            f"💎 {payment['package_name']}\n"
                            f"💵 ৳{payment['amount']}\n"
                            f"🆔 Player ID: {payment['player_id']}\n\n"
                            "🚀 Your LIVE top-up request has been sent.\n"
                            "⏳ Delivery may take a little time."
                        ),
                    )
                except Exception:
                    log.exception("Failed to notify customer")
            else:
                await query.edit_message_text(
                    "❌ RechargeGames order failed।\n\n"
                    "Payment approve করা হয়নি।\n\n"
                    f"HTTP: {response.status_code}\n{result}"
                )
        except Exception as e:
            log.exception("LIVE supplier order failed")
            await query.edit_message_text(
                "❌ RechargeGames connection/order failed।\n\n"
                "Payment approve করা হয়নি।"
            )
        return

    # =====================================================
    # ADMIN: DIRECT ORDER REJECT
    # =====================================================
    if data.startswith("reject:"):
        if str(user_id) != str(ADMIN_USER_ID):
            await query.answer("❌ আপনি Admin নন।", show_alert=True)
            return
        payment_id = int(data.split(":", 1)[1])
        payment = get_payment(payment_id)
        if not payment:
            await query.edit_message_text("❌ Payment request পাওয়া যায়নি।")
            return
        if payment["status"] != "pending":
            await query.answer("এই payment already processed.", show_alert=True)
            return
        update_payment_status(payment_id, "rejected")
        await query.edit_message_text(
            "❌ PAYMENT REJECTED\n\n"
            f"👤 User ID: {payment['user_id']}\n"
            f"🆔 Player ID: {payment['player_id']}\n"
            f"💎 {payment['package_name']}\n"
            f"💵 ৳{payment['amount']}\n"
            f"🧾 Txn ID: {payment['transaction_id']}"
        )
        try:
            await context.bot.send_message(
                chat_id=payment["user_id"],
                text=(
                    "❌ Payment request rejected.\n\n"
                    f"💎 {payment['package_name']}\n"
                    f"🧾 Txn ID: {payment['transaction_id']}\n\n"
                    "দয়া করে payment details check করে আবার চেষ্টা করুন।"
                ),
            )
        except Exception:
            log.exception("Failed to notify customer after rejection")
        return

    # =====================================================
    # ADMIN: WALLET RECHARGE APPROVE
    # =====================================================
    if data.startswith("wapprove:"):
        if str(user_id) != str(ADMIN_USER_ID):
            await query.answer("❌ আপনি Admin নন।", show_alert=True)
            return
        recharge_id = int(data.split(":", 1)[1])
        recharge = get_wallet_recharge(recharge_id)
        if not recharge:
            await query.edit_message_text("❌ Wallet recharge request পাওয়া যায়নি।")
            return
        if recharge["status"] != "pending":
            await query.answer("এই recharge already processed.", show_alert=True)
            return
        update_wallet_recharge_status(recharge_id, "approved")
        add_balance(recharge["user_id"], float(recharge["amount"]))
        new_balance = get_balance(recharge["user_id"])
        await query.edit_message_text(
            "✅ WALLET RECHARGE APPROVED\n\n"
            f"👤 User ID: {recharge['user_id']}\n"
            f"💵 Added: ৳{recharge['amount']:.2f}\n"
            f"🧾 Txn ID: {recharge['transaction_id']}\n"
            f"💰 New Balance: ৳{new_balance:.2f}"
        )
        try:
            await context.bot.send_message(
                chat_id=recharge["user_id"],
                text=(
                    "✅ Wallet recharge approved!\n\n"
                    f"💵 Added: ৳{recharge['amount']:.2f}\n"
                    f"💰 New Balance: ৳{new_balance:.2f}"
                ),
            )
        except Exception:
            log.exception("Failed to notify wallet user")
        return

    # =====================================================
    # ADMIN: WALLET RECHARGE REJECT
    # =====================================================
    if data.startswith("wreject:"):
        if str(user_id) != str(ADMIN_USER_ID):
            await query.answer("❌ আপনি Admin নন।", show_alert=True)
            return
        recharge_id = int(data.split(":", 1)[1])
        recharge = get_wallet_recharge(recharge_id)
        if not recharge:
            await query.edit_message_text("❌ Wallet recharge request পাওয়া যায়নি।")
            return
        if recharge["status"] != "pending":
            await query.answer("এই recharge already processed.", show_alert=True)
            return
        update_wallet_recharge_status(recharge_id, "rejected")
        await query.edit_message_text(
            "❌ WALLET RECHARGE REJECTED\n\n"
            f"👤 User ID: {recharge['user_id']}\n"
            f"💵 Amount: ৳{recharge['amount']:.2f}\n"
            f"🧾 Txn ID: {recharge['transaction_id']}"
        )
        try:
            await context.bot.send_message(
                chat_id=recharge["user_id"],
                text=(
                    "❌ Wallet recharge rejected.\n\n"
                    f"💵 Amount: ৳{recharge['amount']:.2f}\n"
                    f"🧾 Txn ID: {recharge['transaction_id']}"
                ),
            )
        except Exception:
            log.exception("Failed to notify wallet user after rejection")
        return

# =========================================================
# TEXT HANDLER
# =========================================================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)
    state = context.user_data.get("state")
    raw = update.message.text.strip()

    if state == "player":
        player_id = raw
        if not player_id.isdigit() or not 5 <= len(player_id) <= 20:
            await update.message.reply_text("❌ শুধু সঠিক সংখ্যার Player ID দিন।")
            return
        context.user_data["player_id"] = player_id
        context.user_data["state"] = "package"
        await update.message.reply_text(
            f"✅ Player ID: {player_id}\n\n💎 Package নির্বাচন করুন:",
            reply_markup=package_menu(),
        )
        return

    if state == "transaction_id":
        transaction_id = raw
        package_key = context.user_data.get("package")
        player_id = context.user_data.get("player_id")
        if not transaction_id or not package_key or not player_id:
            await update.message.reply_text("❌ Order information পাওয়া যায়নি। আবার /start করুন।")
            return
        package = PACKAGES[package_key]
        payment_id = create_payment(user_id, player_id, package_key, package["name"], package["selling_price"], transaction_id)
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Payment request submitted!\n\n"
            f"📋 Payment ID: #{payment_id}\n"
            f"💎 {package['name']}\n"
            f"💵 ৳{package['selling_price']}\n"
            f"🧾 Txn ID: {transaction_id}\n\n"
            "⏳ Admin payment verify করছেন।\n"
            "Approve হলে LIVE order process হবে।",
            reply_markup=main_menu(),
        )
        try:
            admin_keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ APPROVE", callback_data=f"approve:{payment_id}"),
                InlineKeyboardButton("❌ REJECT", callback_data=f"reject:{payment_id}"),
            ]])
            await context.bot.send_message(
                chat_id=int(ADMIN_USER_ID),
                text=(
                    "💳 NEW PAYMENT REQUEST\n\n"
                    f"📋 Payment ID: #{payment_id}\n"
                    f"👤 User ID: {user_id}\n"
                    f"🆔 Player ID: {player_id}\n"
                    f"💎 Package: {package['name']}\n"
                    f"💵 Amount: ৳{package['selling_price']}\n"
                    f"🧾 Txn ID: {transaction_id}\n\n"
                    "⚠️ আগে Nagad app-এ payment verify করুন।\n"
                    "তারপর APPROVE চাপুন।"
                ),
                reply_markup=admin_keyboard,
            )
        except Exception:
            log.exception("Failed to notify admin about payment")
        return

    if state == "wallet_amount":
        try:
            amount = float(raw)
        except ValueError:
            await update.message.reply_text("❌ সঠিক amount দিন। যেমন: 500")
            return
        if amount < 10 or amount > 100000:
            await update.message.reply_text("❌ Amount ৳10 থেকে ৳100,000-এর মধ্যে দিন।")
            return
        context.user_data["wallet_amount"] = amount
        context.user_data["state"] = "wallet_payment"
        await update.message.reply_text(
            "➕ Wallet Recharge\n\n"
            f"💵 Amount: ৳{amount:.2f}\n"
            f"📱 Nagad Number: `{NAGAD_NUMBER}`\n\n"
            "১️⃣ এই নম্বরে টাকা পাঠান।\n"
            "২️⃣ টাকা পাঠানোর পর I Paid চাপুন।",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ I Paid", callback_data="wallet_paid")],
                [InlineKeyboardButton("❌ Cancel", callback_data="home")],
            ]),
        )
        return

    if state == "wallet_transaction_id":
        transaction_id = raw
        amount = context.user_data.get("wallet_amount")
        if not transaction_id or not amount:
            await update.message.reply_text("❌ Recharge information পাওয়া যায়নি। আবার চেষ্টা করুন।")
            return
        recharge_id = create_wallet_recharge(user_id, float(amount), transaction_id)
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Wallet recharge request submitted!\n\n"
            f"📋 Recharge ID: #{recharge_id}\n"
            f"💵 Amount: ৳{float(amount):.2f}\n"
            f"🧾 Txn ID: {transaction_id}\n\n"
            "⏳ Admin payment verify করছেন। Approve হলে balance add হবে।",
            reply_markup=main_menu(),
        )
        try:
            admin_keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ APPROVE", callback_data=f"wapprove:{recharge_id}"),
                InlineKeyboardButton("❌ REJECT", callback_data=f"wreject:{recharge_id}"),
            ]])
            await context.bot.send_message(
                chat_id=int(ADMIN_USER_ID),
                text=(
                    "➕ NEW WALLET RECHARGE\n\n"
                    f"📋 Recharge ID: #{recharge_id}\n"
                    f"👤 User ID: {user_id}\n"
                    f"💵 Amount: ৳{float(amount):.2f}\n"
                    f"🧾 Txn ID: {transaction_id}\n\n"
                    "⚠️ আগে Nagad app-এ payment verify করুন।"
                ),
                reply_markup=admin_keyboard,
            )
        except Exception:
            log.exception("Failed to notify admin about wallet recharge")
        return

    await update.message.reply_text("নিচের menu ব্যবহার করুন 👇", reply_markup=main_menu())

# =========================================================
# MAIN
# =========================================================
def main():
    init_db()
    if not NAGAD_NUMBER:
        log.warning("NAGAD_NUMBER is missing")
    if not API_KEY:
        log.warning("RECHARGEGAME_API_KEY is missing")
    log.info("Game TopUp BD bot started — LIVE supplier mode")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
