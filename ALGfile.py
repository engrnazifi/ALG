# bot.py  (Merged final with language persistence fixes - bug fixed + Fulani added)
import telebot
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import time
# ====== DATABASE CONNECTION ======
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "main.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row

# small globals
admin_states = {}
last_menu_msg = {}
last_category_msg = {}
last_allfilms_msg = {}
allfilms_sessions = {}
cart_sessions = {}
series_sessions = {}
user_states = {}
# =========================
# DATABASE TABLES (SAFE)
# =========================

# -------- MOVIES --------
conn.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    price INTEGER,
    file_id TEXT,
    file_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    channel_msg_id INTEGER,
    channel_username TEXT
)
""")
# -------- ITEMS (MOVIES) --------
conn.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    price INTEGER,
    file_id TEXT,
    file_name TEXT,
    group_key TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    channel_msg_id INTEGER,
    channel_username TEXT
)
""")

# -------- ORDERS --------
conn.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    movie_id INTEGER,                 -- legacy
    item_id INTEGER,                  -- NEW (safe)
    amount INTEGER,
    paid INTEGER DEFAULT 0,
    pay_ref TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- ORDER ITEMS --------
conn.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    movie_id INTEGER,                 -- legacy
    item_id INTEGER,                  -- NEW
    price INTEGER,
    file_id TEXT                      -- NEW (delivery safe)
)
""")

# -------- WEEKLY --------
conn.execute("""
CREATE TABLE IF NOT EXISTS weekly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poster_file_id TEXT,
    items TEXT,
    file_name TEXT,
    file_id TEXT,
    channel_msg_id INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- CART --------
conn.execute("""
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,                 -- legacy
    item_id INTEGER,                  -- NEW
    price INTEGER,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- REFERRALS --------
conn.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reward_granted INTEGER DEFAULT 0
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS reorders (
    old_order_id INTEGER,
    new_order_id INTEGER,
    user_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (old_order_id, user_id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS referral_credits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    amount INTEGER,
    used INTEGER DEFAULT 0,
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- USER PREFS --------
conn.execute("""
CREATE TABLE IF NOT EXISTS user_prefs (
    user_id INTEGER PRIMARY KEY,
    lang TEXT DEFAULT 'ha'
)
""")

# -------- USER LIBRARY --------
conn.execute("""
CREATE TABLE IF NOT EXISTS user_library (
    user_id INTEGER NOT NULL,
    movie_id INTEGER,                 -- legacy
    item_id INTEGER,                  -- NEW
    acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, movie_id, item_id)
)
""")

# -------- BUY ALL TOKENS --------
conn.execute("""
CREATE TABLE IF NOT EXISTS buyall_tokens (
    token TEXT PRIMARY KEY,
    ids TEXT
)
""")

# -------- USER MOVIES (RESEND) --------
conn.execute("""
CREATE TABLE IF NOT EXISTS user_movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,                 -- legacy
    item_id INTEGER,                  -- NEW
    order_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resend_count INTEGER DEFAULT 0
)
""")

# =====================
# SERIES
# =====================

conn.execute("""
CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    file_name TEXT,
    file_id TEXT,
    price INTEGER,
    poster_file_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    channel_msg_id INTEGER,
    channel_username TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS series_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER,
    movie_id INTEGER,                 -- legacy
    item_id INTEGER,                  -- NEW
    file_id TEXT,
    title TEXT,
    order_id TEXT,
    price INTEGER DEFAULT 0,
    channel_msg_id INTEGER,
    channel_username TEXT,
    file_name TEXT
)
""")

# =====================
# FEEDBACK
# =====================

conn.execute("""
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    mood TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS resend_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    used_at TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# =====================
# HAUSA SERIES
# =====================

conn.execute("""
CREATE TABLE IF NOT EXISTS hausa_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    file_name TEXT,
    file_id TEXT,
    price INTEGER,
    series_id TEXT,
    poster_file_id TEXT,
    channel_msg_id INTEGER,
    channel_username TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS hausa_series_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hausa_series_id INTEGER,
    movie_id INTEGER,                 -- legacy
    item_id INTEGER,                  -- NEW
    price INTEGER,
    file_id TEXT,
    title TEXT,
    order_id TEXT,
    series_id INTEGER,
    channel_msg_id INTEGER,
    channel_username TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_name TEXT
)
""")
# ================= VISITED USERS =================
conn.execute("""
CREATE TABLE IF NOT EXISTS visited_users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- ADMIN CONTROLS --------
conn.execute("""
CREATE TABLE IF NOT EXISTS admin_controls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER UNIQUE,
    sendmovie_enabled INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
# ================= HOW TO BUY STORAGE =================
conn.execute("""
CREATE TABLE IF NOT EXISTS how_to_buy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hausa_text TEXT,
    english_text TEXT,
    media_file_id TEXT,
    media_type TEXT,        -- video | document | photo
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


import uuid
import re
import json
import requests
import traceback
import random
import difflib
from datetime import datetime, timedelta
import urllib.parse
import os
import hmac
import hashlib

admin_states = {}

# --- Admins configuration ---
ADMINS = [6603268127]

# ========= CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN")

BOT_MODE = os.getenv("BOT_MODE", "polling")

ADMIN_ID = 6603268127
OTP_ADMIN_ID = 6603268127

BOT_USERNAME = "Algaitabot"
CHANNEL = "@Algaitamoviestore"

# ========= PAYSTACK CONFIG =========
PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET")
PAYSTACK_PUBLIC = os.getenv("PAYSTACK_PUBLIC")
PAYSTACK_REDIRECT_URL = os.getenv("PAYSTACK_REDIRECT_URL")
PAYSTACK_WEBHOOK_SECRET = os.getenv("PAYSTACK_WEBHOOK_SECRET")

PAYSTACK_BASE = "https://api.paystack.co"


# === PAYMENTS / STORAGE ===
PAYMENT_NOTIFY_GROUP = -1003520788779
STORAGE_CHANNEL = -1003520788779
SEND_ADMIN_PAYMENT_NOTIF = False

ADMIN_USERNAME = "Nazifiibr"

# ========= IMPORTS =========
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========= BOT =========
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ========= FLASK =========
app = Flask(__name__)

# ========= PAYSTACK PAYMENT =========
def create_paystack_payment(user_id, order_id, amount, title):
    if not PAYSTACK_SECRET or not PAYSTACK_REDIRECT_URL:
        print("❌ Paystack env missing")
        return None

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }

    payload = {
        "reference": str(order_id),
        "amount": int(amount) * 100,  # Kobo
        "currency": "NGN",
        "callback_url": PAYSTACK_REDIRECT_URL,
        "email": f"user{user_id}@telegram.com",
        "metadata": {
            "order_id": str(order_id),
            "user_id": user_id,
            "title": title[:50]
        }
    }

    try:
        r = requests.post(
            f"{PAYSTACK_BASE}/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=30
        )

        data = r.json()
        if not data.get("status"):
            print("❌ Paystack error:", data)
            return None

        return data["data"]["authorization_url"]

    except Exception as e:
        print("❌ create_paystack_payment error:", e)
        return None





# ========= HOME / KEEP ALIVE =========
@app.route("/")
def home():
    return "OK", 200


# ========= CALLBACK PAGE =========
@app.route("/paystack-callback", methods=["GET"])
def paystack_callback():
    return """
    <html>
    <head>
        <title>Payment Successful</title>
        <meta http-equiv="refresh" content="5;url=https://t.me/Aslamtv2bot">
    </head>
    <body style="font-family: Arial; text-align: center; padding-top: 150px; font-size: 22px;">
        <h2>✅ Payment Successful</h2>
        <p>An tabbatar da biyan ka.</p>
        <p>Kashe browser ka koma telegram</p>
        <a href="https://t.me/Algaitabot">Komawa Telegram yanzu</a>
    </body>
    </html>
    """

# ========= FEEDBACK =========
def send_feedback_prompt(user_id, order_id):
    exists = conn.execute(
        "SELECT 1 FROM feedbacks WHERE order_id=?",
        (order_id,)
    ).fetchone()
    if exists:
        return

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("😁 Very good", callback_data=f"feedback:very:{order_id}"),
        InlineKeyboardButton("🙂 Good", callback_data=f"feedback:good:{order_id}")
    )
    kb.add(
        InlineKeyboardButton("😓 Not sure", callback_data=f"feedback:neutral:{order_id}"),
        InlineKeyboardButton("😠 Angry", callback_data=f"feedback:angry:{order_id}")
    )

    bot.send_message(
        user_id,
        "We hope you enjoyed your shopping 🥰\nPlease choose how you’re feeling right now.",
        reply_markup=kb
    )



# ========= PAYSTACK WEBHOOK =========
@app.route("/webhook", methods=["POST"])
def paystack_webhook():

    print("🔔 PAYSTACK WEBHOOK RECEIVED")

    if not PAYSTACK_WEBHOOK_SECRET:
        print("❌ PAYSTACK_WEBHOOK_SECRET missing")
        return "Server error", 500

    signature = request.headers.get("x-paystack-signature")
    if not signature:
        print("❌ Missing signature")
        return "Missing signature", 401

    computed = hmac.new(
        PAYSTACK_WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha512
    ).hexdigest()

    if signature != computed:
        print("❌ Invalid signature")
        return "Invalid signature", 401

    payload = request.json or {}
    event = payload.get("event")
    data = payload.get("data", {})

    if event != "charge.success":
        return "Ignored", 200

    order_id = data.get("reference")
    paid_amount = int(data.get("amount", 0) / 100)
    currency = data.get("currency")

    row = conn.execute(
        "SELECT user_id, amount, paid FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    if not row:
        return "Order not found", 200

    user_id, expected_amount, paid = row

    if paid == 1:
        return "Already processed", 200

    if paid_amount != expected_amount or currency != "NGN":
        return "Wrong payment", 200

    items_count = conn.execute(
        "SELECT COUNT(*) FROM order_items WHERE order_id=?",
        (order_id,)
    ).fetchone()[0]

    if items_count == 0:
        return "Empty order", 200

    conn.execute(
        "UPDATE orders SET paid=1 WHERE id=?",
        (order_id,)
    )
    conn.commit()

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "⬇️ DOWNLOAD NOW",
            callback_data=f"deliver:{order_id}"
        )
    )

    bot.send_message(
        user_id,
        f"""🎉 <b>Payment Successful!</b>

🧾 Order ID: <code>{order_id}</code>
💳 Amount: ₦{paid_amount}
Click download our costumer:""",
        parse_mode="HTML",
        reply_markup=kb
    )

    print("✅ WEBHOOK PROCESSED:", order_id)
    return "OK", 200







@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200

@bot.callback_query_handler(func=lambda c: c.data.startswith("deliver:"))
def deliver_items(call):
    user_id = call.from_user.id

    try:
        _, order_id = call.data.split(":", 1)
    except:
        bot.answer_callback_query(call.id, "❌ Error from order infor..")
        return

    # 1️⃣ DUBA ORDER
    order = conn.execute(
        "SELECT paid FROM orders WHERE id=? AND user_id=?",
        (order_id, user_id)
    ).fetchone()

    if not order:
        bot.answer_callback_query(call.id, "❌ Order not found.")
        return

    if order["paid"] != 1:
        bot.answer_callback_query(call.id, "❌ Your payment has not been confirmed.")
        return

    # 2️⃣ KAR A SAKE TURAWA (ORDER LEVEL)
    already = conn.execute(
        "SELECT 1 FROM user_movies WHERE order_id=? LIMIT 1",
        (order_id,)
    ).fetchone()

    if already:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎥PAID MOVIES", callback_data="my_movies"))
        bot.send_message(
            user_id,
            "ℹ🚫You have already received your movie.",
            reply_markup=kb
        )
        return

    bot.answer_callback_query(call.id, "📤 We sent your items🥳. Thanks😇")

    # 3️⃣ DAUKO ITEMS (SOURCE NA GASKIYA ✔️)
    items = conn.execute(
        """
        SELECT 
            oi.item_id,
            oi.file_id,
            i.title
        FROM order_items oi
        JOIN items i ON i.id = oi.item_id
        WHERE oi.order_id=?
        """,
        (order_id,)
    ).fetchall()

    if not items:
        bot.send_message(
            user_id,
            "❌ There is an issue with your order.\nPlease contact the admin for assistance."
        )
        return

    sent = 0

    # 4️⃣ TURAWA (ITEM BY ITEM ✔️)
    for item_id, file_id, title in items:
        if not file_id:
            print("❌ NO FILE_ID:", item_id)
            continue

        # 🔒 KARIYA: KAR A SA ITEM SAU BIYU
        exists = conn.execute(
            """
            SELECT 1 FROM user_movies
            WHERE user_id=? AND item_id=?
            """,
            (user_id, item_id)
        ).fetchone()

        if exists:
            continue

        sent_ok = False

        try:
            bot.send_video(
                user_id,
                file_id,
                caption=f"🎬 {title}"
            )
            sent_ok = True
        except:
            try:
                bot.send_document(
                    user_id,
                    file_id,
                    caption=f"📁 {title}"
                )
                sent_ok = True
            except Exception as e:
                print("❌ SEND FAILED:", e)

        if sent_ok:
            conn.execute(
                """
                INSERT INTO user_movies (user_id, item_id, order_id)
                VALUES (?, ?, ?)
                """,
                (user_id, item_id, order_id)
            )
            sent += 1

    conn.commit()

    # 5️⃣ FEEDBACK
    if sent == 0:
        bot.send_message(
            user_id,
            "❌ The movie could not be sent successfully.\nPlease contact the admin for assistance."
        )
        return

    bot.send_message(
        user_id,
        f"✅ We sent your items ({sent}).\nThank you, Our value customer😇🤗"
    )

    send_feedback_prompt(user_id, order_id)


# =========================================================
# ========= HARD START HOWTO (DEEPLINK LOCK) ===============
# =========================================================
@bot.message_handler(
    func=lambda m: (
        m.text
        and m.text.startswith("/start ")
        and len(m.text.split(" ", 1)) > 1
        and m.text.split(" ", 1)[1].startswith("howto_")
    )
)
def __hard_start_howto(msg):
    """
    Wannan handler:
    - Yana rike howto_ deeplink
    - Yana hana komawa main /start
    - Yana kira howto_start_handler kai tsaye
    """
    return howto_start_handler(msg)
# ================= HOW TO BUY STATE =================
HOWTO_STATE = {}


# ======================================================
# /update  (ADMIN ONLY)
# ======================================================
@bot.message_handler(commands=["update"])
def update_howto_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return

    HOWTO_STATE[m.from_user.id] = {"stage": "hausa"}

    bot.send_message(
        m.chat.id,
        "✍️ <b>Rubuta HAUSA version cikakke:</b>",
        parse_mode="HTML"
    )


# ======================================================
# UPDATE FLOW (HAUSA → ENGLISH → MEDIA)
# ======================================================
@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in HOWTO_STATE,
    content_types=["text", "video", "document", "photo"]
)
def howto_update_flow(m):
    state = HOWTO_STATE.get(m.from_user.id)
    if not state:
        return

    stage = state["stage"]

    # ---------- HAUSA ----------
    if stage == "hausa":
        if m.content_type != "text":
            bot.send_message(m.chat.id, "❌ Hausa text kawai ake bukata.")
            return
        state["hausa_text"] = m.text
        state["stage"] = "english"
        bot.send_message(
            m.chat.id,
            "✍️ <b>Rubuta ENGLISH version:</b>",
            parse_mode="HTML"
        )
        return

    # ---------- ENGLISH ----------
    if stage == "english":
        if m.content_type != "text":
            bot.send_message(m.chat.id, "❌ English text kawai ake bukata.")
            return
        state["english_text"] = m.text
        state["stage"] = "media"
        bot.send_message(
            m.chat.id,
            "🎬 Turo <b>VIDEO / DOCUMENT / PHOTO</b>:",
            parse_mode="HTML"
        )
        return

    # ---------- MEDIA ----------
    if stage == "media":
        file_id = None
        media_type = None

        if m.content_type == "video":
            file_id = m.video.file_id
            media_type = "video"
        elif m.content_type == "document":
            file_id = m.document.file_id
            media_type = "document"
        elif m.content_type == "photo":
            file_id = m.photo[-1].file_id
            media_type = "photo"
        else:
            bot.send_message(m.chat.id, "❌ Media bai dace ba.")
            return

        last_version = conn.execute(
            "SELECT MAX(version) FROM how_to_buy"
        ).fetchone()[0] or 0

        conn.execute(
            """
            INSERT INTO how_to_buy
            (hausa_text, english_text, media_file_id, media_type, version)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                state["hausa_text"],
                state["english_text"],
                file_id,
                media_type,
                last_version + 1
            )
        )
        conn.commit()

        HOWTO_STATE.pop(m.from_user.id, None)

        bot.send_message(
            m.chat.id,
            "✅ <b>HOW TO BUY an sabunta successfully</b>",
            parse_mode="HTML"
        )


