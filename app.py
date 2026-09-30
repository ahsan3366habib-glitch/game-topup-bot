import os
import sqlite3
import secrets
import hashlib
from datetime import datetime
from functools import wraps

import requests
from flask import (
    Flask,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    render_template_string,
    send_from_directory,
)


# =========================================================
# APP
# =========================================================

APP = Flask(__name__)
app = APP

APP.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    secrets.token_hex(32)
)


# =========================================================
# DATABASE
# =========================================================

# Vercel-এর জন্য /tmp ব্যবহার করা হচ্ছে।
# Vercel environment-এ project folder-এ SQLite write করা যাবে না।
if os.environ.get("VERCEL"):
    DB_FILE = "/tmp/chatni_topup.db"
else:
    DB_FILE = os.environ.get(
        "DB_FILE",
        "chatni_topup.db"
    )


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

ADMIN_USER_ID = int(
    os.environ.get(
        "ADMIN_USER_ID",
        "6907180282"
    )
)

ADMIN_PANEL_PASSWORD = os.environ.get(
    "ADMIN_PANEL_PASSWORD",
    ""
)


# =========================================================
# PAYMENT / SUPPORT
# =========================================================

BKASH_NUMBER = os.environ.get(
    "BKASH_NUMBER",
    "01316897399"
)

NAGAD_NUMBER = os.environ.get(
    "NAGAD_NUMBER",
    "01410897399"
)

UPAY_NUMBER = os.environ.get(
    "UPAY_NUMBER",
    "01316897399"
)

SUPPORT_ID = "@Ahsanvai10"

WHATSAPP_1 = "01410897399"
WHATSAPP_2 = "01316897399"


# =========================================================
# PACKAGES
# =========================================================

PACKAGES = {

    # Diamonds
    "d25": ("💎 25 Diamonds", 23),
    "d50": ("💎 50 Diamonds", 40),
    "d115": ("💎 115 Diamonds", 82),
    "d240": ("💎 240 Diamonds", 158),
    "d610": ("💎 610 Diamonds", 392),
    "d1240": ("💎 1240 Diamonds", 780),
    "d2530": ("💎 2530 Diamonds", 1560),

    # Membership
    "weekly": ("🎁 Weekly Membership", 159),
    "wlite": ("🎁 Weekly Lite", 45),
    "monthly": ("🎁 Monthly Membership", 775),

    # Level Up
    "lu6": ("🎫 Level Up-6", 50),
    "lu10": ("🎫 Level Up-10", 80),
    "lu15": ("🎫 Level Up-15", 80),
    "lu20": ("🎫 Level Up-20", 80),
    "lu25": ("🎫 Level Up-25", 80),
    "lu30": ("🎫 Level Up-30", 130),
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def db():
    con = sqlite3.connect(
        DB_FILE,
        timeout=30
    )

    con.row_factory = sqlite3.Row

    return con


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    with db() as con:

        # USERS
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ORDERS
        con.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                username TEXT,

                player_id TEXT NOT NULL,

                package_key TEXT NOT NULL,
                package_name TEXT NOT NULL,

                amount INTEGER NOT NULL,

                payment_method TEXT NOT NULL,
                txn_id TEXT NOT NULL,

                status TEXT NOT NULL
                    DEFAULT 'payment_pending',

                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        con.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_orders_status
            ON orders(status)
        """)

        con.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_orders_created
            ON orders(created_at)
        """)

        con.commit()


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

def send_telegram(chat_id, text):

    if not BOT_TOKEN:
        return False, "BOT_TOKEN is not configured"

    try:

        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },

            timeout=15
        )

        if response.ok:
            return True, None

        return False, response.text[:500]

    except requests.RequestException as exc:

        return False, str(exc)


# =========================================================
# PACKAGE HELPER
# =========================================================

def package_from_name(name):

    name = str(name).strip()

    for key, (
        package_name,
        amount
    ) in PACKAGES.items():

        if name == package_name:
            return key, package_name, amount

        if name == f"{package_name} — ৳{amount}":
            return key, package_name, amount

        if name == f"{package_name} - ৳{amount}":
            return key, package_name, amount

    return None


# =========================================================
# CURRENT USER
# =========================================================

