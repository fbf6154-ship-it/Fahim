import os
import threading
import time
import requests
from flask import Flask
import telebot
from telebot import types

# --- ⚙️ CONFIGURATION ---
BOT_TOKEN = os.environ.get("TOKEN", "8802176680:AAFmyUJ1XIHFTVtXyLv3xcP6JdoEzj6c6JA")
ADMIN_ID = "7166927766"  # আপনার এডমিন আইডি
DEFAULT_CHANNEL_ID = "@FHx_Technical_Creator"
DEFAULT_CHANNEL_URL = "https://t.me/FHx_Technical_Creator"

# Firebase Realtime Database URL
FIREBASE_URL = "https://tournament-ace22-default-rtdb.asia-southeast1.firebasedatabase.app"

# ⚡ মাল্টি-থ্রেডেড টেলিগ্রাম ইঞ্জিন
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True, num_threads=30)

# ⚡ HTTP Connection Pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=30)
session.mount('https://', adapter)
session.mount('http://', adapter)

# --- ⚡ IN-MEMORY TURBO CACHE ---
CACHE = {
    "settings": {
        "lang": "bn",
        "currency": "bKash",
        "photo": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800",
        "support": "☎️ <b>উইথড্র দেওয়ার ২৪ ঘন্টার মধ্যে পেমেন্ট না পেলে যোগাযোগ করুন:</b>\n👤 @Promoter_from_bd\n\n📢 <b>উইথড্র দেওয়ার পর অবশ্যই নক দিবেন:</b> @FHx_Technical_Creator",
        "min_withdraw": 15.0,
        "max_withdraw": 100.0,
        "refer_bonus": 2.0,
        "daily_bonus": 0.1,
        "bonus_cooldown": 24,
        "withdraw_status": True,
        "maintenance": False,
        "total_withdrawn": 0.0
    },
    "channels": {}
}

# --- 🌐 FLASK KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ Telegram Premium Refer Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 🗄️ FIREBASE DATABASE FUNCTIONS ---
def load_initial_cache():
    try:
        res = session.get(f"{FIREBASE_URL}/settings.json", timeout=4)
        if res.status_code == 200 and res.json() and isinstance(res.json(), dict):
            CACHE["settings"].update(res.json())
        
        res2 = session.get(f"{FIREBASE_URL}/channels.json", timeout=4)
        if res2.status_code == 200 and res2.json():
            data = res2.json()
            if isinstance(data, dict):
                CACHE["channels"] = data
            elif isinstance(data, list):
                CACHE["channels"] = {str(i): v for i, v in enumerate(data) if isinstance(v, dict)}
    except Exception as e:
        print(f"Cache init error: {e}")

load_initial_cache()

def get_settings():
    return CACHE["settings"]

def update_settings(data):
    CACHE["settings"].update(data)
    threading.Thread(target=lambda: session.patch(f"{FIREBASE_URL}/settings.json", json=data, timeout=5)).start()

def get_user(user_id):
    try:
        res = session.get(f"{FIREBASE_URL}/users/{user_id}.json", timeout=3)
        data = res.json()
        return data if isinstance(data, dict) else {}
    except:
        return {}

def update_user(user_id, data):
    threading.Thread(target=lambda: session.patch(f"{FIREBASE_URL}/users/{user_id}.json", json=data, timeout=5)).start()

def get_all_users():
    try:
        res = session.get(f"{FIREBASE_URL}/users.json", timeout=4)
        data = res.json()
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return {str(i): v for i, v in enumerate(data) if v is not None}
        return {}
    except:
        return {}

def save_withdrawal(w_id, data):
    threading.Thread(target=lambda: session.put(f"{FIREBASE_URL}/withdrawals/{w_id}.json", json=data, timeout=5)).start()

def get_withdrawal(w_id):
    try:
        res = session.get(f"{FIREBASE_URL}/withdrawals/{w_id}.json", timeout=3)
        return res.json()
    except:
        return None