# ======================================================
# /post  (ADMIN ONLY)
# ======================================================
@bot.message_handler(commands=["post"])
def post_to_channel(m):
    if m.from_user.id != ADMIN_ID:
        return

    row = conn.execute(
        """
        SELECT version
        FROM how_to_buy
        ORDER BY version DESC
        LIMIT 1
        """
    ).fetchone()

    if not row:
        bot.send_message(m.chat.id, "❌ Babu HOW TO BUY da aka saita tukuna.")
        return

    version = row["version"]
    deeplink = f"https://t.me/{BOT_USERNAME}?start=howto_{version}"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "👉 Click here",
            url=deeplink
        )
    )

    bot.send_message(
        CHANNEL,
        " <b>📸📢📢📢📢📢\n\n 👥Koyi yadda zaka siya 🎬fim a 🤖BOT ɗinmu, cikin sauri da sauki sosai\n\n Cikin aminci ba jirah🥰\n\n\n 🤖@Aslamtv2bot\n\nDANNA (Click here)\n\n🔰🔰🔰🔰🔰</b>",
        parse_mode="HTML",
        reply_markup=kb
    )

    bot.send_message(m.chat.id, "✅ An tura post zuwa channel.")


# ======================================================
# DEEPLINK HANDLER
# ======================================================
# HOW TO START (HOWTO ONLY)
# ======================================================
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start howto_"))
def howto_start_handler(m):
    args = m.text.split()

    # kariya (defensive, ko da filter ya riga ya rufe)
    if len(args) < 2 or not args[1].startswith("howto_"):
        return

    try:
        version = int(args[1].split("_")[1])
    except Exception:
        return

    row = conn.execute(
        """
        SELECT hausa_text, english_text, media_file_id, media_type
        FROM how_to_buy
        WHERE version=?
        """,
        (version,)
    ).fetchone()

    if not row:
        bot.send_message(m.chat.id, "❌ Wannan version bai wanzu ba.")
        return

    hausa_text, english_text, file_id, media_type = row

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("🇬🇧 English", callback_data=f"howto_en:{version}"),
        types.InlineKeyboardButton("🇳🇬 Hausa", callback_data=f"howto_ha:{version}")
    )

    caption = hausa_text

    if media_type == "video":
        bot.send_video(m.chat.id, file_id, caption=caption, reply_markup=kb)
    elif media_type == "document":
        bot.send_document(m.chat.id, file_id, caption=caption, reply_markup=kb)
    else:
        bot.send_photo(m.chat.id, file_id, caption=caption, reply_markup=kb)


# ======================================================
# LANGUAGE SWITCH (EDIT ONLY)
# ======================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("howto_"))
def howto_language_switch(c):
    try:
        lang, version = c.data.split(":")
        version = int(version)
    except:
        return

    row = conn.execute(
        """
        SELECT hausa_text, english_text
        FROM how_to_buy
        WHERE version=?
        """,
        (version,)
    ).fetchone()

    if not row:
        bot.answer_callback_query(c.id, "❌ Version bai wanzu ba.")
        return

    hausa_text, english_text = row

    text = english_text if lang == "howto_en" else hausa_text

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("🇬🇧 English", callback_data=f"howto_en:{version}"),
        types.InlineKeyboardButton("🇳🇬 Hausa", callback_data=f"howto_ha:{version}")
    )

    try:
        bot.edit_message_caption(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            caption=text,
            reply_markup=kb
        )
    except:
        pass

    bot.answer_callback_query(c.id)

# ======================================================

# ========= HARD START BUYD =========
@bot.message_handler(
    func=lambda m: m.text
    and m.text.startswith("/start ")
    and m.text.split(" ", 1)[1].startswith("buyd_")
)
def __hard_start_buyd(msg):
    return buyd_deeplink_handler(msg)


# ========= HARD START GROUPITEM =========
@bot.message_handler(
    func=lambda m: m.text
    and m.text.startswith("/start ")
    and m.text.split(" ", 1)[1].startswith("groupitem_")
)
def __hard_start_groupitem(msg):
    return groupitem_deeplink_handler(msg)

# --- Added deep-link start handler for viewall/weakupdate (runs before other start handlers) ---  
@bot.message_handler(func=lambda m: (m.text or "").strip().split(" ")[0]=="/start" and len((m.text or "").strip().split(" "))>1 and (m.text or "").strip().split(" ")[1] in ("viewall","weakupdate"))  
def _start_deeplink_handler(msg):  
    """  
    Catch /start viewall or /start weakupdate deep-links from channel posts.  
    This handler tries to send the weekly list directly and then returns without invoking the normal start flow.  
    Placed early to take precedence over other start handlers.  
    """  
    try:  
        send_weekly_list(msg)  
    except Exception as e:  
        try:  
            bot.send_message(msg.chat.id, "An samu matsala wajen nuna weekly list.")  
        except:  
            pass  
    return




# ================== END RUKUNI B ==================

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("cancel:"))
def cancel_order_handler(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)

    try:
        order_id = c.data.split("cancel:", 1)[1]
    except:
        return

    # 🔎 Tabbatar order na wannan user ne kuma unpaid
    order = conn.execute(
        """
        SELECT id
        FROM orders
        WHERE id=? AND user_id=? AND paid=0
        """,
        (order_id, uid)
    ).fetchone()

    if not order:
        bot.send_message(
            uid,
            "❌ <b>No order was found. It has already been paid for.</b>",
            parse_mode="HTML"
        )
        return

    # 🧹 Goge order_items
    conn.execute(
        "DELETE FROM order_items WHERE order_id=?",
        (order_id,)
    )

    # 🧹 Goge order
    conn.execute(
        "DELETE FROM orders WHERE id=?",
        (order_id,)
    )

    conn.commit()

    bot.send_message(
        uid,
        "❌ <b>You cancled this order.</b>",
        parse_mode="HTML"
    )

# --- Added callback handler for in-bot "View All Movies" buttons ---
@bot.callback_query_handler(func=lambda c: c.data in ("view_all_movies","viewall"))
def _callback_view_all(call):
    uid = call.from_user.id
    # Build a small message-like object expected by send_weekly_list
    class _Msg:
        def __init__(self, uid):
            self.chat = type('X', (), {'id': uid})
            self.text = ""
    try:
        send_weekly_list(_Msg(uid))
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "An samu matsala wajen nuna jerin.")





# ========== HELPERS ==========
def check_join(uid):
    try:
        member = bot.get_chat_member(CHANNEL, uid)
        return member.status in ("member", "administrator", "creator", "restricted")
    except Exception:
        return False

# name anonymization
def mask_name(fullname):
    """Mask parts of the name as requested: Muhmad, Khid, Sa*i style."""
    if not fullname:
        return "User"
    s = re.sub(r"\s+", " ", fullname.strip())
    # split on non-alphanumeric to preserve parts
    parts = re.split(r'(\W+)', s)
    out = []
    for p in parts:
        if not p or re.match(r'\W+', p):
            out.append(p)
            continue
        # p is a word
        n = len(p)
        if n <= 2:
            out.append(p[0] + "*"*(n-1))
            continue
        # keep first 2 and last 1, hide middle with **
        if n <= 4:
            keep = p[0] + "*"*(n-2) + p[-1]
            out.append(keep)
        else:
            # first two, two stars, last one
            out.append(p[:2] + "**" + p[-1])
    return "".join(out)

def tr_user(uid, key, default=""):
    return default

#farko
def reply_menu(uid=None):
    kb = InlineKeyboardMarkup()

    # ===== Labels =====
    paid_orders_label = "🗂Paid Orders"
    my_orders_label   = "Pending order"

    cart_label    = tr_user(uid, "btn_cart", default="Check cart")
    support_label = tr_user(uid, "btn_support", default="📞Help Center")
    channel_label = tr_user(uid, "btn_channel", default="🏘Our Channel")

    # ===== ROW 1 (PAID + MY ORDERS) =====
    kb.row(
        InlineKeyboardButton(paid_orders_label, callback_data="paid_orders"),
        InlineKeyboardButton(my_orders_label, callback_data="myorders_new")
    )

    # ===== ROW 2 (CART + SUPPORT) =====
    kb.row(
        InlineKeyboardButton(cart_label, callback_data="viewcart"),
        InlineKeyboardButton(
            support_label,
            url=f"https://t.me/{ADMIN_USERNAME}"
        )
    )

    # ===== ROW 3 (OUR CHANNEL - URL) =====
    kb.add(
        InlineKeyboardButton(
            channel_label,
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        )
    )

    # ===== ADMIN ONLY BUTTONS =====
    if uid in ADMINS:
        kb.add(InlineKeyboardButton("☢SERIES&ADD🎬", callback_data="groupitems"))
        
    return kb
#end

def user_main_menu(uid=None):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cart_label = tr_user(uid, "btn_cart", default="Check cart")
    help_label = tr_user(uid, "btn_help", default="HELP")

    # An cire "Films din wannan satin"
    # Buttons 1   2 a layi daya
    kb.add(
        KeyboardButton(help_label),
        KeyboardButton(cart_label)
    )

    return kb

#Start
def movie_buttons_inline(mid, user_id=None):
    kb = InlineKeyboardMarkup()

    add_cart = tr_user(user_id, "btn_add_cart", default="➕ Add to Cart")
    buy_now  = tr_user(user_id, "btn_buy_now", default="💳 Buy Now")
    channel  = tr_user(user_id, "btn_channel", default="🏘Our Channel")

    kb.add(
        InlineKeyboardButton(add_cart, callback_data=f"addcartdm:{mid}"),
        InlineKeyboardButton(
            buy_now,
            url=f"https://t.me/{BOT_USERNAME}?start=buyd_{mid}"
        )
    )
#end
    # 🛑 Idan user_id == None → channel ne → kada a ƙara sauran buttons
    if user_id is None:
        return kb

    # 🔰 Idan private chat ne → saka sauran buttons
    kb.row(
        
        InlineKeyboardButton(channel, url=f"https://t.me/{CHANNEL.lstrip('@')}")
    )

  

    return kb
#END

# ========== START ==========
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    fname = message.from_user.first_name or ""
    uname = f"@{message.from_user.username}" if message.from_user.username else "Babu username"
    text = (message.text or "").strip()

    # ========= REF =========
    param = None
    if text.startswith("/start "):
        param = text.split(" ", 1)[1].strip()
    elif text.startswith("/start"):
        parts = text.split(" ", 1)
        if len(parts) > 1:
            param = parts[1].strip()

    if param and param.startswith("ref"):
        try:
            ref_id = int(param[3:])
            add_referral(ref_id, uid)
            try:
                bot.send_message(
                    ref_id,
                    f"Someone used your invite link! ID: <code>{uid}</code>",
                    parse_mode="HTML"
                )
            except:
                pass
        except:
            pass

    # ========= ADMIN NOTIFY =========
    try:
        bot.send_message(
            ADMIN_ID,
            f"🟢 SABON VISITOR!\n\n"
            f"👤 Sunan: <b>{fname}</b>\n"
            f"🔗 Username: {uname}\n"
            f"🆔 ID: <code>{uid}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        print("Failed to notify admin about visitor:", e)

    # ========= JOIN CHECK =========
    joined = check_join(uid)



    # ❌ IDAN BAI SHIGA BA
    if not joined:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "Join Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        kb.add(
            InlineKeyboardButton(
                "I've Joined✅",
                callback_data="checkjoin"
            )
        )
        bot.send_message(
            uid,
            "⚠️ Kafin ka ci gaba, dole ne ka shiga channel ɗinmu.",
            reply_markup=kb
        )
        return

    # ========= MENUS =========
    bot.send_message(
        uid,
        "Abokin hulɗa, muna farin cikin maraba da kai na zuwa shagon fina-finanmu.",
        reply_markup=user_main_menu(uid)
    )
    bot.send_message(
        uid,
        "Shagon Algaita Movie Store na kawo maka zaɓaɓɓun fina-finai masu inganci. Mun tace su tsaf daga ɗanyen kaya, mun ware mafi kyau kawai. Duk fim ɗin da ka siya a nan, tabbas ba za mu ba ka kunya ba.\n\n Muna kawo fina-finan kowanne kamfanin fassara anan.",
        reply_markup=reply_menu(uid)
    )




@bot.message_handler(
    func=lambda msg: isinstance(getattr(msg, "text", None), str)
    and msg.text in ["HELP", "Check cart"]
)
def user_buttons(message):
    txt = message.text
    uid = message.from_user.id

    if txt == "Films ditin":
        try:
            send_weekly_list(message)
        except Exception as e:
            print("Films din wannan satin ERROR:", e)
            bot.send_message(
                message.chat.id,
                "⚠️ An samu matsala wajen nuna fina-finan wannan satin."
            )
        return
# ======= TAIMAKO =======                
    if txt == "HELP":                
        kb = InlineKeyboardMarkup()                

        # ALWAYS open admin DM directly – no callback, no message sending
        if ADMIN_USERNAME:                
            kb.add(InlineKeyboardButton("Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}"))                
        else:                
            kb.add(InlineKeyboardButton("🆘 Support Help", url="https://t.me/{}".format(ADMIN_USERNAME)))                

        bot.send_message(                
            message.chat.id,                
            "Need help? Contact the admin.",                
            reply_markup=kb                
        )                
        return            

    # ======= CART =======            
    if txt == "Check cart":            
        show_cart(message.chat.id, message.from_user.id)            
        return


def clear_cart(uid):
    conn.execute(
        "DELETE FROM cart WHERE user_id = ?",
        (uid,)
    )
    conn.commit()


def get_cart(uid):
    cur = conn.execute("""
        SELECT
            c.item_id,
            i.title,
            i.price,
            i.file_id
        FROM cart c
        JOIN items i ON i.id = c.item_id
        WHERE c.user_id = ?
        ORDER BY c.id DESC
    """, (uid,))
    return cur.fetchall()
# ======================================
# PARSE CAPTION (TITLE + PRICE)
# ======================================
def parse_caption_for_title_price(text):
    if not text:
        return None, None

    text = text.replace("₦", "").strip()

    m = re.match(r"^(.*?)[\s\-]+(\d+)$", text)
    if m:
        return m.group(1).strip(), int(m.group(2))

    parts = text.splitlines()
    if len(parts) >= 2 and parts[1].strip().isdigit():
        return parts[0].strip(), int(parts[1].strip())

    return None, None