def get_current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    with db() as con:

        return con.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            WHERE id=?
            """,
            (user_id,)
        ).fetchone()


# =========================================================
# ADMIN AUTH
# =========================================================

def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get(
            "admin_authenticated"
        ):

            return redirect(
                url_for("admin_login")
            )

        return view(*args, **kwargs)

    return wrapped


# =========================================================
# WEBSITE FILES
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

WEBSITE_DIR = os.path.join(
    BASE_DIR,
    "website"
)


@APP.get("/")
def home():

    index_file = os.path.join(
        WEBSITE_DIR,
        "index.html"
    )

    if os.path.exists(index_file):

        return send_from_directory(
            WEBSITE_DIR,
            "index.html"
        )

    return redirect("/admin")


@APP.get("/website/<path:filename>")
def website_files(filename):

    return send_from_directory(
        WEBSITE_DIR,
        filename
    )


# =========================================================
# HEALTH
# =========================================================

@APP.get("/health")
def health():

    return jsonify({
        "ok": True,
        "service": "CHATNI TOP UP",
        "mode": "manual"
    })


# =========================================================
# PACKAGES API
# =========================================================

@APP.get("/api/packages")
def api_packages():

    return jsonify([
        {
            "key": key,
            "name": name,
            "price": price
        }

        for key, (
            name,
            price
        ) in PACKAGES.items()
    ])


# =========================================================
# ME
# =========================================================

@APP.get("/api/me")
def api_me():

    user = get_current_user()

    if not user:

        return jsonify({
            "authenticated": False,
            "user": None
        })

    return jsonify({
        "authenticated": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })


# =========================================================
# REGISTER
# =========================================================

@APP.post("/api/register")
def api_register():

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

    if len(name) < 2:

        return jsonify({
            "error": "Name is required"
        }), 400

    if "@" not in email:

        return jsonify({
            "error": "Valid email is required"
        }), 400

    if len(password) < 6:

        return jsonify({
            "error":
            "Password must be at least 6 characters"
        }), 400

    with db() as con:

        existing = con.execute(
            """
            SELECT id
            FROM users
            WHERE email=?
            """,
            (email,)
        ).fetchone()

        if existing:

            return jsonify({
                "error":
                "Email already registered"
            }), 409

        cur = con.execute(
            """
            INSERT INTO users
            (name,email,password_hash,created_at)
            VALUES(?,?,?,?)
            """,
            (
                name,
                email,
                hash_password(password),
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )

        user_id = cur.lastrowid

        con.commit()

    session.clear()

    session["user_id"] = user_id

    return jsonify({
        "ok": True,
        "message": "Registration successful",
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }), 201


# =========================================================
# LOGIN
# =========================================================

@APP.post("/api/login")
def api_login():

    data = request.get_json(
        silent=True
    ) or {}

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    with db() as con:

        user = con.execute(
            """
            SELECT *
            FROM users
            WHERE email=?
            """,
            (email,)
        ).fetchone()

    if not user:

        return jsonify({
            "error":
            "Invalid email or password"
        }), 401

    if not secrets.compare_digest(
        user["password_hash"],
        hash_password(password)
    ):

        return jsonify({
            "error":
            "Invalid email or password"
        }), 401

    session.clear()

    session["user_id"] = user["id"]

    return jsonify({
        "ok": True,
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })


# =========================================================
# LOGOUT
# =========================================================

@APP.post("/api/logout")
def api_logout():

    session.clear()

    return jsonify({
        "ok": True
    })


# =========================================================
# CREATE ORDER
# =========================================================

@APP.post("/api/orders")
def create_web_order():

    user = get_current_user()

    if not user:

        return jsonify({
            "error":
            "Please login first"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    # Accept multiple frontend field names
    uid = str(
        data.get("player_id")
        or data.get("uid")
        or ""
    ).strip()

    package_name_input = str(
        data.get("package_name")
        or data.get("package")
        or ""
    ).strip()

    payment_method = str(
        data.get("payment_method")
        or ""
    ).strip()

    txn_id = str(
        data.get("transaction_id")
        or data.get("trx_id")
        or ""
    ).strip()

    # UID validation
    if (
        not uid
        or not uid.isdigit()
        or not (5 <= len(uid) <= 20)
    ):

        return jsonify({
            "error":
            "Invalid Free Fire UID"
        }), 400

    # Package validation
    package = package_from_name(
        package_name_input
    )

    if not package:

        # Also allow package key
        if package_name_input in PACKAGES:

            package_key = package_name_input

            package_name, amount = PACKAGES[
                package_key
            ]

            package = (
                package_key,
                package_name,
                amount
            )

        else:

            return jsonify({
                "error":
                "Invalid package"
            }), 400

    # Payment validation
    if payment_method not in {
        "bKash",
        "Nagad",
        "Upay"
    }:

        return jsonify({
            "error":
            "Invalid payment method"
        }), 400

    # Transaction ID validation
    if len(txn_id) < 4 or len(txn_id) > 100:

        return jsonify({
            "error":
            "Invalid transaction ID"
        }), 400

    package_key, package_name, amount = package

    username = user["name"]

    with db() as con:

        cur = con.execute(
            """
            INSERT INTO orders
            (
                user_id,
                username,
                player_id,
                package_key,
                package_name,
                amount,
                payment_method,
                txn_id,
                status,
                created_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                user["id"],
                username,
                uid,
                package_key,
                package_name,
                amount,
                payment_method,
                txn_id,
                "payment_pending",
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )

        order_id = cur.lastrowid

        con.commit()

    # Telegram admin notification
    admin_text = (
        "🔔 *NEW WEBSITE ORDER*\n\n"
        f"🆔 Order: `#{order_id}`\n"
        "🎮 Game: Free Fire\n"
        f"👤 Customer: {username}\n"
        f"📧 Email: {user['email']}\n"
        f"🆔 UID: `{uid}`\n"
        f"📦 Package: {package_name}\n"
        f"💰 Amount: *৳{amount}*\n"
        f"💳 Payment: {payment_method}\n"
        f"🧾 Txn ID: `{txn_id}`\n\n"
        "⚠️ Payment verify করুন।\n"
        "তারপর manual top-up করে "
        "TOP-UP DONE করুন।"
    )

    sent, telegram_error = send_telegram(
        ADMIN_USER_ID,
        admin_text
    )

    return jsonify({
        "ok": True,
        "order_id": order_id,
        "status": "payment_pending",
        "telegram_notified": sent,
        "telegram_error":
            telegram_error if not sent else None
    }), 201


