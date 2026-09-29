import os, sqlite3, secrets, hashlib
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request, session, redirect, url_for, render_template_string, send_from_directory
import requests

APP = Flask(__name__, static_folder=None)
APP.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

DB_FILE = os.environ.get('DB_FILE', 'topup_bot.db')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID', '6907180282'))
ADMIN_PANEL_PASSWORD = os.environ.get('ADMIN_PANEL_PASSWORD', '')
SUPPORT_ID = '@Ahsanvai10'

PACKAGES = {
    'lu6': ('🎫 Level Up-6', 50),
    'lu10': ('🎫 Level Up-10', 80),
    'lu15': ('🎫 Level Up-15', 80),
    'lu20': ('🎫 Level Up-20', 80),
    'lu25': ('🎫 Level Up-25', 80),
    'lu30': ('🎫 Level Up-30', 130),
    'wlite': ('🎁 Weekly Lite', 50),
    'weekly': ('🎁 Weekly Membership', 170),
    'monthly': ('🎁 Monthly Membership', 800),
    'd25': ('💎 25 Diamonds', 25),
    'd50': ('💎 50 Diamonds', 40),
    'd115': ('💎 115 Diamonds', 85),
    'd240': ('💎 240 Diamonds', 165),
    'd610': ('💎 610 Diamonds', 410),
    'd1240': ('💎 1240 Diamonds', 800),
    'd2530': ('💎 2530 Diamonds', 1600)
}


def db():
    c = sqlite3.connect(DB_FILE, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    with db() as c:
        c.execute('''
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                player_id TEXT NOT NULL,
                package_key TEXT NOT NULL,
                package_name TEXT NOT NULL,
                amount INTEGER NOT NULL,
                txn_id TEXT NOT NULL,
                payment_method TEXT,
                status TEXT NOT NULL DEFAULT "payment_pending",
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        ''')

        try:
            c.execute('ALTER TABLE orders ADD COLUMN payment_method TEXT')
        except sqlite3.OperationalError:
            pass

        c.commit()


def send_telegram(chat_id, text):
    if not BOT_TOKEN:
        return False

    try:
        r = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': text
            },
            timeout=15
        )
        return r.ok
    except requests.RequestException:
        return False


def package_from_name(name):
    for key, (pkg_name, price) in PACKAGES.items():
        if name == pkg_name or name == f'{pkg_name} — ৳{price}':
            return key, pkg_name, price

    return None


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin_login'))

        return f(*args, **kwargs)

    return wrapper


# =========================
# WEBSITE
# =========================

@APP.get('/')
def home():
    return send_from_directory(
        os.path.join(APP.root_path, 'website'),
        'index.html'
    )


# =========================
# STATIC FILE FIX
# =========================

@APP.get('/static/<path:filename>')
def static_files(filename):

    base = os.path.join(APP.root_path, 'website')
    path = os.path.join(base, filename)

    if os.path.isfile(path):
        return send_from_directory(base, filename)

    # Banner fallback
    if filename.startswith('banners/'):
        name = filename.split('/', 1)[1]

        if os.path.isfile(os.path.join(base, name)):
            return send_from_directory(base, name)

    return ('Not found', 404)


# =========================
# HEALTH
# =========================

@APP.get('/health')
def health():
    return jsonify(
        ok=True,
        service='TopUpZone BD',
        mode='manual'
    )


# =========================
# PACKAGES API
# =========================

@APP.get('/api/packages')
def api_packages():

    return jsonify([
        {
            'key': key,
            'name': name,
            'price': price
        }
        for key, (name, price) in PACKAGES.items()
    ])


# =========================
# SIGN UP
# =========================

