import os
import time
import sqlite3
import logging
import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]

API_KEY = os.environ.get(
    "RECHARGEGAME_API_KEY",
    ""
)

NAGAD_NUMBER = os.environ.get(
    "NAGAD_NUMBER",
    ""
)

ADMIN_USER_ID = os.environ.get(
    "ADMIN_USER_ID",
    ""
)

API = "https://api.rechargegame.games"

DB_FILE = "topup_bot.db"


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(__name__)


# =========================================================
# PACKAGES
# =========================================================

PACKAGES = {

    "ff_115": {
        "name": "115 Diamonds",
        "supplier_product": "Free Fire 115 Diamonds",
        "supplier_cost": "$0.61",
        "selling_price": 80
    },

    "ff_240": {
        "name": "240 Diamonds",
        "supplier_product": "Free Fire 240 Diamonds",
        "supplier_cost": "$1.22",
        "selling_price": 160
    },

    "ff_610": {
        "name": "610 Diamonds",
        "supplier_product": "Free Fire 610 Diamonds",
        "supplier_cost": "$3.07",
        "selling_price": 400
    },

    "ff_1240": {
        "name": "1240 Diamonds",
        "supplier_product": "Free Fire 1240 Diamonds",
        "supplier_cost": "$6.11",
        "selling_price": 800
    },

    "ff_2830": {
        "name": "2830 Diamonds",
        "supplier_product": "Free Fire 2830 Diamonds",
        "supplier_cost": "$19.25",
        "selling_price": 2500
    },

    "ff_wlite": {
        "name": "Weekly Lite",
        "supplier_product": "Free Fire Weekly Lite",
        "supplier_cost": "$0.34",
        "selling_price": 50
    },

    "ff_weekly": {
        "name": "Weekly Membership",
        "supplier_product": "Free Fire Weekly Membership",
        "supplier_cost": "$1.22",
        "selling_price": 170
    },

    "ff_monthly": {
        "name": "Monthly Membership",
        "supplier_product": "Free Fire Monthly Membership",
        "supplier_cost": "$6.10",
        "selling_price": 850
    }
}


# =========================================================
# DATABASE
# =========================================================

def get_db():

    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )

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

    conn.commit()
    conn.close()


def ensure_user(user_id):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    row = cur.fetchone()

    if not row:

        cur.execute(
            """
            INSERT INTO users
            (user_id, balance, referral_code, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                0,
                f"REF{user_id}",
                int(time.time())
            )
        )

        conn.commit()

    conn.close()


def get_balance(user_id):

    ensure_user(user_id)

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return float(row["balance"])

    return 0


def create_payment(
    user_id,
    player_id,
    package_key,
    package_name,
    amount,
    transaction_id
):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO payments
        (
            user_id,
            player_id,
            package_key,
            package_name,
            amount,
            transaction_id,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            player_id,
            package_key,
            package_name,
            amount,
            transaction_id,
            "pending",
            int(time.time())
        )
    )

    conn.commit()

    payment_id = cur.lastrowid

    conn.close()

    return payment_id


def get_payment(payment_id):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM payments
        WHERE id = ?
        """,
        (payment_id,)
    )

    row = cur.fetchone()

    conn.close()

    return row


def update_payment_status(
    payment_id,
    status
):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE payments
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            payment_id
        )
    )

    conn.commit()
    conn.close()


def save_order(
    user_id,
    player_id,
    package_key,
    package_name,
    selling_price,
    payment_status,
    transaction_id,
    supplier_order_id,
    supplier_status,
    buyer_ref
):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO orders
        (
            user_id,
            player_id,
            package_key,
            package_name,
            selling_price,
            payment_status,
            transaction_id,
            supplier_order_id,
            supplier_status,
            buyer_ref,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            player_id,
            package_key,
            package_name,
            selling_price,
            payment_status,
            transaction_id,
            supplier_order_id,
            supplier_status,
            buyer_ref,
            int(time.time())
        )
    )

    conn.commit()

    order_id = cur.lastrowid

    conn.close()

    return order_id


