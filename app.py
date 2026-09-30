import os
import sqlite3
import hashlib
import secrets
import requests

from flask import (
    Flask,
    request,
    jsonify,
    session,
    send_from_directory,
    redirect
)

# =========================================================
# CHATNI TOP UP
# COMPLETE FLASK BACKEND
# =========================================================

APP = Flask(__name__)

APP.secret_key = os.getenv(
    "SECRET_KEY",
    "chatni-top-up-change-this-secret-key"
)

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

DB_FILE = os.getenv(
    "DB_FILE",
    "chatni_topup.db"
)

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
)

ADMIN_USER_ID = os.getenv(
    "ADMIN_USER_ID",
    "6907180282"
)

ADMIN_PANEL_PASSWORD = os.getenv(
    "ADMIN_PANEL_PASSWORD",
    ""
)

TELEGRAM_BOT_USERNAME = "@TopUpZoneBD_bot"


# ---------------------------------------------------------
# PAYMENT NUMBERS
# ---------------------------------------------------------

PAYMENT_NUMBERS = {
    "bKash": "01316897399",
    "Nagad": "01410897399",
    "Upay": "01316897399"
}


# ---------------------------------------------------------
# PACKAGES
# ---------------------------------------------------------

PACKAGES = [

    # Diamonds

    {
        "type": "diamonds",
        "name": "25 Diamonds",
        "amount": "25 💎",
        "price": 23
    },

    {
        "type": "diamonds",
        "name": "50 Diamonds",
        "amount": "50 💎",
        "price": 40
    },

    {
        "type": "diamonds",
        "name": "115 Diamonds",
        "amount": "115 💎",
        "price": 82
    },

    {
        "type": "diamonds",
        "name": "240 Diamonds",
        "amount": "240 💎",
        "price": 158
    },

    {
        "type": "diamonds",
        "name": "610 Diamonds",
        "amount": "610 💎",
        "price": 392
    },

    {
        "type": "diamonds",
        "name": "1240 Diamonds",
        "amount": "1240 💎",
        "price": 780
    },

    {
        "type": "diamonds",
        "name": "2530 Diamonds",
        "amount": "2530 💎",
        "price": 1560
    },

    # Membership

    {
        "type": "membership",
        "name": "Weekly",
        "amount": "Weekly Membership",
        "price": 159
    },

    {
        "type": "membership",
        "name": "Weekly Lite",
        "amount": "Weekly Lite",
        "price": 45
    },

    {
        "type": "membership",
        "name": "Monthly",
        "amount": "Monthly Membership",
        "price": 775
    },

    # Level Up

    {
        "type": "levelup",
        "name": "Level Up-6",
        "amount": "Level Up-6",
        "price": 50
    },

    {
        "type": "levelup",
        "name": "Level Up-10",
        "amount": "Level Up-10",
        "price": 80
    },

    {
        "type": "levelup",
        "name": "Level Up-15",
        "amount": "Level Up-15",
        "price": 80
    },

    {
        "type": "levelup",
        "name": "Level Up-20",
        "amount": "Level Up-20",
        "price": 80
    },

    {
        "type": "levelup",
        "name": "Level Up-25",
        "amount": "Level Up-25",
        "price": 80
    },

    {
        "type": "levelup",
        "name": "Level Up-30",
        "amount": "Level Up-30",
        "price": 130
    }
]


# =========================================================
# DATABASE
# =========================================================

def get_db():

    db = sqlite3.connect(
        DB_FILE,
        timeout=30
    )

    db.row_factory = sqlite3.Row

    return db


def init_db():

    db = get_db()

    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            game TEXT DEFAULT 'Free Fire',

            uid TEXT NOT NULL,

            package TEXT NOT NULL,

            price INTEGER NOT NULL,

            payment_method TEXT NOT NULL,

            trx_id TEXT NOT NULL,

            status TEXT DEFAULT 'PENDING',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            verified_at TIMESTAMP,

            completed_at TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)

        )
    """)

    db.commit()

    db.close()


init_db()


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# TELEGRAM
# =========================================================

def telegram(message):

    if not BOT_TOKEN:
        print("BOT_TOKEN is not configured.")
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": ADMIN_USER_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        return response.ok

    except Exception as e:

        print("Telegram error:", e)

        return False


# =========================================================
# WEBSITE FILES
# =========================================================

@APP.route("/")
def home():

    return send_from_directory(
        "website",
        "index.html"
    )


@APP.route("/website/<path:filename>")
def website_files(filename):

    return send_from_directory(
        "website",
        filename
    )


# =========================================================
# HEALTH
# =========================================================

@APP.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "service": "CHATNI TOP UP"
    })


# =========================================================
# CURRENT USER
# =========================================================

@APP.route("/api/me", methods=["GET"])
def api_me():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "user": None
        })

    db = get_db()

    user = db.execute(
        """
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    db.close()

    if not user:

        session.clear()

        return jsonify({
            "user": None
        })

    return jsonify({
        "user": dict(user)
    })