@APP.post('/api/register')
def register():

    data = request.get_json(silent=True) or {}

    name = str(data.get('name', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    if len(name) < 2 or '@' not in email or len(password) < 6:
        return jsonify(
            error='Name, valid email and 6+ character password required'
        ), 400

    try:
        with db() as c:
            c.execute(
                '''
                INSERT INTO users
                (name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                ''',
                (
                    name,
                    email,
                    hash_pw(password),
                    datetime.now().isoformat(timespec='seconds')
                )
            )

    except sqlite3.IntegrityError:
        return jsonify(
            error='This email is already registered'
        ), 409

    return jsonify(ok=True), 201


# =========================
# LOGIN
# =========================

@APP.post('/api/login')
def login():

    data = request.get_json(silent=True) or {}

    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    with db() as c:
        user = c.execute(
            'SELECT * FROM users WHERE email=?',
            (email,)
        ).fetchone()

    if not user or not secrets.compare_digest(
        user['password_hash'],
        hash_pw(password)
    ):
        return jsonify(
            error='Invalid email or password'
        ), 401

    session['user_id'] = user['id']
    session['user_name'] = user['name']

    return jsonify(
        ok=True,
        name=user['name']
    )


# =========================
# LOGOUT
# =========================

@APP.post('/api/logout')
def logout():

    session.pop('user_id', None)
    session.pop('user_name', None)

    return jsonify(ok=True)


# =========================
# MY ORDERS
# =========================

@APP.get('/api/my-orders')
def my_orders():

    user_id = session.get('user_id')

    if not user_id:
        return jsonify(
            authenticated=False,
            orders=[]
        )

    with db() as c:
        rows = c.execute(
            '''
            SELECT *
            FROM orders
            WHERE user_id=?
            ORDER BY id DESC
            ''',
            (user_id,)
        ).fetchall()

    labels = {
        'payment_pending': 'Payment Pending',
        'payment_verified': 'Payment Verified — Top-up Pending',
        'completed': 'Completed',
        'rejected': 'Rejected'
    }

    orders = []

    for row in rows:
        item = dict(row)
        item['status_label'] = labels.get(
            row['status'],
            row['status']
        )
        orders.append(item)

    return jsonify(
        authenticated=True,
        orders=orders
    )


# =========================
# CREATE ORDER
# =========================

@APP.post('/api/orders')
def create_order():

    data = request.get_json(silent=True) or {}

    player_id = str(
        data.get('player_id', '')
    ).strip()

    payment_method = str(
        data.get('payment_method', '')
    ).strip()

    transaction_id = str(
        data.get('transaction_id', '')
    ).strip()

    package_name = str(
        data.get('package_name', '')
    ).strip()

    if not player_id.isdigit() or not 5 <= len(player_id) <= 20:
        return jsonify(
            error='Invalid Free Fire UID'
        ), 400

    if payment_method not in {
        'bKash',
        'Nagad',
        'Upay'
    }:
        return jsonify(
            error='Invalid payment method'
        ), 400

    if not 4 <= len(transaction_id) <= 100:
        return jsonify(
            error='Invalid transaction ID'
        ), 400

    package = package_from_name(package_name)

    if not package:
        return jsonify(
            error='Invalid package'
        ), 400

    package_key, name, amount = package

    user_id = session.get('user_id', 0)
    username = session.get(
        'user_name',
        'website'
    )

    with db() as c:

        cur = c.execute(
            '''
            INSERT INTO orders
            (
                user_id,
                username,
                player_id,
                package_key,
                package_name,
                amount,
                txn_id,
                payment_method,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                username,
                player_id,
                package_key,
                name,
                amount,
                transaction_id,
                payment_method,
                'payment_pending',
                datetime.now().isoformat(timespec='seconds')
            )
        )

        order_id = cur.lastrowid

    telegram_sent = send_telegram(
        ADMIN_USER_ID,
        f'''🔔 NEW WEBSITE ORDER

Order: #{order_id}
Game: Free Fire
UID: {player_id}
Package: {name}
Amount: ৳{amount}
Payment: {payment_method}
Txn ID: {transaction_id}

Admin Panel থেকে verify করুন।'''
    )

    return jsonify(
        ok=True,
        order_id=order_id,
        status='payment_pending',
        telegram_notified=telegram_sent
    ), 201


# =========================
# ADMIN LOGIN PAGE
# =========================

LOGIN_HTML = '''
<!doctype html>

<html lang="bn">

<head>

<meta charset="utf-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1"
>

<title>TopUpZone BD Admin Login</title>

<style>

body{
margin:0;
background:#050914;
color:white;
font-family:Arial;
display:grid;
place-items:center;
min-height:100vh
}

.c{
width:min(390px,90%);
padding:25px;
background:#0b1628;
border:1px solid #164a7a;
border-radius:18px
}

.c input,
.c button{
width:100%;
padding:13px;
margin-top:10px;
box-sizing:border-box;
border-radius:10px
}

.c input{
background:#050914;
color:white;
border:1px solid #254a72
}

.c button{
border:0;
background:#00d9ff;
font-weight:900
}

.err{
color:#fca5a5;
margin:8px 0
}

</style>

</head>

<body>

<div class="c">

<h2>👑 TopUpZone BD</h2>

<p>Admin Panel Login</p>

{% if error %}

<div class="err">
{{ error }}
</div>

{% endif %}

<form method="post">

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
'''


@APP.get('/admin/login')
def admin_login():

    if session.get('admin_authenticated'):
        return redirect('/admin')

    return render_template_string(
        LOGIN_HTML,
        error=None
    )


@APP.post('/admin/login')
def admin_login_post():

    password = request.form.get(
        'password',
        ''
    )

    if not ADMIN_PANEL_PASSWORD:

        return render_template_string(
            LOGIN_HTML,
            error='ADMIN_PANEL_PASSWORD Render Environment-এ সেট করুন।'
        ), 500

    if secrets.compare_digest(
        password,
        ADMIN_PANEL_PASSWORD
    ):

        session.clear()
        session['admin_authenticated'] = True

        return redirect('/admin')

    return render_template_string(
        LOGIN_HTML,
        error='❌ ভুল password।'
    ), 401


@APP.get('/admin/logout')
def admin_logout():

    session.clear()

    return redirect('/admin/login')


# =========================
# ADMIN PANEL
# =========================

@APP.get('/admin')
@admin_required
def admin_panel():

    status = request.args.get(
        'status',
        'all'
    )

    allowed = {
        'all',
        'payment_pending',
        'payment_verified',
        'completed',
        'rejected'
    }

    if status not in allowed:
        status = 'all'

    with db() as c:

        if status == 'all':

            rows = c.execute(
                '''
                SELECT *
                FROM orders
                ORDER BY id DESC
                LIMIT 200
                '''
            ).fetchall()

        else:

            rows = c.execute(
                '''
                SELECT *
                FROM orders
                WHERE status=?
                ORDER BY id DESC
                LIMIT 200
                ''',
                (status,)
            ).fetchall()

        counts = {
            'all': c.execute(
                'SELECT COUNT(*) FROM orders'
            ).fetchone()[0],

            'pending': c.execute(
                "SELECT COUNT(*) FROM orders WHERE status='payment_pending'"
            ).fetchone()[0],

            'verified': c.execute(
                "SELECT COUNT(*) FROM orders WHERE status='payment_verified'"
            ).fetchone()[0],

            'completed': c.execute(
                "SELECT COUNT(*) FROM orders WHERE status='completed'"
            ).fetchone()[0]
        }

    labels = {
        'payment_pending':
            '⏳ Payment Pending',

        'payment_verified':
            '✅ Payment Verified — Top-up Pending',

        'completed':
            '🎉 Completed',

        'rejected':
            '❌ Rejected'
    }

    return render_template_string(
        ADMIN_HTML,
        orders=rows,
        counts=counts,
        status=status,
        status_map=labels
    )


# =========================
# ADMIN HTML
# =========================

ADMIN_HTML = '''
<!doctype html>

<html lang="bn">

<head>

<meta charset="utf-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1"
>

<title>TopUpZone BD Admin</title>

<style>

*{
box-sizing:border-box
}

body{
margin:0;
background:#050914;
color:#f5f7ff;
font-family:Arial,"Noto Sans Bengali",sans-serif
}

.wrap{
width:min(1180px,94%);
margin:auto
}

.top{
padding:20px 0;
display:flex;
justify-content:space-between;
gap:12px
}

.top a,
.filter a{
background:#10223b;
color:#dff6ff;
padding:9px 12px;
border-radius:9px;
text-decoration:none;
font-size:12px
}

.stats{
display:grid;
grid-template-columns:repeat(4,1fr);
gap:10px
}

.stat,
.order{
background:#0b1628;
border:1px solid #164a7a;
border-radius:15px
}

.stat{
padding:15px
}

.stat small{
color:#8fa6c4
}

.stat strong{
display:block;
font-size:24px;
margin-top:5px
}

.filter{
display:flex;
gap:7px;
flex-wrap:wrap;
margin:16px 0
}

.filter .active{
background:#00d9ff;
color:#001018
}

.orders{
display:grid;
gap:12px
}

.order{
padding:16px
}

.head{
display:flex;
justify-content:space-between;
gap:8px
}

.id{
color:#00eaff;
font-weight:900
}

.grid{
display:grid;
grid-template-columns:repeat(2,1fr);
gap:8px;
margin:14px 0;
color:#b6c9df;
font-size:13px
}

.grid b{
color:white
}

.actions{
display:flex;
gap:8px;
flex-wrap:wrap
}

.actions form{
margin:0
}

.actions button{
border:0;
padding:10px 12px;
border-radius:9px;
color:white;
font-weight:900
}

.v{
background:#15803d
}

.d{
background:#0369a1
}

.r{
background:#991b1b
}

.status{
font-size:11px
}

.empty{
padding:25px;
text-align:center;
background:#0b1628;
border-radius:15px;
color:#8fa6c4
}

@media(max-width:700px){

.stats{
grid-template-columns:repeat(2,1fr)
}

.grid{
grid-template-columns:1fr
}

.head{
align-items:flex-start;
flex-direction:column
}

}

</style>

</head>

<body>

<div class="wrap">

<div class="top">

<div>

<h2>
👑 TopUpZone BD — Admin Panel
</h2>

<small>
Manual payment verification & top-up
</small>

</div>

<div>

<a href="/">
Website
</a>

<a href="/admin/logout">
Logout
</a>

</div>

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


<div class="filter">

{% for k,l in [
("all","All"),
("payment_pending","Payment Pending"),
("payment_verified","Payment Verified"),
("completed","Completed"),
("rejected","Rejected")
] %}

<a
class="{% if status==k %}active{% endif %}"
href="/admin?status={{k}}"
>
{{l}}
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
#{{o.id}}
</span>

{{o.package_name}}

</div>

<span class="status">
{{status_map.get(o.status,o.status)}}
</span>

</div>


<div class="grid">

<div>
🎮 Game:
<b>Free Fire</b>
</div>

<div>
🆔 UID:
<b>{{o.player_id}}</b>
</div>

<div>
💰 Amount:
<b>৳{{o.amount}}</b>
</div>

<div>
💳 Payment:
<b>{{o.payment_method or "-"}}</b>
</div>

<div>
🧾 Txn ID:
<b>{{o.txn_id}}</b>
</div>

<div>
👤 User:
<b>{{o.username or "website"}}</b>
</div>

<div>
🕒
<b>{{o.created_at}}</b>
</div>

</div>


<div class="actions">

{% if o.status=="payment_pending" %}

<form
method="post"
action="/admin/orders/{{o.id}}/verify"
>

<button class="v">
✅ PAYMENT VERIFIED
</button>

</form>

{% endif %}


{% if o.status in ["payment_pending","payment_verified"] %}

<form
method="post"
action="/admin/orders/{{o.id}}/done"
>

<button class="d">
🎮 TOP-UP DONE
</button>

</form>


<form
method="post"
action="/admin/orders/{{o.id}}/reject"
>

<button class="r">
❌ REJECT
</button>

</form>

{% endif %}

</div>

</div>

{% endfor %}

{% else %}

<div class="empty">
কোনো order নেই।
</div>

{% endif %}

</div>

</div>

</body>

</html>
'''


# =========================
# ADMIN ORDER ACTION
# =========================

@APP.post('/admin/orders/<int:oid>/<action>')
@admin_required
def admin_action(oid, action):

    with db() as c:

        order = c.execute(
            'SELECT * FROM orders WHERE id=?',
            (oid,)
        ).fetchone()

    if not order:
        return 'Order not found', 404

    if action == 'verify':
        new_status = 'payment_verified'

    elif action == 'done':
        new_status = 'completed'

    elif action == 'reject':
        new_status = 'rejected'

    else:
        return 'Invalid action', 400

    with db() as c:

        if new_status == 'completed':

            c.execute(
                '''
                UPDATE orders
                SET status=?, completed_at=?
                WHERE id=?
                ''',
                (
                    new_status,
                    datetime.now().isoformat(timespec='seconds'),
                    oid
                )
            )

        else:

            c.execute(
                '''
                UPDATE orders
                SET status=?
                WHERE id=?
                ''',
                (
                    new_status,
                    oid
                )
            )

    # Telegram notification only when an actual Telegram user ID exists
    if order['user_id']:

        messages = {

            'payment_verified':
                f'⚠️ Payment verified for Order #{oid}. Manual top-up processing চলছে।',

            'completed':
                f'🎉 Order #{oid} top-up completed. Thank you! ❤️',

            'rejected':
                f'❌ Order #{oid} rejected. Support: {SUPPORT_ID}'
        }

        send_telegram(
            order['user_id'],
            messages[new_status]
        )

    return redirect('/admin')


# =========================
# 404
# =========================

@APP.errorhandler(404)
def not_found(error):

    if request.path.startswith('/api/'):
        return jsonify(
            error='Not found'
        ), 404

    return 'Not found', 404


# =========================
# START
# =========================

init_db()


if __name__ == '__main__':

    APP.run(
        host='0.0.0.0',
        port=int(
            os.environ.get(
                'PORT',
                '5000'
            )
        )
    )