# --- 📢 CHANNELS MANAGEMENT ---
def get_channels():
    if not CACHE["channels"]:
        return {"default": {"channel_id": DEFAULT_CHANNEL_ID, "url": DEFAULT_CHANNEL_URL, "title": "🔗 Join Channel 1"}}
    return CACHE["channels"]

def save_channel_to_db(ch_id, url, title):
    clean_key = ch_id.replace("@", "").replace("-", "_").replace(".", "_")
    payload = {"channel_id": ch_id, "url": url, "title": title}
    CACHE["channels"][clean_key] = payload
    threading.Thread(target=lambda: session.put(f"{FIREBASE_URL}/channels/{clean_key}.json", json=payload, timeout=5)).start()
    return True

def remove_channel_from_db(ch_id):
    clean_key = ch_id.replace("@", "").replace("-", "_").replace(".", "_")
    if clean_key in CACHE["channels"]:
        del CACHE["channels"][clean_key]
    threading.Thread(target=lambda: session.delete(f"{FIREBASE_URL}/channels/{clean_key}.json", timeout=5)).start()
    return True

# --- 🔍 ফিক্সড এবং শক্তিশালী MEMBERSHIP CHECK ---
def is_joined(user_id):
    channels = get_channels()
    if not channels:
        channels = {"default": {"channel_id": DEFAULT_CHANNEL_ID}}

    for key, ch in channels.items():
        ch_id = ch.get("channel_id") if isinstance(ch, dict) else ch
        if not ch_id or not isinstance(ch_id, str):
            continue
        try:
            member = bot.get_chat_member(ch_id.strip(), int(user_id))
            # creator, administrator, member অথবা restricted (joined) হলে পাস
            if member.status in ['member', 'administrator', 'creator', 'restricted']:
                continue
            else:
                return False
        except Exception as e:
            print(f"⚠️ [Verification Error] Channel: {ch_id} | User: {user_id} | Error: {e}")
            # মনে রাখবেন: বট চ্যানেলে এডমিন না থাকলে এই ইরোর আসবে!
            return False
    return True