# =========================================================
# MY ORDERS
# =========================================================

@APP.get("/api/my-orders")
def my_orders():

    user = get_current_user()

    if not user:

        return jsonify({
            "error":
            "Please login first"
        }), 401

    with db() as con:

        orders = con.execute(
            """
            SELECT
                id,
                player_id,
                package_key,
                package_name,
                amount,
                payment_method,
                txn_id,
                status,
                created_at,
                completed_at
            FROM orders
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 100
            """,
            (user["id"],)
        ).fetchall()

    return jsonify([
        dict(order)
        for order in orders
    ])


# =========================================================
# ADMIN LOGIN PAGE
# =========================================================

LOGIN_HTML = """
<!doctype html>

<html lang="bn">

<head>

<meta charset="utf-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1"
>

<title>CHATNI TOP UP — Admin Login</title>

<style>

body{
    margin:0;
    background:#070a12;
    color:#fff;
    font-family:Arial,sans-serif;
    min-height:100vh;
    display:grid;
    place-items:center;
}

.card{
    width:min(390px,90%);
    background:#101522;
    border:1px solid #273149;
    border-radius:20px;
    padding:24px;
    box-shadow:0 20px 60px #0008;
}

h1{
    font-size:22px;
    margin:0 0 8px;
}

p{
    color:#9ca7bd;
    font-size:13px;
}

input{
    width:100%;
    padding:13px;
    box-sizing:border-box;
    border-radius:11px;
    border:1px solid #303b55;
    background:#090e18;
    color:#fff;
    margin:12px 0;
}

button{
    width:100%;
    padding:13px;
    border:0;
    border-radius:11px;
    background:#00e5ff;
    color:#001018;
    font-weight:900;
    cursor:pointer;
}

.error{
    color:#f87171;
    font-size:13px;
}

</style>

</head>

<body>

<div class="card">

<h1>🔐 CHATNI TOP UP</h1>

<p>Admin Panel Login</p>

{% if error %}
<div class="error">
{{ error }}
</div>
{% endif %}

<form method="post">

<input
type="password"
name="password"
placeholder="Admin password"
required
autofocus
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
# ADMIN HTML
# =========================================================

ADMIN_HTML = """

