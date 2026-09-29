import asyncio
import os
import threading
from functools import wraps

from flask import Flask, jsonify, request, send_from_directory, session

import bot_manual

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
WEBSITE_DIR = os.path.join(APP_ROOT, "website")

app = Flask(__name__, static_folder=WEBSITE_DIR, static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
)

ADMIN_PANEL_PASSWORD = os.environ.get("ADMIN_PANEL_PASSWORD", "")


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_ok"):
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


def create_web_order(uid, package_key, txn_id, payment_method):
    package = bot_manual.PACKAGES.get(package_key)
    if not package:
        raise ValueError("Invalid package")

    uid = str(uid or "").strip()
    if not uid.isdigit() or not 5 <= len(uid) <= 20:
        raise ValueError("Invalid Free Fire UID")

    txn_id = str(txn_id or "").strip()
    if len(txn_id) < 4 or len(txn_id) > 80:
        raise ValueError("Invalid transaction ID")

    payment_method = str(payment_method or "").strip()
    if payment_method not in {"bKash", "Nagad", "Upay"}:
        raise ValueError("Invalid payment method")

    name, amount = package
    with bot_manual.db() as con:
        cur = con.execute(
            """
            INSERT INTO orders
            (user_id, username, player_id, package_key, package_name, amount,
             txn_id, status, created_at, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'), ?)
            """,
            (0, "website", uid, package_key, name, amount, txn_id,
             "payment_pending", payment_method),
        )
        return cur.lastrowid, name, amount


def notify_admin(order_id):
    """Send a website order to the Telegram admin from the bot's event loop."""
    order = bot_manual.get_order(order_id)
    if not order:
        return

    bot_app = bot_manual.BOT_APP
    bot_loop = bot_manual.BOT_LOOP
    if not bot_app or not bot_loop or not bot_loop.is_running():
        bot_manual.log.warning("Telegram bot loop is not ready; order #%s saved", order_id)
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ PAYMENT VERIFIED", callback_data=f"admin:verify:{order_id}")],
        [InlineKeyboardButton("🎮 TOP-UP DONE", callback_data=f"admin:done:{order_id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"admin:reject:{order_id}")],
    ])

    payment_method = order["payment_method"] if "payment_method" in order.keys() else "-"
    text = (
        "🔔 *NEW WEBSITE ORDER*\n\n"
        f"🆔 Order: `#{order_id}`\n"
        f"🆔 UID: `{order['player_id']}`\n"
        f"📦 Package: {order['package_name']}\n"
        f"💰 Amount: *৳{order['amount']}*\n"
        f"💳 Payment: `{payment_method}`\n"
        f"🧾 TxnID: `{order['txn_id']}`\n\n"
        "⚠️ Payment manually verify করুন।"
    )

    future = asyncio.run_coroutine_threadsafe(
        bot_app.bot.send_message(
            chat_id=bot_manual.ADMIN_USER_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        ),
        bot_loop,
    )
    future.result(timeout=15)


@app.get("/")
def home():
    return send_from_directory(WEBSITE_DIR, "index.html")


@app.get("/admin")
@app.get("/admin.html")
def admin_page():
    return send_from_directory(WEBSITE_DIR, "admin.html")


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "TopUpZone BD",
        "telegram_bot_running": bool(bot_manual.BOT_LOOP and bot_manual.BOT_LOOP.is_running()),
    })


@app.post("/api/orders")
def web_order():
    data = request.get_json(silent=True) or {}
    try:
        oid, name, amount = create_web_order(
            uid=data.get("uid") or data.get("player_id"),
            package_key=str(data.get("package_key") or ""),
            txn_id=data.get("txn_id") or data.get("transaction_id"),
            payment_method=data.get("payment_method") or "",
        )
    except (ValueError, TypeError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception:
        bot_manual.log.exception("Failed to create website order")
        return jsonify({"ok": False, "error": "Could not create order"}), 500

    try:
        notify_admin(oid)
    except Exception:
        bot_manual.log.exception("Failed to notify Telegram admin for order #%s", oid)

    return jsonify({
        "ok": True,
        "order_id": oid,
        "package": name,
        "amount": amount,
        "status": "payment_pending",
        "message": "Order submitted. Payment verification pending.",
    }), 201


@app.post("/admin/login")
def admin_login():
    if not ADMIN_PANEL_PASSWORD:
        return jsonify({"ok": False, "error": "Admin password is not configured"}), 503

    data = request.get_json(silent=True) or {}
    if data.get("password") != ADMIN_PANEL_PASSWORD:
        return jsonify({"ok": False, "error": "Invalid password"}), 401

    session["admin_ok"] = True
    return jsonify({"ok": True})


@app.post("/admin/logout")
def admin_logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/admin/orders")
@admin_required
def admin_orders():
    with bot_manual.db() as con:
        rows = con.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify({"ok": True, "orders": [dict(row) for row in rows]})


def notify_customer(order, status):
    user_id = int(order["user_id"] or 0)
    if user_id <= 0:
        return

    bot_app = bot_manual.BOT_APP
    bot_loop = bot_manual.BOT_LOOP
    if not bot_app or not bot_loop or not bot_loop.is_running():
        return

    messages = {
        "payment_verified": (
            "✅ *Payment Verified*\n\n"
            f"Order #{order['id']}\n"
            f"📦 {order['package_name']}\n"
            f"🆔 UID: `{order['player_id']}`\n\n"
            "🎮 এখন আপনার Top-up processing হচ্ছে।"
        ),
        "completed": (
            "🎉 *Top-up Completed!*\n\n"
            f"Order #{order['id']}\n"
            f"📦 {order['package_name']}\n"
            f"🆔 UID: `{order['player_id']}`\n"
            f"💰 ৳{order['amount']}\n\n"
            "ধন্যবাদ! ❤️"
        ),
        "rejected": (
            "❌ *Order Rejected*\n\n"
            f"Order #{order['id']}\n"
            f"📦 {order['package_name']}\n\n"
            f"প্রয়োজনে Support: {bot_manual.SUPPORT_ID}"
        ),
    }

    text = messages[status]
    future = asyncio.run_coroutine_threadsafe(
        bot_app.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown",
        ),
        bot_loop,
    )
    future.result(timeout=15)


@app.post("/api/admin/orders/<int:oid>/status")
@admin_required
def admin_status(oid):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"payment_verified", "completed", "rejected"}:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    order = bot_manual.get_order(oid)
    if not order:
        return jsonify({"ok": False, "error": "Order not found"}), 404

    current = order["status"]
    if status == "payment_verified" and current != "payment_pending":
        return jsonify({"ok": False, "error": "Payment is already processed"}), 409
    if status == "completed" and current != "payment_verified":
        return jsonify({"ok": False, "error": "Verify payment first"}), 409
    if status == "rejected" and current in {"completed", "rejected"}:
        return jsonify({"ok": False, "error": "Order is already closed"}), 409

    bot_manual.set_status(oid, status)

    try:
        notify_customer(order, status)
    except Exception:
        bot_manual.log.exception("Customer notification failed for order #%s", oid)

    return jsonify({"ok": True, "status": status})


def start_bot_thread():
    def runner():
        try:
            bot_manual.run_bot_forever()
        except Exception:
            bot_manual.log.exception("Telegram bot thread stopped")

    thread = threading.Thread(target=runner, name="telegram-bot", daemon=True)
    thread.start()


# Render runs one Gunicorn worker. Starting the Telegram polling bot here keeps
# the website/API and manual Telegram admin workflow in the same service.
start_bot_thread()