def get_user_orders(user_id, limit=10):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit
        )
    )

    rows = cur.fetchall()

    conn.close()

    return rows


# =========================================================
# MENUS
# =========================================================

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🎮 Game Top Up",
                callback_data="games"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 My Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "📋 My Orders",
                callback_data="orders"
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 Referral",
                callback_data="referral"
            ),
            InlineKeyboardButton(
                "🆘 Support",
                callback_data="support"
            )
        ]
    ])


def games_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔥 Free Fire",
                callback_data="freefire"
            )
        ],

        [
            InlineKeyboardButton(
                "⚔️ Mobile Legends",
                callback_data="ml"
            ),
            InlineKeyboardButton(
                "🎯 PUBG Mobile",
                callback_data="pubg"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    ])


def package_menu():

    rows = []

    for key, package in PACKAGES.items():

        rows.append([
            InlineKeyboardButton(
                f"💎 {package['name']} — ৳{package['selling_price']}",
                callback_data=key
            )
        ])

    rows.append([
        InlineKeyboardButton(
            "🔙 Back",
            callback_data="games"
        )
    ])

    return InlineKeyboardMarkup(rows)


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ensure_user(user_id)

    context.user_data.clear()

    await update.message.reply_text(
        "🎮 Game TopUp BD\n\n"
        "স্বাগতম! একটি অপশন বেছে নিন 👇",
        reply_markup=main_menu()
    )


# =========================================================
# HELP
# =========================================================

async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "/start — Main menu\n"
        "/ping — RechargeGames API test\n"
        "/help — Help"
    )


# =========================================================
# PING
# =========================================================

async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not API_KEY:

        await update.message.reply_text(
            "❌ RechargeGames API key পাওয়া যাচ্ছে না।"
        )

        return

    try:

        response = requests.get(
            f"{API}/v1/ping",
            headers={
                "X-API-Key": API_KEY
            },
            timeout=20
        )

        data = response.json()

        if response.ok and data.get("ok"):

            await update.message.reply_text(
                "✅ Bot online\n"
                "✅ RechargeGames connected\n\n"
                f"Buyer: {data.get('buyer', 'unknown')}"
            )

        else:

            await update.message.reply_text(
                f"⚠️ API response:\n\n{data}"
            )

    except Exception as e:

        log.exception("Ping failed")

        await update.message.reply_text(
            f"❌ API connection failed.\n\n{e}"
        )