# --- 🌐 TEXTS ---
TEXTS = {
    "bn": {
        "access_title": "🔒 <b>Access Restricted</b>\n━━━━━━━━━━━━━━━━━━━━━\n⚠️ <b>You must join all our channels to unlock bot features.</b>\n\n📢 <b>Subscribe to every channel using the buttons below.</b>\n\n✅ <b>After joining all channels, tap the Verify Membership button.</b>",
        "verify_btn": "✅ Verify Membership",
        "verify_success": "🎉 <b>Membership Verified! Welcome to the main menu.</b>",
        "verify_fail": "❌ আপনি এখনো চ্যানেলে জয়েন করেননি! সব চ্যানেলে জয়েন করে আবার চেষ্টা করুন।",
        "btn_bal": "🖥️ একাউন্ট",
        "btn_ref": "⚡ রেফারেল",
        "btn_with": "💲 উইথড্র",
        "btn_wall": "💳 ওয়ালেট",
        "btn_bonus": "🎁 বোনাস",
        "btn_stat": "📊 স্ট্যাটাস",
        "btn_supp": "SUPPORT 💸",
        "set_wallet_prompt": "📝 <b>অনুগ্রহ করে আপনার বিকাশ/নগদ নম্বর লিখুন:</b>",
        "wallet_saved": "✅ <b>আপনার ওয়ালেট সফলভাবে সেট হয়েছে:</b>",
        "min_with_err": "❌ সর্বনিম্ন উইথড্র পরিমাণ {min_w} {curr}।",
        "with_prompt": "💰 <b>সর্বনিম্ন:</b> {min_w} {curr}\n🚀 <b>বর্তমান ব্যালেন্স:</b> {bal:.2f} {curr}\n\n📝 <b>আপনি কত টাকা উইথড্র করতে চান পরিমাণ লিখুন:</b>",
        "with_success": "উইথড্র রিকোয়েস্ট সফল হয়েছে ✅\n\n💰 <b>পরিমাণ:</b> {amt} {curr}\n⏳ <b>পেমেন্ট স্ট্যাটাস:</b> Pending\n💳 <b>ওয়ালেট:</b> <code>{wal}</code>\n🔖 <b>রিকোয়েস্ট আইডি:</b> <code>{wid}</code>\n\n<i>এডমিন শীঘ্রই আপনার পেমেন্ট ভেরিফাই করে পাঠিয়ে দিবে।</i>"
    },
    "en": {
        "access_title": "🔒 <b>Access Restricted</b>\n━━━━━━━━━━━━━━━━━━━━━\n⚠️ <b>You must join all our channels to unlock bot features.</b>\n\n📢 <b>Subscribe to every channel using the buttons below.</b>\n\n✅ <b>After joining all channels, tap the Verify Membership button.</b>",
        "verify_btn": "✅ Verify Membership",
        "verify_success": "🎉 <b>Membership Verified! Welcome to the main menu.</b>",
        "verify_fail": "❌ You haven't joined all channels yet! Please join first.",
        "btn_bal": "💰 BALANCE",
        "btn_ref": "🧑‍🤝‍🧑 REFERRAL",
        "btn_with": "📥 WITHDRAW",
        "btn_wall": "💳 WALLET",
        "btn_bonus": "🎁 BONUS",
        "btn_stat": "🔋 STATISTICS",
        "btn_supp": "SUPPORT 💸",
        "set_wallet_prompt": "📝 <b>Please Enter Your Bkash/Nagad Number:</b>",
        "wallet_saved": "✅ <b>Wallet successfully updated to:</b>",
        "min_with_err": "❌ Minimum withdrawal amount is {min_w} {curr}.",
        "with_prompt": "💰 <b>Minimum:</b> {min_w} {curr}\n🚀 <b>Balance:</b> {bal:.2f} {curr}\n\n📝 <b>Enter the amount you want to withdraw:</b>",
        "with_success": "Withdrawal Request Successful ✅\n\n💰 <b>Amount:</b> {amt} {curr}\n⏳ <b>Payment Status:</b> Pending\n💳 <b>Wallet:</b> <code>{wal}</code>\n🔖 <b>Request ID:</b> <code>{wid}</code>\n\n<i>Admin will verify and process your payment shortly.</i>"
    }
}

def get_t(key):
    lang = CACHE["settings"].get("lang", "bn")
    return TEXTS.get(lang, TEXTS["bn"]).get(key, "")

# --- ⌨️ KEYBOARDS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(get_t("btn_bal"), get_t("btn_ref"))
    markup.add(get_t("btn_wall"), get_t("btn_with"))
    markup.add(get_t("btn_supp"), get_t("btn_stat"))
    markup.add(get_t("btn_bonus"))
    return markup

def join_keyboard():
    markup = types.InlineKeyboardMarkup()
    channels = get_channels()
    
    has_btn = False
    if isinstance(channels, dict):
        for key, ch in channels.items():
            if isinstance(ch, dict) and "url" in ch and isinstance(ch["url"], str):
                url = ch["url"].strip()
                if url.startswith("http://") or url.startswith("https://") or url.startswith("tg://"):
                    btn_title = ch.get("title", "🔗 Join Channel")
                    markup.add(types.InlineKeyboardButton(btn_title, url=url))
                    has_btn = True
        
    if not has_btn:
        markup.add(types.InlineKeyboardButton("🔗 Join Channel 1", url=DEFAULT_CHANNEL_URL))
        
    verify_text = get_t("verify_btn") or "✅ Verify Membership"
    markup.add(types.InlineKeyboardButton(verify_text, callback_data="verify_membership"))
    return markup