# =========================================================
# REGISTER
# =========================================================

@APP.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not name:

        return jsonify({
            "message": "Name is required."
        }), 400

    if not email:

        return jsonify({
            "message": "Email is required."
        }), 400

    if len(password) < 6:

        return jsonify({
            "message":
                "Password must be at least 6 characters."
        }), 400

    db = get_db()

    existing = db.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    if existing:

        db.close()

        return jsonify({
            "message":
                "This email is already registered."
        }), 409

    cur = db.execute(
        """
        INSERT INTO users
        (
            name,
            email,
            password
        )
        VALUES (?, ?, ?)
        """,
        (
            name,
            email,
            hash_password(password)
        )
    )

    user_id = cur.lastrowid

    db.commit()

    user = db.execute(
        """
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    db.close()

    session["user_id"] = user_id

    return jsonify({
        "message":
            "Account created successfully.",
        "user": dict(user)
    })


# =========================================================
# LOGIN
# =========================================================

@APP.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(
        silent=True
    ) or {}

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not email or not password:

        return jsonify({
            "message":
                "Email and password are required."
        }), 400

    db = get_db()

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    db.close()

    if not user:

        return jsonify({
            "message":
                "Invalid email or password."
        }), 401

    if user["password"] != hash_password(password):

        return jsonify({
            "message":
                "Invalid email or password."
        }), 401

    session["user_id"] = user["id"]

    return jsonify({
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
    })


# =========================================================
# LOGOUT
# =========================================================

@APP.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "message": "Logged out successfully."
    })


# =========================================================
# PACKAGES API
# =========================================================

@APP.route("/api/packages", methods=["GET"])
def packages_api():

    return jsonify({
        "packages": PACKAGES
    })


# =========================================================
# CREATE ORDER
# =========================================================

@APP.route("/api/orders", methods=["POST"])
def create_order():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "message":
                "Please login before placing an order."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    game = str(
        data.get("game", "Free Fire")
    ).strip()

    uid = str(
        data.get("uid", "")
    ).strip()

    package_name = str(
        data.get("package", "")
    ).strip()

    payment_method = str(
        data.get("payment_method", "")
    ).strip()

    trx_id = str(
        data.get("trx_id", "")
    ).strip()

    if not uid:

        return jsonify({
            "message":
                "Free Fire UID is required."
        }), 400

    if not package_name:

        return jsonify({
            "message":
                "Please select a package."
        }), 400

    if payment_method not in PAYMENT_NUMBERS:

        return jsonify({
            "message":
                "Invalid payment method."
        }), 400

    if not trx_id:

        return jsonify({
            "message":
                "Transaction ID is required."
        }), 400

    # Find official package price
    selected = None

    for item in PACKAGES:

        if item["name"] == package_name:

            selected = item
            break

    if not selected:

        return jsonify({
            "message":
                "Invalid package selected."
        }), 400

    price = selected["price"]

    db = get_db()

    cur = db.execute(
        """
        INSERT INTO orders
        (
            user_id,
            game,
            uid,
            package,
            price,
            payment_method,
            trx_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            game,
            uid,
            package_name,
            price,
            payment_method,
            trx_id,
            "PENDING"
        )
    )

    order_id = cur.lastrowid

    db.commit()

    user = db.execute(
        """
        SELECT name, email
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    db.close()

    # -----------------------------------------------------
    # TELEGRAM ADMIN NOTIFICATION
    # -----------------------------------------------------

    customer_name = (
        user["name"]
        if user
        else "Unknown"
    )

    message = f"""
<b>🔥 NEW CHATNI TOP UP ORDER</b>

🆔 Order ID: #{order_id}

👤 Customer:
{customer_name}

🎮 Game:
{game}

🆔 UID:
<code>{uid}</code>

📦 Package:
{package_name}

💰 Price:
৳{price}

💳 Payment:
{payment_method}

🧾 Transaction ID:
<code>{trx_id}</code>

⏳ Status:
PENDING

Please verify the payment manually.
"""

    telegram(message)

    return jsonify({
        "message":
            "Order submitted successfully.",
        "order_id": order_id,
        "status": "PENDING"
    }), 201


# =========================================================
# CUSTOMER ORDERS
# =========================================================

@APP.route("/api/my-orders", methods=["GET"])
def my_orders():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "orders": []
        })

    db = get_db()

    rows = db.execute(
        """
        SELECT
            id,
            game,
            uid,
            package,
            price,
            payment_method,
            trx_id,
            status,
            created_at,
            verified_at,
            completed_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    db.close()

    return jsonify({
        "orders": [
            dict(row)
            for row in rows
        ]
    })


# =========================================================
# ADMIN AUTH
# =========================================================

def admin_authenticated():

    return session.get(
        "admin_authenticated",
        False
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@APP.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        data = request.get_json(
            silent=True
        ) or {}

        password = str(
            data.get("password", "")
        )

        if not ADMIN_PANEL_PASSWORD:

            return jsonify({
                "message":
                    "ADMIN_PANEL_PASSWORD is not configured."
            }), 500

        if secrets.compare_digest(
            password,
            ADMIN_PANEL_PASSWORD
        ):

            session[
                "admin_authenticated"
            ] = True

            return jsonify({
                "message":
                    "Admin login successful."
            })

        return jsonify({
            "message":
                "Invalid admin password."
        }), 401

    if admin_authenticated():

        return redirect("/admin")

    return """
    <!doctype html>
    <html>
    <head>
        <meta name="viewport"
              content="width=device-width,initial-scale=1">
        <title>CHATNI TOP UP Admin</title>

        <style>

            body{
                margin:0;
                min-height:100vh;
                display:grid;
                place-items:center;
                background:#070812;
                color:#fff;
                font-family:Arial,sans-serif;
            }

            .box{
                width:min(90%,380px);
                padding:25px;
                border-radius:20px;
                background:#10121f;
                border:1px solid #292c40;
            }

            input{
                width:100%;
                height:45px;
                margin:10px 0;
                padding:0 12px;
                box-sizing:border-box;
                border-radius:10px;
                border:1px solid #303348;
                background:#080a12;
                color:#fff;
            }

            button{
                width:100%;
                height:45px;
                border:0;
                border-radius:10px;
                color:#fff;
                font-weight:bold;
                background:linear-gradient(
                    135deg,
                    #8b5cf6,
                    #3b82f6
                );
            }

        </style>
    </head>

    <body>

        <div class="box">

            <h2>CHATNI TOP UP</h2>

            <p>Admin Panel Login</p>

            <form method="POST">

                <input
                    type="password"
                    name="password"
                    placeholder="Admin password"
                    required
                >

                <button>
                    LOGIN
                </button>

            </form>

        </div>

    </body>
    </html>
    """


# =========================================================
# ADMIN PANEL
# =========================================================

@APP.route("/admin")
def admin_panel():

    if not admin_authenticated():

        return redirect("/admin/login")

    db = get_db()

    rows = db.execute(
        """
        SELECT
            orders.*,
            users.name AS customer_name,
            users.email AS customer_email
        FROM orders
        LEFT JOIN users
            ON users.id = orders.user_id
        ORDER BY orders.id DESC
        """
    ).fetchall()

    db.close()

    html = """
    <!doctype html>

    <html>

    <head>

        <meta name="viewport"
              content="width=device-width,initial-scale=1">

        <title>CHATNI TOP UP Admin</title>

        <style>

            *{
                box-sizing:border-box;
            }

            body{
                margin:0;
                background:#070812;
                color:#fff;
                font-family:Arial,sans-serif;
                padding:20px;
            }

            h1{
                margin-bottom:5px;
            }

            .sub{
                color:#888da5;
                margin-bottom:20px;
            }

            .table-wrap{
                overflow:auto;
                background:#10121f;
                border:1px solid #25283a;
                border-radius:16px;
            }

            table{
                width:100%;
                border-collapse:collapse;
                min-width:1050px;
            }

            th,
            td{
                padding:13px;
                border-bottom:1px solid #222536;
                text-align:left;
                font-size:12px;
            }

            th{
                color:#9da2bb;
                font-size:10px;
                text-transform:uppercase;
            }

            .pending{
                color:#facc15;
            }

            .verified{
                color:#22d3ee;
            }

            .done{
                color:#22c55e;
            }

            .rejected{
                color:#ef4444;
            }

            .btn{
                display:inline-block;
                padding:7px 9px;
                margin:2px;
                border-radius:8px;
                color:#fff;
                text-decoration:none;
                font-size:10px;
                font-weight:bold;
            }

            .verify{
                background:#2563eb;
            }

            .done-btn{
                background:#16a34a;
            }

            .reject{
                background:#dc2626;
            }

        </style>

    </head>

    <body>

        <h1>🎮 CHATNI TOP UP</h1>

        <div class="sub">
            Manual Order Management
        </div>

        <div class="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th>ID</th>
                        <th>Customer</th>
                        <th>UID</th>
                        <th>Package</th>
                        <th>Price</th>
                        <th>Payment</th>
                        <th>TRX</th>
                        <th>Status</th>
                        <th>Action</th>

                    </tr>

                </thead>

                <tbody>

                    {% for order in orders %}

                    <tr>

                        <td>
                            #{{ order["id"] }}
                        </td>

                        <td>
                            {{ order["customer_name"] or "Unknown" }}
                            <br>
                            <small>
                                {{ order["customer_email"] or "" }}
                            </small>
                        </td>

                        <td>
                            {{ order["uid"] }}
                        </td>

                        <td>
                            {{ order["package"] }}
                        </td>

                        <td>
                            ৳{{ order["price"] }}
                        </td>

                        <td>
                            {{ order["payment_method"] }}
                        </td>

                        <td>
                            {{ order["trx_id"] }}
                        </td>

                        <td class="{{ order["status"]|lower }}">
                            {{ order["status"] }}
                        </td>

                        <td>

                            <a
                                class="btn verify"
                                href="/admin/orders/{{ order["id"] }}/verify"
                            >
                                VERIFY
                            </a>

                            <a
                                class="btn done-btn"
                                href="/admin/orders/{{ order["id"] }}/done"
                            >
                                TOP-UP DONE
                            </a>

                            <a
                                class="btn reject"
                                href="/admin/orders/{{ order["id"] }}/reject"
                            >
                                REJECT
                            </a>

                        </td>

                    </tr>

                    {% endfor %}

                </tbody>

            </table>

        </div>

    </body>

    </html>
    """

    from flask import render_template_string

    return render_template_string(
        html,
        orders=rows
    )


# =========================================================
# ADMIN ORDER ACTION
# =========================================================

@APP.route(
    "/admin/orders/<int:order_id>/<action>",
    methods=["GET"]
)
def admin_order_action(
    order_id,
    action
):

    if not admin_authenticated():

        return redirect("/admin/login")

    allowed = [
        "verify",
        "done",
        "reject"
    ]

    if action not in allowed:

        return "Invalid action", 400

    if action == "verify":

        status = "VERIFIED"

    elif action == "done":

        status = "TOP-UP DONE"

    else:

        status = "REJECTED"

    db = get_db()

    order = db.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    ).fetchone()

    if not order:

        db.close()

        return "Order not found", 404

    if action == "verify":

        db.execute(
            """
            UPDATE orders
            SET
                status = ?,
                verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                order_id
            )
        )

    elif action == "done":

        db.execute(
            """
            UPDATE orders
            SET
                status = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                order_id
            )
        )

    else:

        db.execute(
            """
            UPDATE orders
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                order_id
            )
        )

    db.commit()

    db.close()

    # -----------------------------------------------------
    # TELEGRAM STATUS NOTIFICATION
    # -----------------------------------------------------

    telegram(
        f"""
<b>📢 ORDER STATUS UPDATED</b>

🆔 Order:
#{order_id}

🆔 UID:
<code>{order["uid"]}</code>

📦 Package:
{order["package"]}

💰 Price:
৳{order["price"]}

📌 Status:
<b>{status}</b>
"""
    )

    return redirect("/admin")


# =========================================================
# ADMIN LOGOUT
# =========================================================

@APP.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_authenticated",
        None
    )

    return redirect("/admin/login")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    APP.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        )
    )