@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in admin_states
)
def admin_inputs(message):
    try:
        state_entry = admin_states.get(message.from_user.id)
        if not state_entry:
            return

        state = state_entry.get("state")

        # ⚠️ NOTE:
        # An cire ADD MOVIE logic, amma sauran admin states
        # (weak_update, update_week, da sauransu)
        # suna nan a sauran code ɗinka

        return

    except Exception as e:
        print("ADMIN INPUT ERROR:", e)
        return




    # ========== CANCEL ==========
@bot.message_handler(commands=["cancel"])
def cancel_cmd(message):
    if message.from_user.id == ADMIN_ID and admin_states.get(ADMIN_ID) and admin_states[ADMIN_ID].get("state") in ("weak_update", "update_week"):
        inst = admin_states[ADMIN_ID]
        inst_msg_id = inst.get("inst_msg_id")
        if inst_msg_id:
            try:
                bot.delete_message(chat_id=ADMIN_ID, message_id=inst_msg_id)
            except Exception as e:
                print("Failed to delete instruction message on cancel:", e)
        admin_states.pop(ADMIN_ID, None)
        bot.reply_to(message, "An soke Update/Weak update kuma an goge sakon instruction.")
        return

    if message.from_user.id == ADMIN_ID and admin_states.get(ADMIN_ID):
        admin_states.pop(ADMIN_ID, None)
        bot.reply_to(message, "An soke aikin admin na yanzu.")
        return

# ==================================================
# ========== GET CART (GROUP-AWARE SAFE) ============
# ==================================================
def get_cart(uid):
    return conn.execute(
        """
        SELECT
            c.item_id,          -- movie_id
            i.title,            -- title
            i.price,            -- price (GROUP price)
            i.file_id,          -- file_id
            i.group_key         -- GROUP KEY
        FROM cart c
        JOIN items i ON i.id = c.item_id
        WHERE c.user_id=?
        """,
        (uid,)
    ).fetchall()
# ========== BUILD CART VIEW (GROUP-AWARE - FIXED) ==========
def build_cart_view(uid):
    rows = get_cart(uid)

    kb = InlineKeyboardMarkup()

    # ===== IDAN CART BABU KOMAI =====
    if not rows:
        text = "🛒 <b>You haven’t added any items to your cart yet,\n\n Check our channel to buy movie.</b>"

        kb.row(
            
            InlineKeyboardButton(
                "🏘Our Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        return text, kb

    total = 0
    lines = []

    # ===============================
    # HADA ITEMS TA GROUP_KEY
    # ===============================
    grouped = {}

    for movie_id, title, price, file_id, group_key in rows:
        key = group_key or f"single_{movie_id}"

        if key not in grouped:
            grouped[key] = {
                "ids": [],
                "title": title or "📦 Group / Series Item",
                "price": int(price or 0)
            }

        grouped[key]["ids"].append(movie_id)

    # ===============================
    # DISPLAY ITEMS
    # ===============================
    for g in grouped.values():
        ids = g["ids"]
        title = g["title"]
        price = g["price"]

        total += price

        lines.append(f"🎬 {title} — ₦{price}")

        ids_str = "_".join(str(i) for i in ids)

        kb.add(
            InlineKeyboardButton(
                f"❌ Remove: {title}",
                callback_data=f"removecart:{ids_str}"
            )
        )

    # ===== TOTAL =====
    lines.append("")
    lines.append(f"<b>Total:</b> ₦{total}")

    text = (
        "🛒 <b>Your cart list.</b>\n\n"
        + "\n".join(lines)
    )

    # ===== ACTION BUTTONS =====
    kb.add(
        InlineKeyboardButton("🧹 Clear Cart", callback_data="clearcart")
    )
    kb.add(
        InlineKeyboardButton("💵 CHECKOUT", callback_data="checkout")
    )

   

    return text, kb
# ================= ADMIN ON / OFF =================
@bot.message_handler(commands=["on"])
def admin_on(m):
    if m.chat.type != "private" or m.from_user.id != ADMIN_ID:
        return

    conn.execute(
        "INSERT OR REPLACE INTO admin_controls (admin_id, sendmovie_enabled) VALUES (?,1)",
        (ADMIN_ID,)
    )
    conn.commit()
    bot.reply_to(m, "✅ An kunna SENDMOVIE / GETID")


@bot.message_handler(commands=["off"])
def admin_off(m):
    if m.chat.type != "private" or m.from_user.id != ADMIN_ID:
        return

    conn.execute(
        "INSERT OR REPLACE INTO admin_controls (admin_id, sendmovie_enabled) VALUES (?,0)",
        (ADMIN_ID,)
    )
    conn.commit()
    bot.reply_to(m, "⛔ An kashe SENDMOVIE / GETID")


def admin_feature_enabled():
    row = conn.execute(
        "SELECT sendmovie_enabled FROM admin_controls WHERE admin_id=?",
        (ADMIN_ID,)
    ).fetchone()
    return row and row[0] == 1


# ================= GETID (FILE_NAME SEARCH) =================
@bot.message_handler(commands=["getid"])
def getid_command(message):
    # 🔒 TSARO: admin + sai an kunna
    if message.from_user.id != ADMIN_ID:
        return
    if not admin_feature_enabled():
        return

    text = message.text or ""
    parts = text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(
            message,
            "Amfani: /getid Sunan item\nMisali: /getid Wutar jeji"
        )
        return

    query = parts[1].strip()

    # ====== EXACT MATCH (PRIORITY) ======
    row = conn.execute(
        """
        SELECT id, title
        FROM items
        WHERE LOWER(title) = LOWER(?)
        LIMIT 1
        """,
        (query,)
    ).fetchone()

    if row:
        bot.reply_to(
            message,
            f"Kamar yadda ka bukata ga ID ɗin fim din <b>{row['title']}</b>: <code>{row['id']}</code>",
            parse_mode="HTML"
        )
        return

    # ====== CONTAINS MATCH ======
    rows = conn.execute(
        """
        SELECT id, title
        FROM items
        WHERE LOWER(title) LIKE LOWER(?)
        ORDER BY title ASC
        LIMIT 10
        """,
        (f"%{query}%",)
    ).fetchall()

    # ====== BABU KOMAI ======
    if not rows:
        bot.reply_to(
            message,
            "❌ Ban samu fim da kake nema ba."
        )
        return

    # ====== MATCH 1 ======
    if len(rows) == 1:
        r = rows[0]
        bot.reply_to(
            message,
            f"Kamar yadda ka bukata ga ID ɗin fim din da kake nema <b>{r['title']}</b>: <code>{r['id']}</code>",
            parse_mode="HTML"
        )
        return

    # ====== MATCH DAYA FIYE ======
    text_out = "An samu fina-finai masu kama:\n"
    for r in rows:
        text_out += f"• {r['title']} — ID: {r['id']}\n"

    bot.reply_to(message, text_out)


# ================= SENDMOVIE (ID / GROUP_KEY / NAME) =================
@bot.message_handler(commands=["sendmovie"])
def sendmovie_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    if not admin_feature_enabled():
        return

    parts = m.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(
            m,
            "Amfani:\n"
            "/sendmovie 20\n"
            "/sendmovie 1,2,3,7\n"
            "/sendmovie karn tsaye S1\n"
            "/sendmovie avatar"
        )
        return

    raw = parts[1].strip()

    # ===============================
    # MODE 1: ID MODE
    # ===============================
    ids = []
    for x in raw.replace(" ", "").split(","):
        if x.isdigit():
            ids.append(int(x))

    rows = []

    if ids:
        # ===== FETCH BY IDS =====
        for item_id in ids:
            row = conn.execute(
                """
                SELECT file_id, title
                FROM items
                WHERE id=?
                """,
                (item_id,)
            ).fetchone()

            if row:
                rows.append(row)

        not_found_ids = [str(i) for i in ids if i not in [
            r[0] for r in conn.execute(
                "SELECT id FROM items WHERE id IN (%s)" %
                ",".join("?" * len(ids)),
                ids
            ).fetchall()
        ]]

    else:
        # ===============================
        # MODE 2: GROUP_KEY / NAME MODE
        # ===============================
        q = raw.lower()

        # 🔹 1) GROUP_KEY
        rows = conn.execute(
            """
            SELECT file_id, title
            FROM items
            WHERE LOWER(group_key) = ?
            ORDER BY id ASC
            """,
            (q,)
        ).fetchall()

        # 🔹 2) TITLE / FILE_NAME (fallback)
        if not rows:
            rows = conn.execute(
                """
                SELECT file_id, title
                FROM items
                WHERE LOWER(title) LIKE ?
                   OR LOWER(file_name) LIKE ?
                ORDER BY title ASC
                """,
                (f"%{q}%", f"%{q}%")
            ).fetchall()

        not_found_ids = []

    # ===============================
    # NOTHING FOUND
    # ===============================
    if not rows:
        bot.reply_to(
            m,
            "❌ Ban samu fim ko group ɗin da ka nema ba."
        )
        return

    # ===============================
    # SEND FILES
    # ===============================
    sent = 0

    for file_id, title in rows:
        try:
            try:
                bot.send_video(
                    m.chat.id,
                    file_id,
                    caption=f"🎬 {title}"
                )
            except:
                bot.send_document(
                    m.chat.id,
                    file_id,
                    caption=f"🎬 {title}"
                )
            sent += 1
        except Exception as e:
            print("sendmovie error:", e)

    # ===============================
    # REPORT
    # ===============================
    report = f"✅ An tura fina-finai: {sent}"

    if not_found_ids:
        report += (
            "\n\n❌ Ba a samu waɗannan IDs ba:\n"
            + ", ".join(not_found_ids)
        )

    bot.reply_to(m, report)
    # ================= USER RESEND SEARCH (USING user_movies) =================

@bot.message_handler(
    func=lambda m: m.from_user.id in admin_states
    and admin_states.get(m.from_user.id, {}).get("state") in (
        "search_menu",
        "browse_menu",
        "series_menu",
        "search_trending",
    )
)
def ignore_unexpected_text(m):
    uid = m.from_user.id
    bot.send_message(
        uid,
        "ℹ️ Don Allah ka yi amfani da *buttons* da ke ƙasa.",
        parse_mode="Markdown"
    )
# ======================================================
# ACTIVE BUYERS (ADMIN ONLY | PAGINATION | EDIT MODE)
# ======================================================

# ================== END RUKUNI B ==================

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("cancel:"))
def cancel_order_handler(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)

    try:
        order_id = c.data.split("cancel:", 1)[1]
    except:
        return

    # 🔎 Tabbatar order na wannan user ne kuma unpaid
    order = conn.execute(
        """
        SELECT id
        FROM orders
        WHERE id=? AND user_id=? AND paid=0
        """,
        (order_id, uid)
    ).fetchone()

    if not order:
        bot.send_message(
            uid,
            "❌ <b>Ba a sami order ba ko kuma an riga an biya shi.</b>",
            parse_mode="HTML"
        )
        return

    # 🧹 Goge order_items
    conn.execute(
        "DELETE FROM order_items WHERE order_id=?",
        (order_id,)
    )

    # 🧹 Goge order
    conn.execute(
        "DELETE FROM orders WHERE id=?",
        (order_id,)
    )

    conn.commit()

    bot.send_message(
        uid,
        "❌ <b>An soke wannan order ɗin.</b>",
        parse_mode="HTML"
    )

# --- Added callback handler for in-bot "View All Movies" buttons ---
@bot.callback_query_handler(func=lambda c: c.data in ("view_all_movies","viewall"))
def _callback_view_all(call):
    uid = call.from_user.id
    # Build a small message-like object expected by send_weekly_list
    class _Msg:
        def __init__(self, uid):
            self.chat = type('X', (), {'id': uid})
            self.text = ""
    try:
        send_weekly_list(_Msg(uid))
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "An samu matsala wajen nuna jerin.")




@bot.message_handler(
    func=lambda m: user_states.get(m.from_user.id, {}).get("action") == "_resend_search_"
)
def handle_resend_search_text(m):
    uid = m.from_user.id
    query = m.text.strip()

    # 1️⃣ Tabbatar da rubutu
    if len(query) < 2:
        bot.send_message(
            uid,
            "❌ Rubuta akalla haruffa 2 ko fiye.\nMisali: damisa, mash, mai"
        )
        return

    # 2️⃣ DUBA KO USER YA TABA SAMUN DELIVERY
    total_owned = conn.execute(
        "SELECT COUNT(*) FROM user_movies WHERE user_id=?",
        (uid,)
    ).fetchone()[0]

    if total_owned == 0:
        user_states.pop(uid, None)
        bot.send_message(
            uid,
            "❌ <b>Baka taɓa siyan wani fim ba.</b>\n"
            "Je ka siya daga bangaren siyayya.",
            parse_mode="HTML"
        )
        return

    # 3️⃣ DUBA IYAKAR SAKE TURAWA
    used = conn.execute(
        "SELECT COUNT(*) FROM resend_logs WHERE user_id=?",
        (uid,)
    ).fetchone()[0]

    if used >= 10:
        user_states.pop(uid, None)
        bot.send_message(
            uid,
            "⚠️ Ka kai iyakar sake karɓa (sau 10).\n"
            "Sai ka sake siya."
        )
        return

    # 4️⃣ NEMO ITEMS DA USER YA MALLAKA (SINGLE + GROUP KEY)
    rows = conn.execute(
        """
        SELECT
            i.id            AS item_id,
            i.title         AS title,
            i.group_key     AS group_key
        FROM user_movies um
        JOIN items i ON i.id = um.item_id
        WHERE um.user_id = ?
          AND i.title LIKE ?
        ORDER BY i.title ASC
        """,
        (uid, f"%{query}%")
    ).fetchall()

    # 5️⃣ IDAN BABU MATCH → CI GABA DA JIRA
    if not rows:
        bot.send_message(
            uid,
            "❌ Babu fim da wannan suna cikin fina-finai da ka taba siya.\n\n"
            "Sake gwada wani suna.\nIna jiranka… 😊"
        )
        return  # ⚠️ KAR A CIRE STATE

    # 6️⃣ GROUP KEY LOGIC (NUNA SUNA 1 KACAL)
    user_states.pop(uid, None)

    kb = InlineKeyboardMarkup()
    shown_groups = set()

    for r in rows:
        item_id   = r["item_id"]
        title     = r["title"]
        group_key = r["group_key"]

        if group_key:
            if group_key in shown_groups:
                continue
            shown_groups.add(group_key)

            kb.add(
                InlineKeyboardButton(
                    title,
                    callback_data=f"resend_group:{group_key}"
                )
            )
        else:
            kb.add(
                InlineKeyboardButton(
                    title,
                    callback_data=f"resend_one:{item_id}"
                )
            )

    bot.send_message(
        uid,
        "🎬 <b>An samu fina-finai:</b>\n"
        "Danna suna domin a sake turo maka:",
        parse_mode="HTML",
        reply_markup=kb
    )
# ========== HELPERS =======
# ========== detect forwarded channel post ==========
@bot.message_handler(func=lambda m: getattr(m, "forward_from_chat", None) is not None or getattr(m, "forward_from_message_id", None) is not None)
def handle_forwarded_post(m):
    fc = getattr(m, "forward_from_chat", None)
    fid = getattr(m, "forward_from_message_id", None)
    if not fc and not fid:
        return
    try:
        chat_info = ""
        if fc:
            if getattr(fc, "username", None):
                chat_info = f"@{fc.username}"
            else:
                chat_info = f"chat_id:{fc.id}"
        else:
            chat_info = "Unknown channel"
        if fid:
            bot.reply_to(m, f"Original channel: {chat_info}\nOriginal message id: {fid}")
        else:
            bot.reply_to(m, f"Original channel: {chat_info}\nMessage id not found.")
    except Exception as e:
        print("forward handler error:", e)