# --- 🚀 START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = str(message.chat.id)
        settings = get_settings()

        if settings.get("maintenance") and user_id != ADMIN_ID:
            bot.send_message(user_id, "🛠️ <b>Bot is currently under maintenance. Please come back later!</b>")
            return

        text_split = message.text.split()
        user_data = get_user(user_id)

        if user_data.get("status") == "banned":
            bot.send_message(user_id, "🚫 <b>You are banned from using this bot!</b>")
            return

        first_name = message.from_user.first_name or "User"
        username = message.from_user.username or "No Username"

        if not user_data:
            new_data = {
                "name": first_name,
                "username": username,
                "balance": 0.0,
                "ref_count": 0,
                "wallet": "Not Set",
                "referred_by": None,
                "bonus_claimed": False,
                "last_bonus": 0,
                "status": "active"
            }
            if len(text_split) > 1 and text_split[1] != user_id:
                new_data["referred_by"] = text_split[1]
            update_user(user_id, new_data)

        if is_joined(user_id):
            bot.send_message(user_id, "🎉 <b>স্বাগতম! নিচের মেনু থেকে অপশন সিলেক্ট করুন:</b>", reply_markup=main_menu())
            return

        welcome_text = get_t("access_title")
        img_url = settings.get("photo")

        sent = False
        if img_url and (img_url.startswith("http://") or img_url.startswith("https://")):
            try:
                bot.send_photo(user_id, photo=img_url, caption=welcome_text, reply_markup=join_keyboard())
                sent = True
            except Exception:
                sent = False

        if not sent:
            bot.send_message(user_id, welcome_text, reply_markup=join_keyboard())

    except Exception as e:
        print(f"Start command error: {e}")
        bot.send_message(message.chat.id, "🎉 <b>Welcome!</b>", reply_markup=main_menu())

# --- 🔍 VERIFY CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_callback(call):
    user_id = str(call.from_user.id)
    if is_joined(user_id):
        user_data = get_user(user_id)
        refer_bonus = float(CACHE["settings"].get("refer_bonus", 2.0))
        currency = CACHE["settings"].get("currency", "bKash")
        
        referrer_id = user_data.get("referred_by")
        if referrer_id and not user_data.get("bonus_claimed"):
            ref_data = get_user(referrer_id)
            if ref_data:
                new_balance = float(ref_data.get("balance", 0)) + refer_bonus
                new_ref_count = int(ref_data.get("ref_count", 0)) + 1
                update_user(referrer_id, {"balance": new_balance, "ref_count": new_ref_count})
                
                try:
                    bot.send_message(referrer_id, f"🎉 <b>অভিনন্দন! আপনার রেফার লিংকের মাধ্যমে নতুন ইউজার যুক্ত হওয়ায় আপনি +{refer_bonus} {currency} বোনাস পেয়েছেন!</b>")
                except:
                    pass
            update_user(user_id, {"bonus_claimed": True})

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(user_id, get_t("verify_success"), reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, get_t("verify_fail"), show_alert=True)