<!doctype html>

<html lang="bn">

<head>

<meta charset="utf-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1"
>

<title>CHATNI TOP UP — Admin</title>

<style>

*{
    box-sizing:border-box
}

body{
    margin:0;
    background:#070a12;
    color:#f5f7ff;
    font-family:Arial,
    "Noto Sans Bengali",
    sans-serif
}

.wrap{
    width:min(1180px,94%);
    margin:auto
}

.top{
    padding:20px 0;
    display:flex;
    justify-content:space-between;
    gap:12px;
    align-items:center
}

.top h1{
    font-size:22px;
    margin:0
}

.logout{
    color:#fff;
    text-decoration:none;
    background:#182136;
    padding:9px 13px;
    border-radius:10px;
    font-size:12px
}

.stats{
    display:grid;
    grid-template-columns:
    repeat(4,1fr);
    gap:12px;
    margin-bottom:18px
}

.stat,
.order{
    background:#101522;
    border:1px solid #273149;
    border-radius:16px
}

.stat{
    padding:16px
}

.stat small{
    color:#9ca7bd
}

.stat strong{
    display:block;
    font-size:25px;
    margin-top:5px
}

.filters{
    display:flex;
    gap:8px;
    flex-wrap:wrap;
    margin-bottom:16px
}

.filters a{
    padding:9px 12px;
    background:#101522;
    border:1px solid #273149;
    color:#cbd5e1;
    text-decoration:none;
    border-radius:10px;
    font-size:12px
}

.filters a.active{
    background:#00e5ff;
    color:#001018;
    border-color:#00e5ff
}

.orders{
    display:grid;
    gap:12px
}

.order{
    padding:17px
}

.head{
    display:flex;
    justify-content:space-between;
    gap:10px;
    flex-wrap:wrap
}

.id{
    font-weight:900;
    color:#00e5ff
}

.status{
    font-size:11px;
    padding:5px 8px;
    border-radius:20px;
    background:#1d2639
}

.pending{
    color:#fde68a
}

.verified{
    color:#86efac
}

.completed{
    color:#4ade80
}

.rejected{
    color:#fca5a5
}

.grid{
    display:grid;
    grid-template-columns:
    repeat(2,1fr);
    gap:7px;
    margin:14px 0;
    color:#cbd5e1;
    font-size:13px
}

.grid b{
    color:#fff
}

.actions{
    display:flex;
    gap:8px;
    flex-wrap:wrap
}

.actions button{
    border:0;
    padding:10px 12px;
    border-radius:10px;
    color:#fff;
    font-weight:800;
    cursor:pointer
}

.verify{
    background:#15803d
}

.done{
    background:#0369a1
}

.reject{
    background:#991b1b
}

.empty{
    padding:30px;
    text-align:center;
    color:#9ca7bd;
    background:#101522;
    border:1px solid #273149;
    border-radius:16px
}

@media(max-width:700px){

    .stats{
        grid-template-columns:
        repeat(2,1fr)
    }

    .grid{
        grid-template-columns:1fr
    }

    .top{
        align-items:flex-start
    }

}

</style>

</head>

<body>

<div class="wrap">

<div class="top">

<div>

<h1>
🎮 CHATNI TOP UP — Admin Panel
</h1>

<div
style="
color:#9ca7bd;
font-size:12px;
margin-top:5px
"
>
Manual payment verification
& top-up management
</div>

</div>

<a
class="logout"
href="{{ url_for('admin_logout') }}"
>
Logout
</a>

</div>


<div class="stats">

<div class="stat">

<small>
All Orders
</small>

<strong>
{{ counts.all }}
</strong>

</div>


<div class="stat">

<small>
Payment Pending
</small>

<strong>
{{ counts.pending }}
</strong>

</div>


<div class="stat">

<small>
Top-up Pending
</small>

<strong>
{{ counts.verified }}
</strong>

</div>


<div class="stat">

<small>
Completed
</small>

<strong>
{{ counts.completed }}
</strong>

</div>

</div>


<div class="filters">

