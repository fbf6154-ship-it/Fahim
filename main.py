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

# ⚡ টেলিগ্রাম বট ইঞ্জিন (মাল্টি-থ্রেডেড)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True, num_threads=30)

# ⚡ HTTP কানেকশন পুলিং
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=30)
session.mount('https://', adapter)
session.mount('http://', adapter)

# --- ⚡ ইন-মেমোরি টার্বো ক্যাশ ---
CACHE = {
    "settings": {
        "lang": "bn",
        "currency": "bKash",
        "photo": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800",
        "support": "☎️ <b>সাপোর্ট ও হেল্প ডেস্ক:</b>\n━━━━━━━━━━━━━━━━━━━━━\nউইথড্র বা যেকোনো প্রয়োজনে সরাসরি মেসেজ দিন:\n\n👤 <b>Admin:</b> @Promoter_from_bd\n📢 <b>Official Channel:</b> @FHx_Technical_Creator",
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

# --- 🌐 FLASK KEEP-ALIVE SERVER (24/7 সচল রাখার জন্য) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ Turbo Premium Refer Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 🗄️ FIREBASE DATABASE FUNCTIONS ---
def load_initial_cache():
    try:
        res = session.get(f"{FIREBASE_URL}/settings.json", timeout=3)
        if res.status_code == 200 and res.json() and isinstance(res.json(), dict):
            CACHE["settings"].update(res.json())
        
        res2 = session.get(f"{FIREBASE_URL}/channels.json", timeout=3)
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
        res = session.get(f"{FIREBASE_URL}/users/{user_id}.json", timeout=2)
        data = res.json()
        return data if isinstance(data, dict) else {}
    except:
        return {}

def update_user(user_id, data):
    threading.Thread(target=lambda: session.patch(f"{FIREBASE_URL}/users/{user_id}.json", json=data, timeout=5)).start()

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

# --- 📢 CHANNEL DATABASE ---
def get_channels():
    if not CACHE["channels"]:
        return {"ch_1": {"channel_id": DEFAULT_CHANNEL_ID, "url": DEFAULT_CHANNEL_URL, "title": "JOIN"}}
    return CACHE["channels"]

def save_channel_to_db(ch_id, url, title):
    clean_key = ch_id.replace("@", "").replace("-", "_").replace(".", "_")
    payload = {"channel_id": ch_id, "url": url, "title": title}
    CACHE["channels"][clean_key] = payload
    threading.Thread(target=lambda: session.put(f"{FIREBASE_URL}/channels/{clean_key}.json", json=payload, timeout=5)).start()
    return True

def remove_channel_from_db(clean_key):
    if clean_key in CACHE["channels"]:
        del CACHE["channels"][clean_key]
    threading.Thread(target=lambda: session.delete(f"{FIREBASE_URL}/channels/{clean_key}.json", timeout=5)).start()
    return True

# --- 🔍 MEMBERSHIP CHECK ---
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

# --- 🎨 DYNAMIC JOIN UI BUILDER ---
def build_join_ui():
    channels = get_channels()
    
    # আপনার পূর্বের অরিজিনাল স্টাইলিশ জয়েন মেসেজ
    text = """🔒 <b>Access Restricted</b>
━━━━━━━━━━━━━━━━━━━━━
⚠️ <b>You must join all our channels to unlock bot features.</b>

📢 <b>Subscribe to every channel using the buttons below:</b>

✅ <b>After joining all channels, tap the Joined Done button.</b>"""
    
    markup = types.InlineKeyboardMarkup()
    buttons = []
    idx = 1
    
    for key, ch in channels.items():
        title = ch.get("title", f"JOIN {idx}")
        url = ch.get("url", DEFAULT_CHANNEL_URL)
        buttons.append(types.InlineKeyboardButton(f"📢 {title}", url=url))
        idx += 1

    # চ্যানেল বাটনগুলোকে সুন্দরভাবে ২ কলামে বিন্যাস
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i+1])
        else:
            markup.row(buttons[i])

    # নিচে ভেরিফিকেশন বাটন
    markup.add(types.InlineKeyboardButton("✅ Joined Done", callback_data="verify_membership"))
    return text, markup