# --- 💰 ACCOUNT / BALANCE ---
@bot.message_handler(func=lambda m: m.text in ["💰 BALANCE", "🖥️ একাউন্ট", "🖥️ Account", "/balance"])
def account(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    first_name = message.from_user.first_name or "User"
    currency = CACHE["settings"].get("currency", "bKash")
    
    balance = float(user_data.get("balance", 0.0))
    wallet = user_data.get("wallet", "Not Set")

    msg = f"""💰 <b>ACCOUNT BALANCE</b>
━━━━━━━━━━━━━━━━━━━━━
👤 <b>Name:</b> {first_name}
🆔 <b>User ID:</b> <code>{user_id}</code>

💵 <b>Current Balance:</b> {balance:.2f} {currency}
🏦 <b>Active Method:</b> {wallet if wallet != 'Not Set' else f'{currency} (Not Set)'}"""
    bot.send_message(user_id, msg)

# --- 🧑‍🤝‍🧑 REFERRAL ---
@bot.message_handler(func=lambda m: m.text in ["🧑‍🤝‍🧑 REFERRAL", "⚡ রেফারেল", "⚡ Referral", "/referral"])
def referral(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    ref_bonus = CACHE["settings"].get("refer_bonus", 2.0)
    currency = CACHE["settings"].get("currency", "bKash")
    
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = user_data.get("ref_count", 0)

    markup = types.InlineKeyboardMarkup()
    share_url = f"https://t.me/share/url?url={ref_link}&text=🚀 Join this bot to earn {currency} daily!"
    markup.add(types.InlineKeyboardButton("🚀 Share Link", url=share_url))

    msg = f"""🧑‍🤝‍🧑 <b>REFERRAL HUB</b>
━━━━━━━━━━━━━━━━━━━━━
🎁 <b>Reward Per Refer:</b> {ref_bonus} {currency}

🎉 <b>Your Referral Link 🔗</b>
<code>{ref_link}</code>

👥 <b>Total Invited:</b> {ref_count} Users
━━━━━━━━━━━━━━━━━━━━━
<i>Share this link with your friends to earn rewards!</i>"""
    bot.send_message(user_id, msg, reply_markup=markup)

# --- 🎁 BONUS ---
@bot.message_handler(func=lambda m: m.text in ["🎁 BONUS", "🎁 বোনাস", "🎁 Bonus", "/bonus"])
def daily_bonus_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    currency = settings.get("currency", "bKash")

    bonus_amt = float(settings.get("daily_bonus", 0.1))
    cooldown_hours = int(settings.get("bonus_cooldown", 24))
    cooldown_seconds = cooldown_hours * 3600

    last_time = float(user_data.get("last_bonus", 0))
    current_time = time.time()

    if current_time - last_time >= cooldown_seconds:
        current_bal = float(user_data.get("balance", 0.0))
        new_bal = current_bal + bonus_amt
        update_user(user_id, {"balance": new_bal, "last_bonus": current_time})

        msg = f"""🎁 <b>DAILY BONUS CLAIMED!</b>
━━━━━━━━━━━━━━━━━━━━━
🎉 অভিনন্দন! আপনি সফলভাবে আজকের বোনাস পেয়েছেন।

💰 <b>Reward Received:</b> +{bonus_amt} {currency}
🕒 <b>Come back after {cooldown_hours} Hours!</b>
━━━━━━━━━━━━━━━━━━━━━"""
        bot.send_message(user_id, msg)
    else:
        remaining = cooldown_seconds - (current_time - last_time)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)

        msg = f"""⏳ <b>Daily Bonus Already Claimed!</b>
━━━━━━━━━━━━━━━━━━━━━
আপনি আজকের বোনাস ইতিপূর্বে ক্লেইম করেছেন।

🕒 <b>পরবর্তী বোনাস পেতে অপেক্ষা করুন:</b>
👉 <b>{hours} ঘণ্টা {minutes} মিনিট পর</b> আবার আসুন!"""
        bot.send_message(user_id, msg)

# --- 📊 STATISTICS ---
@bot.message_handler(func=lambda m: m.text in ["🔋 STATISTICS", "📊 স্ট্যাটাস", "📊 Status", "/stats"])
def statistics_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    currency = settings.get("currency", "bKash")

    users_data = get_all_users()
    total_users = len(users_data) if users_data else 1
    total_withdrawn = float(settings.get("total_withdrawn", 0.0))
    user_balance = float(user_data.get("balance", 0.0))

    msg = f"""🌐 <b>GLOBAL SYSTEM STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━
👥 <b>Active Members :</b> {total_users}
💸 <b>Total Withdrawn :</b> {total_withdrawn:.2f} {currency}
━━━━━━━━━━━━━━━━━━━━━

👤 <b>PERSONAL PROFILE</b>
🔷 <b>Account ID :</b> <code>{user_id}</code>
🔷 <b>Membership :</b> ✅ Verified
🔷 <b>Total Earnings :</b> {user_balance:.2f} {currency}

⭐ <i>Keep inviting friends to unlock more rewards!</i>"""
    bot.send_message(user_id, msg)

# --- 💳 WALLET ---
@bot.message_handler(func=lambda m: m.text in ["💳 WALLET", "💳 ওয়ালেট", "💳 Wallet", "/wallet"])
def wallet_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    current_wallet = user_data.get("wallet", "Not Set")
    currency = CACHE["settings"].get("currency", "bKash")

    msg = f"""💳 <b>WALLET INFORMATION</b>
━━━━━━━━━━━━━━━━━━━━━
🏦 <b>Active {currency} Number:</b> <code>{current_wallet}</code>

⚙️ <i>To set or change your wallet, click here:</i> /SetWallet"""
    bot.send_message(user_id, msg)

@bot.message_handler(commands=['SetWallet'])
def set_wallet_prompt(message):
    msg = bot.send_message(message.chat.id, get_t("set_wallet_prompt"))
    bot.register_next_step_handler(msg, save_wallet)

def save_wallet(message):
    user_id = str(message.chat.id)
    wallet_number = message.text.strip()
    update_user(user_id, {"wallet": wallet_number})
    bot.send_message(user_id, f"{get_t('wallet_saved')} <code>{wallet_number}</code>", reply_markup=main_menu())

# --- 📥 WITHDRAW ---
@bot.message_handler(func=lambda m: m.text in ["📥 WITHDRAW", "💲 উইথড্র", "💲 Withdrawal", "/withdraw"])
def withdraw_prompt(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    currency = settings.get("currency", "bKash")

    if not settings.get("withdraw_status", True):
        bot.send_message(user_id, "⚠️ <b>Withdrawals are currently disabled by Admin!</b>")
        return

    balance = float(user_data.get("balance", 0))
    min_withdraw = float(settings.get("min_withdraw", 15.0))
    wallet = user_data.get("wallet", "Not Set")

    if wallet == "Not Set":
        bot.send_message(user_id, "😎 Please set your wallet first using /SetWallet.")
        return

    if balance < min_withdraw:
        bot.send_message(user_id, get_t("min_with_err").format(min_w=min_withdraw, curr=currency))
        return

    msg_text = get_t("with_prompt").format(min_w=min_withdraw, bal=balance, curr=currency)
    msg = bot.send_message(user_id, msg_text)
    bot.register_next_step_handler(msg, process_withdraw, balance, wallet, min_withdraw, currency)

def process_withdraw(message, balance, wallet, min_withdraw, currency):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text.strip())
    except ValueError:
        bot.send_message(user_id, "⚠️ Invalid amount! Please enter numbers only.")
        return

    if amount < min_withdraw:
        bot.send_message(user_id, get_t("min_with_err").format(min_w=min_withdraw, curr=currency))
        return
    if amount > balance:
        bot.send_message(user_id, "😳 The withdrawal amount exceeds your available balance.")
        return

    new_balance = balance - amount
    update_user(user_id, {"balance": new_balance})

    username = message.from_user.username or "No Username"
    w_id = f"W{int(time.time())}"
    
    withdraw_data = {
        "user_id": user_id,
        "username": username,
        "amount": amount,
        "wallet": wallet,
        "status": "Pending",
        "timestamp": int(time.time())
    }
    save_withdrawal(w_id, withdraw_data)

    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        types.InlineKeyboardButton("✅ Confirm / Paid", callback_data=f"appr_{w_id}"),
        types.InlineKeyboardButton("❌ Reject / Refund", callback_data=f"rej_{w_id}")
    )
    admin_text = f"""🔔 <b>New Withdrawal Request!</b>\n\n🆔 <b>User ID:</b> <code>{user_id}</code>\n👤 <b>Username:</b> @{username}\n💰 <b>Amount:</b> {amount} {currency}\n💳 <b>Wallet:</b> <code>{wallet}</code>\n🔖 <b>Trx ID:</b> <code>{w_id}</code>"""
    
    try:
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup)
    except Exception as e:
        print(f"Admin send error: {e}")

    success_msg = get_t("with_success").format(amt=amount, wal=wallet, wid=w_id, curr=currency)
    bot.send_message(user_id, success_msg)

