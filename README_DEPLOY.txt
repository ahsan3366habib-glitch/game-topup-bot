TOPUPZONE BD — FINAL PUBLISH BUILD

1) GitHub repo root:
   app.py
   requirements.txt
   website/index.html
   website/style.css
   website/logo.png
   website/banners/banner1.jpg
   website/banners/banner2.jpg
   website/banners/banner3.jpg

2) Render Build Command:
   pip install -r requirements.txt

3) Render Start Command:
   gunicorn app:APP --workers 1 --threads 4 --timeout 120

4) Required Environment Variables:
   BOT_TOKEN = your Telegram bot token (keep secret)
   ADMIN_USER_ID = 6907180282
   ADMIN_PANEL_PASSWORD = your chosen admin password
   FLASK_SECRET_KEY = a long random secret

5) Payment numbers already fixed in website:
   bKash 01316897399
   Nagad 01410897399
   Upay 01316897399
   Text: Payment করতে Send Money করুন

6) Admin login:
   https://YOUR-DOMAIN/admin/login
   Password is the value of ADMIN_PANEL_PASSWORD in Render.

7) Telegram polling conflict:
   This web app DOES NOT start bot polling. Keep only one separate bot worker/process running bot_manual.py. If two bot polling processes use the same token, Telegram will show Conflict: terminated by other getUpdates request.

8) SQLite note: Render free filesystem is not permanent. For production order history, move DB_FILE to Postgres later.