# ========== show_cart ==========
def show_cart(chat_id, user_id):
    rows = get_cart(user_id)

    if not rows:
        kb = InlineKeyboardMarkup()
        kb.row(
            
            InlineKeyboardButton("🏘Our Channel", url=f"https://t.me/{CHANNEL.lstrip('@')}")
        )
        
        s = tr_user(user_id, "cart_empty", default="You haven’t added any items to your cart yet,\n\n Check our channel to buy movie.")
        bot.send_message(chat_id, s, reply_markup=kb)
        return

    text_lines = ["This is your cart list."]
    kb = InlineKeyboardMarkup()

    total = 0  # ✅ total ɗaya kacal

    # ===============================
    # HADA ITEMS TA GROUP_KEY
    # ===============================
    grouped = {}

    for movie_id, title, price, file_id, group_key in rows:
        key = group_key or f"single_{movie_id}"

        if key not in grouped:
            grouped[key] = {
                "ids": [],
                "title": title or "📦 Group / Series Item",
                "price": int(price or 0)
            }

        grouped[key]["ids"].append(movie_id)

    # ===============================
    # DISPLAY (SINGLE + GROUP)
    # ===============================
    for g in grouped.values():
        ids = g["ids"]
        title = g["title"]
        price = g["price"]

        total += price  # ✅ ba ya ninkawa

        if price == 0:
            text_lines.append(f"• {title} — 📦 Series")
        else:
            text_lines.append(f"• {title} — ₦{price}")

        ids_str = "_".join(str(i) for i in ids)

        kb.add(
            InlineKeyboardButton(
                f"❌ Remove: {title[:18]}",
                callback_data=f"removecart:{ids_str}"
            )
        )

    text_lines.append(f"\nTotal: ₦{total}")

    # ===============================
    # CREDIT INFO (KAMAR YADDA YAKE)
    # ===============================
    total_available, credit_rows = get_credits_for_user(user_id)
    credit_info = ""
    if total_available > 0:
        credit_info = (
            f"\n\nNote: Available referral credit: N{total_available}. "
            f"It will be automatically applied at checkout."
        )

    # ===============================
    # ACTION BUTTONS
    # ===============================
    kb.add(
        InlineKeyboardButton("🧹 Clear Cart", callback_data="clearcart"),
        InlineKeyboardButton("💵 CHECKOUT", callback_data="checkout")
    )

    kb.row(
        
        InlineKeyboardButton("🏘Our Channel", url=f"https://t.me/{CHANNEL.lstrip('@')}")
    )

  

    bot.send_message(
        chat_id,
        "\n".join(text_lines) + credit_info,
        reply_markup=kb
    )




# ---------- weekly button ----------
@bot.callback_query_handler(func=lambda c: c.data == "weekly_films")
def send_weekly_films(call):
    return send_weekly_list(call.message)


# ---------- My Orders (UNPAID with per-item REMOVE) ----------
ORDERS_PER_PAGE = 5

def build_unpaid_orders_view(uid, page):
    offset = page * ORDERS_PER_PAGE

    total = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id=? AND paid=0",
        (uid,)
    ).fetchone()[0]

    if total == 0:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "🏘 Our Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        return "📩<b>There are no unpaid orders. \n\n Go to our channel to buy Films</b>", kb

    # ===== TOTAL AMOUNT (GYARA NA ASALI) =====
    total_amount = conn.execute(
        """
        SELECT COALESCE(SUM(
            CASE
                WHEN gk_count = 1 THEN base_price
                ELSE amount
            END
        ),0)
        FROM (
            SELECT
                o.id,
                COUNT(DISTINCT i.group_key) AS gk_count,
                SUM(oi.price) AS amount,
                MIN(oi.price) AS base_price
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            LEFT JOIN items i ON i.id = oi.item_id
            WHERE o.user_id=? AND o.paid=0
            GROUP BY o.id
        )
        """,
        (uid,)
    ).fetchone()[0]

    rows = conn.execute(
        """
        SELECT
            o.id,
            COUNT(oi.item_id) AS items_count,
            SUM(oi.price) AS amount,
            MAX(i.title) AS title,
            COUNT(DISTINCT i.group_key) AS gk_count,
            MIN(oi.price) AS base_price,
            MIN(i.group_key) AS group_key
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN items i ON i.id = oi.item_id
        WHERE o.user_id=? AND o.paid=0
        GROUP BY o.id
        ORDER BY o.rowid DESC
        LIMIT ? OFFSET ?
        """,
        (uid, ORDERS_PER_PAGE, offset)
    ).fetchall()

    text = f"📩<b>Your unpaid orders ({total})</b>\n\n"
    kb = InlineKeyboardMarkup()

    for oid, count, amount, title, gk_count, base_price, group_key in rows:
        if count > 1 and gk_count == 1:
            name = f"{title} (EP {count})"
            show_amount = base_price
        else:
            if count == 1:
                name = title or "Single item"
            else:
                name = f"Group order ({count} items)"
            show_amount = amount

        short = name[:27] + "…" if len(name) > 27 else name
        text += f"• {short} — ₦{int(show_amount)}\n"

        kb.row(
            InlineKeyboardButton(
                f"❌ Remove{short}",
                callback_data=f"remove_unpaid:{oid}"
            )
        )

    text += f"\n<b>Total balance:</b> ₦{int(total_amount)}"

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "◀️ Back",
                callback_data=f"unpaid_prev:{page-1}"
            )
        )
    if offset + ORDERS_PER_PAGE < total:
        nav.append(
            InlineKeyboardButton(
                "Next ▶️",
                callback_data=f"unpaid_next:{page+1}"
            )
        )
    if nav:
        kb.row(*nav)

    kb.row(
        InlineKeyboardButton("💳 Pay all", callback_data="payall:"),
        InlineKeyboardButton("📩 Paid orders", callback_data="paid_orders")
    )

    kb.row(
        InlineKeyboardButton("🗑 Delete unpaid", callback_data="delete_unpaid")
    )

    # ✅ GYARA KAƊAI: OUR CHANNEL URL (MAIMAKON GO_HOME)
    kb.row(
        InlineKeyboardButton(
            "🏘 Our Channel",
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        )
    )

    return text, kb

def build_paid_orders_view(uid, page):
    offset = page * ORDERS_PER_PAGE

    total = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id=? AND paid=1",
        (uid,)
    ).fetchone()[0]

    if total == 0:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🎥 PAID) MOVIES", callback_data="my_movies")
        )
        kb.add(
            InlineKeyboardButton(
                "🏘 Our Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        return "📩 <b>There are no paid orders.\n\n Go to our Channel to buy films</b>", kb

    rows = conn.execute(
        """
        SELECT
            o.id,
            COUNT(oi.item_id) AS items_count,
            MAX(i.title) AS title,
            COUNT(DISTINCT i.group_key) AS gk_count
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN items i ON i.id = oi.item_id
        WHERE o.user_id=? AND o.paid=1
        GROUP BY o.id
        ORDER BY o.rowid DESC
        LIMIT ? OFFSET ?
        """,
        (uid, ORDERS_PER_PAGE, offset)
    ).fetchall()

    text = f"📩 <b>Your paid orders ({total})</b>\n\n"
    kb = InlineKeyboardMarkup()

    for oid, count, title, gk_count in rows:

        delivered = conn.execute(
            "SELECT COUNT(*) FROM user_movies WHERE order_id=? AND user_id=?",
            (oid, uid)
        ).fetchone()[0]

        remain = count - delivered

        if count > 1 and gk_count == 1:
            name = f"{title} (EP {count})"
        else:
            name = title or f"Group order ({count} items)"

        short = name[:27] + "…" if len(name) > 27 else name

        if remain > 0:
            text += f"• {short} — ✅ Paid (Remaining: {remain})\n"
        else:
            text += f"• {short} — ✅ Arrived\n"

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "◀️ Back",
                callback_data=f"paid_prev:{page-1}"
            )
        )
    if offset + ORDERS_PER_PAGE < total:
        nav.append(
            InlineKeyboardButton(
                "Next ▶️",
                callback_data=f"paid_next:{page+1}"
            )
        )
    if nav:
        kb.row(*nav)

    kb.add(
        InlineKeyboardButton("🎥PAID MOVIES", callback_data="my_movies")
    )

    # ✅ GYARA KAƊAI: OUR CHANNEL URL
    kb.add(
        InlineKeyboardButton(
            "🏘Our Channel",
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        )
    )

    return text, kb

# ---------- START handler (VIEW) ----------
@bot.message_handler(commands=['start'])
def start_handler(msg):

    track_visited_user(msg)

    # 🛑 BAR BUYD DA GROUPITEM SU WUCE
    if msg.text.startswith("/start buyd_"):
        return
    if msg.text.startswith("/start groupitem_"):
        return
    # ===== ASALIN VIEW DINKA (BA A TABA SHI BA) =====
    args = msg.text.split()
    if len(args) > 1 and args[1] == "weakupdate":
        return send_weekly_list(msg)
    if len(args) > 1 and args[1] == "viewall":
        return send_weekly_list(msg)

    bot.send_message(msg.chat.id, "Welcome!")

# ========= BUYD (ITEM ONLY | DEEP LINK → DM) =========

# ========= BUYD (ITEM ONLY | DEEP LINK → DM) =========
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start buyd_"))
def buyd_deeplink_handler(msg):
    try:
        uid = msg.from_user.id
        item_id = int(msg.text.split("buyd_", 1)[1])
    except:
        bot.reply_to(msg, "❌ Buy link ɗin bai dace ba.")
        return

    item = conn.execute(
        "SELECT id, title, price, file_id FROM items WHERE id=?",
        (item_id,)
    ).fetchone()

    if not item:
        bot.send_message(uid, "❌ Item not found.")
        return

    if not item["file_id"]:
        bot.send_message(uid, "❌ Wannan item ba shi da file.")
        return

    title = item["title"]
    price = int(item["price"] or 0)

    # 🛑 KARIYA 1: OWNERSHIP (ITEM ✔️)
    owned = conn.execute(
        "SELECT 1 FROM user_movies WHERE user_id=? AND item_id=? LIMIT 1",
        (uid, item_id)
    ).fetchone()

    if owned:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎥PAID MOVIES", callback_data="my_movies"))
        bot.send_message(
            uid,
            "✅ <b>Ka riga ka mallaki wannan fim tini/n/n DUBA MY MOVIES\n Acen zaka rubuta sunansa za'a sake turama kyauta idan kana bukata.</b>",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    # 🛑 KARIYA 2: UNPAID ORDER MAI WANNAN ITEM (ITEM LEVEL ✔️)
    old = conn.execute(
        """
        SELECT o.id, o.amount
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.user_id=? AND o.paid=0 AND oi.item_id=?
        LIMIT 1
        """,
        (uid, item_id)
    ).fetchone()

    if old:
        order_id = old["id"]
        total = old["amount"]
    else:
        order_id = str(uuid.uuid4())

        conn.execute(
            """
            INSERT INTO orders (id, user_id, amount, paid)
            VALUES (?, ?, ?, 0)
            """,
            (order_id, uid, price)
        )

        conn.execute(
            """
            INSERT INTO order_items (order_id, item_id, file_id, price)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, item_id, item["file_id"], price)
        )

        total = price
        conn.commit()

    # 🧪 DEBUG
    bot.send_message(
        uid,
        f"🤩<b>SINGLE MOVIE ORDER CREATED</b>\n\n• {title}",
        parse_mode="HTML"
    )

    pay_url = create_flutterwave_payment(uid, order_id, total, title)
    if not pay_url:
        bot.send_message(uid, "❌ Payment error.")
        return

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

    bot.send_message(
        uid,
        f"""🎬 <b>{title}</b>

💵 <b>Price:</b> ₦{total}

🆔 <b>Order ID:</b>
<code>{order_id}</code>

⚠️ <b>MUHIMMI:</b>
<i>Ajiye wannan Order ID sosai.
Idan wata matsala ta faru (biyan kudi ko delivery),
ka tura wannan Order ID kai tsaye zuwa admin.</i>
""",
        parse_mode="HTML",
        reply_markup=kb
    )


# ========= GROUPITEM (ITEMS ONLY | DEEP LINK → DM) =========
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start groupitem_"))
def groupitem_deeplink_handler(msg):
    try:
        uid = msg.from_user.id
        raw = msg.text.split("groupitem_", 1)[1]
        sep = "_" if "_" in raw else ","
        item_ids = [int(x) for x in raw.split(sep) if x.strip().isdigit()]
    except:
        bot.reply_to(msg, "❌ Invalid link.")
        return

    if not item_ids:
        bot.send_message(uid, "❌ Babu item.")
        return

    placeholders = ",".join("?" * len(item_ids))

    items = conn.execute(
        f"""
        SELECT id, title, price, file_id, group_key
        FROM items
        WHERE id IN ({placeholders})
        """,
        item_ids
    ).fetchall()

    if not items:
        bot.send_message(uid, "❌ Items not found.")
        return

    # 🛑 KAR A SAYAR DA ITEM MARA FILE
    items = [i for i in items if i["file_id"]]
    if not items:
        bot.send_message(uid, "❌ Babu item mai file.")
        return

    # 🔹 DISPLAY TITLE (SERIES NAME)
    display_title = items[0]["title"]

    # 🛑 KARIYA 1: OWNERSHIP (ITEM LEVEL ✔️)
    owned = conn.execute(
        f"""
        SELECT 1 FROM user_movies
        WHERE user_id=? AND item_id IN ({placeholders})
        LIMIT 1
        """,
        (uid, *[i["id"] for i in items])
    ).fetchone()

    if owned:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎥PAID MOVIES", callback_data="my_movies"))
        bot.send_message(
            uid,
            "✅ <b>Ka riga ka mallaki wannan fim tini/n/n DUBA MY MOVIES\n Acen zaka rubuta sunansa za'a sake turama kyauta idan kana bukata.</b>",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    # ===============================
    # ✅ TOTAL (GROUP-AWARE – PRICE 1)
    # ===============================
    groups = {}

    for i in items:
        key = i["group_key"] or f"single_{i['id']}"

        if key not in groups:
            groups[key] = int(i["price"] or 0)

    total = sum(groups.values())

    # 🛑 KARIYA 2: UNPAID ORDER MAI WANNAN ITEMS (ITEM LEVEL ✔️)
    old = conn.execute(
        f"""
        SELECT o.id, o.amount
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.user_id=? AND o.paid=0
          AND oi.item_id IN ({placeholders})
        LIMIT 1
        """,
        (uid, *[i["id"] for i in items])
    ).fetchone()

    if old:
        order_id = old["id"]
        total = old["amount"]
    else:
        order_id = str(uuid.uuid4())

        conn.execute(
            """
            INSERT INTO orders (id, user_id, amount, paid)
            VALUES (?, ?, ?, 0)
            """,
            (order_id, uid, total)
        )

        for i in items:
            conn.execute(
                """
                INSERT INTO order_items (order_id, item_id, file_id, price)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, i["id"], i["file_id"], int(i["price"] or 0))
            )

        conn.commit()

    # 🧪 DEBUG
    dbg = (
        "🤩<b>SERIES ORDER CREATED</b>\n\n"
        f"• {display_title}\n"
        f"📦 Episodes: {len(items)}\n"
    )

    bot.send_message(uid, dbg, parse_mode="HTML")

    title = display_title

    # ✅ PAYSTACK PAYMENT LINK
    pay_url = create_paystack_payment(uid, order_id, total, title)
    if not pay_url:
        bot.send_message(uid, "❌ Payment error.")
        return

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

    bot.send_message(
        uid,
        f"""🧾 <b>FILMS CHECKOUT</b>

📦 <b>Items:</b> {len(items)}
💵 <b>Total:</b> ₦{total}

🆔 <b>Order ID:</b>
<code>{order_id}</code>

⚠️ <b>MUHIMMI:</b>
<i>Ajiye wannan Order ID sosai.
Idan wata matsala ta faru (biyan kudi ko delivery),
ka tura wannan Order ID kai tsaye zuwa admin.</i>
""",
        parse_mode="HTML",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("buy_again:"))