# --- 👑 ADMIN ACTION HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("appr_") or call.data.startswith("rej_"))
def handle_withdraw_admin(call):
    if str(call.from_user.id) != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin can do this!")
        return

    action, w_id = call.data.split("_")
    w_data = get_withdrawal(w_id)

    if not w_data:
        bot.answer_callback_query(call.id, "❌ Request Not Found!")
        return

    user_id = w_data["user_id"]
    amount = float(w_data["amount"])
    wallet = w_data["wallet"]
    currency = CACHE["settings"].get("currency", "bKash")

    if action == "appr":
        save_withdrawal(w_id, {**w_data, "status": "Approved"})
        current_total = float(CACHE["settings"].get("total_withdrawn", 0.0))
        update_settings({"total_withdrawn": current_total + amount})

        bot.edit_message_text(f"{call.message.text}\n\n✅ <b>STATUS: APPROVED & PAID</b>", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_id, f"🎉 <b>আপনার {amount} {currency} উইথড্র সফল হয়েছে এবং পেমেন্ট পাঠানো হয়েছে!</b>\n💳 Wallet: <code>{wallet}</code>")
        except:
            pass

    elif action == "rej":
        user_info = get_user(user_id)
        current_bal = float(user_info.get("balance", 0))
        update_user(user_id, {"balance": current_bal + amount})
        save_withdrawal(w_id, {**w_data, "status": "Rejected"})

        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>STATUS: REJECTED & REFUNDED</b>", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_id, f"❌ <b>আপনার {amount} {currency} উইথড্র বাতিল করা হয়েছে এবং টাকা আপনার ব্যালেন্সে রিফান্ড করা হয়েছে।</b>")
        except:
            pass