{% for key,label in [

('all','All'),

('payment_pending','Payment Pending'),

('payment_verified','Payment Verified'),

('completed','Completed'),

('rejected','Rejected')

] %}

<a
class="{% if status==key %}active{% endif %}"
href="{{ url_for(
'admin_panel',
status=key
) }}"
>
{{ label }}
</a>

{% endfor %}

</div>


<div class="orders">

{% if orders %}

{% for o in orders %}

<div class="order">


<div class="head">

<div>

<span class="id">
#{{ o.id }}
</span>

—

{{ o.package_name }}

</div>


<span
class="
status
{% if o.status=='payment_pending' %}
pending
{% elif o.status=='payment_verified' %}
verified
{% elif o.status=='completed' %}
completed
{% else %}
rejected
{% endif %}
"
>

{{ status_map.get(
o.status,
o.status
) }}

</span>

</div>


<div class="grid">

<div>
🎮 Game:
<b>Free Fire</b>
</div>

<div>
🆔 UID:
<b>{{ o.player_id }}</b>
</div>

<div>
💰 Amount:
<b>৳{{ o.amount }}</b>
</div>

<div>
💳 Payment:
<b>{{ o.payment_method }}</b>
</div>

<div>
🧾 Txn ID:
<b>{{ o.txn_id }}</b>
</div>

<div>
👤 User:
<b>{{ o.username or '-' }}</b>
</div>

<div>
📧 User ID:
<b>{{ o.user_id }}</b>
</div>

<div>
🕒 {{ o.created_at }}
</div>

</div>


<div class="actions">

{% if o.status=='payment_pending' %}

<form
method="post"
action="{{ url_for(
'admin_action',
order_id=o.id,
action='verify'
) }}"
>

<button class="verify">
✅ PAYMENT VERIFIED
</button>

</form>

{% endif %}


{% if o.status in
['payment_pending',
'payment_verified']
%}

<form
method="post"
action="{{ url_for(
'admin_action',
order_id=o.id,
action='done'
) }}"
>

<button class="done">
🎮 TOP-UP DONE
</button>

</form>


<form
method="post"
action="{{ url_for(
'admin_action',
order_id=o.id,
action='reject'
) }}"
>

<button class="reject">
❌ REJECT
</button>

</form>

{% endif %}

</div>

</div>

{% endfor %}

{% else %}

<div class="empty">

এই filter-এ কোনো order নেই।

</div>

{% endif %}

</div>

</div>

</body>

</html>

"""


# =========================================================
# ADMIN LOGIN
# =========================================================

@APP.get("/admin/login")
def admin_login():

    if session.get(
        "admin_authenticated"
    ):

        return redirect(
            url_for("admin_panel")
        )

    return render_template_string(
        LOGIN_HTML,
        error=None
    )


@APP.post("/admin/login")
def admin_login_post():

    password = request.form.get(
        "password",
        ""
    )

    if not ADMIN_PANEL_PASSWORD:

        return render_template_string(
            LOGIN_HTML,
            error=(
                "ADMIN_PANEL_PASSWORD "
                "Environment Variable-এ "
                "set করা নেই।"
            )
        ), 500

    if secrets.compare_digest(
        password,
        ADMIN_PANEL_PASSWORD
    ):

        session.clear()

        session[
            "admin_authenticated"
        ] = True

        return redirect(
            url_for("admin_panel")
        )

    return render_template_string(
        LOGIN_HTML,
        error="❌ ভুল password।"
    ), 401


# =========================================================
# ADMIN LOGOUT
# =========================================================

@APP.get("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# GET ORDERS
# =========================================================

def get_orders(
    status=None,
    limit=200
):

    with db() as con:

        if (
            status
            and status != "all"
        ):

            return con.execute(
                """
                SELECT *
                FROM orders
                WHERE status=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    status,
                    limit
                )
            ).fetchall()

        return con.execute(
            """
            SELECT *
            FROM orders
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()


# =========================================================
# SET STATUS
# =========================================================

def set_status(
    order_id,
    status
):

    with db() as con:

        if status == "completed":

            con.execute(
                """
                UPDATE orders
                SET status=?,
                    completed_at=?
                WHERE id=?
                """,
                (
                    status,
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                    order_id
                )
            )

        else:

            con.execute(
                """
                UPDATE orders
                SET status=?
                WHERE id=?
                """,
                (
                    status,
                    order_id
                )
            )

        con.commit()


# =========================================================
# ADMIN PANEL
# =========================================================

@APP.get("/admin")
@admin_required
def admin_panel():

    status = request.args.get(
        "status",
        "all"
    )

    allowed = {
        "all",
        "payment_pending",
        "payment_verified",
        "completed",
        "rejected"
    }

    if status not in allowed:

        status = "all"

    orders = get_orders(
        status=status,
        limit=200
    )

    with db() as con:

        counts = {

            "all":
                con.execute(
                    "SELECT COUNT(*) FROM orders"
                ).fetchone()[0],

            "pending":
                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM orders
                    WHERE status='payment_pending'
                    """
                ).fetchone()[0],

            "verified":
                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM orders
                    WHERE status='payment_verified'
                    """
                ).fetchone()[0],

            "completed":
                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM orders
                    WHERE status='completed'
                    """
                ).fetchone()[0]
        }

    status_map = {

        "payment_pending":
            "⏳ Payment Pending",

        "payment_verified":
            "✅ Payment Verified — Top-up Pending",

        "completed":
            "🎉 Completed",

        "rejected":
            "❌ Rejected"
    }

    return render_template_string(

        ADMIN_HTML,

        orders=orders,

        counts=counts,

        status=status,

        status_map=status_map
    )