# --- ⌨️ MAIN MENU KEYBOARD ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💰 ব্যালেন্স", "🧑‍🤝‍🧑 রেফারেল")
    markup.add("📥 উইথড্র", "💳 ওয়ালেট")
    markup.add("🎁 ডেইলি বোনাস", "🔋 স্ট্যাটাস")
    markup.add("☎️ সাপোর্ট")
    return markup

# --- 🚀 START COMMAND ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        user_id = str(message.chat.id)
        settings = get_settings()

        if settings.get("maintenance") and user_id != ADMIN_ID:
            bot.send_message(user_id, "🛠️ <b>বটটিতে বর্তমানে মেইনটেনেন্স এর কাজ চলছে। অনুগ্রহ করে কিছুক্ষণ পর চেষ্টা করুন!</b>")
            return

        text_split = message.text.split()
        user_data = get_user(user_id)

        if user_data.get("status") == "banned":
            bot.send_message(user_id, "🚫 <b>আপনাকে বটটি ব্যবহার থেকে নিষিদ্ধ করা হয়েছে!</b>")
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

        # যদি অলরেডি জয়েন করা থাকে
        if is_joined(user_id):
            bot.send_message(user_id, "🎉 <b>স্বাগতম! নিচের মেনু থেকে অপশন নির্বাচন করুন:</b>", reply_markup=main_menu())
            return

        join_text, join_markup = build_join_ui()
        img_url = settings.get("photo")

        sent = False
        if img_url and (img_url.startswith("http://") or img_url.startswith("https://")):
            try:
                bot.send_photo(user_id, photo=img_url, caption=join_text, reply_markup=join_markup)
                sent = True
            except:
                sent = False

        if not sent:
            bot.send_message(user_id, join_text, reply_markup=join_markup)

    except Exception as e:
        print(f"Start error: {e}")

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
                    bot.send_message(referrer_id, f"🎉 <b>অভিনন্দন! আপনার রেফার লিংকের মাধ্যমে নতুন মেম্বার যুক্ত হওয়ায় আপনি +{refer_bonus} {currency} পেয়েছেন!</b>")
                except:
                    pass
            update_user(user_id, {"bonus_claimed": True})

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(user_id, "🎉 <b>Membership Verified! Welcome to the main menu.</b>", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! আগে জয়েন করুন।", show_alert=True)

# --- 💰 BALANCE ---
@bot.message_handler(func=lambda m: m.text in ["💰 ব্যালেন্স", "💰 BALANCE", "🖥️ একাউন্ট"])
def balance_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    first_name = message.from_user.first_name or "User"
    currency = CACHE["settings"].get("currency", "bKash")
    balance = float(user_data.get("balance", 0.0))
    wallet = user_data.get("wallet", "Not Set")

    msg = f"""💰 <b>আপনার একাউন্ট তথ্য</b>
━━━━━━━━━━━━━━━━━━━━━
👤 <b>নাম:</b> {first_name}
🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>

💵 <b>বর্তমান ব্যালেন্স:</b> <b>{balance:.2f} {currency}</b>
🏦 <b>পেমেন্ট ওয়ালেট:</b> <code>{wallet}</code>
━━━━━━━━━━━━━━━━━━━━━"""
    bot.send_message(user_id, msg)

# --- 🧑‍🤝‍🧑 REFERRAL ---
@bot.message_handler(func=lambda m: m.text in ["🧑‍🤝‍🧑 রেফারেল", "🧑‍🤝‍🧑 REFERRAL"])
def referral_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    ref_bonus = CACHE["settings"].get("refer_bonus", 2.0)
    currency = CACHE["settings"].get("currency", "bKash")
    
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = user_data.get("ref_count", 0)

    markup = types.InlineKeyboardMarkup()
    share_url = f"https://t.me/share/url?url={ref_link}&text=🚀 এই বটে জয়েন করে প্রতি রেফারে {ref_bonus} {currency} ফ্রিতে ইনকাম করুন!"
    markup.add(types.InlineKeyboardButton("🚀 বন্ধুদের মাঝে শেয়ার করুন", url=share_url))

    msg = f"""🧑‍🤝‍🧑 <b>রেফারেল প্রোগ্রাম</b>
━━━━━━━━━━━━━━━━━━━━━
🎁 <b>প্রতি রেফারে পাবেন:</b> <b>{ref_bonus} {currency}</b>

🔗 <b>আপনার রেফারেল লিংক:</b>
<code>{ref_link}</code>

👥 <b>মোট সফল রেফার:</b> <b>{ref_count} জন</b>
━━━━━━━━━━━━━━━━━━━━━
<i>লিংকটি শেয়ার করে বন্ধুদের ইনভাইট করুন এবং বোনাস আয় করুন!</i>"""
    bot.send_message(user_id, msg, reply_markup=markup)

# --- 🎁 DAILY BONUS ---
@bot.message_handler(func=lambda m: m.text in ["🎁 ডেইলি বোনাস", "🎁 BONUS", "🎁 Bonus"])
def bonus_handler(message):
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

        msg = f"""🎁 <b>ডেইলি বোনাস সফল!</b>
━━━━━━━━━━━━━━━━━━━━━
🎉 আপনি আজকের বোনাস সফলভাবে গ্রহণ করেছেন!

💰 <b>বোনাস পেয়েছেন:</b> +{bonus_amt} {currency}
🕒 পরবর্তী বোনাস <b>{cooldown_hours} ঘণ্টা</b> পর আবার নিতে পারবেন।
━━━━━━━━━━━━━━━━━━━━━"""
        bot.send_message(user_id, msg)
    else:
        remaining = cooldown_seconds - (current_time - last_time)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)

        msg = f"""⏳ <b>ডেইলি বোনাস ইতিমধ্যে নেওয়া হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━
🕒 <b>পরবর্তী বোনাস পেতে অপেক্ষা করুন:</b>
👉 <b>{hours} ঘণ্টা {minutes} মিনিট</b> পর আবার আসুন!"""
        bot.send_message(user_id, msg)