# --- 👑 ADMIN PANEL & HELPERS ---
def build_admin_keyboard():
    settings = get_settings()
    markup = types.InlineKeyboardMarkup(row_width=2)

    maint_status = "✅ ON" if settings.get("maintenance") else "❌ OFF"
    wd_status = "✅ ON" if settings.get("withdraw_status", True) else "❌ OFF"
    currency = settings.get("currency", "bKash")

    markup.add(
        types.InlineKeyboardButton(f"🛠️ Maint: {maint_status}", callback_data="adm_toggle_maint"),
        types.InlineKeyboardButton(f"🌐 Withdraw: {wd_status}", callback_data="adm_toggle_wd")
    )
    markup.add(
        types.InlineKeyboardButton(f"💱 Currency: {currency}", callback_data="adm_set_curr"),
        types.InlineKeyboardButton(f"👥 Refer Bonus", callback_data="adm_set_refb")
    )
    markup.add(
        types.InlineKeyboardButton("➕ Add Channel", callback_data="adm_prompt_addch"),
        types.InlineKeyboardButton("➖ Rem Channel", callback_data="adm_prompt_remch")
    )
    markup.add(
        types.InlineKeyboardButton("👥 All Users", callback_data="adm_show_allusers"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_prompt_bcast")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_panel_handler(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    bot.send_message(
        ADMIN_ID,
        "👑 <b>INTERACTIVE ADMIN CONTROL PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━\nনিচের অপশনগুলো ব্যবহার করুন:",
        reply_markup=build_admin_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callbacks(call):
    if str(call.from_user.id) != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Access Denied!")
        return

    data = call.data
    settings = get_settings()

    if data == "adm_toggle_maint":
        new_val = not settings.get("maintenance", False)
        update_settings({"maintenance": new_val})
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=build_admin_keyboard())
    elif data == "adm_toggle_wd":
        new_val = not settings.get("withdraw_status", True)
        update_settings({"withdraw_status": new_val})
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=build_admin_keyboard())
    elif data == "adm_show_allusers":
        admin_all_users_func()
    elif data == "adm_prompt_addch":
        msg = bot.send_message(ADMIN_ID, "➕ ফরম্যাট: <code>@channelusername link Title</code>\nযেমন: <code>@FHx_Technical_Creator https://t.me/FHx_Technical_Creator Join Channel</code>")
        bot.register_next_step_handler(msg, admin_do_add_channel)
    elif data == "adm_prompt_remch":
        msg = bot.send_message(ADMIN_ID, "➖ মুছে ফেলার জন্য চ্যানেলের ইউজারনেম দিন (যেমন: <code>@FHx_Technical_Creator</code>):")
        bot.register_next_step_handler(msg, admin_do_rem_channel)
    elif data == "adm_prompt_bcast":
        msg = bot.send_message(ADMIN_ID, "📢 যে মেসেজটি সবাইকে পাঠাতে চান তা লিখুন:")
        bot.register_next_step_handler(msg, send_broadcast)