def buy_again_handler(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)

    try:
        old_order_id = c.data.split("buy_again:", 1)[1]
    except:
        bot.send_message(uid, "❌ Invalid order reference.")
        return

    # ===============================
    # FETCH OLD ORDER ITEMS
    # ===============================
    rows = conn.execute(
        """
        SELECT
            oi.item_id,
            oi.file_id,
            oi.price,
            i.title
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        LEFT JOIN items i ON i.id = oi.item_id
        WHERE o.id=? AND o.user_id=? AND o.paid=1
        """,
        (old_order_id, uid)
    ).fetchall()

    if not rows:
        bot.send_message(uid, "❌ Ba a samu wannan order ba.")
        return

    # ===============================
    # ITEMS LIST
    # ===============================
    items = []
    for r in rows:
        if r["file_id"]:
            items.append(r)

    if not items:
        bot.send_message(uid, "❌ Wannan order babu item mai file.")
        return

    # ===============================
    # TOTAL PRICE (GROUP SAFE)
    # ===============================
    group_keys = conn.execute(
        """
        SELECT COUNT(DISTINCT i.group_key) AS gk
        FROM order_items oi
        LEFT JOIN items i ON i.id = oi.item_id
        WHERE oi.order_id=?
        """,
        (old_order_id,)
    ).fetchone()["gk"]

    if len(items) > 1 and group_keys == 1:
        total = int(items[0]["price"] or 0)
    else:
        total = sum(int(i["price"] or 0) for i in items)

    # ===============================
    # CREATE NEW ORDER (ALWAYS NEW)
    # ===============================
    new_order_id = str(uuid.uuid4())

    conn.execute(
        """
        INSERT INTO orders (id, user_id, amount, paid)
        VALUES (?, ?, ?, 0)
        """,
        (new_order_id, uid, total)
    )

    for i in items:
        conn.execute(
            """
            INSERT INTO order_items (order_id, item_id, file_id, price)
            VALUES (?, ?, ?, ?)
            """,
            (
                new_order_id,
                i["item_id"],
                i["file_id"],
                int(i["price"] or 0)
            )
        )

    conn.commit()

    # ===============================
    # DEBUG MESSAGE (KAMAR WANCAN)
    # ===============================
    if len(items) > 1:
        dbg = (
            "🔁 <b>BUY AGAIN – GROUP ORDER</b>\n\n"
            f"📦 Episodes: {len(items)}"
        )
    else:
        dbg = (
            "🔁 <b>BUY AGAIN – ORDER</b>\n\n"
            f"• {items[0]['title']}"
        )

    bot.send_message(uid, dbg, parse_mode="HTML")

    # ===============================
    # PAYMENT
    # ===============================
    title = " / ".join({i["title"] for i in items if i["title"]})

    pay_url = create_flutterwave_payment(uid, new_order_id, total, title)
    if not pay_url:
        bot.send_message(uid, "❌ Payment error.")
        return

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{new_order_id}"))

    # ===============================
    # FINAL MESSAGE (FORMAT IRIN NAKA)
    # ===============================
    bot.send_message(
        uid,
        f"""🧾 <b>CHECKOUT</b>

📦 <b>Items:</b> {len(items)}
💵 <b>Total:</b> ₦{total}

🆔 <b>Order ID:</b>
<code>{new_order_id}</code>

⚠️ <b>MUHIMMI:</b>
<i>Ajiye wannan Order ID sosai.
Idan wata matsala ta faru (biyan kudi ko delivery),
ka tura wannan Order ID kai tsaye zuwa admin.</i>
""",
        parse_mode="HTML",
        reply_markup=kb
    )

# ======================================================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("buygroup:"))
def buygroup_handler(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)

    try:
        raw = c.data.split("buygroup:", 1)[1]
        sep = "_" if "_" in raw else ","
        item_ids = [int(x) for x in raw.split(sep) if x.strip().isdigit()]
    except:
        bot.send_message(uid, "❌ Invalid group data.")
        return

    if not item_ids:
        bot.send_message(uid, "❌ Babu item a wannan group.")
        return

    placeholders = ",".join("?" * len(item_ids))

    # ===============================
    # FETCH ITEMS
    # ===============================
    items = conn.execute(
        f"""
        SELECT id, title, price, file_id, group_key
        FROM items
        WHERE id IN ({placeholders})
        """,
        item_ids
    ).fetchall()

    if not items:
        bot.send_message(uid, "❌ Items ba su samu ba.")
        return

    # 🛑 KAR A SAYAR DA ITEM MARA FILE
    items = [i for i in items if i["file_id"] and int(i["price"] or 0) > 0]
    if not items:
        bot.send_message(uid, "❌ Babu item mai file.")
        return

    # ===============================
    # 🛑 OWNERSHIP CHECK
    # ===============================
    owned = conn.execute(
        f"""
        SELECT 1
        FROM user_movies
        WHERE user_id=? AND item_id IN ({placeholders})
        LIMIT 1
        """,
        (uid, *[i["id"] for i in items])
    ).fetchone()

    if owned:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎥PAID MOVIES", callback_data="my_movies"))
        bot.send_message(
            uid,
            "✅ <b>Ka riga ka mallaki wannan fim tuni.</b>",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    # ===============================
    # GROUP LIKE CHECKOUT
    # ===============================
    groups = {}

    for i in items:
        key = i["group_key"] or f"single_{i['id']}"

        if key not in groups:
            groups[key] = {
                "price": int(i["price"]),
                "items": []
            }

        groups[key]["items"].append(i)

    # ===============================
    # TOTAL (GROUP = 1 PRICE)
    # ===============================
    total = sum(g["price"] for g in groups.values())
    if total <= 0:
        bot.send_message(uid, "❌ Amount error.")
        return

    # ===============================
    # 🛑 UNPAID ORDER CHECK (SAFE)
    # ===============================
    old = conn.execute(
        """
        SELECT id, amount
        FROM orders
        WHERE user_id=? AND paid=0
        ORDER BY ROWID DESC
        LIMIT 1
        """,
        (uid,)
    ).fetchone()

    if old:
        order_id = old["id"]
        conn.execute(
            "UPDATE orders SET amount=? WHERE id=?",
            (total, order_id)
        )
    else:
        order_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO orders (id, user_id, amount, paid)
            VALUES (?, ?, ?, 0)
            """,
            (order_id, uid, total)
        )

        # ===============================
        # ORDER ITEMS (GROUP PRICE)
        # ===============================
        for g in groups.values():
            group_price = g["price"]
            for i in g["items"]:
                conn.execute(
                    """
                    INSERT INTO order_items
                    (order_id, item_id, file_id, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, i["id"], i["file_id"], group_price)
                )

    conn.commit()

    # ===============================
    # 🧪 DEBUG (KAR A CIRE)
    # ===============================
    dbg = "🤩 <b>GROUP ORDER CREATED</b>\n\n"

    for key, g in groups.items():
        title = g["items"][0]["title"]
        if key.startswith("single_"):
            dbg += f"• {title}\n"
        else:
            dbg += f"• {title} — 📦 Episodes: {len(g['items'])}\n"

    bot.send_message(uid, dbg, parse_mode="HTML")

    # ===============================
    # PAYMENT
    # ===============================
    tx_ref = f"{order_id}_{int(time.time())}"
    title = " / ".join({g["items"][0]["title"] for g in groups.values()})

    pay_url = create_flutterwave_payment(
        uid,
        tx_ref,
        total,
        title
    )

    if not pay_url:
        bot.send_message(uid, "❌ Payment error.")
        return

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

    bot.send_message(
        uid,
        f"""🧾 <b>GROUP CHECKOUT</b>

📦 <b>Items:</b> {sum(len(g['items']) for g in groups.values())}
💵 <b>Total:</b> ₦{total}

🆔 <b>Order ID:</b>
<code>{order_id}</code>

⚠️ <b>MUHIMMI:</b>
<i>Ajiye wannan Order ID sosai, Idan matsala ta faru tintubi admin tare da order id.</i>
""",
        parse_mode="HTML",
        reply_markup=kb
    )
# ================= ADMIN MANUAL SUPPORT SYSTEM =================

ADMIN_SUPPORT = {}

# ---------- /problem ----------
@bot.message_handler(commands=["problem"])
def admin_problem_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return

    ADMIN_SUPPORT[m.from_user.id] = {"stage": "menu"}

    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🔁 RESEND ORDER", callback_data="admin_resend"),
        InlineKeyboardButton("🎁 GIFT", callback_data="admin_gift")
    )

    bot.send_message(
        m.chat.id,
        "🧩 <b>ADMIN SUPPORT PANEL</b>\n\nZabi abin da kake so:",
        parse_mode="HTML",
        reply_markup=kb
    )


# ---------- RESEND ----------
@bot.callback_query_handler(func=lambda c: c.data == "admin_resend")
def admin_resend_start(c):
    if c.from_user.id != ADMIN_ID:
        return

    ADMIN_SUPPORT[c.from_user.id] = {"stage": "wait_order_id"}
    bot.answer_callback_query(c.id)
    bot.send_message(
        c.from_user.id,
        "🧾 Turo <b>ORDER ID</b>:",
        parse_mode="HTML"
    )


# ---------- GIFT ----------
@bot.callback_query_handler(func=lambda c: c.data == "admin_gift")
def admin_gift_start(c):
    if c.from_user.id != ADMIN_ID:
        return

    ADMIN_SUPPORT[c.from_user.id] = {"stage": "gift_user"}
    bot.answer_callback_query(c.id)
    bot.send_message(
        c.from_user.id,
        "👤 Turo <b>USER ID</b> wanda za a bawa kyauta:",
        parse_mode="HTML"
    )


