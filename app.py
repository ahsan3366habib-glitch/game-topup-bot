# CHATNI TOP UP
# Single-file Flask website
# Render Start Command:
# gunicorn app:APP --workers 1 --threads 4 --timeout 120

import os
import sqlite3
import hashlib
import secrets
import requests
from flask import Flask, request, jsonify, session, redirect, render_template_string

APP = Flask(__name__)
APP.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

DB_FILE = os.getenv("DB_FILE", "chatni_topup.db")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "6907180282")
ADMIN_PANEL_PASSWORD = os.getenv("ADMIN_PANEL_PASSWORD", "change-this-password")

BKASH = "01316897399"
NAGAD = "01410897399"
UPAY = "01316897399"
SUPPORT = "@Ahsanvai10"

PACKAGES = [
    ("25 Diamonds", "💎", 23, "diamond"),
    ("50 Diamonds", "💎", 40, "diamond"),
    ("115 Diamonds", "💎", 82, "diamond"),
    ("240 Diamonds", "💎", 158, "diamond"),
    ("610 Diamonds", "💎", 392, "diamond"),
    ("1240 Diamonds", "💎", 780, "diamond"),
    ("2530 Diamonds", "💎", 1560, "diamond"),

    ("Weekly Membership", "🔥", 159, "membership"),
    ("Weekly Lite", "⚡", 45, "membership"),
    ("Monthly Membership", "👑", 775, "membership"),

    ("Level Up-6", "⚡", 50, "level"),
    ("Level Up-10", "⚡", 80, "level"),
    ("Level Up-15", "⚡", 80, "level"),
    ("Level Up-20", "⚡", 80, "level"),
    ("Level Up-25", "⚡", 80, "level"),
    ("Level Up-30", "⚡", 130, "level"),
]


def db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 0,
            name TEXT,
            email TEXT,
            game TEXT DEFAULT 'Free Fire',
            uid TEXT NOT NULL,
            package TEXT NOT NULL,
            price INTEGER NOT NULL,
            payment_method TEXT,
            transaction_id TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.commit()
    con.close()


init_db()


def telegram(message):
    if not BOT_TOKEN or not ADMIN_USER_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(
            url,
            json={
                "chat_id": ADMIN_USER_ID,
                "text": message,
                "parse_mode": "HTML"
            },
            timeout=10
        )
    except Exception:
        pass


