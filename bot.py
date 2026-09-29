import os
import logging
import requests
import time

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


# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]
API_KEY = os.environ.get("RECHARGEGAME_API_KEY", "")

API = "https://api.rechargegame.games"


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(__name__)


# =========================
# FREE FIRE PACKAGES
# =========================
#
# product = RechargeGames product name
# price   = supplier cost shown in bot
#
# These are the package names/prices
# we were using during setup.
#
# Later we can replace these with
# your actual Bangladesh selling prices.
#

PACKAGES = {

    "ff_115": (
        "115 Diamonds",
        "Free Fire 115 Diamonds",
        "$0.61"
    ),

    "ff_240": (
        "240 Diamonds",
        "Free Fire 240 Diamonds",
        "$1.22"
    ),

    "ff_610": (
        "610 Diamonds",
        "Free Fire 610 Diamonds",
        "$3.07"
    ),

    "ff_1240": (
        "1240 Diamonds",
        "Free Fire 1240 Diamonds",
        "$6.11"
    ),

    "ff_2830": (
        "2830 Diamonds",
        "Free Fire 2830 Diamonds",
        "$19.25"
    ),

    "ff_wlite": (
        "Weekly Lite",
        "Free Fire Weekly Lite",
        "$0.34"
    ),

    "ff_weekly": (
        "Weekly Membership",
        "Free Fire Weekly Membership",
        "$1.22"
    ),

    "ff_monthly": (
        "Monthly Membership",
        "Free Fire Monthly Membership",
        "$6.10"
    ),
}


# =========================
# MAIN MENU
# =========================

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


# =========================
# GAME MENU
# =========================

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


# =========================
# PACKAGE MENU
# =========================

def package_menu():

    rows = []

    for key, (name, product, price) in PACKAGES.items():

        rows.append([
            InlineKeyboardButton(
                f"{name} — {price}",
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


# =========================
# /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(

        "🎮 Game TopUp BD\n\n"
        "স্বাগতম! একটি অপশন বেছে নিন 👇",

        reply_markup=main_menu()
    )


# =========================
# /HELP
# =========================

async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "/start — Main menu\n"
        "/ping — Telegram + RechargeGames API test\n"
        "/help — Help"
    )


# =========================
# /PING
# =========================

async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not API_KEY:

        await update.message.reply_text(
            "❌ RECHARGEGAME_API_KEY Render Environment Variables-এ নেই।"
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

                "⚠️ RechargeGames API response:\n\n"
                f"{data}"
            )

    except Exception as e:

        log.exception("Ping failed")

        await update.message.reply_text(

            "❌ API connection failed.\n\n"
            f"{e}"
        )


# =========================
# BUTTON HANDLER
# =========================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data


    # =====================
    # HOME
    # =====================

    if data == "home":

        context.user_data.clear()

        await query.edit_message_text(

            "🏠 Main menu",

            reply_markup=main_menu()
        )

        return


    # =====================
    # GAME MENU
    # =====================

    if data == "games":

        await query.edit_message_text(

            "🎮 Select a game:",

            reply_markup=games_menu()
        )

        return


    # =====================
    # FREE FIRE
    # =====================

    if data == "freefire":

        context.user_data.clear()

        context.user_data["state"] = "player"

        await query.edit_message_text(

            "🔥 Free Fire\n\n"
            "আপনার Player ID পাঠান:\n\n"
            "উদাহরণ: 51234567"
        )

        return


    # =====================
    # ML / PUBG
    # =====================

    if data in ("ml", "pubg"):

        await query.edit_message_text(

            "⏳ এই game এখনো configure করা হয়নি।\n\n"
            "আগে Free Fire চালু করছি।",

            reply_markup=games_menu()
        )

        return


    # =====================
    # PACKAGE SELECT
    # =====================

    if data in PACKAGES:

        if context.user_data.get("state") != "package":

            await query.edit_message_text(

                "❌ আগে Player ID দিন।",

                reply_markup=games_menu()
            )

            return


        context.user_data["package"] = data

        name, product, price = PACKAGES[data]

        player_id = context.user_data.get(
            "player_id"
        )


        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "✅ Confirm",
                    callback_data="confirm"
                ),

                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel"
                )
            ]

        ])


        await query.edit_message_text(

            "📋 Order Summary\n\n"

            "🎮 Game: Free Fire\n"

            f"🆔 Player ID: {player_id}\n"

            f"💎 Package: {name}\n"

            f"💵 Supplier cost: {price}\n\n"

            "🧪 TEST MODE\n"
            "Confirm করলে RechargeGames-এ TEST order পাঠানো হবে।\n\n"

            "⚠️ Payment system এখনো চালু হয়নি।",

            reply_markup=keyboard
        )

        return


    # =====================
    # CONFIRM
    # =====================

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

                "❌ Order information পাওয়া যায়নি।\n"
                "আবার চেষ্টা করুন।",

                reply_markup=main_menu()
            )

            return


        name, product, price = PACKAGES[
            package_key
        ]


        # Unique TEST reference
        buyer_ref = (
            f"TEST-"
            f"{query.from_user.id}-"
            f"{int(time.time())}"
        )


        # =====================
        # RECHARGEGAMES PAYLOAD
        # =====================

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


            # =====================
            # SUCCESS
            # =====================

            if response.status_code in (200, 201):

                order_id = result.get(
                    "order_id",
                    "unknown"
                )

                status = result.get(
                    "status",
                    "pending"
                )


                await query.edit_message_text(

                    "🧪 RechargeGames TEST order created!\n\n"

                    "🎮 Free Fire\n"

                    f"🆔 Player ID: {player_id}\n"

                    f"💎 Package: {name}\n"

                    f"🆔 Supplier Order: {order_id}\n"

                    f"📦 Status: {status}\n\n"

                    "⚠️ এটি TEST order।\n"
                    "Payment system এখনো চালু হয়নি।",

                    reply_markup=main_menu()
                )


            # =====================
            # FAILED
            # =====================

            else:

                await query.edit_message_text(

                    "❌ RechargeGames order failed.\n\n"

                    f"HTTP Status: "
                    f"{response.status_code}\n\n"

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


    # =====================
    # CANCEL
    # =====================

    if data == "cancel":

        context.user_data.clear()

        await query.edit_message_text(

            "❌ Order cancelled.",

            reply_markup=main_menu()
        )

        return


    # =====================
    # BALANCE
    # =====================

    if data == "balance":

        await query.edit_message_text(

            "💰 Balance system পরে যোগ হবে।",

            reply_markup=main_menu()
        )

        return


    # =====================
    # ORDERS
    # =====================

    if data == "orders":

        await query.edit_message_text(

            "📋 Order history পরে যোগ হবে।",

            reply_markup=main_menu()
        )

        return


    # =====================
    # REFERRAL
    # =====================

    if data == "referral":

        await query.edit_message_text(

            "🎁 Referral system পরে যোগ হবে।",

            reply_markup=main_menu()
        )

        return


    # =====================
    # SUPPORT
    # =====================

    if data == "support":

        await query.edit_message_text(

            "🆘 Support contact পরে সেট হবে।",

            reply_markup=main_menu()
        )

        return


# =========================
# TEXT HANDLER
# =========================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if context.user_data.get("state") == "player":

        player_id = update.message.text.strip()


        # Player ID validation

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


    await update.message.reply_text(

        "নিচের menu ব্যবহার করুন 👇",

        reply_markup=main_menu()
    )


# =========================
# MAIN
# =========================

def main():

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


    # Start bot

    log.info(
        "Game TopUp BD bot started"
    )

    app.run_polling()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