# ---------- ADMIN FLOW ----------
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in ADMIN_SUPPORT)
def admin_support_flow(m):
    data = ADMIN_SUPPORT.get(m.from_user.id)
    if not data:
        return

    stage = data.get("stage")
    text = m.text.strip()

    # ===== RESEND ORDER =====
    if stage == "wait_order_id":

        row = conn.execute(
            "SELECT user_id, amount, paid FROM orders WHERE id=?",
            (text,)
        ).fetchone()

        # ❌ ORDER ID BAYA WUJUWA
        if not row:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "❌ <b>Order ID bai dace ba.</b>\nBabu wannan order a system.",
                parse_mode="HTML"
            )
            return

        # ⚠️ ORDER BAI BIYA BA
        if row["paid"] != 1:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "⚠️ <b>ORDER BAI BIYA BA</b>\nFaɗa wa user ya kammala biya.",
                parse_mode="HTML"
            )
            return

        user_id = row["user_id"]
        amount = row["amount"]

        items = conn.execute(
            """
            SELECT item_id
            FROM order_items
            WHERE order_id=?
            """,
            (text,)
        ).fetchall()

        # ❌ BA ITEMS
        if not items:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "⚠️ Wannan order ɗin babu items a cikinsa.\nDuba order_items table."
            )
            return

        item_ids = [r["item_id"] for r in items]

        ADMIN_SUPPORT[m.from_user.id] = {
            "stage": "resend_confirm",
            "user_id": user_id,
            "items": item_ids
        }

        bot.send_message(
            m.chat.id,
            f"""✅ <b>ORDER VERIFIED</b>

🆔 Order ID: <code>{text}</code>
👤 User ID: <code>{user_id}</code>
💰 Amount: ₦{amount}
🎬 Items: {len(item_ids)}

Tura <b>/sendall</b> domin a sake tura items.""",
            parse_mode="HTML"
        )
        return

    # ===== GIFT FLOW =====
    if stage == "gift_user":
        if not text.isdigit():
            bot.send_message(m.chat.id, "❌ Rubuta USER ID mai inganci.")
            return

        data["gift_user"] = int(text)
        data["stage"] = "gift_message"
        bot.send_message(
            m.chat.id,
            "✍️ Rubuta <b>MESSAGE</b> da user zai gani:",
            parse_mode="HTML"
        )
        return

    if stage == "gift_message":
        data["gift_message"] = text
        data["stage"] = "gift_item"
        bot.send_message(
            m.chat.id,
            "🎬 Rubuta <b>SUNAN ITEM</b> (title ko file name):",
            parse_mode="HTML"
        )
        return

    if stage == "gift_item":
        q = text.lower()

        row = conn.execute(
            """
            SELECT file_id, title
            FROM items
            WHERE title LIKE ? OR file_name LIKE ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (f"%{q}%", f"%{q}%")
        ).fetchone()

        if not row:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "❌ Ba a samu item a ITEMS table ba.",
                parse_mode="HTML"
            )
            return

        file_id, title = row["file_id"], row["title"]

        try:
            bot.send_video(data["gift_user"], file_id, caption=data["gift_message"])
        except:
            bot.send_document(data["gift_user"], file_id, caption=data["gift_message"])

        bot.send_message(
            m.chat.id,
            f"""🎁 <b>An kammala</b>

👤 User ID: <code>{data['gift_user']}</code>
🎬 Item: <b>{title}</b>""",
            parse_mode="HTML"
        )

        ADMIN_SUPPORT.pop(m.from_user.id, None)




import time

# ===== PAY ALL UNPAID (FINAL SAFE – CHECKOUT STYLE | PAYSTACK) =====
@bot.callback_query_handler(func=lambda c: c.data == "payall:")
def pay_all_unpaid(call):
    user_id = call.from_user.id

    # 1️⃣ DAUKO DUK UNPAID ITEMS
    rows = conn.execute(
        """
        SELECT
            oi.item_id,
            oi.file_id,
            oi.price,
            i.title AS item_title,
            i.group_key
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        JOIN items i ON i.id = oi.item_id
        WHERE o.user_id=? AND o.paid=0
        """,
        (user_id,)
    ).fetchall()

    if not rows:
        bot.answer_callback_query(call.id, "❌ Babu unpaid order")
        return

    # 🔒 KAR A SHIGA ITEM MARA FILE
    rows = [r for r in rows if r["file_id"] and int(r["price"] or 0) > 0]
    if not rows:
        bot.answer_callback_query(call.id, "❌ Babu item mai delivery")
        return

    # 🛑 HANA SIYAN ABIN DA AKA RIGA AKA BIYA
    filtered = []
    for r in rows:
        paid_before = conn.execute(
            """
            SELECT 1
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.user_id=? AND o.paid=1 AND oi.item_id=?
            LIMIT 1
            """,
            (user_id, r["item_id"])
        ).fetchone()

        if not paid_before:
            filtered.append(r)

    rows = filtered
    if not rows:
        bot.answer_callback_query(call.id, "❌ Ka riga ka sayi dukkan wadannan items")
        return

    # ================== TOTAL (CHECKOUT STYLE) ==================
    groups = {}

    for r in rows:
        price = int(r["price"] or 0)
        if price <= 0:
            continue

        key = r["group_key"] or f"single_{r['item_id']}"

        if key not in groups:
            groups[key] = {
                "price": price,
                "items": []
            }

        groups[key]["items"].append(r)

    total_amount = sum(g["price"] for g in groups.values())
    # ===========================================================

    if total_amount <= 0:
        bot.answer_callback_query(call.id, "❌ Amount error")
        return

    # 🛑 AMFANI DA UNPAID ORDER ƊAYA KAWAI
    old = conn.execute(
        """
        SELECT id
        FROM orders
        WHERE user_id=? AND paid=0
        ORDER BY ROWID DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    if not old:
        bot.answer_callback_query(call.id, "❌ Babu unpaid order da za a biya.")
        return

    order_id = old["id"]

    # 🔒 SABUNTA AMOUNT KAWAI
    conn.execute(
        "UPDATE orders SET amount=? WHERE id=?",
        (total_amount, order_id)
    )
    conn.commit()

    # ================== DEBUG (KAR A CIRE) ==================
    dbg = "🤩 <b>PAY-ALL ORDER READY</b>\n\n"

    for g in groups.values():
        items = g["items"]

        if items[0]["group_key"]:
            dbg += (
                f"• {items[0]['item_title']}\n"
                f"📦 Episodes: {len(items)}\n"
            )
        else:
            dbg += f"• {items[0]['item_title']}\n"

    bot.send_message(user_id, dbg, parse_mode="HTML")

    # ================== PAYSTACK ==================
    pay_url = create_paystack_payment(
        user_id,
        order_id,
        total_amount,
        "Pay All Orders"
    )

    if not pay_url:
        bot.send_message(user_id, "❌ Payment error.")
        return

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

    bot.send_message(
        user_id,
        f"""🧾 <b>PAY ALL ORDERS</b>

📦 <b>Groups:</b> {len(groups)}
💰 <b>Total:</b> ₦{int(total_amount)}

🆔 <b>Order ID:</b>
<code>{order_id}</code>

⚠️ <b>GARGADI:</b>
<i>Da fatan ka adana wannan Order ID sosai.</i>
<i>Idan wata matsala ta faru wajen biya ko delivery, tuntubi admin tare da Order ID.</i>
""",
        parse_mode="HTML",
        reply_markup=kb
    )

    bot.answer_callback_query(call.id)
# ===================== BUY ALL (CUSTOM IDS | PAYSTACK) =====================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("buyall:"))
def buy_all_handler(c):
    uid = c.from_user.id

    try:
        ids_raw = c.data.split("buyall:", 1)[1]
        item_ids = [int(x) for x in ids_raw.split(",") if x.strip().isdigit()]
    except:
        bot.answer_callback_query(c.id, "Invalid BUY ALL data.")
        return

    if not item_ids:
        bot.answer_callback_query(c.id, "No movies selected.")
        return

    items = []

    for iid in item_ids:
        row = conn.execute(
            "SELECT id, title, price, file_id FROM items WHERE id=?",
            (iid,)
        ).fetchone()

        # 🔒 KAR A SHIGA ITEM MARA FILE
        if row and row["file_id"]:
            items.append({
                "id": row["id"],
                "title": row["title"],
                "price": int(row["price"] or 0),
                "file_id": row["file_id"]
            })

    if not items:
        bot.answer_callback_query(c.id, "❌ No item mai delivery.")
        return

    _create_and_send_buyall(uid, items, c)


# ===================== COMMON BUY ALL LOGIC (PAYSTACK) =====================
def _create_and_send_buyall(uid, items, c):
    movie_count = len(items)
    total = sum(i["price"] for i in items)

    discount = int(total * 0.10) if movie_count >= 10 else 0
    final_total = total - discount

    # 🛑 KARIYA 1: OWNERSHIP (ITEM LEVEL ✔️)
    placeholders = ",".join("?" * len(items))
    owned = conn.execute(
        f"""
        SELECT 1 FROM user_movies
        WHERE user_id=? AND item_id IN ({placeholders})
        LIMIT 1
        """,
        (uid, *[i["id"] for i in items])
    ).fetchone()

    if owned:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎥PAID MOVIES", callback_data="my_movies"))
        bot.send_message(
            uid,
            "✅ <b>Ka riga ka mallaki wannan fim tini/n/n DUBA MY MOVIES\n"
            "Acen zaka rubuta sunansa za'a sake turama kyauta idan kana bukata.</b>",
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(c.id)
        return

    # 🛑 KARIYA 2: UNPAID ORDER MAI WANNAN ITEMS
    old = conn.execute(
        f"""
        SELECT o.id, o.amount
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.user_id=? AND o.paid=0
          AND oi.item_id IN ({placeholders})
        LIMIT 1
        """,
        (uid, *[i["id"] for i in items])
    ).fetchone()

    if old:
        order_id = old["id"]
        final_total = old["amount"]
    else:
        order_id = str(uuid.uuid4())

        conn.execute(
            """
            INSERT INTO orders (id, user_id, item_id, amount, paid)
            VALUES (?, ?, NULL, ?, 0)
            """,
            (order_id, uid, final_total)
        )

        for it in items:
            conn.execute(
                """
                INSERT INTO order_items
                (order_id, item_id, file_id, price)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, it["id"], it["file_id"], it["price"])
            )

        conn.commit()

    # 🧪 DEBUG
    dbg = "🤩 <b>BUY ALL ORDER CREATED</b>\n\n"
    for it in items:
        dbg += f"• {it['title']}\n"

    bot.send_message(uid, dbg, parse_mode="HTML")

    # ================== PAYSTACK ==================
    pay_url = create_paystack_payment(
        uid,
        order_id,
        final_total,
        "Buy All Movies"
    )

    if not pay_url:
        bot.answer_callback_query(c.id, "Payment error.")
        return

    # 🧾 SUMMARY
    lines = [f"🎬 {i['title']} — ₦{i['price']}" for i in items]
    summary = "\n".join(lines)

    text = f"""🧾 <b>BUY ALL ORDER</b>

{summary}

🎞 <b>Movies:</b> {movie_count}
💵 <b>Total:</b> ₦{total}
🏷 <b>Discount:</b> ₦{discount}
✅ <b>Final:</b> ₦{final_total}

🆔 <b>Order ID:</b>
<code>{order_id}</code>

⚠️ <b>MUHIMMI:</b>
<i>Ajiye wannan Order ID sosai.
Idan wata matsala ta faru (biyan kudi ko delivery),
ka tura wannan Order ID kai tsaye zuwa admin.</i>
"""

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel:{order_id}"))

    bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)
    bot.answer_callback_query(c.id)

import uuid
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===============================
# SERIES UPLOAD – FULL FLOW (FIXED)
# ===============================

series_sessions = {}

# ===============================
# COLLECT SERIES FILES (DM → MEMORY ONLY)
# ===============================
@bot.message_handler(
    content_types=["video", "document"],
    func=lambda m: m.from_user.id in series_sessions
)
def series_collect_files(m):
    uid = m.from_user.id
    sess = series_sessions.get(uid)

    if not sess or sess.get("stage") != "collect":
        return

    if m.video:
        dm_file_id = m.video.file_id
        file_name = m.video.file_name or "video.mp4"
    else:
        dm_file_id = m.document.file_id
        file_name = m.document.file_name or "file"

    sess["files"].append({
        "dm_file_id": dm_file_id,
        "file_name": file_name
    })

    bot.send_message(
        uid,
        f"✅ An karɓi: <b>{file_name}</b>",
        parse_mode="HTML"
    )


# ===============================
# DONE
# ===============================
@bot.message_handler(
    func=lambda m: (
        m.text
        and m.text.lower().strip() == "done"
        and m.from_user.id in series_sessions
    )
)
def series_done(m):
    uid = m.from_user.id
    sess = series_sessions.get(uid)

    if not sess or sess.get("stage") != "collect":
        return

    if not sess.get("files"):
        bot.send_message(uid, "❌ Babu fim da aka turo.")
        return

    text = "✅ <b>An karɓi fina-finai:</b>\n\n"
    for f in sess["files"]:
        text += f"• {f['file_name']}\n"

    text += "\n❓ <b>Akwai Hausa series a ciki?</b>"
    sess["stage"] = "ask_hausa"

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ EH", callback_data="hausa_yes"),
        InlineKeyboardButton("❌ A'A", callback_data="hausa_no")
    )

    bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)


# ===============================
# HAUSA CHOICE
# ===============================
@bot.callback_query_handler(
    func=lambda c: c.data in ["hausa_yes", "hausa_no"] and c.from_user.id in series_sessions
)
def handle_hausa_choice(c):
    uid = c.from_user.id
    sess = series_sessions.get(uid)
    bot.answer_callback_query(c.id)

    if c.data == "hausa_no":
        sess["hausa_matches"] = []
        sess["stage"] = "meta"
        bot.send_message(uid, "📸 Turo poster + caption (suna da farashi)")
        return

    sess["stage"] = "hausa_names"
    bot.send_message(uid, "✍️ Rubuta sunayen Hausa series (layi-layi)")


# ===============================
# RECEIVE HAUSA TITLES
# ===============================
@bot.message_handler(
    func=lambda m: (
        m.text
        and m.from_user.id in series_sessions
        and series_sessions[m.from_user.id].get("stage") == "hausa_names"
    )
)
def receive_hausa_titles(m):
    uid = m.from_user.id
    sess = series_sessions.get(uid)

    titles = [t.strip().lower() for t in m.text.split("\n") if t.strip()]
    matches = []

    for f in sess["files"]:
        fname = f["file_name"].lower()
        for t in titles:
            if t in fname:
                matches.append(f["file_name"])
                break

    sess["hausa_matches"] = matches
    sess["stage"] = "meta"

    bot.send_message(uid, "📸 Yanzu turo poster + caption (suna da farashi)")


# ===============================
# FINALIZE (UPLOAD + DB)
# ===============================
@bot.message_handler(
    content_types=["photo"],
    func=lambda m: m.from_user.id in series_sessions
)
def series_finalize(m):
    uid = m.from_user.id
    sess = series_sessions.get(uid)

    if sess.get("stage") != "meta":
        return

    try:
        title, raw_price = m.caption.strip().rsplit("\n", 1)

        # ===============================
        # ✅ KARI KAWAI: TUNA YADDA ADMIN YA RUBUTA FARASHI
        # ===============================
        has_comma = "," in raw_price
        price = raw_price.replace(",", "").strip()
        price = int(price)

    except:
        bot.send_message(uid, "❌ Caption bai dace ba.")
        return

    poster_file_id = m.photo[-1].file_id
    cur = conn.cursor()

    # CREATE SERIES
    cur.execute(
        "INSERT INTO series (title, price, poster_file_id) VALUES (?,?,?)",
        (title, price, poster_file_id)
    )
    series_id = cur.lastrowid

    item_ids = []
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # 🔑 GROUP KEY (DAYA GA DUK SERIES)
    group_key = str(uuid.uuid4())

    for f in sess["files"]:
        msg = bot.send_document(
            STORAGE_CHANNEL,
            f["dm_file_id"],
            caption=f["file_name"]
        )
        doc = msg.document or msg.video

        cur.execute(
            """
            INSERT INTO items
            (title, price, file_id, file_name, group_key, created_at, channel_msg_id, channel_username)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                title,
                price,
                doc.file_id,
                f["file_name"],
                group_key,
                created_at,
                msg.message_id,
                STORAGE_CHANNEL
            )
        )
        item_ids.append(cur.lastrowid)

    conn.commit()

    # ===============================
    # PUBLIC POST  ✅ (PRICE FORMAT SAFE)
    # ===============================
    display_price = f"{price:,}" if has_comma else str(price)
    ids_str = "_".join(str(i) for i in item_ids)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "🗃 Add to cart",
            callback_data=f"addcartdm:{ids_str}"
        ),
        InlineKeyboardButton(
            "💳 Buy now",
            url=f"https://t.me/{BOT_USERNAME}?start=groupitem_{ids_str}"
        )
    )

    bot.send_photo(
        CHANNEL,
        poster_file_id,
        caption=f"🎬 <b>{title}</b>\n💵Price:₦{display_price}",
        parse_mode="HTML",
        reply_markup=kb
    )

    bot.send_message(uid, "🎉 Series an adana dukka series lafiya.")
    del series_sessions[uid]



@bot.callback_query_handler(func=lambda c: True)
def handle_callback(c):
    uid = c.from_user.id
    data = c.data or ""




