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

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- 🌐 FLASK KEEP-ALIVE SERVER (Render 24/7) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Refer & Admin Bot is Running 24/7 with UptimeRobot!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 🗄️ FIREBASE DATABASE FUNCTIONS ---
def get_settings():
    try:
        res = requests.get(f"{FIREBASE_URL}/settings.json", timeout=5)
        data = res.json() or {}
        return {
            "lang": data.get("lang", "bn"),
            "photo": data.get("photo", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"),
            "support": data.get("support", "☎️ <b>উইথড্র দেওয়ার ২৪ ঘন্টার মধ্যে পেমেন্ট না পেলে যোগাযোগ করুন:</b>\n👤 @Promoter_from_bd\n\n📢 <b>উইথড্র দেওয়ার পর অবশ্যই নক দিবেন:</b> @FHx_Technical_Creator"),
            "min_withdraw": float(data.get("min_withdraw", 10.0)),
            "refer_bonus": float(data.get("refer_bonus", 1.0))
        }
    except:
        return {
            "lang": "bn",
            "photo": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800",
            "support": "☎️ <b>উইথড্র দেওয়ার ২৪ ঘন্টার মধ্যে পেমেন্ট না পেলে যোগাযোগ করুন:</b>\n👤 @Promoter_from_bd\n\n📢 <b>উইথড্র দেওয়ার পর অবশ্যই নক দিবেন:</b> @FHx_Technical_Creator",
            "min_withdraw": 10.0,
            "refer_bonus": 1.0
        }

def update_settings(data):
    try:
        requests.patch(f"{FIREBASE_URL}/settings.json", json=data, timeout=5)
    except Exception as e:
        print(f"Error updating settings: {e}")

def get_user(user_id):
    try:
        res = requests.get(f"{FIREBASE_URL}/users/{user_id}.json", timeout=5)
        return res.json() or {}
    except:
        return {}

def update_user(user_id, data):
    try:
        requests.patch(f"{FIREBASE_URL}/users/{user_id}.json", json=data, timeout=5)
    except Exception as e:
        print(f"Error updating user: {e}")

def delete_user_from_db(user_id):
    try:
        requests.delete(f"{FIREBASE_URL}/users/{user_id}.json", timeout=5)
        return True
    except:
        return False

def get_all_users():
    try:
        res = requests.get(f"{FIREBASE_URL}/users.json", timeout=5)
        data = res.json()
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return {str(i): v for i, v in enumerate(data) if v is not None}
        return {}
    except:
        return {}

def save_withdrawal(w_id, data):
    try:
        requests.put(f"{FIREBASE_URL}/withdrawals/{w_id}.json", json=data, timeout=5)
    except Exception as e:
        print(f"Error saving withdrawal: {e}")

def get_withdrawal(w_id):
    try:
        res = requests.get(f"{FIREBASE_URL}/withdrawals/{w_id}.json", timeout=5)
        return res.json()
    except:
        return None

# --- 📢 DYNAMIC CHANNELS MANAGEMENT ---
def get_channels():
    try:
        res = requests.get(f"{FIREBASE_URL}/channels.json", timeout=5)
        data = res.json()
        clean_channels = {}
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    clean_channels[k] = v
                elif isinstance(v, str) and not v.startswith("{"):
                    clean_channels[k] = {
                        "channel_id": v,
                        "url": f"https://t.me/{v.replace('@', '')}",
                        "title": "🔗 Join Channel"
                    }
        return clean_channels
    except:
        return {}

def save_channel_to_db(ch_id, url, title):
    try:
        clean_key = ch_id.replace("@", "").replace("-", "_").replace(".", "_")
        payload = {"channel_id": ch_id, "url": url, "title": title}
        requests.put(f"{FIREBASE_URL}/channels/{clean_key}.json", json=payload, timeout=5)
        return True
    except:
        return False

def remove_channel_from_db(ch_id):
    try:
        clean_key = ch_id.replace("@", "").replace("-", "_").replace(".", "_")
        requests.delete(f"{FIREBASE_URL}/channels/{clean_key}.json", timeout=5)
        return True
    except:
        return False

# --- 🔍 STRICT MEMBERSHIP CHECK ---
def is_joined(user_id):
    channels = get_channels()
    if not channels:
        channels = {"default": {"channel_id": DEFAULT_CHANNEL_ID}}

    for key, ch in channels.items():
        ch_id = ch.get("channel_id") if isinstance(ch, dict) else ch
        if not ch_id or not isinstance(ch_id, str):
            continue
        try:
            member = bot.get_chat_member(ch_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Channel check error for {ch_id}: {e}")
            return False
    return True

# --- 🌐 LANGUAGE DICTIONARY ---
TEXTS = {
    "bn": {
        "access_title": "🔒 <b>প্রবেশাধিকার সীমিত</b>\n━━━━━━━━━━━━━━━━━━━━━\n⚠️ <b>বটের সকল ফিচার ব্যবহার করতে নিচের চ্যানেলে জয়েন করুন।</b>\n\n📢 <b>নিচের বাটনে ক্লিক করে চ্যানেলে সাবস্ক্রাইব করুন।</b>\n\n✅ <b>জয়েন করার পর 'ভেরিফাই করুন' বাটনে চাপ দিন।</b>",
        "verify_btn": "✅ ভেরিফাই করুন",
        "verify_success": "🎉 <b>ভেরিফিকেশন সফল হয়েছে! মেইন মেনুতে স্বাগতম।</b>",
        "verify_fail": "❌ আপনি এখনো আমাদের চ্যানেলে জয়েন করেননি! আগে জয়েন করুন।",
        "acc_btn": "🖥️ একাউন্ট",
        "ref_btn": "⚡ রেফারেল",
        "wall_btn": "💳 ওয়ালেট",
        "with_btn": "💲 উইথড্র",
        "supp_btn": "SUPPORT 💸",
        "stat_btn": "📊 স্ট্যাটাস",
        "ref_bonus_msg": "💰 <b>নতুন ইউজার রেফার করার জন্য আপনি {bonus} টাকা বোনাস পেয়েছেন!</b>",
        "set_wallet_prompt": "📝 <b>অনুগ্রহ করে আপনার বিকাশ/নগদ নম্বর লিখুন:</b>",
        "wallet_saved": "✅ <b>আপনার ওয়ালেট সফলভাবে সেট হয়েছে:</b>",
        "min_with_err": "❌ সর্বনিম্ন উইথড্র পরিমাণ {min_w} টাকা।",
        "with_prompt": "💰 <b>সর্বনিম্ন:</b> {min_w} টাকা\n🚀 <b>বর্তমান ব্যালেন্স:</b> {bal} টাকা\n\n📝 <b>আপনি কত টাকা উইথড্র করতে চান লিখুন:</b>",
        "with_success": "উইথড্র রিকোয়েস্ট সফল হয়েছে ✅\n\n💰 <b>পরিমাণ:</b> {amt} টাকা\n⏳ <b>পেমেন্ট স্ট্যাটাস:</b> Pending\n💳 <b>ওয়ালেট:</b> <code>{wal}</code>\n🔖 <b>রিকোয়েস্ট আইডি:</b> <code>{wid}</code>\n\n<i>এডমিন শীঘ্রই আপনার পেমেন্ট ভেরিফাই করে পাঠিয়ে দিবে।</i>"
    },
    "en": {
        "access_title": "🔒 <b>Access Restricted</b>\n━━━━━━━━━━━━━━━━━━━━━\n⚠️ <b>You must join all our channels to unlock bot features.</b>\n\n📢 <b>Subscribe to every channel using the buttons below.</b>\n\n✅ <b>After joining all channels, tap the Verify Membership button.</b>",
        "verify_btn": "✅ Verify Membership",
        "verify_success": "🎉 <b>Membership Verified! Welcome to the main menu.</b>",
        "verify_fail": "❌ You haven't joined all channels yet! Please join first.",
        "acc_btn": "🖥️ Account",
        "ref_btn": "⚡ Referral",
        "wall_btn": "💳 Wallet",
        "with_btn": "💲 Withdrawal",
        "supp_btn": "SUPPORT 💸",
        "stat_btn": "📊 Status",
        "ref_bonus_msg": "💰 <b>You have received {bonus} Taka for referring a new user!</b>",
        "set_wallet_prompt": "📝 <b>Please Enter Your Bkash/Nagad Number:</b>",
        "wallet_saved": "✅ <b>Wallet successfully updated to:</b>",
        "min_with_err": "❌ Minimum withdrawal amount is {min_w} Taka.",
        "with_prompt": "💰 <b>Minimum:</b> {min_w} Taka\n🚀 <b>Balance:</b> {bal} Taka\n\n📝 <b>Enter the amount you want to withdraw:</b>",
        "with_success": "Withdrawal Request Successful ✅\n\n💰 <b>Amount:</b> {amt} Taka\n⏳ <b>Payment Status:</b> Pending\n💳 <b>Wallet:</b> <code>{wal}</code>\n🔖 <b>Request ID:</b> <code>{wid}</code>\n\n<i>Admin will verify and process your payment shortly.</i>"
    }
}

def get_t(key):
    settings = get_settings()
    lang = settings.get("lang", "bn")
    return TEXTS.get(lang, TEXTS["bn"]).get(key, "")

# --- ⌨️ KEYBOARDS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(get_t("acc_btn"), get_t("ref_btn"))
    markup.add(get_t("wall_btn"), get_t("with_btn"))
    markup.add(get_t("supp_btn"))
    markup.add(get_t("stat_btn"))
    return markup

def join_keyboard():
    markup = types.InlineKeyboardMarkup()
    channels = get_channels()
    
    valid_channels = False
    if channels:
        for key, ch in channels.items():
            if isinstance(ch, dict) and "url" in ch and "http" in ch.get("url", ""):
                btn_title = ch.get("title", "🔗 Join Channel 1")
                btn_url = ch.get("url")
                if "deactivated" not in btn_url and "error" not in btn_url:
                    markup.add(types.InlineKeyboardButton(btn_title, url=btn_url))
                    valid_channels = True
        
    if not valid_channels:
        markup.add(types.InlineKeyboardButton("🔗 Join Channel 1", url=DEFAULT_CHANNEL_URL))
        
    markup.add(types.InlineKeyboardButton(get_t("verify_btn"), callback_data="verify_membership"))
    return markup

# --- 🚀 START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    text_split = message.text.split()
    user_data = get_user(user_id)
    settings = get_settings()

    first_name = message.from_user.first_name or "No Name"
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
            "status": "active"
        }
        if len(text_split) > 1 and text_split[1] != user_id:
            new_data["referred_by"] = text_split[1]
        update_user(user_id, new_data)

    welcome_text = get_t("access_title")
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
        settings = get_settings()
        refer_bonus = settings.get("refer_bonus", 1.0)
        
        referrer_id = user_data.get("referred_by")
        if referrer_id and not user_data.get("bonus_claimed"):
            ref_data = get_user(referrer_id)
            if ref_data:
                new_balance = float(ref_data.get("balance", 0)) + refer_bonus
                new_ref_count = int(ref_data.get("ref_count", 0)) + 1
                update_user(referrer_id, {"balance": new_balance, "ref_count": new_ref_count})
                
                try:
                    bonus_msg = get_t("ref_bonus_msg").format(bonus=refer_bonus)
                    bot.send_message(referrer_id, bonus_msg)
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

# --- 📱 USER MENU HANDLERS ---
@bot.message_handler(func=lambda m: m.text in ["🖥️ একাউন্ট", "🖥️ Account"])
def account(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    first_name = message.from_user.first_name or "No Name"
    username = message.from_user.username or "No Username"
    
    balance = user_data.get("balance", 0.0)
    wallet = user_data.get("wallet", "Not Set")

    settings = get_settings()
    if settings.get("lang") == "en":
        msg = f"""🙍‍♂️ <b>Your Name:</b> {first_name}\n🔥 <b>Username:</b> @{username}\n🚀 <b>User ID:</b> <code>{user_id}</code>\n💳 <b>Wallet:</b> <code>{wallet}</code>\n💰 <b>Balance:</b> {balance} Taka"""
    else:
        msg = f"""🙍‍♂️ <b>আপনার নাম:</b> {first_name}\n🔥 <b>ইউজারনেম:</b> @{username}\n🚀 <b>ইউজার আইডি:</b> <code>{user_id}</code>\n💳 <b>ওয়ালেট:</b> <code>{wallet}</code>\n💰 <b>ব্যালেন্স:</b> {balance} টাকা"""
    bot.send_message(user_id, msg)

@bot.message_handler(func=lambda m: m.text in ["⚡ রেফারেল", "⚡ Referral"])
def referral(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    ref_bonus = settings.get("refer_bonus", 1.0)
    
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = user_data.get("ref_count", 0)

    if settings.get("lang") == "en":
        msg = f"""🏅 <b>Per Referral:</b> {ref_bonus} Taka\n\n📎 <b>Your Referral Link:</b>\n{ref_link}\n\n📊 <b>Your Total Referrals:</b> {ref_count}\n\n🚫 <i>Fake and cheat referrals will not be paid</i>"""
    else:
        msg = f"""🏅 <b>প্রতি রেফার:</b> {ref_bonus} টাকা\n\n📎 <b>আপনার রেফারেল লিংক:</b>\n{ref_link}\n\n📊 <b>আপনার মোট রেফার:</b> {ref_count} জন\n\n🚫 <i>ফেক বা চিটিং রেফার করলে পেমেন্ট পাবেন না</i>"""
    bot.send_message(user_id, msg)

@bot.message_handler(func=lambda m: m.text in ["💳 ওয়ালেট", "💳 Wallet"])
def wallet(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    current_wallet = user_data.get("wallet", "Not Set")

    settings = get_settings()
    if settings.get("lang") == "en":
        msg = f"""💳 <b>Current Wallet:</b> <code>{current_wallet}</code>\n\n⚙️ To set or change your wallet, click here: /SetWallet"""
    else:
        msg = f"""💳 <b>বর্তমান ওয়ালেট:</b> <code>{current_wallet}</code>\n\n⚙️ ওয়ালেট পরিবর্তন করতে এখানে চাপুন: /SetWallet"""
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

# --- 📊 STATUS ---
@bot.message_handler(func=lambda m: m.text in ["📊 স্ট্যাটাস", "📊 Status"])
def status(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    
    ref_bonus = settings.get("refer_bonus", 1.0)
    min_w = settings.get("min_withdraw", 10.0)
    ref_count = user_data.get("ref_count", 0)
    balance = user_data.get("balance", 0.0)

    msg = f"""📊 <b>Status</b>

• 💰 <b>Per Referral:</b> ৳{ref_bonus}
• 👥 <b>Your Referrals:</b> {ref_count}
• 💵 <b>Your Earnings:</b> ৳{balance}
• 💳 <b>Minimum Withdrawal:</b> ৳{min_w}
• 🟢 <b>Payment Status:</b> Active"""
    bot.send_message(user_id, msg)

# --- 💲 WITHDRAWAL SYSTEM (শুধুমাত্র এডমিনের কাছে মেসেজ যাবে) ---
@bot.message_handler(func=lambda m: m.text in ["💲 উইথড্র", "💲 Withdrawal"])
def withdraw_prompt(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    settings = get_settings()
    
    balance = float(user_data.get("balance", 0))
    min_withdraw = settings.get("min_withdraw", 10.0)
    wallet = user_data.get("wallet", "Not Set")

    if wallet == "Not Set":
        bot.send_message(user_id, "😎 Please set your wallet first with /SetWallet.")
        return

    if balance < min_withdraw:
        err_text = get_t("min_with_err").format(min_w=min_withdraw)
        bot.send_message(user_id, err_text)
        return

    msg_text = get_t("with_prompt").format(min_w=min_withdraw, bal=balance)
    msg = bot.send_message(user_id, msg_text)
    bot.register_next_step_handler(msg, process_withdraw, balance, wallet, min_withdraw)

def process_withdraw(message, balance, wallet, min_withdraw):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text.strip())
    except ValueError:
        bot.send_message(user_id, "⚠️ Invalid amount! Please enter numbers only.")
        return

    if amount < min_withdraw:
        err_text = get_t("min_with_err").format(min_w=min_withdraw)
        bot.send_message(user_id, err_text)
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

    # শুধুমাত্র এডমিনের ইনবক্সে রিকোয়েস্ট বাটন পাঠানো
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        types.InlineKeyboardButton("✅ Confirm / Paid", callback_data=f"appr_{w_id}"),
        types.InlineKeyboardButton("❌ Reject / Refund", callback_data=f"rej_{w_id}")
    )
    admin_text = f"""🔔 <b>New Withdrawal Request!</b>\n\n🆔 <b>User ID:</b> <code>{user_id}</code>\n👤 <b>Username:</b> @{username}\n💰 <b>Amount:</b> {amount} টাকা\n💳 <b>Wallet:</b> <code>{wallet}</code>\n🔖 <b>Trx ID:</b> <code>{w_id}</code>"""
    
    try:
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup)
    except Exception as e:
        print(f"Error sending to admin: {e}")

    # ইউজারের কাছে কনফার্মেশন পাঠানো
    success_msg = get_t("with_success").format(amt=amount, wal=wallet, wid=w_id)
    bot.send_message(user_id, success_msg)

# --- 👑 ADMIN ACTION HANDLERS (চ্যানেল ছাড়া শুধু এডমিন ও ইউজারের নোটিফিকেশন) ---
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
    amount = w_data["amount"]
    wallet = w_data["wallet"]

    if action == "appr":
        save_withdrawal(w_id, {**w_data, "status": "Approved"})
        bot.edit_message_text(f"{call.message.text}\n\n✅ <b>STATUS: APPROVED & PAID</b>", call.message.chat.id, call.message.message_id)
        
        # ইউজারের কাছে পেমেন্ট সফল মেসেজ পাঠানো
        try:
            bot.send_message(user_id, f"🎉 <b>আপনার {amount} টাকা উইথড্র সফল হয়েছে এবং পেমেন্ট পাঠানো হয়েছে!</b>\n💳 Wallet: <code>{wallet}</code>")
        except:
            pass

    elif action == "rej":
        user_info = get_user(user_id)
        current_bal = float(user_info.get("balance", 0))
        update_user(user_id, {"balance": current_bal + amount})
        save_withdrawal(w_id, {**w_data, "status": "Rejected"})

        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>STATUS: REJECTED & REFUNDED</b>", call.message.chat.id, call.message.message_id)

        # ইউজারের কাছে রিফান্ড মেসেজ পাঠানো
        try:
            bot.send_message(user_id, f"❌ <b>আপনার {amount} টাকা উইথড্র বাতিল করা হয়েছে এবং টাকা আপনার একাউন্টে রিফান্ড করা হয়েছে।</b>")
        except:
            pass

# --- 👑 ADMIN DYNAMIC SETTINGS COMMANDS ---
@bot.message_handler(commands=['setrefer'])
def admin_set_refer(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        amt = float(message.text.split()[1])
        update_settings({"refer_bonus": amt})
        bot.send_message(ADMIN_ID, f"✅ <b>প্রতি রেফারের বোনাস সফলভাবে {amt} টাকা করা হয়েছে!</b>")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/setrefer 2</code> বা <code>/setrefer 5</code>")

@bot.message_handler(commands=['setminwith'])
def admin_set_min_with(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        amt = float(message.text.split()[1])
        update_settings({"min_withdraw": amt})
        bot.send_message(ADMIN_ID, f"✅ <b>সর্বনিম্ন উইথড্র লিমিট সফলভাবে {amt} টাকা করা হয়েছে!</b>")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/setminwith 20</code> বা <code>/setminwith 50</code>")

@bot.message_handler(commands=['setphoto'])
def admin_set_photo(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        photo_url = message.text.split(maxsplit=1)[1]
        update_settings({"photo": photo_url})
        bot.send_message(ADMIN_ID, f"✅ <b>ব্যানার ফটো সফলভাবে পরিবর্তন হয়েছে!</b>\nনতুন লিংক: {photo_url}")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/setphoto https://example.com/image.jpg</code>")

@bot.message_handler(commands=['setsupport'])
def admin_set_support(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        new_text = message.text.split(maxsplit=1)[1]
        update_settings({"support": new_text})
        bot.send_message(ADMIN_ID, "✅ <b>সাপোর্ট মেসেজ সফলভাবে আপডেট করা হয়েছে!</b>")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/setsupport আপনার_নতুন_মেসেজ</code>")

@bot.message_handler(commands=['setlang'])
def admin_set_lang(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        lang = message.text.split()[1].lower()
        if lang in ["bn", "en"]:
            update_settings({"lang": lang})
            lang_name = "বাংলা" if lang == "bn" else "English"
            bot.send_message(ADMIN_ID, f"✅ <b>বটের ভাষা সফলভাবে {lang_name}-তে পরিবর্তন করা হয়েছে!</b>")
        else:
            bot.send_message(ADMIN_ID, "⚠️ শুধু <code>bn</code> অথবা <code>en</code> লিখুন।")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/setlang bn</code> অথবা <code>/setlang en</code>")

@bot.message_handler(commands=['allusers'])
def admin_all_users(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    users = get_all_users()
    if not users:
        bot.send_message(ADMIN_ID, "ℹ️ ডাটাবেজে কোনো ইউজার নেই।")
        return
    
    report = f"👥 <b>সকল ইউজারের তালিকা (মোট: {len(users)}):</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
    for uid, u in list(users.items())[:50]:
        if isinstance(u, dict):
            name = u.get("name", "N/A")
            bal = u.get("balance", 0)
            wal = u.get("wallet", "Not Set")
            refs = u.get("ref_count", 0)
            report += f"🆔 <code>{uid}</code> | {name} | 💰 {bal}৳ | 💳 {wal} | 👥 {refs}\n"
    
    bot.send_message(ADMIN_ID, report)

# --- SUPPORT BUTTON ---
@bot.message_handler(func=lambda m: m.text == "SUPPORT 💸")
def support(message):
    settings = get_settings()
    bot.send_message(message.chat.id, settings.get("support"))

# --- 👑 OTHER ADMIN COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_help(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    msg = """👑 <b>Admin Control Panel:</b>

💰 <b>রেফারেল ও উইথড্র লিমিট:</b>
🔹 <code>/setrefer &lt;amount&gt;</code> - প্রতি রেফারের টাকা সেট করুন
🔹 <code>/setminwith &lt;amount&gt;</code> - সর্বনিম্ন উইথড্র সেট করুন

🖼️ <b>ছবি ও টেক্সট পরিবর্তন:</b>
🔹 <code>/setphoto &lt;url&gt;</code> - ওয়েলকাম ব্যানার ছবি পরিবর্তন
🔹 <code>/setsupport &lt;text&gt;</code> - সাপোর্ট মেসেজ পরিবর্তন
🔹 <code>/setlang bn</code> বা <code>/setlang en</code> - ভাষা পরিবর্তন

👥 <b>ইউজার ম্যানেজমেন্ট:</b>
🔹 <code>/allusers</code> - সব ইউজারের লিস্ট একসাথে দেখুন
🔹 <code>/user &lt;id&gt;</code> - ইউজারের তথ্য দেখুন
🔹 <code>/addbal &lt;id&gt; &lt;amount&gt;</code> - ব্যালেন্স যোগ করুন
🔹 <code>/cutbal &lt;id&gt; &lt;amount&gt;</code> - ব্যালেন্স কাটুন
🔹 <code>/deluser &lt;id&gt;</code> - ইউজার ডিলিট করুন
🔹 <code>/bcast</code> - সকল ইউজারকে ব্রডকাস্ট করুন

📢 <b>চ্যানেল ম্যানেজমেন্ট:</b>
🔹 <code>/addchannel &lt;id&gt; &lt;link&gt; &lt;title&gt;</code> - নতুন চ্যানেল যোগ
🔹 <code>/delchannel &lt;id&gt;</code> - চ্যানেল ডিলিট
🔹 <code>/channels</code> - চ্যানেল লিস্ট"""
    bot.send_message(ADMIN_ID, msg)

@bot.message_handler(commands=['channels'])
def admin_list_channels(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    channels = get_channels()
    if not channels:
        bot.send_message(ADMIN_ID, "ℹ️ কোনো চ্যানেল সেভ করা নেই।")
        return
    text = "📢 <b>বর্তমান চ্যানেল তালিকা:</b>\n\n"
    for k, v in channels.items():
        if isinstance(v, dict):
            text += f"🔹 <b>Title:</b> {v.get('title')}\n   <b>ID:</b> <code>{v.get('channel_id')}</code>\n   <b>Link:</b> {v.get('url')}\n\n"
    bot.send_message(ADMIN_ID, text)

@bot.message_handler(commands=['addchannel'])
def admin_add_channel(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        parts = message.text.split(maxsplit=3)
        ch_id = parts[1]
        ch_url = parts[2]
        ch_title = parts[3] if len(parts) > 3 else "🔗 Join Channel"
        save_channel_to_db(ch_id, ch_url, ch_title)
        bot.send_message(ADMIN_ID, f"✅ চ্যানেল যুক্ত হয়েছে!\n🔹 ID: <code>{ch_id}</code>")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/addchannel @username https://t.me/link বাটনের_নাম</code>")

@bot.message_handler(commands=['delchannel'])
def admin_del_channel(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        ch_id = message.text.split()[1]
        remove_channel_from_db(ch_id)
        bot.send_message(ADMIN_ID, f"🗑️ চ্যানেল <code>{ch_id}</code> ডিলিট করা হয়েছে।")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/delchannel @username</code>")

@bot.message_handler(commands=['user'])
def admin_view_user(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        uid = message.text.split()[1]
        u = get_user(uid)
        if not u:
            bot.send_message(ADMIN_ID, "❌ User not found.")
            return
        msg = f"""👤 <b>User Info:</b> <code>{uid}</code>\n📝 <b>Name:</b> {u.get('name', 'N/A')}\n🔗 <b>Username:</b> @{u.get('username', 'N/A')}\n💰 <b>Balance:</b> {u.get('balance', 0)} টাকা\n👥 <b>Total Refer:</b> {u.get('ref_count', 0)}\n💳 <b>Wallet:</b> <code>{u.get('wallet', 'Not Set')}</code>"""
        bot.send_message(ADMIN_ID, msg)
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/user 123456789</code>")

@bot.message_handler(commands=['addbal'])
def admin_add_balance(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        _, uid, amt = message.text.split()
        amt = float(amt)
        u = get_user(uid)
        if not u:
            bot.send_message(ADMIN_ID, "❌ User not found.")
            return
        new_bal = float(u.get("balance", 0)) + amt
        update_user(uid, {"balance": new_bal})
        bot.send_message(ADMIN_ID, f"✅ Added {amt} টাকা. New Balance: {new_bal}")
        bot.send_message(uid, f"🎁 <b>Admin has added {amt} টাকা to your balance!</b>")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/addbal 123456789 10</code>")

@bot.message_handler(commands=['cutbal'])
def admin_cut_balance(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        _, uid, amt = message.text.split()
        amt = float(amt)
        u = get_user(uid)
        if not u:
            bot.send_message(ADMIN_ID, "❌ User not found.")
            return
        new_bal = max(0.0, float(u.get("balance", 0)) - amt)
        update_user(uid, {"balance": new_bal})
        bot.send_message(ADMIN_ID, f"✅ Deducted {amt} টাকা. New Balance: {new_bal}")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/cutbal 123456789 10</code>")

@bot.message_handler(commands=['deluser'])
def admin_delete_user(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        uid = message.text.split()[1]
        delete_user_from_db(uid)
        bot.send_message(ADMIN_ID, f"🗑️ User <code>{uid}</code> ডিলিট করা হয়েছে।")
    except:
        bot.send_message(ADMIN_ID, "⚠️ ব্যবহার: <code>/deluser 123456789</code>")

@bot.message_handler(commands=['bcast'])
def bcast_prompt(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "🔍 <b>Send or Forward the message to broadcast:</b>")
    bot.register_next_step_handler(msg, send_broadcast)

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

# --- 🚀 RUN BOT ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is starting polling...")
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(2)
    except Exception as e:
        print(f"Webhook clear error: {e}")

    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Polling conflict/error: {e}")
            time.sleep(5)