def admin_do_add_channel(message):
    try:
        raw_text = message.text.replace("/addchannel", "").strip()
        parts = raw_text.split(maxsplit=2)
        ch_id = parts[0]
        ch_url = parts[1]
        ch_title = parts[2] if len(parts) > 2 else "🔗 Join Channel"
        save_channel_to_db(ch_id, ch_url, ch_title)
        bot.send_message(ADMIN_ID, f"✅ চ্যানেল যুক্ত হয়েছে:\n🔹 ID: {ch_id}\n🔹 Title: {ch_title}\n\n⚠️ <b>অবশ্যই বটকে ওই চ্যানেলে Admin বানিয়ে নিন!</b>")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ ভুল ফরম্যাট! Error: {e}")

def admin_do_rem_channel(message):
    try:
        ch_id = message.text.replace("/delchannel", "").strip()
        remove_channel_from_db(ch_id)
        bot.send_message(ADMIN_ID, f"🗑️ চ্যানেল মুছে ফেলা হয়েছে: {ch_id}")
    except:
        bot.send_message(ADMIN_ID, "⚠️ সমস্যা হয়েছে!")

def admin_all_users_func():
    users = get_all_users()
    if not users:
        bot.send_message(ADMIN_ID, "ℹ️ কোনো ইউজার নেই।")
        return
    currency = CACHE["settings"].get("currency", "bKash")
    report = f"👥 <b>সকল ইউজার তালিকা (মোট: {len(users)}):</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
    for uid, u in list(users.items())[:40]:
        if isinstance(u, dict):
            report += f"🆔 <code>{uid}</code> | {u.get('name','N/A')} | 💰 {float(u.get('balance',0)):.2f} {currency}\n"
    bot.send_message(ADMIN_ID, report)

@bot.message_handler(commands=['addchannel'])
def admin_add_channel_cmd(message):
    if str(message.chat.id) == ADMIN_ID:
        admin_do_add_channel(message)

@bot.message_handler(commands=['delchannel'])
def admin_del_channel_cmd(message):
    if str(message.chat.id) == ADMIN_ID:
        admin_do_rem_channel(message)

def send_broadcast(message):
    users = get_all_users()
    count = 0
    for uid in users:
        try:
            bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"📣 <b>Broadcast সফল হয়েছে {count} জন ইউজারের কাছে!</b>")

# --- 📞 SUPPORT ---
@bot.message_handler(func=lambda m: m.text in ["SUPPORT 💸", "সাপোর্ট 💸", "/support"])
def support_handler(message):
    bot.send_message(message.chat.id, CACHE["settings"].get("support"))

# --- 🚀 RUN BOT ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Turbo Refer Bot is starting...")
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception as e:
        print(f"Webhook clear error: {e}")

    while True:
        try:
            bot.infinity_polling(timeout=15, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)