HTML = r"""
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CHATNI TOP UP</title>

<style>
*{
    box-sizing:border-box;
    margin:0;
    padding:0;
}

body{
    font-family:Arial,"Noto Sans Bengali",sans-serif;
    background:
      radial-gradient(circle at 15% 10%,rgba(76,0,255,.22),transparent 30%),
      radial-gradient(circle at 90% 20%,rgba(0,220,255,.15),transparent 28%),
      linear-gradient(135deg,#050713,#090b1d 45%,#07040f);
    color:#fff;
    min-height:100vh;
    padding-bottom:90px;
}

button,input,select{
    font:inherit;
}

button{
    cursor:pointer;
}

.container{
    width:min(1100px,94%);
    margin:auto;
}

header{
    position:sticky;
    top:0;
    z-index:100;
    background:rgba(5,7,19,.78);
    backdrop-filter:blur(18px);
    border-bottom:1px solid rgba(255,255,255,.08);
}

.header-inner{
    min-height:68px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:15px;
}

.logo{
    font-size:20px;
    font-weight:900;
    background:linear-gradient(90deg,#8c5cff,#00eaff,#ff4bd8);
    -webkit-background-clip:text;
    color:transparent;
}

.logo small{
    display:block;
    color:#aeb6d5;
    font-size:10px;
    letter-spacing:1px;
    margin-top:2px;
}

.top-actions{
    display:flex;
    gap:8px;
}

.btn{
    border:0;
    padding:10px 15px;
    border-radius:12px;
    color:#fff;
    background:linear-gradient(135deg,#6b35ff,#b52dff);
    font-weight:800;
    box-shadow:0 8px 25px rgba(108,45,255,.25);
}

.btn.secondary{
    background:rgba(255,255,255,.07);
    border:1px solid rgba(255,255,255,.1);
}

.hero{
    margin-top:18px;
    border-radius:26px;
    overflow:hidden;
    min-height:350px;
    position:relative;
    display:flex;
    align-items:center;
    background:
      linear-gradient(90deg,rgba(5,6,20,.96),rgba(10,8,30,.68),rgba(8,5,25,.35)),
      radial-gradient(circle at 80% 30%,#6925ff55,transparent 40%),
      linear-gradient(135deg,#10152d,#24104b);
    border:1px solid rgba(255,255,255,.1);
    box-shadow:0 20px 70px rgba(0,0,0,.35);
}

.hero:after{
    content:"";
    position:absolute;
    inset:0;
    background:
      linear-gradient(120deg,transparent 35%,rgba(255,255,255,.05),transparent 65%);
    animation:shine 5s infinite;
}

@keyframes shine{
    0%{transform:translateX(-100%)}
    50%,100%{transform:translateX(100%)}
}

.hero-content{
    position:relative;
    z-index:2;
    padding:35px;
    max-width:650px;
}

.badge{
    display:inline-block;
    padding:7px 12px;
    border-radius:30px;
    background:rgba(139,92,246,.16);
    border:1px solid rgba(139,92,246,.35);
    color:#cbbaff;
    font-size:12px;
    margin-bottom:15px;
}

.hero h1{
    font-size:clamp(32px,7vw,64px);
    line-height:1;
    margin-bottom:15px;
}

.gradient{
    background:linear-gradient(90deg,#9d72ff,#00eaff,#ff58d7);
    -webkit-background-clip:text;
    color:transparent;
}

.hero p{
    color:#bdc4dd;
    line-height:1.7;
}

.hero-buttons{
    display:flex;
    flex-wrap:wrap;
    gap:10px;
    margin-top:22px;
}

.section{
    margin-top:28px;
}

.section-title{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:15px;
}

.section-title h2{
    font-size:22px;
}

.section-title span{
    color:#8189aa;
    font-size:12px;
}

.cards{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:12px;
}

.card{
    background:rgba(255,255,255,.055);
    border:1px solid rgba(255,255,255,.09);
    border-radius:18px;
    padding:16px;
    backdrop-filter:blur(14px);
    transition:.25s;
}

.card:hover{
    transform:translateY(-4px);
    border-color:#8b5cff66;
    box-shadow:0 15px 35px rgba(75,25,180,.2);
}

.package-icon{
    font-size:26px;
}

.package-name{
    margin-top:9px;
    font-weight:800;
    font-size:14px;
}

.price{
    margin:9px 0;
    font-size:23px;
    font-weight:900;
    color:#73f3ff;
}

.order-btn{
    width:100%;
    padding:10px;
    border:0;
    border-radius:10px;
    background:linear-gradient(90deg,#6937ff,#d12eff);
    color:#fff;
    font-weight:800;
}

.review-wrap{
    overflow:hidden;
    border-radius:18px;
}

.reviews{
    display:flex;
    gap:12px;
    width:max-content;
    animation:moveReviews 28s linear infinite;
}

@keyframes moveReviews{
    from{transform:translateX(0)}
    to{transform:translateX(-50%)}
}

.review{
    width:260px;
    padding:15px;
    border-radius:17px;
    background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.08);
}

.review-top{
    display:flex;
    justify-content:space-between;
    color:#b7bfdc;
    font-size:12px;
}

.review p{
    margin-top:10px;
    color:#e7e9f5;
    font-size:13px;
    line-height:1.5;
}

.demo{
    color:#9b7bff;
    font-size:9px;
}

.bottom-nav{
    position:fixed;
    z-index:200;
    bottom:10px;
    left:50%;
    transform:translateX(-50%);
    width:min(650px,94%);
    padding:8px;
    border-radius:20px;
    background:rgba(8,9,22,.88);
    backdrop-filter:blur(22px);
    border:1px solid rgba(255,255,255,.1);
    display:grid;
    grid-template-columns:repeat(5,1fr);
    gap:4px;
}

.nav-btn{
    border:0;
    background:transparent;
    color:#9299b9;
    padding:8px 3px;
    border-radius:13px;
    font-size:11px;
}

.nav-btn.active,
.nav-btn:hover{
    background:rgba(116,67,255,.2);
    color:#fff;
}

.modal{
    display:none;
    position:fixed;
    z-index:500;
    inset:0;
    background:rgba(0,0,0,.72);
    backdrop-filter:blur(8px);
    padding:20px;
    overflow:auto;
}

.modal-box{
    width:min(520px,100%);
    margin:50px auto;
    background:#0d1023;
    border:1px solid rgba(255,255,255,.1);
    border-radius:22px;
    padding:22px;
    box-shadow:0 25px 80px #000;
}

.modal-head{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:18px;
}

.close{
    border:0;
    background:transparent;
    color:#fff;
    font-size:25px;
}

.form-group{
    margin-bottom:13px;
}

.form-group label{
    display:block;
    color:#aab1cc;
    font-size:12px;
    margin-bottom:6px;
}

.form-group input,
.form-group select{
    width:100%;
    padding:13px;
    border-radius:12px;
    color:#fff;
    background:#080a18;
    border:1px solid rgba(255,255,255,.1);
    outline:none;
}

.form-group input:focus,
.form-group select:focus{
    border-color:#8c5cff;
}

.full{
    width:100%;
    margin-top:5px;
}

.payment-box{
    background:rgba(0,234,255,.05);
    border:1px solid rgba(0,234,255,.15);
    padding:14px;
    border-radius:14px;
    margin:12px 0;
    line-height:1.8;
    font-size:13px;
}

.notice{
    color:#ffcf6b;
    font-size:12px;
    margin-top:10px;
    line-height:1.5;
}

.order-row{
    padding:14px;
    margin-bottom:10px;
    background:rgba(255,255,255,.05);
    border-radius:15px;
    border:1px solid rgba(255,255,255,.07);
}

.status{
    display:inline-block;
    margin-top:7px;
    padding:5px 9px;
    border-radius:20px;
    font-size:10px;
    background:#373b54;
}

.status.DONE{
    background:#0b714a;
}

.status.VERIFIED{
    background:#1456a0;
}

.status.REJECTED{
    background:#8b2635;
}

.empty{
    color:#8d94b0;
    padding:20px;
    text-align:center;
}

.admin-table{
    width:100%;
    border-collapse:collapse;
    font-size:12px;
}

.admin-table th,
.admin-table td{
    padding:9px;
    border-bottom:1px solid rgba(255,255,255,.08);
    text-align:left;
}

.admin-table button{
    margin:2px;
    padding:6px 9px;
    border-radius:8px;
    border:0;
    font-size:10px;
}

.verify{background:#0877d1;color:#fff}
.done{background:#087a51;color:#fff}
.reject{background:#9c2937;color:#fff}

@media(max-width:800px){
    .cards{
        grid-template-columns:repeat(2,1fr);
    }

    .hero{
        min-height:380px;
    }

    .hero-content{
        padding:25px;
    }
}

@media(max-width:480px){
    .top-actions .btn{
        padding:8px 10px;
        font-size:11px;
    }

    .cards{
        grid-template-columns:repeat(2,1fr);
        gap:9px;
    }

    .card{
        padding:12px;
    }

    .package-name{
        font-size:12px;
    }

    .price{
        font-size:19px;
    }

    .hero h1{
        font-size:37px;
    }
}
</style>
</head>

<body>

<header>
<div class="container header-inner">
    <div class="logo">
        🎮 CHATNI TOP UP
        <small>চাটনি টপআপ • FAST GAME TOP-UP</small>
    </div>

    <div class="top-actions" id="authButtons">
        <button class="btn secondary" onclick="openModal('loginModal')">Login</button>
        <button class="btn" onclick="openModal('signupModal')">Sign Up</button>
    </div>

    <div class="top-actions" id="userButtons" style="display:none">
        <button class="btn secondary" onclick="openOrders()">📦 Orders</button>
        <button class="btn" onclick="logout()">Logout</button>
    </div>
</div>
</header>

<main class="container">

<section class="hero">
    <div class="hero-content">
        <span class="badge">🔥 NEW • CHATNI TOP UP</span>
        <h1>
            Game Top-Up<br>
            <span class="gradient">Made Simple.</span>
        </h1>
        <p>
            Free Fire Diamonds, Membership এবং Level Up Pass।
            সহজে Order করুন এবং payment verification-এর পর top-up নিন।
        </p>

        <div class="hero-buttons">
            <button class="btn" onclick="scrollToPackages()">💎 Top Up Now</button>
            <button class="btn secondary" onclick="openOrders()">📦 My Orders</button>
        </div>
    </div>
</section>


<section class="section">
<div class="section-title">
    <h2>💎 Diamond Top-Up</h2>
    <span>Launch Price</span>
</div>

<div class="cards">
{% for p in packages if p[3] == "diamond" %}
<div class="card">
    <div class="package-icon">{{p[1]}}</div>
    <div class="package-name">{{p[0]}}</div>
    <div class="price">৳{{p[2]}}</div>
    <button class="order-btn"
      onclick="openOrder('{{p[0]}}',{{p[2]}})">
      TOP UP NOW
    </button>
</div>
{% endfor %}
</div>
</section>


<section class="section">
<div class="section-title">
    <h2>🔥 Membership</h2>
    <span>Special Price</span>
</div>

<div class="cards">
{% for p in packages if p[3] == "membership" %}
<div class="card">
    <div class="package-icon">{{p[1]}}</div>
    <div class="package-name">{{p[0]}}</div>
    <div class="price">৳{{p[2]}}</div>
    <button class="order-btn"
      onclick="openOrder('{{p[0]}}',{{p[2]}})">
      ORDER NOW
    </button>
</div>
{% endfor %}
</div>
</section>


<section class="section">
<div class="section-title">
    <h2>⚡ Level Up Pass</h2>
    <span>Popular</span>
</div>

<div class="cards">
{% for p in packages if p[3] == "level" %}
<div class="card">
    <div class="package-icon">{{p[1]}}</div>
    <div class="package-name">{{p[0]}}</div>
    <div class="price">৳{{p[2]}}</div>
    <button class="order-btn"
      onclick="openOrder('{{p[0]}}',{{p[2]}})">
      ORDER NOW
    </button>
</div>
{% endfor %}
</div>
</section>


<section class="section">
<div class="section-title">
    <h2>💬 Customer Feedback</h2>
    <span>Sample / Demo</span>
</div>

<div class="review-wrap">
<div class="reviews">

{% set reviews = [
"Diamond নিয়েছি, ALHAMDULILLAH অনেক ভালো সার্ভিস ❤️",
"Payment দেওয়ার পর খুব সহজেই order complete করেছি!",
"CHATNI TOP UP থেকে প্রথমবার নিলাম, service ভালো লেগেছে।",
"Diamond পেয়েছি, ALHAMDULILLAH ❤️",
"সহজে order করেছি, কোনো ঝামেলা হয়নি।",
"আবার top-up নিতে আসবো ইনশাআল্লাহ 🔥",
"Price সুন্দর আর order process সহজ।",
"Level Up Pass নিয়েছি, সব ঠিকঠাক পেয়েছি।"
] %}

{% for r in reviews %}
<div class="review">
    <div class="review-top">
        <b>⭐ Customer</b>
        <span class="demo">DEMO</span>
    </div>
    <p>{{r}}</p>
</div>
{% endfor %}

{% for r in reviews %}
<div class="review">
    <div class="review-top">
        <b>⭐ Customer</b>
        <span class="demo">DEMO</span>
    </div>
    <p>{{r}}</p>
</div>
{% endfor %}

</div>
</div>
</section>


<section class="section">
<div class="card">
    <h2>💳 Payment</h2>
    <div class="payment-box">
        <b>bKash:</b> {{bkash}}<br>
        <b>Nagad:</b> {{nagad}}<br>
        <b>Upay:</b> {{upay}}<br><br>
        <b>Payment করতে Send Money করুন</b>
    </div>
    <div class="notice">
        ⚠️ Payment করার পরে Transaction ID সঠিকভাবে দিন।
        Admin payment verify করার পর order process হবে।
    </div>
</div>
</section>

</main>


<nav class="bottom-nav">
    <button class="nav-btn active" onclick="window.scrollTo({top:0,behavior:'smooth'})">
        🏠<br>Home
    </button>
    <button class="nav-btn" onclick="scrollToPackages()">
        💎<br>Topup
    </button>
    <button class="nav-btn" onclick="openOrders()">
        📦<br>Trajection
    </button>
    <button class="nav-btn" onclick="openSupport()">
        💬<br>Support
    </button>
    <button class="nav-btn" onclick="openSettings()">
        ⚙️<br>Setting
    </button>
</nav>


<!-- LOGIN -->
<div class="modal" id="loginModal">
<div class="modal-box">
<div class="modal-head">
    <h2>🔐 Login</h2>
    <button class="close" onclick="closeModal('loginModal')">×</button>
</div>

<div class="form-group">
<label>Email</label>
<input id="loginEmail" type="email" placeholder="Enter email">
</div>

<div class="form-group">
<label>Password</label>
<input id="loginPassword" type="password" placeholder="Enter password">
</div>

<button class="btn full" onclick="login()">LOGIN</button>
</div>
</div>


<!-- SIGNUP -->
<div class="modal" id="signupModal">
<div class="modal-box">
<div class="modal-head">
    <h2>📝 Create Account</h2>
    <button class="close" onclick="closeModal('signupModal')">×</button>
</div>

<div class="form-group">
<label>Name</label>
<input id="signupName" placeholder="Your name">
</div>

<div class="form-group">
<label>Email</label>
<input id="signupEmail" type="email" placeholder="Your email">
</div>

<div class="form-group">
<label>Password</label>
<input id="signupPassword" type="password" placeholder="Create password">
</div>

<button class="btn full" onclick="signup()">CREATE ACCOUNT</button>
</div>
</div>


<!-- ORDER -->
<div class="modal" id="orderModal">
<div class="modal-box">
<div class="modal-head">
    <h2>🎮 Place Order</h2>
    <button class="close" onclick="closeModal('orderModal')">×</button>
</div>

<div id="selectedPackage" class="payment-box"></div>

<div class="form-group">
<label>Free Fire UID</label>
<input id="orderUid" placeholder="Enter your Free Fire UID">
</div>

<div class="form-group">
<label>Payment Method</label>
<select id="paymentMethod">
<option>bKash</option>
<option>Nagad</option>
<option>Upay</option>
</select>
</div>

<div class="form-group">
<label>Transaction ID</label>
<input id="transactionId" placeholder="Enter Transaction ID">
</div>

<div class="payment-box">
    <b>bKash:</b> {{bkash}}<br>
    <b>Nagad:</b> {{nagad}}<br>
    <b>Upay:</b> {{upay}}<br><br>
    Payment করতে Send Money করুন
</div>

<button class="btn full" onclick="submitOrder()">SUBMIT ORDER</button>
</div>
</div>


<!-- ORDERS -->
<div class="modal" id="ordersModal">
<div class="modal-box">
<div class="modal-head">
    <h2>📦 My Orders</h2>
    <button class="close" onclick="closeModal('ordersModal')">×</button>
</div>
<div id="ordersList"></div>
</div>
</div>


<!-- SETTINGS -->
<div class="modal" id="settingsModal">
<div class="modal-box">
<div class="modal-head">
    <h2>⚙️ Account</h2>
    <button class="close" onclick="closeModal('settingsModal')">×</button>
</div>
<div id="accountInfo"></div>
<button class="btn full" onclick="logout()">LOGOUT</button>
</div>
</div>


<script>
let selectedPackage = "";
let selectedPrice = 0;


function openModal(id){
    document.getElementById(id).style.display="block";
}

function closeModal(id){
    document.getElementById(id).style.display="none";
}

function scrollToPackages(){
    document.querySelector(".section").scrollIntoView({
        behavior:"smooth"
    });
}

function openSupport(){
    window.open("https://t.me/Ahsanvai10","_blank");
}

function openSettings(){
    fetch("/api/me")
    .then(r=>r.json())
    .then(data=>{
        if(!data.logged_in){
            openModal("loginModal");
            return;
        }

        document.getElementById("accountInfo").innerHTML = `
            <div class="payment-box">
                <b>👤 Name:</b> ${data.user.name}<br>
                <b>📧 Email:</b> ${data.user.email}<br>
                <b>💰 Balance:</b> ৳${data.user.balance}
            </div>
        `;

        openModal("settingsModal");
    });
}


function openOrder(name,price){
    selectedPackage=name;
    selectedPrice=price;

    document.getElementById("selectedPackage").innerHTML =
        `<b>${name}</b><br><span style="font-size:24px">৳${price}</span>`;

    fetch("/api/me")
    .then(r=>r.json())
    .then(data=>{
        if(!data.logged_in){
            closeModal("orderModal");
            openModal("loginModal");
            return;
        }

        openModal("orderModal");
    });
}


function signup(){
    let name=document.getElementById("signupName").value.trim();
    let email=document.getElementById("signupEmail").value.trim();
    let password=document.getElementById("signupPassword").value;

    if(!name || !email || !password){
        alert("সব তথ্য পূরণ করুন");
        return;
    }

    fetch("/api/register",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name,email,password})
    })
    .then(r=>r.json())
    .then(data=>{
        alert(data.message);

        if(data.ok){
            closeModal("signupModal");
            updateAuth();
        }
    });
}


function login(){
    let email=document.getElementById("loginEmail").value.trim();
    let password=document.getElementById("loginPassword").value;

    fetch("/api/login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email,password})
    })
    .then(r=>r.json())
    .then(data=>{
        alert(data.message);

        if(data.ok){
            closeModal("loginModal");
            updateAuth();
        }
    });
}


function logout(){
    fetch("/api/logout")
    .then(()=>{
        closeModal("settingsModal");
        closeModal("ordersModal");
        updateAuth();
        alert("Logout successful");
    });
}


function updateAuth(){
    fetch("/api/me")
    .then(r=>r.json())
    .then(data=>{
        document.getElementById("authButtons").style.display =
            data.logged_in ? "none" : "flex";

        document.getElementById("userButtons").style.display =
            data.logged_in ? "flex" : "none";
    });
}


function submitOrder(){
    let uid=document.getElementById("orderUid").value.trim();
    let payment=document.getElementById("paymentMethod").value;
    let trx=document.getElementById("transactionId").value.trim();

    if(!uid || !trx){
        alert("UID এবং Transaction ID দিন");
        return;
    }

    fetch("/api/orders",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            uid:uid,
            package:selectedPackage,
            price:selectedPrice,
            payment_method:payment,
            transaction_id:trx
        })
    })
    .then(r=>r.json())
    .then(data=>{
        alert(data.message);

        if(data.ok){
            closeModal("orderModal");
            openOrders();
        }
    });
}


function openOrders(){
    fetch("/api/my-orders")
    .then(r=>r.json())
    .then(data=>{
        if(!data.logged_in){
            openModal("loginModal");
            return;
        }

        let box=document.getElementById("ordersList");

        if(!data.orders.length){
            box.innerHTML=`<div class="empty">এখনও কোনো order নেই।</div>`;
        }else{
            box.innerHTML=data.orders.map(o=>`
                <div class="order-row">
                    <b>🎮 ${o.package}</b><br>
                    UID: ${o.uid}<br>
                    Price: ৳${o.price}<br>
                    Txn: ${o.transaction_id}<br>
                    <span class="status ${o.status}">
                        ${o.status}
                    </span>
                </div>
            `).join("");
        }

        openModal("ordersModal");
    });
}


updateAuth();
</script>

</body>
</html>
"""


