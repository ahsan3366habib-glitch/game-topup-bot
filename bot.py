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
# PACKAGE LIST
# =========================================================
#
# Customer sees BDT price.
#
# supplier_product = RechargeGames product name
# supplier_cost   = internal supplier cost
# selling_price    = customer price in BDT
#
# Change selling_price whenever you want.
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

    # Users / wallet

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            referral_code TEXT,
            referred_by INTEGER,
            created_at INTEGER
        )
    """)

    # Orders

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            player_id TEXT,
            package_key TEXT,
            package_name TEXT,
            selling_price REAL,
            supplier_order_id TEXT,
            supplier_status TEXT,
            buyer_ref TEXT UNIQUE,
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

        referral_code = f"REF{user_id}"

        cur.execute(
            """
            INSERT INTO users
            (user_id, balance, referral_code, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                0,
                referral_code,
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


def save_order(
    user_id,
    player_id,
    package_key,
    package_name,
    selling_price,
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
            supplier_order_id,
            supplier_status,
            buyer_ref,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            player_id,
            package_key,
            package_name,
            selling_price,
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


def get_order(order_id, user_id):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        AND user_id = ?
        """,
        (
            order_id,
            user_id
        )
    )

    row = cur.fetchone()

    conn.close()

    return row


def update_supplier_status(
    order_id,
    status
):

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE orders
        SET supplier_status = ?
        WHERE id = ?
        """,
        (
            status,
            order_id
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# MAIN MENU
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


# =========================================================
# GAME MENU
# =========================================================

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


# =========================================================
# PACKAGE MENU
# =========================================================

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
# /START
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
# /HELP
# =========================================================

async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎮 Game TopUp BD\n\n"

        "/start — Main menu\n"
        "/ping — RechargeGames API test\n"
        "/help — Help"
    )


# =========================================================
# /PING
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

                "⚠️ API response:\n\n"
                f"{data}"
            )

    except Exception as e:

        log.exception("Ping failed")

        await update.message.reply_text(

            "❌ API connection failed.\n\n"
            f"{e}"
        )


# =========================================================
# BUTTON HANDLER
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
    # PACKAGE SELECT
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

        balance = get_balance(user_id)

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🧪 Confirm TEST Order",
                    callback_data="confirm"
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

            f"💵 Price: ৳{package['selling_price']}\n"

            f"💰 Balance: ৳{balance:.2f}\n\n"

            "🧪 TEST MODE\n"
            "Confirm করলে RechargeGames-এ TEST order যাবে।\n\n"

            "⚠️ Customer payment এখনো চালু হয়নি।",

            reply_markup=keyboard
        )

        return


    # =====================================================
    # CONFIRM TEST ORDER
    # =====================================================

    if data == "confirm":

        if not API_KEY:

            await query.edit_message_text(

                "❌ RechargeGames API key পাওয়া যাচ্ছে না।",

                reply_markup=main_menu()
            )

            return


        player_id = context.user_data.get(
            "player_id"
        )

        package_key = context.user_data.get(
            "package"
        )


        if not player_id or not package_key:

            await query.edit_message_text(

                "❌ Order information পাওয়া যায়নি।",

                reply_markup=main_menu()
            )

            return


        package = PACKAGES[package_key]

        product = package[
            "supplier_product"
        ]

        buyer_ref = (
            f"TEST-"
            f"{user_id}-"
            f"{int(time.time())}"
        )


        payload = {

            "product": f"TEST {product}",

            "region": "Bangladesh",

            "quantity": 1,

            "player_id": player_id,

            "buyer_ref": buyer_ref
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
                    "raw_response":
                        response.text
                }


            # =================================================
            # SUCCESS
            # =================================================

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

                    user_id=user_id,

                    player_id=player_id,

                    package_key=package_key,

                    package_name=package["name"],

                    selling_price=package[
                        "selling_price"
                    ],

                    supplier_order_id=supplier_order_id,

                    supplier_status=supplier_status,

                    buyer_ref=buyer_ref
                )


                await query.edit_message_text(

                    "🧪 TEST ORDER CREATED ✅\n\n"

                    f"📋 Order ID: #{local_order_id}\n"

                    f"🎮 Free Fire\n"

                    f"🆔 Player ID: {player_id}\n"

                    f"💎 {package['name']}\n"

                    f"💵 Price: ৳{package['selling_price']}\n"

                    f"📦 Status: {supplier_status}\n"

                    f"🆔 Supplier ID: {supplier_order_id}\n\n"

                    "⚠️ এটি TEST order।",

                    reply_markup=main_menu()
                )


            # =================================================
            # FAILED
            # =================================================

            else:

                await query.edit_message_text(

                    "❌ RechargeGames order failed.\n\n"

                    f"HTTP: {response.status_code}\n\n"

                    f"Response:\n{result}",

                    reply_markup=main_menu()
                )


        except Exception as e:

            log.exception(
                "Supplier order failed"
            )


            await query.edit_message_text(

                "❌ RechargeGames connection failed.\n\n"
                f"{e}",

                reply_markup=main_menu()
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

            "ℹ️ Balance recharge/payment system "
            "এখনো চালু হয়নি।",

            reply_markup=main_menu()
        )

        return


    # =====================================================
    # ORDER HISTORY
    # =====================================================

    if data == "orders":

        orders = get_user_orders(
            user_id,
            limit=10
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

                f"📦 Status: {order['supplier_status']}\n\n"
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

        ensure_user(user_id)

        conn = get_db()

        cur = conn.cursor()

        cur.execute(

            """
            SELECT referral_code
            FROM users
            WHERE user_id = ?
            """,

            (user_id,)
        )

        row = cur.fetchone()

        conn.close()


        referral_code = (
            row["referral_code"]
            if row
            else f"REF{user_id}"
        )


        await query.edit_message_text(

            "🎁 Referral\n\n"

            f"Your referral code:\n"
            f"`{referral_code}`\n\n"

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

            "কোনো সমস্যা হলে Admin-এর সাথে যোগাযোগ করুন।\n\n"

            "📞 Support system পরে configure করা হবে।",

            reply_markup=main_menu()
        )

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


    # =====================================================
    # PLAYER ID
    # =====================================================

    if context.user_data.get("state") == "player":

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

    # Create database/tables
    init_db()


    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )


    # Commands

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


    # Buttons

    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )


    # Text

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