# =========================================================
# ADMIN ACTION
# =========================================================

@APP.post(
    "/admin/orders/<int:order_id>/<action>"
)
@admin_required
def admin_action(
    order_id,
    action
):

    with db() as con:

        order = con.execute(
            """
            SELECT *
            FROM orders
            WHERE id=?
            """,
            (order_id,)
        ).fetchone()

    if not order:

        return "Order not found", 404


    # -----------------------------------------------------
    # PAYMENT VERIFIED
    # -----------------------------------------------------

    if action == "verify":

        if order["status"] != "payment_pending":

            return redirect(
                url_for("admin_panel")
            )

        set_status(
            order_id,
            "payment_verified"
        )

        send_telegram(
            ADMIN_USER_ID,

            "✅ *PAYMENT VERIFIED*\n\n"

            f"Order: `#{order_id}`\n"
            f"Package: {order['package_name']}\n"
            f"UID: `{order['player_id']}`\n"
            f"Amount: ৳{order['amount']}\n\n"

            "এখন manual top-up করুন।"
        )


    # -----------------------------------------------------
    # TOP-UP DONE
    # -----------------------------------------------------

    elif action == "done":

        if order["status"] not in {
            "payment_pending",
            "payment_verified"
        }:

            return redirect(
                url_for("admin_panel")
            )

        set_status(
            order_id,
            "completed"
        )

        send_telegram(
            ADMIN_USER_ID,

            "🎉 *TOP-UP COMPLETED*\n\n"

            f"Order: `#{order_id}`\n"
            f"Package: {order['package_name']}\n"
            f"UID: `{order['player_id']}`\n"
            f"Amount: ৳{order['amount']}\n"
        )


    # -----------------------------------------------------
    # REJECT
    # -----------------------------------------------------

    elif action == "reject":

        if order["status"] not in {
            "payment_pending",
            "payment_verified"
        }:

            return redirect(
                url_for("admin_panel")
            )

        set_status(
            order_id,
            "rejected"
        )

        send_telegram(
            ADMIN_USER_ID,

            "❌ *ORDER REJECTED*\n\n"

            f"Order: `#{order_id}`\n"
            f"Package: {order['package_name']}\n"
            f"UID: `{order['player_id']}`\n\n"

            f"Support: {SUPPORT_ID}"
        )


    else:

        return "Invalid action", 400


    return redirect(
        url_for("admin_panel")
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@APP.errorhandler(404)
def not_found(_):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({
            "error": "Not found"
        }), 404

    return "Not found", 404


@APP.errorhandler(500)
def server_error(_):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({
            "error":
            "Internal server error"
        }), 500

    return "Internal server error", 500


# =========================================================
# INIT DATABASE
# =========================================================

init_db()


# =========================================================
# LOCAL RUN
# =========================================================

if __name__ == "__main__":

    APP.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                "5000"
            )
        )
        )