@APP.route("/")
def home():
    return render_template_string(
        HTML,
        packages=PACKAGES,
        bkash=BKASH,
        nagad=NAGAD,
        upay=UPAY
    )


@APP.route("/api/me")
def me():
    uid = session.get("user_id")

    if not uid:
        return jsonify({"logged_in": False})

    con = db()
    user = con.execute(
        "SELECT id,name,email,balance FROM users WHERE id=?",
        (uid,)
    ).fetchone()
    con.close()

    if not user:
        session.clear()
        return jsonify({"logged_in": False})

    return jsonify({
        "logged_in": True,
        "user": dict(user)
    })


@APP.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not name or not email or not password:
        return jsonify({
            "ok": False,
            "message": "সব তথ্য পূরণ করুন।"
        })

    if len(password) < 6:
        return jsonify({
            "ok": False,
            "message": "Password কমপক্ষে 6 characters হতে হবে।"
        })

    con = db()

    try:
        cur = con.execute(
            """
            INSERT INTO users(name,email,password)
            VALUES(?,?,?)
            """,
            (name,email,hash_password(password))
        )

        con.commit()
        session["user_id"] = cur.lastrowid

        return jsonify({
            "ok": True,
            "message": "Account তৈরি হয়েছে।"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "ok": False,
            "message": "এই email দিয়ে account আগে থেকেই আছে।"
        })

    finally:
        con.close()