# --- 🔋 STATISTICS (আপনার হুবহু ফরম্যাট অনুযায়ী সুন্দর ইউজার প্রোফাইল) ---
@bot.message_handler(func=lambda m: m.text in ["🔋 স্ট্যাটাস", "🔋 STATISTICS", "📊 স্ট্যাটাস"])
def stats_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    currency = settings.get("currency", "bKash")

    user_bal = float(user_data.get("balance", 0.0))
    user_refs = user_data.get("ref_count", 0)
    wallet = user_data.get("wallet", "Not Set")

    msg = f"""📊 <b>বট ও ব্যক্তিগত স্ট্যাটাস</b>
━━━━━━━━━━━━━━━━━━━━━
👤 <b>ইউজার প্রোফাইল:</b>
🆔 <b>আপনার আইডি:</b> <code>{user_id}</code>
💰 <b>ব্যালেন্স:</b> <b>{user_bal:.2f} {currency}</b>
👥 <b>রেফার করেছেন:</b> <b>{user_refs} জন</b>
💳 <b>ওয়ালেট:</b> <code>{wallet}</code>
🔰 <b>মেম্বারশিপ:</b> ✅ ভেরিফাইড মেম্বার
━━━━━━━━━━━━━━━━━━━━━"""
    bot.send_message(user_id, msg)