# =========================================================
# BUTTONS
# =========================================================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    user_id = query.from_user.id

    ensure_user(user_id)


    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        context.user_data.clear()

        await query.edit_message_text(
            "🏠 Main menu",
            reply_markup=main_menu()
        )

        return


    # =====================================================
    # GAMES
    # =====================================================

    if data == "games":

        await query.edit_message_text(
            "🎮 Select a game:",
            reply_markup=games_menu()
        )

        return


    # =====================================================
    # FREE FIRE
    # =====================================================

    if data == "freefire":

        context.user_data.clear()

        context.user_data["state"] = "player"

        await query.edit_message_text(
            "🔥 Free Fire\n\n"
            "আপনার Player ID পাঠান:\n\n"
            "উদাহরণ: 51234567"
        )

        return


    # =====================================================
    # ML / PUBG
    # =====================================================

    if data in ("ml", "pubg"):

        await query.edit_message_text(
            "⏳ এই game এখনো configure করা হয়নি।\n\n"
            "আগে Free Fire চালু করছি।",
            reply_markup=games_menu()
        )

        return


    # =====================================================
    # PACKAGE
    # =====================================================

    if data in PACKAGES:

        if context.user_data.get("state") != "package":

            await query.edit_message_text(
                "❌ আগে Player ID দিন।",
                reply_markup=games_menu()
            )

            return


        context.user_data["package"] = data

        package = PACKAGES[data]

        player_id = context.user_data.get(
            "player_id"
        )


        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "💳 Pay with Nagad",
                    callback_data="pay_nagad"
                )
            ],

            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel"
                )
            ]
        ])


        await query.edit_message_text(

            "📋 Order Summary\n\n"
            "🎮 Free Fire\n"
            f"🆔 Player ID: {player_id}\n"
            f"💎 Package: {package['name']}\n"
            f"💵 Price: ৳{package['selling_price']}\n\n"
            "Payment করতে নিচের button চাপুন 👇",

            reply_markup=keyboard
        )

        return


    # =====================================================
    # NAGAD PAYMENT
    # =====================================================

    if data == "pay_nagad":

        package_key = context.user_data.get(
            "package"
        )

        player_id = context.user_data.get(
            "player_id"
        )


        if not package_key or not player_id:

            await query.edit_message_text(
                "❌ Order information পাওয়া যায়নি।",
                reply_markup=main_menu()
            )

            return


        package = PACKAGES[package_key]

        amount = package["selling_price"]


        await query.edit_message_text(

            "💳 Nagad Payment\n\n"

            "📱 Nagad Number:\n"
            f"`{NAGAD_NUMBER}`\n\n"

            f"💵 Amount: ৳{amount}\n\n"

            "১️⃣ উপরের Nagad নম্বরে টাকা পাঠান।\n"
            "২️⃣ টাকা পাঠানোর পর নিচের "
            "I Paid button চাপুন।\n"
            "৩️⃣ তারপর Transaction ID দিন।",

            parse_mode="Markdown",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "✅ I Paid",
                        callback_data="i_paid"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data=package_key
                    )
                ]
            ])
        )

        return


    # =====================================================
    # I PAID
    # =====================================================

    if data == "i_paid":

        package_key = context.user_data.get(
            "package"
        )

        player_id = context.user_data.get(
            "player_id"
        )


        if not package_key or not player_id:

            await query.edit_message_text(
                "❌ Order information পাওয়া যায়নি।",
                reply_markup=main_menu()
            )

            return


        context.user_data["state"] = (
            "transaction_id"
        )


        await query.edit_message_text(

            "🧾 Transaction ID দিন:\n\n"
            "উদাহরণ:\n"
            "`8A7B6C5D9E`\n\n"
            "শুধু Transaction ID পাঠান।",

            parse_mode="Markdown"
        )

        return


    # =====================================================
    # CANCEL
    # =====================================================

    if data == "cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "❌ Order cancelled.",
            reply_markup=main_menu()
        )

        return


    # =====================================================
    # BALANCE
    # =====================================================

    if data == "balance":

        balance = get_balance(user_id)

        await query.edit_message_text(

            "💰 My Balance\n\n"
            f"💵 Balance: ৳{balance:.2f}\n\n"
            "ℹ️ Wallet recharge এখনো চালু হয়নি।",

            reply_markup=main_menu()
        )

        return


    # =====================================================
    # ORDERS
    # =====================================================

    if data == "orders":

        orders = get_user_orders(
            user_id,
            10
        )


        if not orders:

            await query.edit_message_text(
                "📋 My Orders\n\n"
                "এখনো কোনো order নেই।",
                reply_markup=main_menu()
            )

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


        await query.edit_message_text(
            text,
            reply_markup=main_menu()
        )

        return


    # =====================================================
    # REFERRAL
    # =====================================================

    if data == "referral":

        await query.edit_message_text(

            "🎁 Referral\n\n"
            f"Your referral code:\n"
            f"`REF{user_id}`\n\n"
            "Referral reward system পরে চালু হবে।",

            parse_mode="Markdown",

            reply_markup=main_menu()
        )

        return


    # =====================================================
    # SUPPORT
    # =====================================================

    if data == "support":

        await query.edit_message_text(

            "🆘 Support\n\n"
            "কোনো সমস্যা হলে Admin-এর সাথে যোগাযোগ করুন।",

            reply_markup=main_menu()
        )

        return


    # =====================================================
    # ADMIN APPROVE
    # =====================================================

    if data.startswith("approve:"):

        if str(user_id) != str(ADMIN_USER_ID):

            await query.answer(
                "❌ আপনি Admin নন।",
                show_alert=True
            )

            return


        payment_id = int(
            data.split(":")[1]
        )

        payment = get_payment(
            payment_id
        )


        if not payment:

            await query.edit_message_text(
                "❌ Payment request পাওয়া যায়নি।"
            )

            return


        if payment["status"] != "pending":

            await query.answer(
                "এই payment already processed.",
                show_alert=True
            )

            return


        update_payment_status(
            payment_id,
            "approved"
        )


        package = PACKAGES[
            payment["package_key"]
        ]


        # =================================================
        # RECHARGEGAMES TEST ORDER
        # =================================================

        if not API_KEY:

            await query.edit_message_text(
                "❌ API key পাওয়া যাচ্ছে না।"
            )

            return


        buyer_ref = (
            f"TEST-"
            f"{payment['user_id']}-"
            f"{int(time.time())}"
        )


        payload = {

            "product":
                f"TEST {package['supplier_product']}",

            "region":
                "Bangladesh",

            "quantity":
                1,

            "player_id":
                payment["player_id"],

            "buyer_ref":
                buyer_ref
        }


        try:

            response = requests.post(

                f"{API}/v1/orders",

                headers={
                    "X-API-Key": API_KEY,
                    "Content-Type":
                        "application/json"
                },

                json=payload,

                timeout=20
            )


            try:
                result = response.json()
            except Exception:
                result = {
                    "raw": response.text
                }


            if response.status_code in (200, 201):

                supplier_order_id = result.get(
                    "order_id",
                    "unknown"
                )

                supplier_status = result.get(
                    "status",
                    "pending"
                )


                local_order_id = save_order(

                    user_id=payment["user_id"],

                    player_id=payment["player_id"],

                    package_key=payment["package_key"],

                    package_name=payment["package_name"],

                    selling_price=payment["amount"],

                    payment_status="approved",

                    transaction_id=payment["transaction_id"],

                    supplier_order_id=supplier_order_id,

                    supplier_status=supplier_status,

                    buyer_ref=buyer_ref
                )


                await query.edit_message_text(

                    "✅ PAYMENT APPROVED\n\n"

                    f"📋 Order: #{local_order_id}\n"
                    f"👤 User ID: {payment['user_id']}\n"
                    f"🆔 Player ID: {payment['player_id']}\n"
                    f"💎 {payment['package_name']}\n"
                    f"💵 ৳{payment['amount']}\n"
                    f"🧾 Txn ID: {payment['transaction_id']}\n\n"
                    f"📦 Supplier: {supplier_status}\n"
                    f"🆔 Supplier ID: {supplier_order_id}\n\n"
                    "🧪 TEST order sent."
                )


                try:

                    await context.bot.send_message(

                        chat_id=payment["user_id"],

                        text=(
                            "✅ Payment approved!\n\n"
                            f"💎 {payment['package_name']}\n"
                            f"💵 ৳{payment['amount']}\n"
                            f"🧾 Txn ID: {payment['transaction_id']}\n\n"
                            "📦 Your top-up request has been sent."
                        )
                    )

                except Exception:
                    pass


            else:

                await query.edit_message_text(

                    "⚠️ Payment approved, "
                    "but supplier order failed.\n\n"
                    f"Response:\n{result}"
                )


        except Exception as e:

            log.exception(
                "Supplier order failed"
            )

            await query.edit_message_text(
                "⚠️ Payment approved, "
                "but RechargeGames connection failed.\n\n"
                f"{e}"
            )

        return


    # =====================================================
    # ADMIN REJECT
    # =====================================================

    if data.startswith("reject:"):

        if str(user_id) != str(ADMIN_USER_ID):

            await query.answer(
                "❌ আপনি Admin নন।",
                show_alert=True
            )

            return


        payment_id = int(
            data.split(":")[1]
        )

        payment = get_payment(
            payment_id
        )


        if not payment:

            await query.edit_message_text(
                "❌ Payment request পাওয়া যায়নি।"
            )

            return


        if payment["status"] != "pending":

            await query.answer(
                "এই payment already processed.",
                show_alert=True
            )

            return


        update_payment_status(
            payment_id,
            "rejected"
        )


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
                    "দয়া করে payment details check করে "
                    "আবার চেষ্টা করুন।"
                )
            )

        except Exception:
            pass

        return


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ensure_user(user_id)

    state = context.user_data.get(
        "state"
    )


    # =====================================================
    # PLAYER ID
    # =====================================================

    if state == "player":

        player_id = update.message.text.strip()


        if (
            not player_id.isdigit()
            or not 5 <= len(player_id) <= 20
        ):

            await update.message.reply_text(
                "❌ শুধু সঠিক সংখ্যার Player ID দিন।"
            )

            return


        context.user_data["player_id"] = (
            player_id
        )

        context.user_data["state"] = (
            "package"
        )


        await update.message.reply_text(
            f"✅ Player ID: {player_id}\n\n"
            "💎 Package নির্বাচন করুন:",
            reply_markup=package_menu()
        )

        return


    # =====================================================
    # TRANSACTION ID
    # =====================================================

    if state == "transaction_id":

        transaction_id = (
            update.message.text.strip()
        )


        if not transaction_id:

            await update.message.reply_text(
                "❌ Transaction ID দিন।"
            )

            return


        package_key = context.user_data.get(
            "package"
        )

        player_id = context.user_data.get(
            "player_id"
        )


        if not package_key or not player_id:

            await update.message.reply_text(
                "❌ Order information পাওয়া যায়নি। "
                "আবার /start করুন।"
            )

            return


        package = PACKAGES[
            package_key
        ]


        payment_id = create_payment(

            user_id=user_id,

            player_id=player_id,

            package_key=package_key,

            package_name=package["name"],

            amount=package["selling_price"],

            transaction_id=transaction_id
        )


        context.user_data.clear()


        await update.message.reply_text(

            "✅ Payment request submitted!\n\n"

            f"📋 Payment ID: #{payment_id}\n"
            f"💎 {package['name']}\n"
            f"💵 ৳{package['selling_price']}\n"
            f"🧾 Txn ID: {transaction_id}\n\n"

            "⏳ Admin payment verify করছেন।\n"
            "Approve হলে order process হবে।",

            reply_markup=main_menu()
        )


        # =================================================
        # SEND PAYMENT REQUEST TO ADMIN
        # =================================================

        if ADMIN_USER_ID:

            admin_keyboard = InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "✅ APPROVE",
                        callback_data=
                        f"approve:{payment_id}"
                    ),

                    InlineKeyboardButton(
                        "❌ REJECT",
                        callback_data=
                        f"reject:{payment_id}"
                    )
                ]

            ])


            try:

                await context.bot.send_message(

                    chat_id=int(
                        ADMIN_USER_ID
                    ),

                    text=(

                        "💳 NEW PAYMENT REQUEST\n\n"

                        f"📋 Payment ID: #{payment_id}\n"

                        f"👤 User ID: {user_id}\n"

                        f"🆔 Player ID: {player_id}\n"

                        f"💎 Package: {package['name']}\n"

                        f"💵 Amount: ৳{package['selling_price']}\n"

                        f"🧾 Txn ID: {transaction_id}\n\n"

                        "⚠️ Nagad app-এ payment "
                        "নিজে verify করে তারপর Approve করুন।"
                    ),

                    reply_markup=admin_keyboard
                )

            except Exception as e:

                log.exception(
                    "Failed to notify admin"
                )

        return


    # =====================================================
    # DEFAULT
    # =====================================================

    await update.message.reply_text(
        "নিচের menu ব্যবহার করুন 👇",
        reply_markup=main_menu()
    )


# =========================================================
# MAIN
# =========================================================

def main():

    init_db()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CommandHandler(
            "help",
            help_cmd
        )
    )


    app.add_handler(
        CommandHandler(
            "ping",
            ping
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )


    log.info(
        "Game TopUp BD bot started"
    )


    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