@APP.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    con = db()

    user = con.execute(
        """
        SELECT * FROM users
        WHERE email=? AND password=?
        """,
        (email,hash_password(password))
    ).fetchone()

    con.close()

    if not user:
        return jsonify({
            "ok": False,
            "message": "Email অথবা password ভুল।"
        })

    session["user_id"] = user["id"]

    return jsonify({
        "ok": True,
        "message": "Login successful।"
    })


@APP.route("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@APP.route("/api/orders", methods=["POST"])
def create_order():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "ok": False,
            "message": "আগে Login করুন।"
        })

    data = request.get_json() or {}

    uid = str(data.get("uid", "")).strip()
    package = str(data.get("package", "")).strip()
    payment_method = str(data.get("payment_method", "")).strip()
    transaction_id = str(data.get("transaction_id", "")).strip()

    try:
        price = int(data.get("price", 0))
    except:
        price = 0

    valid_package = None

    for p in PACKAGES:
        if p[0] == package and p[2] == price:
            valid_package = p
            break

    if not valid_package:
        return jsonify({
            "ok": False,
            "message": "Invalid package।"
        })

    if not uid or not transaction_id:
        return jsonify({
            "ok": False,
            "message": "UID এবং Transaction ID দিন।"
        })

    con = db()

    user = con.execute(
        "SELECT name,email FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    cur = con.execute(
        """
        INSERT INTO orders(
            user_id,name,email,game,uid,package,price,
            payment_method,transaction_id,status
        )
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id,
            user["name"],
            user["email"],
            "Free Fire",
            uid,
            package,
            price,
            payment_method,
            transaction_id,
            "PENDING"
        )
    )

    order_id = cur.lastrowid
    con.commit()
    con.close()

    telegram(
        f"""
<b>🔥 NEW CHATNI TOP UP ORDER</b>

🆔 Order: #{order_id}
👤 Name: {user["name"]}
📧 Email: {user["email"]}

🎮 Game: Free Fire
🆔 UID: {uid}
📦 Package: {package}
💰 Price: ৳{price}

💳 Payment: {payment_method}
🧾 Transaction ID: {transaction_id}

⏳ Status: PENDING
"""
    )

    return jsonify({
        "ok": True,
        "message": f"Order #{order_id} submitted হয়েছে। Payment verify হওয়ার অপেক্ষায় আছে।"
    })


@APP.route("/api/my-orders")
def my_orders():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "logged_in": False,
            "orders": []
        })

    con = db()

    rows = con.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    con.close()

    return jsonify({
        "logged_in": True,
        "orders": [dict(x) for x in rows]
    })


@APP.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password","")

        if password == ADMIN_PANEL_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

        return "Wrong password", 401

    return """
    <html>
    <body style="background:#080a15;color:white;font-family:Arial;padding:40px">
    <h2>CHATNI TOP UP Admin Login</h2>
    <form method="post">
    <input name="password" type="password"
    placeholder="Admin password"
    style="padding:12px">
    <button style="padding:12px">LOGIN</button>
    </form>
    </body>
    </html>
    """


@APP.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin/login")

    con = db()

    orders = con.execute(
        """
        SELECT *
        FROM orders
        ORDER BY id DESC
        """
    ).fetchall()

    con.close()

    rows = ""

    for o in orders:
        rows += f"""
        <tr>
            <td>#{o["id"]}</td>
            <td>{o["name"]}<br>{o["email"]}</td>
            <td>{o["uid"]}</td>
            <td>{o["package"]}</td>
            <td>৳{o["price"]}</td>
            <td>{o["payment_method"]}<br>{o["transaction_id"]}</td>
            <td>{o["status"]}</td>
            <td>
                <button class="verify"
                onclick="action({o["id"]},'verify')">
                VERIFY
                </button>

                <button class="done"
                onclick="action({o["id"]},'done')">
                TOP-UP DONE
                </button>

                <button class="reject"
                onclick="action({o["id"]},'reject')">
                REJECT
                </button>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CHATNI TOP UP ADMIN</title>
    <style>
    body{{
        background:#070814;
        color:#fff;
        font-family:Arial;
        padding:15px;
    }}
    h1{{
        color:#9b6cff;
    }}
    .wrap{{
        overflow:auto;
        background:#0d1022;
        border-radius:15px;
        padding:10px;
    }}
    table{{
        border-collapse:collapse;
        width:100%;
        min-width:1000px;
        font-size:12px;
    }}
    th,td{{
        border-bottom:1px solid #252943;
        padding:10px;
        text-align:left;
    }}
    th{{
        color:#9ca6ce;
    }}
    button{{
        border:0;
        border-radius:7px;
        padding:7px;
        color:white;
        margin:2px;
        cursor:pointer;
    }}
    .verify{{background:#126cc0}}
    .done{{background:#08784e}}
    .reject{{background:#a32638}}
    </style>
    </head>

    <body>

    <h1>🎮 CHATNI TOP UP ADMIN</h1>

    <p>
    Manual Payment Verification + Manual Top-Up
    </p>

    <br>

    <div class="wrap">
    <table>
    <tr>
        <th>ID</th>
        <th>Customer</th>
        <th>UID</th>
        <th>Package</th>
        <th>Price</th>
        <th>Payment</th>
        <th>Status</th>
        <th>Action</th>
    </tr>

    {rows}

    </table>
    </div>

    <script>
    function action(id,type){{
        fetch("/admin/orders/"+id+"/"+type,{{
            method:"POST"
        }})
        .then(r=>r.json())
        .then(d=>{{
            alert(d.message);
            location.reload();
        }});
    }}
    </script>

    </body>
    </html>
    """


@APP.route("/admin/orders/<int:order_id>/<action>", methods=["POST"])
def admin_action(order_id, action):
    if not session.get("admin"):
        return jsonify({
            "ok": False,
            "message": "Unauthorized"
        }), 401

    if action not in ("verify","done","reject"):
        return jsonify({
            "ok": False,
            "message": "Invalid action"
        }), 400

    status_map = {
        "verify": "VERIFIED",
        "done": "DONE",
        "reject": "REJECTED"
    }

    new_status = status_map[action]

    con = db()

    order = con.execute(
        "SELECT * FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    if not order:
        con.close()

        return jsonify({
            "ok": False,
            "message": "Order পাওয়া যায়নি।"
        }), 404

    con.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (new_status,order_id)
    )

    con.commit()
    con.close()

    telegram(
        f"""
<b>🔔 CHATNI TOP UP ORDER UPDATE</b>

🆔 Order: #{order_id}
👤 {order["name"]}
🎮 UID: {order["uid"]}
📦 {order["package"]}
💰 ৳{order["price"]}

📌 Status: <b>{new_status}</b>
"""
    )

    return jsonify({
        "ok": True,
        "message": f"Order #{order_id} → {new_status}"
    })


@APP.route("/health")
def health():
    return "CHATNI TOP UP OK"


if __name__ == "__main__":
    APP.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False
    )