# --- 💳 WALLET ---
@bot.message_handler(func=lambda m: m.text in ["💳 ওয়ালেট", "💳 WALLET"])
def wallet_view(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    current_wallet = user_data.get("wallet", "Not Set")
    currency = CACHE["settings"].get("currency", "bKash")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⚙️ ওয়ালেট পরিবর্তন করুন", callback_data="change_wallet_btn"))

    msg = f"""💳 <b>ওয়ালেট সেটিংস</b>
━━━━━━━━━━━━━━━━━━━━━
🏦 <b>বর্তমান {currency} নম্বর:</b> <code>{current_wallet}</code>

<i>নম্বর যুক্ত বা পরিবর্তন করতে নিচের বাটনে চাপ দিন।</i>"""
    bot.send_message(user_id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "change_wallet_btn")
def change_wallet_cb(call):
    msg = bot.send_message(call.message.chat.id, "📝 <b>আপনার বিকাশ / নগদ নম্বরটি লিখে পাঠান:</b>")
    bot.register_next_step_handler(msg, save_wallet_step)

@bot.message_handler(commands=['SetWallet'])
def set_wallet_cmd(message):
    msg = bot.send_message(message.chat.id, "📝 <b>আপনার বিকাশ / নগদ নম্বরটি লিখে পাঠান:</b>")
    bot.register_next_step_handler(msg, save_wallet_step)

def save_wallet_step(message):
    user_id = str(message.chat.id)
    val = message.text.strip()
    update_user(user_id, {"wallet": val})
    bot.send_message(user_id, f"✅ <b>আপনার ওয়ালেট নম্বর সফলভাবে সেভ হয়েছে:</b> <code>{val}</code>", reply_markup=main_menu())

# --- ☎️ SUPPORT ---
@bot.message_handler(func=lambda m: m.text in ["☎️ সাপোর্ট", "SUPPORT 💸"])
def support_info(message):
    bot.send_message(message.chat.id, CACHE["settings"].get("support"))

# --- 📥 WITHDRAW ---
@bot.message_handler(func=lambda m: m.text in ["📥 উইথড্র", "📥 WITHDRAW"])
def withdraw_init(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    currency = settings.get("currency", "bKash")

    if not settings.get("withdraw_status", True):
        bot.send_message(user_id, "⚠️ <b>বর্তমানে উইথড্র সিস্টেম এডমিন কর্তৃক সাময়িক বন্ধ আছে।</b>")
        return

    balance = float(user_data.get("balance", 0))
    min_withdraw = float(settings.get("min_withdraw", 15.0))
    wallet = user_data.get("wallet", "Not Set")

    if wallet == "Not Set":
        bot.send_message(user_id, "⚠️ <b>আপনার ওয়ালেট নম্বর সেট করা নেই!</b>\nপ্রথমে 💳 <b>ওয়ালেট</b> বাটনে চাপ দিয়ে নম্বর সেট করুন।")
        return

    if balance < min_withdraw:
        bot.send_message(user_id, f"❌ <b>উইথড্র করার জন্য পর্যাপ্ত ব্যালেন্স নেই!</b>\nসর্বনিম্ন উইথড্র: <b>{min_withdraw} {currency}</b>\nআপনার ব্যালেন্স: <b>{balance:.2f} {currency}</b>")
        return

    msg = bot.send_message(user_id, f"💰 <b>সর্বনিম্ন উইথড্র:</b> {min_withdraw} {currency}\n🚀 <b>আপনার ব্যালেন্স:</b> {balance:.2f} {currency}\n💳 <b>পেমেন্ট ওয়ালেট:</b> <code>{wallet}</code>\n\n📝 <b>আপনি কত টাকা উইথড্র করতে চান পরিমাণ লিখুন:</b>")
    bot.register_next_step_handler(msg, process_withdrawal, balance, wallet, min_withdraw, currency)

def process_withdrawal(message, balance, wallet, min_withdraw, currency):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text.strip())
    except:
        bot.send_message(user_id, "⚠️ ভুল ইনপুট! শুধু সংখ্যার পরিমাণ লিখুন।")
        return

    if amount < min_withdraw:
        bot.send_message(user_id, f"❌ সর্বনিম্ন উইথড্র পরিমাণ {min_withdraw} {currency}।")
        return
    if amount > balance:
        bot.send_message(user_id, "❌ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই!")
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
    admin_text = f"🔔 <b>নতুন উইথড্র রিকোয়েস্ট!</b>\n━━━━━━━━━━━━━━━━━━━━━\n🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>\n👤 <b>ইউজারনেম:</b> @{username}\n💰 <b>পরিমাণ:</b> {amount} {currency}\n💳 <b>ওয়ালেট:</b> <code>{wallet}</code>\n🔖 <b>রিকোয়েস্ট আইডি:</b> <code>{w_id}</code>"
    
    try:
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup)
    except:
        pass

    bot.send_message(user_id, f"উইথড্র রিকোয়েস্ট সফল হয়েছে ✅\n\n💰 <b>পরিমাণ:</b> {amount} {currency}\n⏳ <b>পেমেন্ট স্ট্যাটাস:</b> Pending\n💳 <b>ওয়ালেট:</b> <code>{wallet}</code>\n🔖 <b>আইডি:</b> <code>{w_id}</code>\n\n<i>এডমিন শীঘ্রই পেমেন্ট ভেরিফাই করে পাঠিয়ে দিবে।</i>")

