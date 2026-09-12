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

# ⚡ মাল্টি-থ্রেডিং ও সুপারফাস্ট টেলিগ্রাম বট ইঞ্জিন
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True, num_threads=25)

# ⚡ HTTP Connection Pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=25, pool_maxsize=25)
session.mount('https://', adapter)
session.mount('http://', adapter)

# --- ⚡ IN-MEMORY TURBO CACHE ---
CACHE = {
    "settings": {
        "lang": "bn",
        "photo": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800",
        "support": "☎️ <b>উইথড্র দেওয়ার ২৪ ঘন্টার মধ্যে পেমেন্ট না পেলে যোগাযোগ করুন:</b>\n👤 @Promoter_from_bd\n\n📢 <b>উইথড্র দেওয়ার পর অবশ্যই নক দিবেন:</b> @FHx_Technical_Creator",
        "min_withdraw": 15.0,
        "max_withdraw": 100.0,
        "refer_bonus": 2.0,
        "daily_bonus": 0.1,
        "bonus_cooldown": 24, # hours
        "withdraw_status": True,
        "maintenance": False,
        "total_withdrawn": 0.0
    },
    "channels": {}
}

# --- 🌐 FLASK KEEP-ALIVE SERVER (Render 24/7) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ Telegram Premium Refer & BKash Bot is Running 24/7 with UptimeRobot!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 🗄️ FIREBASE DATABASE FUNCTIONS ---
def load_initial_cache():
    try:
        res = session.get(f"{FIREBASE_URL}/settings.json", timeout=3)
        if res.status_code == 200 and res.json():
            CACHE["settings"].update(res.json())
        
        res2 = session.get(f"{FIREBASE_URL}/channels.json", timeout=3)
        if res2.status_code == 200 and res2.json():
            data = res2.json()
            if isinstance(data, dict):
                CACHE["channels"] = data
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
        res = session.get(f"{FIREBASE_URL}/users/{user_id}.json", timeout=2)
        return res.json() or {}
    except:
        return {}

def update_user(user_id, data):
    threading.Thread(target=lambda: session.patch(f"{FIREBASE_URL}/users/{user_id}.json", json=data, timeout=5)).start()

def delete_user_from_db(user_id):
    try:
        session.delete(f"{FIREBASE_URL}/users/{user_id}.json", timeout=3)
        return True
    except:
        return False

def get_all_users():
    try:
        res = session.get(f"{FIREBASE_URL}/users.json", timeout=3)
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