# ======================= MAIN CALLBACK HANDLER =======================



    # =====================
    # VIEW CART (SEND + SAVE MESSAGE)
    # =====================
    if data == "viewcart":
        text, kb = build_cart_view(uid)

        msg = bot.send_message(
            uid,
            text,
            reply_markup=kb,
            parse_mode="HTML"
        )

        cart_sessions[uid] = msg.message_id
        bot.answer_callback_query(c.id)
        return


    # =====================
    # REMOVE FROM CART (SINGLE + GROUP)
    # =====================
    if data.startswith("removecart:"):
        raw = data.split("removecart:", 1)[1]

        try:
            ids = [int(i) for i in raw.split("_") if i.isdigit()]
        except:
            bot.answer_callback_query(c.id, "❌ Invalid remove id")
            return

        if not ids:
            bot.answer_callback_query(c.id, "❌ There is nothing to remove.")
            return

        conn.executemany(
            "DELETE FROM cart WHERE user_id=? AND item_id=?",
            [(uid, i) for i in ids]
        )
        conn.commit()

        text, kb = build_cart_view(uid)

        if uid in cart_sessions:
            try:
                bot.edit_message_text(
                    text,
                    uid,
                    cart_sessions[uid],
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            except:
                pass

        bot.answer_callback_query(c.id, "🗑 you removed")
        return

    # =====================
    # CLEAR CART (DUKKA)
    # =====================
    if data == "clearcart":
        conn.execute(
            "DELETE FROM cart WHERE user_id=?",
            (uid,)
        )
        conn.commit()

        bot.answer_callback_query(c.id, "🧹 You clear cart")

        msg_id = cart_sessions.get(uid)
        if msg_id:
            text, kb = build_cart_view(uid)
            try:
                bot.edit_message_text(
                    chat_id=uid,
                    message_id=msg_id,
                    text=text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            except:
                pass
        return

    # ================= ADD ITEM(S) TO CART (DM / CHANNEL) =================
    if data.startswith("addcartdm:"):
        raw = data.split(":", 1)[1]

        try:
            # 🔑 Zai karbi:
            # addcartdm:7
            # addcartdm:1_2_3
            item_ids = [int(x) for x in raw.split("_") if x.isdigit()]
        except:
            bot.answer_callback_query(c.id, "❌ Invalid")
            return

        if not item_ids:
            bot.answer_callback_query(c.id, "❌ Invalid")
            return

        added = 0
        skipped = 0

        for item_id in item_ids:
            already = conn.execute(
                "SELECT 1 FROM cart WHERE user_id=? AND item_id=? LIMIT 1",
                (uid, item_id)
            ).fetchone()

            if already:
                skipped += 1
                continue

            conn.execute(
                "INSERT INTO cart (user_id, item_id) VALUES (?, ?)",
                (uid, item_id)
            )
            added += 1

        conn.commit()

        # ===== FEEDBACK =====
        if added and skipped:
            bot.answer_callback_query(
                c.id,
                f"✅ You added{added} | ⚠️ {skipped} to cart"
            )
        elif added:
            bot.answer_callback_query(
                c.id,
                f"✅ You added{added} item(s) a cart"
            )
        else:
            bot.answer_callback_query(
                c.id,
                "⚠️ All items are already in your cart."
            )

        return



    # ==================================================
    # CHECKOUT (GROUP-AWARE)
    # ==================================================
    if data == "checkout":
        rows = get_cart(uid)
        if not rows:
            bot.answer_callback_query(c.id, "❌ Your cart is empty.")
            return

        order_id = str(uuid.uuid4())
        total = 0
        groups = {}

        for item_id, title, price, file_id, group_key in rows:
            if not file_id:
                continue

            p = int(price or 0)
            if p <= 0:
                continue

            key = group_key or f"single_{item_id}"

            if key not in groups:
                groups[key] = {"price": p, "items": []}

            groups[key]["items"].append((item_id, title, file_id))

        if not groups:
            bot.answer_callback_query(
                c.id,
                "❌ There are no items in your cart available for delivery."
            )
            return

        for g in groups.values():
            total += g["price"]

        if total <= 0:
            bot.answer_callback_query(c.id, "❌ Farashi bai dace ba.")
            return

        # 1️⃣ CREATE ORDER
        conn.execute(
            """
            INSERT INTO orders (id, user_id, movie_id, amount, paid)
            VALUES (?, ?, NULL, ?, 0)
            """,
            (order_id, uid, total)
        )

        # 2️⃣ ORDER ITEMS
        for g in groups.values():
            for item_id, title, file_id in g["items"]:
                conn.execute(
                    """
                    INSERT INTO order_items
                    (order_id, item_id, file_id, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, item_id, file_id, g["price"])
                )

        conn.commit()
        clear_cart(uid)

        # DISPLAY
        msg = "🤩 <b>CHECKOUT ORDER CREATED</b>\n\n"
        for key, g in groups.items():
            items = g["items"]
            title = items[0][1]
            if not key.startswith("single_"):
                msg += f"• {title} — 📦 Series ({len(items)})\n"
            else:
                msg += f"• {title}\n"

        bot.send_message(uid, msg, parse_mode="HTML")

        # PAYMENT (PAYSTACK)
        pay_url = create_paystack_payment(
            uid,
            order_id,
            total,
            "Cart Order"
        )

        if not pay_url:
            bot.answer_callback_query(c.id, "❌ Payment error.")
            return

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
        kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

        bot.send_message(
            uid,
            f"""🧾 <b>CART ORDER</b>

💵 <b>Price:</b> ₦{total}
🎞 <b>Items:</b> {len(groups)}

🆔 <b>Order ID:</b>
<code>{order_id}</code>
""",
            parse_mode="HTML",
            reply_markup=kb
        )

        bot.answer_callback_query(c.id)
        return

    # ==================================================
    # BUY / BUYDM
    # ==================================================
    if data.startswith("buy:") or data.startswith("buydm:"):
        try:
            raw = data.split(":", 1)[1]
            item_ids = [int(x) for x in raw.split(",") if x.isdigit()]
        except:
            bot.answer_callback_query(c.id, "❌ Invalid buy data.")
            return

        if not item_ids:
            bot.answer_callback_query(c.id, "❌ No item selected.")
            return

        items = []
        for iid in item_ids:
            row = conn.execute(
                "SELECT id, title, price, file_id FROM items WHERE id=?",
                (iid,)
            ).fetchone()

            if row and row["file_id"]:
                items.append({
                    "id": row["id"],
                    "title": row["title"],
                    "price": int(row["price"] or 0),
                    "file_id": row["file_id"]
                })

        if not items:
            bot.answer_callback_query(
                c.id,
                "❌ Babu item mai delivery.",
                show_alert=True
            )
            return

        owned = conn.execute(
            f"""
            SELECT 1 FROM user_movies
            WHERE user_id=?
            AND item_id IN ({",".join("?" * len(item_ids))})
            LIMIT 1
            """,
            (uid, *item_ids)
        ).fetchone()

        if owned:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🎥 PAID MOVIES", callback_data="my_movies"))
            bot.send_message(
                uid,
                "✅ Ka riga ka karɓi wannan fim.",
                reply_markup=kb
            )
            bot.answer_callback_query(c.id)
            return

        old = conn.execute(
            """
            SELECT o.id, o.amount
            FROM orders o
            JOIN order_items oi ON oi.order_id=o.id
            WHERE o.user_id=? AND o.paid=0 AND oi.item_id=?
            LIMIT 1
            """,
            (uid, items[0]["id"])
        ).fetchone()

        if old:
            order_id = old["id"]
            total = old["amount"]
        else:
            order_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO orders (id, user_id, amount, paid) VALUES (?, ?, 0, 0)",
                (order_id, uid)
            )

            for it in items:
                conn.execute(
                    """
                    INSERT INTO order_items
                    (order_id, item_id, file_id, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, it["id"], it["file_id"], it["price"])
                )

            total = conn.execute(
                "SELECT SUM(price) FROM order_items WHERE order_id=?",
                (order_id,)
            ).fetchone()[0]

            conn.execute(
                "UPDATE orders SET amount=? WHERE id=?",
                (total, order_id)
            )
            conn.commit()

        bot.send_message(
            uid,
            "🤩 <b>BUY ORDER CREATED</b>",
            parse_mode="HTML"
        )

        title = items[0]["title"] if len(items) == 1 else f"{len(items)} Items"

        pay_url = create_paystack_payment(
            uid,
            order_id,
            total,
            title
        )

        if not pay_url:
            bot.send_message(uid, "❌ Payment error.")
            return

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
        kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

        bot.send_message(
            uid,
            f"""🧾 <b>{title}</b>

💵 ₦{total}
🆔 <code>{order_id}</code>
""",
            parse_mode="HTML",
            reply_markup=kb
        )

        bot.answer_callback_query(c.id)
        return

    # ================= MY MOVIES =================
    if data == "my_movies":
        kb = InlineKeyboardMarkup()

        kb.add(InlineKeyboardButton("🔍Check movie", callback_data="_resend_search_"))
        
        bot.send_message(
            uid,
            "🎥 <b>PAID MOVIES</b>\n"
            "Your previously purchased movies will be resent to you.\n\n"
            "🔍 If you want to search for a movie you’ve previously purchased, type its name or the first letter(s) of the title Example: (Dan) = Dan Tawaye:",
            parse_mode="HTML",
            reply_markup=kb
        )

        bot.answer_callback_query(c.id)
        return


    # ================= 🔍 RESEND SEARCH (STATE SETTER) =================
    if data == "_resend_search_":
        # ✅ NAN NE MATSALAR DA GYARA
        user_states[uid] = {"action": "_resend_search_"}

        bot.send_message(
            uid,
            "🔍 <b>Checking Mode</b>\n"
            "If you want to search for a movie you’ve previously purchased, type its name or the first letter(s) of the title Example: (Dan) = Dan Tawaye:",
            parse_mode="HTML"
        )

        bot.answer_callback_query(c.id)
        return

# ================= RESEND BY DAYS =================
    if data.startswith("resend:"):
        try:
            days = int(data.split(":")[1])
        except:
            bot.answer_callback_query(c.id, "❌ Invalid time.")
            return

        used = conn.execute(
            "SELECT COUNT(*) FROM resend_logs WHERE user_id=?",
            (uid,)
        ).fetchone()[0]

        if used >= 10:
            bot.send_message(
                uid,
                "⚠️ You’ve reached the maximum resend limit (10 times).\nPlease purchase the movie again to have it sent to you."
            )
            bot.answer_callback_query(c.id)
            return

        rows = conn.execute("""
            SELECT DISTINCT ui.item_id, i.file_id, i.title
            FROM user_movies ui
            JOIN items i ON i.id = ui.item_id
            WHERE ui.user_id = ?
              AND ui.created_at >= datetime('now', ?)
            ORDER BY ui.created_at ASC
        """, (uid, f"-{days} days")).fetchall()

        if not rows:
            bot.send_message(uid, "❌ Babu fim a wannan lokacin.")
            bot.answer_callback_query(c.id)
            return

        for item_id, file_id, title in rows:
            try:
                try:
                    bot.send_video(uid, file_id, caption=f"🎬 {title}")
                except:
                    bot.send_document(uid, file_id, caption=f"🎬 {title}")
            except Exception as e:
                print("Resend error:", e)

        conn.execute(
            "INSERT INTO resend_logs (user_id, used_at) VALUES (?, datetime('now'))",
            (uid,)
        )
        conn.commit()

        bot.send_message(
            uid,
            f"✅ The movies have been resent successfully. ({len(rows)}).\n⚠️The movies have been resent successfully,\n\nPlease note: you can't receive them up to 10 times."
        )
        bot.answer_callback_query(c.id)
        return


    # ================= RESEND ONE ITEM =================
    if data.startswith("resend_one:"):
        try:
            item_id = int(data.split(":", 1)[1])
        except:
            bot.answer_callback_query(c.id, "❌ Invalid movie.")
            return

        used = conn.execute(
            "SELECT COUNT(*) FROM resend_logs WHERE user_id=?",
            (uid,)
        ).fetchone()[0]

        if used >= 10:
            bot.send_message(
                uid,
                "⚠️ You’ve reached the maximum resend limit (10 times).\n"
                "Please purchase the movie again to have it sent to you."
            )
            bot.answer_callback_query(c.id)
            return

        row = conn.execute("""
            SELECT i.file_id, i.title
            FROM user_movies ui
            JOIN items i ON i.id = ui.item_id
            WHERE ui.user_id=? AND ui.item_id=?
            LIMIT 1
        """, (uid, item_id)).fetchone()

        if not row:
            bot.answer_callback_query(c.id, "❌ Ba a samu fim ba.")
            return

        file_id, title = row

        try:
            try:
                bot.send_video(uid, file_id, caption=f"🎬 {title}")
            except:
                bot.send_document(uid, file_id, caption=f"🎬 {title}")
        except:
            bot.answer_callback_query(c.id, "❌ Kuskure wajen tura fim.")
            return

        conn.execute(
            "INSERT INTO resend_logs (user_id, used_at) VALUES (?, datetime('now'))",
            (uid,)
        )
        conn.commit()

        bot.answer_callback_query(
            c.id,
            "✅ The movies have been resent successfully.\n⚠️ Please note: you can only receive them up to 10 times.”."
        )
        return

     # ================= START SERIES MODE =================
    if data == "start_series":
        series_sessions[uid] = {
            "stage": "collect",
            "files": [],
            "hausa_titles": [],
            "hausa_matches": []
        }

        bot.answer_callback_query(c.id)
        bot.send_message(
            uid,
            "📦 <b>Series mode ya fara</b>\n\n"
            "➡️ Turo dukkan fina-finai (video ko document)\n"
            "➡️ Idan ka gama, rubuta <b>done</b>",
            parse_mode="HTML"
        )
        return




    # =====================
    # OPEN UNPAID ORDERS (PAGE 0)
    # =====================
    if data == "myorders_new":
        text, kb = build_unpaid_orders_view(uid, page=0)
        bot.send_message(uid, text, reply_markup=kb, parse_mode="HTML")
        bot.answer_callback_query(c.id)
        return

    # =====================
    # UNPAID PAGINATION
    # =====================
    if data.startswith("unpaid_next:") or data.startswith("unpaid_prev:"):
        page = int(data.split(":")[1])
        text, kb = build_unpaid_orders_view(uid, page)
        bot.edit_message_text(
            chat_id=uid,
            message_id=c.message.message_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id)
        return

    # =====================
    # REMOVE SINGLE UNPAID
    # =====================
    if data.startswith("remove_unpaid:"):
        oid = data.split(":")[1]
        conn.execute(
            "DELETE FROM orders WHERE id=? AND user_id=? AND paid=0",
            (oid, uid)
        )
        conn.commit()

        text, kb = build_unpaid_orders_view(uid, page=0)
        bot.edit_message_text(
            chat_id=uid,
            message_id=c.message.message_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id, "❌ Removed order")
        return

    # ===============================
    # SERIES MODE (ADMIN ONLY)
    # ===============================
    if data == "groupitems":
        if uid != ADMIN_ID:
            return bot.answer_callback_query(c.id, "groupitems.")

        series_sessions[uid] = {
            "files": [],
            "stage": "collect"
        }

        bot.send_message(
            uid,
            "📺 <b>Series Mode ya fara</b>\n\n"
            "Ka fara turo videos/documents.\n"
            "Idan ka gama rubuta <b>Done</b>.",
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id)
        return
    # =====================
    # DELETE ALL UNPAID
    # =====================
    if data == "delete_unpaid":
        conn.execute(
            "DELETE FROM orders WHERE user_id=? AND paid=0",
            (uid,)
        )
        conn.commit()

        text, kb = build_unpaid_orders_view(uid, page=0)
        bot.edit_message_text(
            chat_id=uid,
            message_id=c.message.message_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id, "🗑 Duk an goge")
        return

    # =====================
    # OPEN PAID ORDERS (PAGE 0)
    # =====================
    if data == "paid_orders":
        text, kb = build_paid_orders_view(uid, page=0)
        bot.edit_message_text(
            chat_id=uid,
            message_id=c.message.message_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id)
        return

    #
    if data == "allfilms_prev":
        sess = allfilms_sessions.get(uid)
        if not sess:
            bot.answer_callback_query(c.id)
            return
        idx = sess["index"] - 1
        if idx >= 0:
            send_allfilms_page(uid, idx)
        bot.answer_callback_query(c.id)
        return


    # ================= FEEDBACK =================
    if data.startswith("feedback:"):
        parts = data.split(":")
        if len(parts) != 3:
            bot.answer_callback_query(c.id)
            return

        mood, order_id = parts[1], parts[2]

        # 1️⃣ Tabbatar order paid ne kuma na user
        row = conn.execute(
            "SELECT 1 FROM orders WHERE id=? AND user_id=? AND paid=1",
            (order_id, uid)
        ).fetchone()
        if not row:
            bot.answer_callback_query(c.id, "⚠️ Wannan order ba naka bane.", show_alert=True)
            return

        # 2️⃣ Hana feedback sau biyu
        exists = conn.execute(
            "SELECT 1 FROM feedbacks WHERE order_id=?",
            (order_id,)
        ).fetchone()
        if exists:
            bot.answer_callback_query(c.id, "Ka riga ka bada ra'ayi.", show_alert=True)
            return

        # 3️⃣ Ajiye feedback
        conn.execute(
            "INSERT INTO feedbacks (order_id, user_id, mood) VALUES (?,?,?)",
            (order_id, uid, mood)
        )
        conn.commit()

        # 4️⃣ Samo sunan user
        try:
            chat = bot.get_chat(uid)
            fname = chat.first_name or "User"
        except:
            fname = "User"

        admin_messages = {
            "very": (
                "😘 Gaskiya na ji daɗin siyayya da bot ɗinku\n"
                "Alhamdulillah wannan bot yana sauƙaƙa siyan fim sosai 😇\n"
                "Muna godiya ƙwarai 🥰🙏"
            ),
            "good": (
                "🙂 Na ji daɗin siyayya\n"
                "Tsarin bot ɗin yana da kyau kuma mai sauƙi"
            ),
            "neutral": (
                "😓 Ban gama fahimtar bot ɗin sosai ba\n"
                "Amma ina ganin yana da amfani"
            ),
            "angry": (
                "🤬 Wannan bot yana bani ciwon kai\n"
                "Akwai buƙatar ku gyara tsarin kasuwancin ku"
            )
        }

        user_replies = {
            "very": "🥰 Mun gode sosai! Za mu ci gaba da faranta maka rai Insha Allah.",
            "good": "😊 Mun gode da ra'ayinka! Za mu ƙara inganta tsarin.",
            "neutral": "🤍 Mun gode. Idan kana da shawara, muna maraba da ita.",
            "angry": "🙏 Muna baku haƙuri akan bacin ran da kuka samu. Za mu gyara Insha Allah."
        }

        # 5️⃣ Tura wa ADMIN
        admin_text = (
            f"📣 FEEDBACK RECEIVED\n\n"
            f"👤 User: {fname}\n"
            f"🆔 ID: {uid}\n"
            f"📦 Order: {order_id}\n\n"
            f"{admin_messages.get(mood, mood)}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text)
        except:
            pass

        # 6️⃣ Goge inline buttons
        try:
            bot.edit_message_reply_markup(
                chat_id=c.message.chat.id,
                message_id=c.message.message_id,
                reply_markup=None
            )
        except:
            pass

        bot.answer_callback_query(c.id)
        bot.send_message(uid, user_replies.get(mood, "Mun gode da ra'ayinka 🙏"))
        return





    # =====================
    # ADD MOVIE (ADMIN)
    # =====================
    if data == "addmovie":
        if uid != ADMIN_ID:
            bot.answer_callback_query(c.id, "Only admin.")
            return
        admin_states[uid] = {"state": "add_movie_wait_file"}
        bot.send_message(uid, "Turo film.")
        bot.answer_callback_query(c.id)
        return
    # =====================
    # WEEKLY BUY
    # =====================
    if data.startswith("weekly_buy:"):
        try:
            idx = int(data.split(":",1)[1])
        except:
            bot.answer_callback_query(c.id, "Invalid.")
            return

        row = conn.execute(
            "SELECT items FROM weekly ORDER BY id DESC LIMIT 1"
        ).fetchone()

        items = json.loads(row[0] or "[]")
        item = items[idx]

        title = item["title"]
        price = int(item["price"])

        remaining_price, applied_sum, applied_ids = apply_credits_to_amount(uid, price)
        order_id = create_single_order_for_weekly(uid, title, remaining_price)

        bot.send_message(uid, f"Oda {order_id} – ₦{remaining_price}")
        bot.answer_callback_query(c.id)
        return

    # ======================================================
    # ================= ALL FILMS OPEN =====================
    # ======================================================
    if data == "all_films":
        rows = build_allfilms_rows()
        if not rows:
            bot.answer_callback_query(c.id, "❌ Babu fim a DB")
            return

        pages = paginate(rows, PER_PAGE)

        allfilms_sessions[uid] = {
            "pages": pages,
            "index": 0,
            "last_msg": c.message.message_id
        }

        send_allfilms_page(uid, 0)
        bot.answer_callback_query(c.id)
        return

    # ======================================================
    # ================= ALL FILMS NEXT =====================
    # ======================================================
    if data == "allfilms_next":
        sess = allfilms_sessions.get(uid)
        if not sess:
            bot.answer_callback_query(c.id)
            return

        send_allfilms_page(uid, sess["index"] + 1)
        bot.answer_callback_query(c.id)
        return

    # ======================================================
    # ================= ALL FILMS PREV =====================
    # ======================================================
    if data == "allfilms_prev":
        sess = allfilms_sessions.get(uid)
        if not sess:
            bot.answer_callback_query(c.id)
            return

        send_allfilms_page(uid, sess["index"] - 1)
        bot.answer_callback_query(c.id)
        return


 # Map new erase_all_data callback to existing erase_data handler (compat shim)
    if data == "erase_all_data":
        data = "erase_data"



    # NEW WEAK UPDATE SYSTEM
    if data == "weak_update":
        start_weak_update(msg=c.message)
        return

    # checkjoin: after user clicks I've Joined
    if data == "checkjoin":
        try:
            if check_join(uid):
                bot.answer_callback_query(
                    callback_query_id=c.id,
                    text=tr_user(uid, "joined_ok", default="✔ Channel joined!")
                )

                bot.send_message(
                    uid,
                    "Shagon Algaita Movie Store na kawo maka zaɓaɓɓun fina-finai masu inganci. "
                    "Mun tace su tsaf daga ɗanyen kaya, mun ware mafi kyau kawai. "
                    "Duk fim ɗin da ka siya a nan, tabbas ba za mu ba ka kunya ba.",
                    reply_markup=user_main_menu(uid)
                )

                bot.send_message(
                    uid,
                    "Sannu da zuwa!\n Duk fim din da kakeso ka shiga channel dinmu ka duba shi?:",
                    reply_markup=reply_menu(uid)
                )

            else:
                bot.answer_callback_query(
                    callback_query_id=c.id,
                    text=tr_user(uid, "not_joined", default="❌ You are not logged in.")
                )

        except Exception as e:
            print("checkjoin callback error:", e)

        return

    # go home
    if data == "go_home":
        try:
            bot.answer_callback_query(callback_query_id=c.id)
            bot.send_message(
                uid,
                "Sannu! Ga zabuka, domin fara wa:",
                reply_markup=reply_menu(uid)
            )
        except Exception as e:
            print("go_home error:", e)
        return
    



    # Support Help -> Open admin DM directly (NO messages to admin, NO notifications)
    if data == "support_help":
        try:
            bot.answer_callback_query(callback_query_id=c.id)
        except:
            pass

        if ADMIN_USERNAME:
            # Open admin DM directly
            bot.send_message(uid, f"👉 Tuntuɓi admin kai tsaye: https://t.me/{ADMIN_USERNAME}")
        else:
            bot.send_message(uid, "Admin username bai sa ba. Tuntubi support.")
        return


    # fallback
    try:
        bot.answer_callback_query(callback_query_id=c.id)
    except:
        pass




# ========== /myorders command (SAFE – ITEMS BASED) ==========
@bot.message_handler(commands=["myorders"])
def myorders(message):
    uid = message.from_user.id

    rows = conn.execute(
        """
        SELECT id, amount, paid
        FROM orders
        WHERE user_id=?
        ORDER BY rowid DESC
        """,
        (uid,)
    ).fetchall()

    if not rows:
        bot.reply_to(
            message,
            "❌ You don’t have any orders yet.",
            reply_markup=reply_menu(uid)
        )
        return

    txt = "🛒 <b>Your Orders</b>\n\n"

    for row in rows:
        oid = row["id"]
        amount = int(row["amount"] or 0)
        paid = row["paid"]

        # 🔒 SAFE COUNT (order_items ONLY)
        info = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM order_items
            WHERE order_id=?
            """,
            (oid,)
        ).fetchone()

        items_count = info["cnt"] if info else 0

        # 🛡 KARIYA: idan babu item kwata-kwata, tsallake
        if items_count <= 0:
            continue

        # 🏷 LABEL
        label = "1 item" if items_count == 1 else f"Group items ({items_count})"

        txt += (
            f"🆔 <code>{oid}</code>\n"
            f"📦 {label}\n"
            f"💰 Amount: ₦{amount}\n"
            f"💳 Status: {'✅ Paid' if paid else '❌ Unpaid'}\n\n"
        )

    bot.send_message(
        uid,
        txt,
        parse_mode="HTML",
        reply_markup=reply_menu(uid)
    )

# ========== ADMIN FILE UPLOAD (ITEMS ONLY, FIXED) ==========
@bot.message_handler(content_types=["photo", "video", "document"])
def file_upload(message):

    # 1️⃣ IDAN ADMIN NA CIKIN WANI FLOW
    if message.from_user.id in ADMINS and admin_states.get(message.from_user.id):
        try:
            admin_inputs(message)
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ admin_inputs error: {e}")
        return

    # 2️⃣ IDAN POST YA FITO DAGA CHANNEL
    chat_username = getattr(message.chat, "username", None)
    if chat_username and ("@" + chat_username).lower() == CHANNEL.lower():

        caption = message.caption or ""
        title, price = parse_caption_for_title_price(caption)

        if not title:
            title = f"Item {uuid.uuid4().hex[:6]}"
            price = 0

        # FILE ID
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.content_type == "video":
            file_id = message.video.file_id
            file_type = "video"
        else:
            file_id = message.document.file_id
            file_type = "document"

        try:
            exists = conn.execute(
                "SELECT id FROM items WHERE title=? COLLATE NOCASE",
                (title,)
            ).fetchone()

            if exists:
                bot.send_message(
                    ADMIN_ID,
                    f"⚠️ ITEM YA RIGA YA WUJU\n<b>{title}</b>",
                    parse_mode="HTML"
                )
                return

            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            channel_msg_id = message.message_id

            cur = conn.execute(
                """
                INSERT INTO items
                (title, price, file_id, file_type, created_at, channel_msg_id)
                VALUES (?,?,?,?,?,?)
                """,
                (title, price or 0, file_id, file_type, now, channel_msg_id)
            )
            conn.commit()

            item_id = cur.lastrowid

            bot.send_message(
                ADMIN_ID,
                f"✅ <b>ITEM AN ADANA</b>\n\n"
                f"🆔 ID: <code>{item_id}</code>\n"
                f"🎬 Title: {title}\n"
                f"💰 Price: ₦{price}",
                parse_mode="HTML"
            )

        except Exception as e:
            bot.send_message(
                ADMIN_ID,
                f"❌ ERROR YAYIN SAVE ITEM:\n{e}"
            )

        return

    # 3️⃣ IDAN ADMIN YA TURA FILE A PRIVATE
    if message.from_user.id != ADMIN_ID:
        return

    caption = message.caption or ""
    title, price = parse_caption_for_title_price(caption)

    if not title:
        title = f"Item {uuid.uuid4().hex[:6]}"
        price = 0

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.content_type == "video":
        file_id = message.video.file_id
        file_type = "video"
    else:
        file_id = message.document.file_id
        file_type = "document"

    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        cur = conn.execute(
            """
            INSERT INTO items
            (title, price, file_id, file_type, created_at)
            VALUES (?,?,?,?,?)
            """,
            (title, price or 0, file_id, file_type, now)
        )
        conn.commit()

        item_id = cur.lastrowid

        post_caption = (
            f"🎬 <b>{title}</b>\n"
            f"💵 ₦{price}\n"
            f"Danna maɓalli domin saya ko saka a cart."
        )

        markup = item_buttons_inline(item_id)

        if file_type == "photo":
            sent = bot.send_photo(
                CHANNEL,
                file_id,
                caption=post_caption,
                parse_mode="HTML",
                reply_markup=markup
            )
        elif file_type == "video":
            sent = bot.send_video(
                CHANNEL,
                file_id,
                caption=post_caption,
                parse_mode="HTML",
                reply_markup=markup
            )
        else:
            sent = bot.send_document(
                CHANNEL,
                file_id,
                caption=post_caption,
                parse_mode="HTML",
                reply_markup=markup
            )

        conn.execute(
            "UPDATE items SET channel_msg_id=? WHERE id=?",
            (sent.message_id, item_id)
        )
        conn.commit()

        bot.send_message(
            ADMIN_ID,
            f"✅ <b>AN TURA ZUWA CHANNEL</b>\n"
            f"🆔 Item ID: <code>{item_id}</code>",
            parse_mode="HTML"
        )

    except Exception as e:
        bot.send_message(
            ADMIN_ID,
            f"❌ POST FAILED:\n{e}"
        )




# ================== SALES REPORT SYSTEM (ITEMS BASED) ==================

import threading
import time
from datetime import datetime, timedelta


def _ng_now():
    return datetime.utcnow() + timedelta(hours=1)


def _last_day_of_month(dt):
    next_month = dt.replace(day=28) + timedelta(days=4)
    return (next_month - timedelta(days=next_month.day)).day


# ================= WEEKLY REPORT =================
def send_weekly_sales_report():
    try:
        if not PAYMENT_NOTIFY_GROUP:
            return

        now = _ng_now()
        week_ago = now - timedelta(days=7)

        rows = conn.execute(
            """
            SELECT
                oi.item_id,
                COUNT(*) AS qty,
                SUM(COALESCE(oi.price,0)) AS total
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.paid = 1
              AND o.created_at >= ?
            GROUP BY oi.item_id
            """,
            (week_ago.strftime("%Y-%m-%d %H:%M:%S"),)
        ).fetchall()

        if not rows:
            bot.send_message(
                PAYMENT_NOTIFY_GROUP,
                "📊 WEEKLY SALES REPORT\n\nBabu siyarwa."
            )
            return

        msg = "📊 WEEKLY SALES REPORT\n\n"
        grand = 0

        for item_id, qty, total in rows:
            row = conn.execute(
                "SELECT title FROM items WHERE id=?",
                (item_id,)
            ).fetchone()

            title = row["title"] if row else f"ITEM {item_id}"
            total = int(total or 0)
            grand += total

            msg += f"• {title} ({qty}) — ₦{total}\n"

        msg += f"\n💰 Total: ₦{grand}"
        bot.send_message(PAYMENT_NOTIFY_GROUP, msg)

    except Exception as e:
        print("weekly report error:", e)


# ================= MONTHLY REPORT =================
def send_monthly_sales_report():
    try:
        if not PAYMENT_NOTIFY_GROUP:
            return

        now = _ng_now()
        first_day = now.replace(day=1, hour=0, minute=0, second=0)

        rows = conn.execute(
            """
            SELECT
                oi.item_id,
                COUNT(*) AS qty,
                SUM(COALESCE(oi.price,0)) AS total
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.paid = 1
              AND o.created_at >= ?
            GROUP BY oi.item_id
            """,
            (first_day.strftime("%Y-%m-%d %H:%M:%S"),)
        ).fetchall()

        if not rows:
            bot.send_message(
                PAYMENT_NOTIFY_GROUP,
                "📊 MONTHLY SALES REPORT\n\nBabu siyarwa."
            )
            return

        msg = "📊 MONTHLY SALES REPORT\n\n"
        grand = 0

        for item_id, qty, total in rows:
            row = conn.execute(
                "SELECT title FROM items WHERE id=?",
                (item_id,)
            ).fetchone()

            title = row["title"] if row else f"ITEM {item_id}"
            total = int(total or 0)
            grand += total

            msg += f"• {title} ({qty}) — ₦{total}\n"

        msg += f"\n💰 Total: ₦{grand}"
        bot.send_message(PAYMENT_NOTIFY_GROUP, msg)

    except Exception as e:
        print("monthly report error:", e)


# ================= SCHEDULER =================
def sales_report_scheduler():
    weekly_sent = False
    monthly_sent = False

    while True:
        now = _ng_now()

        # Friday 23:50
        if now.weekday() == 4 and now.hour == 23 and now.minute == 50:
            if not weekly_sent:
                send_weekly_sales_report()
                weekly_sent = True
        else:
            weekly_sent = False

        # Last day of month 23:50
        if now.day == _last_day_of_month(now) and now.hour == 23 and now.minute == 50:
            if not monthly_sent:
                send_monthly_sales_report()
                monthly_sent = True
        else:
            monthly_sent = False

        time.sleep(20)

# ▶️ START BACKGROUND REPORT THREAD
# ================== START SERVER ==================
if __name__ == "__main__":

    if BOT_MODE == "webhook":
        print("🌐 Running in WEBHOOK mode")

        try:
            bot.remove_webhook()
            bot.set_webhook(f"{WEBHOOK_URL}/telegram")
            print("✅ Telegram webhook set successfully")
        except Exception as e:
            print("❌ Failed to set webhook:", e)

        port = int(os.environ.get("PORT", 10000))
        print(f"🚀 Flask server running on port {port}")
        app.run(host="0.0.0.0", port=port)

    else:
        # fallback (local testing only)
        print("🤖 Running in POLLING mode")
        bot.infinity_polling(skip_pending=True)