# --- 👑 ADMIN ACTION ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("appr_") or call.data.startswith("rej_"))
def admin_withdraw_decision(call):
    if str(call.from_user.id) != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ অননুমোদিত অ্যাক্সেস!")
        return

    action, w_id = call.data.split("_")
    w_data = get_withdrawal(w_id)

    if not w_data:
        bot.answer_callback_query(call.id, "❌ রিকোয়েস্ট পাওয়া যায়নি!")
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
            bot.send_message(user_id, f"🎉 <b>আপনার {amount} {currency} উইথড্র সফল হয়েছে এবং পেমেন্ট পাঠানো হয়েছে!</b>\n💳 ওয়ালেট: <code>{wallet}</code>")
        except:
            pass

    elif action == "rej":
        user_info = get_user(user_id)
        current_bal = float(user_info.get("balance", 0))
        update_user(user_id, {"balance": current_bal + amount})
        save_withdrawal(w_id, {**w_data, "status": "Rejected"})
        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>STATUS: REJECTED & REFUNDED</b>", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_id, f"❌ <b>আপনার {amount} {currency} উইথড্র বাতিল করা হয়েছে এবং টাকা ব্যালেন্সে ফেরত দেওয়া হয়েছে।</b>")
        except:
            pass

# --- 👑 INTERACTIVE ADMIN CONTROL PANEL ---
def admin_main_menu_markup():
    settings = get_settings()
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    maint_status = "🟢 ON" if settings.get("maintenance") else "🔴 OFF"
    wd_status = "🟢 ON" if settings.get("withdraw_status", True) else "🔴 OFF"

    markup.add(
        types.InlineKeyboardButton(f"🛠️ Maintenance: {maint_status}", callback_data="adm_toggle_maint"),
        types.InlineKeyboardButton(f"📥 Withdraw: {wd_status}", callback_data="adm_toggle_wd")
    )
    markup.add(
        types.InlineKeyboardButton("📢 চ্যানেল ম্যানেজার", callback_data="adm_channel_mgr"),
        types.InlineKeyboardButton("👥 ইউজার ম্যানেজার", callback_data="adm_user_mgr")
    )
    markup.add(
        types.InlineKeyboardButton(f"💱 Currency ({settings.get('currency')})", callback_data="adm_set_curr"),
        types.InlineKeyboardButton(f"👥 Per Refer ({settings.get('refer_bonus')})", callback_data="adm_set_refb")
    )
    markup.add(
        types.InlineKeyboardButton(f"🔻 Min With ({settings.get('min_withdraw')})", callback_data="adm_set_minw"),
        types.InlineKeyboardButton(f"🎁 Daily Bonus ({settings.get('daily_bonus')})", callback_data="adm_set_dailyb")
    )
    markup.add(
        types.InlineKeyboardButton("🖼️ ব্যানার ফটো সেট", callback_data="adm_set_photo_prompt"),
        types.InlineKeyboardButton("☎️ সাপোর্ট মেসেজ এডিট", callback_data="adm_set_support")
    )
    markup.add(
        types.InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="adm_broadcast")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_panel_open(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    bot.send_message(
        ADMIN_ID,
        "👑 <b>INTERACTIVE ADMIN CONTROL PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━\nনিচের অপশনগুলো ব্যবহার করে সবকিছু ম্যানেজ করুন:",
        reply_markup=admin_main_menu_markup()
    )

# --- 👑 ADMIN CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callbacks(call):
    if str(call.from_user.id) != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ অননুমোদিত!")
        return

    data = call.data
    settings = get_settings()

    if data == "adm_back_main":
        bot.edit_message_text(
            "👑 <b>INTERACTIVE ADMIN CONTROL PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━\nনিচের অপশনগুলো ব্যবহার করে সবকিছু ম্যানেজ করুন:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_main_menu_markup()
        )

    elif data == "adm_toggle_maint":
        new_val = not settings.get("maintenance", False)
        update_settings({"maintenance": new_val})
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu_markup())

    elif data == "adm_toggle_wd":
        new_val = not settings.get("withdraw_status", True)
        update_settings({"withdraw_status": new_val})
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu_markup())

    # --- 📢 চ্যানেল ম্যানেজার ---
    elif data == "adm_channel_mgr":
        channels = get_channels()
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for k, ch in channels.items():
            title = ch.get('title', 'Unknown')
            markup.add(types.InlineKeyboardButton(f"📢 {title} ({ch.get('channel_id')})", callback_data=f"adm_viewch_{k}"))
            
        markup.add(types.InlineKeyboardButton("➕ নতুন চ্যানেল যোগ করুন", callback_data="adm_add_channel_prompt"))
        markup.add(types.InlineKeyboardButton("🔙 ব্যাক", callback_data="adm_back_main"))

        bot.edit_message_text(
            f"📢 <b>চ্যানেল ম্যানেজার:</b>\n━━━━━━━━━━━━━━━━━━━━━\nমোট চ্যানেল: <b>{len(channels)}</b> টি\nযেকোনো চ্যানেলের ওপর চাপ দিয়ে ডিলিট বা লিংক দেখুন:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    elif data.startswith("adm_viewch_"):
        ch_key = data.replace("adm_viewch_", "")
        channels = get_channels()
        ch_info = channels.get(ch_key)
        
        if not ch_info:
            bot.answer_callback_query(call.id, "চ্যানেল পাওয়া যায়নি!")
            return

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑️ এই চ্যানেল ডিলিট করুন", callback_data=f"adm_delch_{ch_key}"))
        markup.add(types.InlineKeyboardButton("🔙 চ্যানেলের তালিকায় ফিরুন", callback_data="adm_channel_mgr"))

        msg_text = f"📢 <b>চ্যানেল বিস্তারিত:</b>\n━━━━━━━━━━━━━━━━━━━━━\n🔹 <b>নাম:</b> {ch_info.get('title')}\n🔹 <b>আইডি/ইউজারনেম:</b> <code>{ch_info.get('channel_id')}</code>\n🔹 <b>লিংক:</b> {ch_info.get('url')}"
        bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif data.startswith("adm_delch_"):
        ch_key = data.replace("adm_delch_", "")
        remove_channel_from_db(ch_key)
        bot.answer_callback_query(call.id, "✅ চ্যানেল ডিলিট হয়েছে!", show_alert=True)
        admin_callbacks(call)

    elif data == "adm_add_channel_prompt":
        msg = bot.send_message(
            ADMIN_ID,
            "➕ <b>নতুন চ্যানেল যোগ করার ফরম্যাট:</b>\n<code>@চ্যানেল_আইডি লিংক বাটনের_নাম</code>\n\n📌 <b>উদাহরণ:</b>\n<code>@FHx_Technical_Creator https://t.me/FHx_Technical_Creator JOIN now</code>"
        )
        bot.register_next_step_handler(msg, process_add_channel_step)

    # --- 👥 ইউজার ম্যানেজার ---
    elif data == "adm_user_mgr":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔍 ইউজার খুঁজুন", callback_data="adm_search_user"),
            types.InlineKeyboardButton("📋 সকল ইউজার লিস্ট", callback_data="adm_list_users")
        )
        markup.add(
            types.InlineKeyboardButton("➕ ব্যালেন্স যোগ", callback_data="adm_add_bal_prompt"),
            types.InlineKeyboardButton("➖ ব্যালেন্স কর্তন", callback_data="adm_cut_bal_prompt")
        )
        markup.add(types.InlineKeyboardButton("🔙 ব্যাক", callback_data="adm_back_main"))

        users = get_all_users()
        bot.edit_message_text(
            f"👥 <b>ইউজার কন্ট্রোল ম্যানেজার:</b>\n━━━━━━━━━━━━━━━━━━━━━\nমোট ইউজার: <b>{len(users)} জন</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    elif data == "adm_list_users":
        users = get_all_users()
        report = f"👥 <b>ইউজার তালিকা (মোট {len(users)} জন):</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
        currency = CACHE["settings"].get("currency", "bKash")
        for uid, u in list(users.items())[:30]:
            if isinstance(u, dict):
                report += f"🆔 <code>{uid}</code> | {u.get('name', 'N/A')} | 💰 {float(u.get('balance', 0)):.2f} {currency}\n"
        bot.send_message(ADMIN_ID, report)

    elif data == "adm_search_user":
        msg = bot.send_message(ADMIN_ID, "🔍 <b>ইউজারের টেলিগ্রাম আইডি পাঠান:</b>")
        bot.register_next_step_handler(msg, search_user_step)

    elif data == "adm_add_bal_prompt":
        msg = bot.send_message(ADMIN_ID, "➕ <b>ফরম্যাট:</b> <code>User_ID Amount</code>\nউদাহরণ: <code>5889152252 50</code>")
        bot.register_next_step_handler(msg, admin_add_balance_step)

    elif data == "adm_cut_bal_prompt":
        msg = bot.send_message(ADMIN_ID, "➖ <b>ফরম্যাট:</b> <code>User_ID Amount</code>\nউদাহরণ: <code>5889152252 20</code>")
        bot.register_next_step_handler(msg, admin_cut_balance_step)

    # --- ⚙️ সেটিংস ---
    elif data == "adm_set_curr":
        msg = bot.send_message(ADMIN_ID, "💱 <b>নতুন কারেন্সি নাম লিখুন (যেমন: bKash, BDT, টাকা):</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"currency": m.text.strip()}), bot.send_message(ADMIN_ID, f"✅ কারেন্সি আপডেট হয়েছে: <b>{m.text.strip()}</b>")])

    elif data == "adm_set_refb":
        msg = bot.send_message(ADMIN_ID, "👥 <b>প্রতি রেফার বোনাস পরিমাণ লিখুন (যেমন: 2):</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"refer_bonus": float(m.text.strip())}), bot.send_message(ADMIN_ID, f"✅ রেফার বোনাস আপডেট হয়েছে!")])

    elif data == "adm_set_minw":
        msg = bot.send_message(ADMIN_ID, "🔻 <b>সর্বনিম্ন উইথড্র লিমিট লিখুন (যেমন: 15):</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"min_withdraw": float(m.text.strip())}), bot.send_message(ADMIN_ID, f"✅ মিনিমাম উইথড্র আপডেট হয়েছে!")])

    elif data == "adm_set_dailyb":
        msg = bot.send_message(ADMIN_ID, "🎁 <b>ডেইলি বোনাস পরিমাণ লিখুন (যেমন: 0.1):</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"daily_bonus": float(m.text.strip())}), bot.send_message(ADMIN_ID, f"✅ ডেইলি বোনাস আপডেট হয়েছে!")])

    elif data == "adm_set_photo_prompt":
        msg = bot.send_message(ADMIN_ID, "🖼️ <b>ছবির ডাইরেক্ট URL লিংক পাঠান:</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"photo": m.text.strip()}), bot.send_message(ADMIN_ID, "✅ ব্যানার ফটো সফলভাবে আপডেট হয়েছে!")])

    elif data == "adm_set_support":
        msg = bot.send_message(ADMIN_ID, "☎️ <b>নতুন সাপোর্ট মেসেজ লিখে পাঠান:</b>")
        bot.register_next_step_handler(msg, lambda m: [update_settings({"support": m.text.strip()}), bot.send_message(ADMIN_ID, "✅ সাপোর্ট টেক্সট আপডেট হয়েছে!")])

    elif data == "adm_broadcast":
        msg = bot.send_message(ADMIN_ID, "📢 <b>সকল ইউজারের কাছে ব্রডকাস্ট করার মেসেজটি পাঠান:</b>")
        bot.register_next_step_handler(msg, do_broadcast_step)

# --- 👑 ADMIN STEP HANDLERS ---
def process_add_channel_step(message):
    try:
        parts = message.text.split(maxsplit=2)
        ch_id = parts[0]
        url = parts[1]
        title = parts[2] if len(parts) > 2 else "JOIN"
        save_channel_to_db(ch_id, url, title)
        bot.send_message(ADMIN_ID, f"✅ <b>চ্যানেল সফলভাবে যুক্ত হয়েছে!</b>\n📢 {title} ({ch_id})", reply_markup=admin_main_menu_markup())
    except:
        bot.send_message(ADMIN_ID, "⚠️ ভুল ফরম্যাট! আবার চেষ্টা করুন।")

def search_user_step(message):
    uid = message.text.strip()
    u = get_user(uid)
    if not u:
        bot.send_message(ADMIN_ID, "❌ এই আইডিতে কোনো ইউজার পাওয়া যায়নি।")
        return
    currency = CACHE["settings"].get("currency", "bKash")
    msg = f"""👤 <b>ইউজার প্রোফাইল:</b> <code>{uid}</code>
━━━━━━━━━━━━━━━━━━━━━
📝 <b>নাম:</b> {u.get('name', 'N/A')}
🔗 <b>ইউজারনেম:</b> @{u.get('username', 'N/A')}
💰 <b>ব্যালেন্স:</b> {float(u.get('balance', 0)):.2f} {currency}
👥 <b>রেফার সংখ্যা:</b> {u.get('ref_count', 0)} জন
💳 <b>ওয়ালেট:</b> <code>{u.get('wallet', 'Not Set')}</code>
🚫 <b>স্ট্যাটাস:</b> {u.get('status', 'active')}"""
    bot.send_message(ADMIN_ID, msg)

def admin_add_balance_step(message):
    try:
        uid, amt = message.text.split()
        amt = float(amt)
        u = get_user(uid)
        new_bal = float(u.get("balance", 0)) + amt
        currency = CACHE["settings"].get("currency", "bKash")
        update_user(uid, {"balance": new_bal})
        bot.send_message(ADMIN_ID, f"✅ ইউজার <code>{uid}</code> কে <b>{amt} {currency}</b> দেওয়া হয়েছে!\nনতুন ব্যালেন্স: <b>{new_bal:.2f} {currency}</b>")
        try:
            bot.send_message(uid, f"🎁 <b>এডমিন আপনার অ্যাকাউন্টে +{amt} {currency} যোগ করেছেন!</b>")
        except:
            pass
    except:
        bot.send_message(ADMIN_ID, "⚠️ ভুল ফরম্যাট! উদাহরণ: <code>5889152252 50</code>")

def admin_cut_balance_step(message):
    try:
        uid, amt = message.text.split()
        amt = float(amt)
        u = get_user(uid)
        new_bal = max(0.0, float(u.get("balance", 0)) - amt)
        currency = CACHE["settings"].get("currency", "bKash")
        update_user(uid, {"balance": new_bal})
        bot.send_message(ADMIN_ID, f"✅ ইউজার <code>{uid}</code> থেকে <b>{amt} {currency}</b> কর্তন করা হয়েছে!\nনতুন ব্যালেন্স: <b>{new_bal:.2f} {currency}</b>")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ভুল ফরম্যাট! উদাহরণ: <code>5889152252 20</code>")

def do_broadcast_step(message):
    users = get_all_users()
    count = 0
    for uid in users:
        try:
            bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"📣 <b>ব্রডকাস্ট সম্পন্ন! {count} জন ইউজারের কাছে সফলভাবে পাঠানো হয়েছে।</b>")

# --- 🚀 RUN ENGINE ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Turbo Refer Bot is running...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except:
        pass

    while True:
        try:
            bot.infinity_polling(timeout=15, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)