# --- 🔍 STRICT MEMBERSHIP CHECK ---
def is_joined(user_id):
    channels = get_channels()
    for key, ch in channels.items():
        ch_id = ch.get("channel_id") if isinstance(ch, dict) else ch
        if not ch_id or not isinstance(ch_id, str):
            continue
        try:
            member = bot.get_chat_member(ch_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

# --- ⌨️ KEYBOARDS (হুবহু স্ক্রিনশটের মতো ৬টি বাটন) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💰 BALANCE", "🧑‍🤝‍🧑 REFERRAL")
    markup.add("📥 WITHDRAW", "💳 WALLET")
    markup.add("🎁 BONUS", "🔋 STATISTICS")
    return markup

def join_keyboard():
    markup = types.InlineKeyboardMarkup()
    channels = get_channels()
    
    for key, ch in channels.items():
        if isinstance(ch, dict) and "url" in ch:
            btn_title = ch.get("title", "🔗 Join Channel 1")
            btn_url = ch.get("url")
            markup.add(types.InlineKeyboardButton(btn_title, url=btn_url))
        
    markup.add(types.InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership"))
    return markup

# --- 🚀 START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    settings = get_settings()

    if settings.get("maintenance") and user_id != ADMIN_ID:
        bot.send_message(user_id, "🛠️ <b>Bot is currently under maintenance. Please come back later!</b>")
        return

    text_split = message.text.split()
    user_data = get_user(user_id)

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

    welcome_text = """🔒 <b>Access Restricted</b>
━━━━━━━━━━━━━━━━━━━━━
⚠️ <b>You must join all our channels to unlock bot features.</b>

📢 <b>Subscribe to every channel using the buttons below.</b>

✅ <b>After joining all channels, tap the Verify Membership button.</b>"""

    img_url = settings.get("photo")

    try:
        bot.send_photo(user_id, photo=img_url, caption=welcome_text, reply_markup=join_keyboard())
    except Exception:
        bot.send_message(user_id, welcome_text, reply_markup=join_keyboard())

# --- 🔍 VERIFY CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_callback(call):
    user_id = str(call.from_user.id)
    if is_joined(user_id):
        user_data = get_user(user_id)
        refer_bonus = CACHE["settings"].get("refer_bonus", 2.0)
        
        referrer_id = user_data.get("referred_by")
        if referrer_id and not user_data.get("bonus_claimed"):
            ref_data = get_user(referrer_id)
            if ref_data:
                new_balance = float(ref_data.get("balance", 0)) + refer_bonus
                new_ref_count = int(ref_data.get("ref_count", 0)) + 1
                update_user(referrer_id, {"balance": new_balance, "ref_count": new_ref_count})
                
                try:
                    bot.send_message(referrer_id, f"🎉 <b>অভিনন্দন! আপনার রেফার লিংকের মাধ্যমে নতুন ইউজার যুক্ত হওয়ায় আপনি +{refer_bonus} টাকা বোনাস পেয়েছেন!</b>")
                except:
                    pass
            update_user(user_id, {"bonus_claimed": True})

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(user_id, "🎉 <b>Membership Verified! Welcome to the main menu.</b>", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি! আগে জয়েন করুন।", show_alert=True)

# --- 💰 BALANCE (হুবহু স্ক্রিনশট-৩ এর মতো ডিজাইন) ---
@bot.message_handler(func=lambda m: m.text in ["💰 BALANCE", "🖥️ একাউন্ট", "🖥️ Account"])
def account(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    first_name = message.from_user.first_name or "User"
    
    balance = float(user_data.get("balance", 0.0))
    wallet = user_data.get("wallet", "Not Set")

    msg = f"""💰 <b>ACCOUNT BALANCE</b>
━━━━━━━━━━━━━━━━━━━━━
👤 <b>Name:</b> {first_name}
🆔 <b>User ID:</b> <code>{user_id}</code>

💵 <b>Current Balance:</b> {balance:.2f} টাকা (BDT)
🏦 <b>Active Method:</b> {wallet if wallet != 'Not Set' else 'bKash (Not Set)'}"""
    bot.send_message(user_id, msg)

# --- 🧑‍🤝‍🧑 REFERRAL (হুবহু স্ক্রিনশট-৩ এর মতো ডিজাইন) ---
@bot.message_handler(func=lambda m: m.text in ["🧑‍🤝‍🧑 REFERRAL", "⚡ রেফারেল", "⚡ Referral"])
def referral(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    ref_bonus = CACHE["settings"].get("refer_bonus", 2.0)
    
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = user_data.get("ref_count", 0)

    markup = types.InlineKeyboardMarkup()
    share_url = f"https://t.me/share/url?url={ref_link}&text=🚀 Join this bot to earn bKash daily!"
    markup.add(types.InlineKeyboardButton("🚀 Share Link", url=share_url))

    msg = f"""🧑‍🤝‍🧑 <b>REFERRAL HUB</b>
━━━━━━━━━━━━━━━━━━━━━
🎁 <b>Reward Per Refer:</b> {ref_bonus} bKash

🎉 <b>Your Referral Link 🔗</b>
<code>{ref_link}</code>

👥 <b>Total Invited:</b> {ref_count} Users
━━━━━━━━━━━━━━━━━━━━━
<i>Share this link with your friends to earn rewards!</i>"""
    bot.send_message(user_id, msg, reply_markup=markup)

# --- 🎁 DAILY BONUS (হুবহু স্ক্রিনশট-২ এর মতো ডিজাইন) ---
@bot.message_handler(func=lambda m: m.text in ["🎁 BONUS", "🎁 Bonus"])
def daily_bonus_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()

    bonus_amt = float(settings.get("daily_bonus", 0.1))
    cooldown_hours = int(settings.get("bonus_cooldown", 24))
    cooldown_seconds = cooldown_hours * 3600

    last_time = float(user_data.get("last_bonus", 0))
    current_time = time.time()

    if current_time - last_time >= cooldown_seconds:
        # বোনাস দেওয়া হবে
        current_bal = float(user_data.get("balance", 0.0))
        new_bal = current_bal + bonus_amt
        update_user(user_id, {"balance": new_bal, "last_bonus": current_time})

        msg = f"""🎁 <b>DAILY BONUS CLAIMED!</b>
━━━━━━━━━━━━━━━━━━━━━
🎉 অভিনন্দন! আপনি সফলভাবে আজকের বোনাস পেয়েছেন।

💰 <b>Reward Received:</b> +{bonus_amt} bKash
🕒 <b>Come back after {cooldown_hours} Hours!</b>
━━━━━━━━━━━━━━━━━━━━━"""
        bot.send_message(user_id, msg)
    else:
        # সময় বাকি আছে
        remaining = cooldown_seconds - (current_time - last_time)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)

        msg = f"""⏳ <b>Daily Bonus Already Claimed!</b>
━━━━━━━━━━━━━━━━━━━━━
আপনি আজকের বোনাস ইতিপূর্বে ক্লেইম করেছেন।

🕒 <b>পরবর্তী বোনাস পেতে অপেক্ষা করুন:</b>
👉 <b>{hours} ঘণ্টা {minutes} মিনিট পর</b> আবার আসুন!"""
        bot.send_message(user_id, msg)

# --- 🔋 STATISTICS (হুবহু স্ক্রিনশট-২ এর মতো ডিজাইন) ---
@bot.message_handler(func=lambda m: m.text in ["🔋 STATISTICS", "📊 স্ট্যাটাস", "📊 Status"])
def statistics_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()

    users_data = get_all_users()
    total_users = len(users_data) if users_data else 1
    total_withdrawn = settings.get("total_withdrawn", 0.0)

    user_balance = float(user_data.get("balance", 0.0))

    msg = f"""🌐 <b>GLOBAL SYSTEM STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━
👥 <b>Active Members :</b> {total_users}
💸 <b>Total Withdrawn :</b> {total_withdrawn:.2f} bKash
━━━━━━━━━━━━━━━━━━━━━

👤 <b>PERSONAL PROFILE</b>
🔷 <b>Account ID :</b> <code>{user_id}</code>
🔷 <b>Membership :</b> ✅ Success
🔷 <b>Total Earnings :</b> {user_balance:.2f} bKash

⭐ <i>Keep inviting friends to unlock more rewards!</i>"""
    bot.send_message(user_id, msg)

# --- 💳 WALLET ---
@bot.message_handler(func=lambda m: m.text in ["💳 WALLET", "💳 ওয়ালেট", "💳 Wallet"])
def wallet_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    current_wallet = user_data.get("wallet", "Not Set")

    msg = f"""💳 <b>WALLET INFORMATION</b>
━━━━━━━━━━━━━━━━━━━━━
🏦 <b>Active bKash/Nagad:</b> <code>{current_wallet}</code>

⚙️ <i>To set or change your wallet, click here:</i> /SetWallet"""
    bot.send_message(user_id, msg)

@bot.message_handler(commands=['SetWallet'])
def set_wallet_prompt(message):
    msg = bot.send_message(message.chat.id, "📝 <b>অনুগ্রহ করে আপনার বিকাশ/নগদ নম্বর লিখুন:</b>")
    bot.register_next_step_handler(msg, save_wallet)

def save_wallet(message):
    user_id = str(message.chat.id)
    wallet_number = message.text.strip()
    update_user(user_id, {"wallet": wallet_number})
    bot.send_message(user_id, f"✅ <b>Wallet successfully updated to:</b> <code>{wallet_number}</code>", reply_markup=main_menu())

# --- 📥 WITHDRAW ---
@bot.message_handler(func=lambda m: m.text in ["📥 WITHDRAW", "💲 উইথড্র", "💲 Withdrawal"])
def withdraw_prompt(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()

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
        bot.send_message(user_id, f"❌ <b>Minimum withdrawal amount is {min_withdraw} টাকা।</b>\nYour Balance: {balance:.2f} টাকা")
        return

    msg = bot.send_message(user_id, f"💰 <b>Minimum:</b> {min_withdraw} টাকা\n🚀 <b>Current Balance:</b> {balance:.2f} টাকা\n\n📝 <b>আপনি কত টাকা উইথড্র করতে চান পরিমাণ লিখুন:</b>")
    bot.register_next_step_handler(msg, process_withdraw, balance, wallet, min_withdraw)

def process_withdraw(message, balance, wallet, min_withdraw):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text.strip())
    except ValueError:
        bot.send_message(user_id, "⚠️ Invalid amount! Please enter numbers only.")
        return

    if amount < min_withdraw:
        bot.send_message(user_id, f"❌ Minimum withdrawal is {min_withdraw} টাকা.")
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
    admin_text = f"""🔔 <b>New Withdrawal Request!</b>\n\n🆔 <b>User ID:</b> <code>{user_id}</code>\n👤 <b>Username:</b> @{username}\n💰 <b>Amount:</b> {amount} টাকা\n💳 <b>Wallet:</b> <code>{wallet}</code>\n🔖 <b>Trx ID:</b> <code>{w_id}</code>"""
    
    try:
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup)
    except Exception as e:
        print(f"Admin send error: {e}")

    bot.send_message(user_id, f"""Withdrawal Request Successful ✅

💰 <b>Amount:</b> {amount} টাকা
⏳ <b>Payment Status:</b> Pending
💳 <b>Wallet:</b> <code>{wallet}</code>
🔖 <b>Request ID:</b> <code>{w_id}</code>

<i>Admin will verify and send your payment shortly.</i>""")

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

    if action == "appr":
        save_withdrawal(w_id, {**w_data, "status": "Approved"})
        
        # গ্লোবাল উইথড্র অ্যামাউন্ট আপডেট
        current_total = float(CACHE["settings"].get("total_withdrawn", 0.0))
        update_settings({"total_withdrawn": current_total + amount})

        bot.edit_message_text(f"{call.message.text}\n\n✅ <b>STATUS: APPROVED & PAID</b>", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_id, f"🎉 <b>আপনার {amount} টাকা উইথড্র সফল হয়েছে এবং বিকাশ/নগদে পেমেন্ট পাঠানো হয়েছে!</b>\n💳 Wallet: <code>{wallet}</code>")
        except:
            pass

    elif action == "rej":
        user_info = get_user(user_id)
        current_bal = float(user_info.get("balance", 0))
        update_user(user_id, {"balance": current_bal + amount})
        save_withdrawal(w_id, {**w_data, "status": "Rejected"})

        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>STATUS: REJECTED & REFUNDED</b>", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_id, f"❌ <b>আপনার {amount} টাকা উইথড্র বাতিল করা হয়েছে এবং টাকা আপনার ব্যালেন্সে রিফান্ড করা হয়েছে।</b>")
        except:
            pass

# --- 👑 INTERACTIVE ADMIN CONTROL PANEL (হুবহু স্ক্রিনশট-১ এর মতো বাটন কন্ট্রোল) ---
def build_admin_keyboard():
    settings = get_settings()
    markup = types.InlineKeyboardMarkup(row_width=2)

    sys_status = "✅ ON"
    maint_status = "✅ ON" if settings.get("maintenance") else "❌ OFF"
    wd_status = "✅ ON" if settings.get("withdraw_status", True) else "❌ OFF"

    min_w = settings.get("min_withdraw", 15.0)
    max_w = settings.get("max_withdraw", 100.0)
    refer_b = settings.get("refer_bonus", 2.0)
    daily_b = settings.get("daily_bonus", 0.1)

    markup.add(
        types.InlineKeyboardButton(f"🤖 System: {sys_status}", callback_data="adm_noop"),
        types.InlineKeyboardButton(f"🛠️ Maint: {maint_status}", callback_data="adm_toggle_maint")
    )
    markup.add(
        types.InlineKeyboardButton(f"🌐 Withdrawals: {wd_status}", callback_data="adm_toggle_wd"),
        types.InlineKeyboardButton("💱 Currency: bKash", callback_data="adm_noop")
    )
    markup.add(
        types.InlineKeyboardButton(f"🔻 Min Withdraw(~ {min_w})", callback_data="adm_set_minw"),
        types.InlineKeyboardButton(f"🔺 Max Withdraw(~ {max_w})", callback_data="adm_set_maxw")
    )
    markup.add(
        types.InlineKeyboardButton(f"👥 Per Refer (~ {refer_b})", callback_data="adm_set_refb"),
        types.InlineKeyboardButton(f"🎁 Daily Bonus (~ {daily_b})", callback_data="adm_set_dailyb")
    )
    markup.add(
        types.InlineKeyboardButton("➕ Add Funds", callback_data="adm_prompt_addfunds"),
        types.InlineKeyboardButton("➖ Deduct Funds", callback_data="adm_prompt_cutfunds")
    )
    markup.add(
        types.InlineKeyboardButton("➕ Add Pub. Ch.", callback_data="adm_prompt_addch"),
        types.InlineKeyboardButton("➖ Rem Pub. Ch.", callback_data="adm_prompt_remch")
    )
    markup.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_prompt_bcast"),
        types.InlineKeyboardButton("👥 All Users", callback_data="adm_show_allusers")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_panel_handler(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    bot.send_message(
        ADMIN_ID,
        "👑 <b>INTERACTIVE ADMIN CONTROL PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━\nনিচের বাটনগুলো দিয়ে সরাসরি বট কনফিগারেশন পরিবর্তন করুন:",
        reply_markup=build_admin_keyboard()
    )

# --- 👑 ADMIN INLINE BUTTON ACTIONS ---
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
        bot.answer_callback_query(call.id, f"Maintenance: {'ON' if new_val else 'OFF'}")

    elif data == "adm_toggle_wd":
        new_val = not settings.get("withdraw_status", True)
        update_settings({"withdraw_status": new_val})
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=build_admin_keyboard())
        bot.answer_callback_query(call.id, f"Withdrawals: {'ON' if new_val else 'OFF'}")

    elif data == "adm_set_minw":
        msg = bot.send_message(ADMIN_ID, "📝 <b>নতুন সর্বনিম্ন উইথড্র (Min Withdraw) অ্যামাউন্ট লিখুন:</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"min_withdraw": float(m.text.strip())}), bot.send_message(ADMIN_ID, "✅ Updated!", reply_markup=build_admin_keyboard())])

    elif data == "adm_set_maxw":
        msg = bot.send_message(ADMIN_ID, "📝 <b>নতুন সর্বোচ্চ উইথড্র (Max Withdraw) অ্যামাউন্ট লিখুন:</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"max_withdraw": float(m.text.strip())}), bot.send_message(ADMIN_ID, "✅ Updated!", reply_markup=build_admin_keyboard())])

    elif data == "adm_set_refb":
        msg = bot.send_message(ADMIN_ID, "📝 <b>প্রতি রেফারের নতুন বোনাস (Per Refer) লিখুন:</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"refer_bonus": float(m.text.strip())}), bot.send_message(ADMIN_ID, "✅ Updated!", reply_markup=build_admin_keyboard())])

    elif data == "adm_set_dailyb":
        msg = bot.send_message(ADMIN_ID, "📝 <b>নতুন ডেইলি বোনাস (Daily Bonus) পরিমাণ লিখুন (যেমন: 0.1 বা 0.5):</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"daily_bonus": float(m.text.strip())}), bot.send_message(ADMIN_ID, "✅ Updated!", reply_markup=build_admin_keyboard())])

    elif data == "adm_prompt_addfunds":
        msg = bot.send_message(ADMIN_ID, "📝 <b>ফরম্যাট:</b> <code>ইউজার_আইডি পরিমাণ</code>\nযেমন: <code>5889152252 10</code>")
        bot.register_next_step_handler(msg, admin_do_add_funds)

    elif data == "adm_prompt_cutfunds":
        msg = bot.send_message(ADMIN_ID, "📝 <b>ফরম্যাট:</b> <code>ইউজার_আইডি পরিমাণ</code>\nযেমন: <code>5889152252 5</code>")
        bot.register_next_step_handler(msg, admin_do_cut_funds)

    elif data == "adm_prompt_addch":
        msg = bot.send_message(ADMIN_ID, "📝 <b>ফরম্যাট:</b> <code>@channel_username https://t.me/link বাটনের_নাম</code>")
        bot.register_next_step_handler(msg, admin_do_add_channel)

    elif data == "adm_prompt_remch":
        msg = bot.send_message(ADMIN_ID, "📝 <b>চ্যানেল ইউজারনেম লিখুন:</b>\nযেমন: <code>@FHx_Technical_Creator</code>")
        bot.register_next_step_handler(msg, admin_do_rem_channel)

    elif data == "adm_prompt_bcast":
        msg = bot.send_message(ADMIN_ID, "🔍 <b>সকলকে ব্রডকাস্ট করার মেসেজটি পাঠান:</b>")
        bot.register_next_step_handler(msg, send_broadcast)

    elif data == "adm_show_allusers":
        admin_all_users_func()

def admin_do_add_funds(message):
    try:
        uid, amt = message.text.split()
        amt = float(amt)
        u = get_user(uid)
        new_bal = float(u.get("balance", 0)) + amt
        update_user(uid, {"balance": new_bal})
        bot.send_message(ADMIN_ID, f"✅ User {uid} কে {amt} টাকা দেওয়া হয়েছে। New Balance: {new_bal:.2f}")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ভুল ফরম্যাট!")

def admin_do_cut_funds(message):
    try:
        uid, amt = message.text.split()
        amt = float(amt)
        u = get_user(uid)
        new_bal = max(0.0, float(u.get("balance", 0)) - amt)
        update_user(uid, {"balance": new_bal})
        bot.send_message(ADMIN_ID, f"✅ User {uid} থেকে {amt} টাকা কাটা হয়েছে। New Balance: {new_bal:.2f}")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ভুল ফরম্যাট!")

def admin_do_add_channel(message):
    try:
        parts = message.text.split(maxsplit=3)
        ch_id = parts[0]
        ch_url = parts[1]
        ch_title = parts[2] if len(parts) > 2 else "🔗 Join Channel"
        save_channel_to_db(ch_id, ch_url, ch_title)
        bot.send_message(ADMIN_ID, f"✅ চ্যানেল যুক্ত হয়েছে: {ch_title} ({ch_id})")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ভুল ফরম্যাট!")

def admin_do_rem_channel(message):
    try:
        ch_id = message.text.strip()
        remove_channel_from_db(ch_id)
        bot.send_message(ADMIN_ID, f"🗑️ চ্যানেল মুছে ফেলা হয়েছে: {ch_id}")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ভুল ফরম্যাট!")

def admin_all_users_func():
    users = get_all_users()
    if not users:
        bot.send_message(ADMIN_ID, "ℹ️ কোনো ইউজার নেই।")
        return
    report = f"👥 <b>সকল ইউজার তালিকা (মোট: {len(users)}):</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
    for uid, u in list(users.items())[:50]:
        if isinstance(u, dict):
            report += f"🆔 <code>{uid}</code> | {u.get('name','N/A')} | 💰 {float(u.get('balance',0)):.2f}৳ | 👥 {u.get('ref_count',0)}\n"
    bot.send_message(ADMIN_ID, report)

def send_broadcast(message):
    users = get_all_users()
    count = 0
    for uid in users:
        try:
            bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"📣 <b>Broadcast sent to {count} users!</b>")

# --- 🚀 RUN BOT (TURBO FAST ENGINE) ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Turbo Premium Refer Bot is starting...")
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception as e:
        print(f"Webhook clear error: {e}")

    while True:
        try:
            bot.infinity_polling(timeout=15, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling conflict/error: {e}")
            time.sleep(3)
