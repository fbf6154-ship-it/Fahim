import os
import threading
import time
import requests
from flask import Flask
import telebot
from telebot import types

# --- ⚙️ CONFIGURATION ---
BOT_TOKEN = os.environ.get("TOKEN", "8866225707:AAF5pFN98buwo2ygG3GYhhCjuU0u71CX3aE")
ADMIN_ID = "7166927766"  # আপনার এডমিন আইডি
PAYMENT_CHANNEL = "@tbpycofficial"  # নোটিফিকেশন চ্যানেল

# Firebase Realtime Database URL
FIREBASE_URL = "https://tournament-ace22-default-rtdb.asia-southeast1.firebasedatabase.app"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- 🌐 FLASK KEEP-ALIVE SERVER (Render 24/7) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Refer & Admin Bot with Dynamic Channels is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 🗄️ FIREBASE DATABASE FUNCTIONS ---
def get_user(user_id):
    try:
        res = requests.get(f"{FIREBASE_URL}/users/{user_id}.json")
        return res.json() or {}
    except:
        return {}

def update_user(user_id, data):
    try:
        requests.patch(f"{FIREBASE_URL}/users/{user_id}.json", json=data)
    except Exception as e:
        print(f"Error updating user: {e}")

def delete_user_from_db(user_id):
    try:
        requests.delete(f"{FIREBASE_URL}/users/{user_id}.json")
        return True
    except:
        return False

def get_all_users():
    try:
        res = requests.get(f"{FIREBASE_URL}/users.json")
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
        requests.put(f"{FIREBASE_URL}/withdrawals/{w_id}.json", json=data)
    except Exception as e:
        print(f"Error saving withdrawal: {e}")

def get_withdrawal(w_id):
    try:
        res = requests.get(f"{FIREBASE_URL}/withdrawals/{w_id}.json")
        return res.json()
    except:
        return None

# --- 📢 SAFE DYNAMIC CHANNELS MANAGEMENT ---
def get_channels():
    try:
        res = requests.get(f"{FIREBASE_URL}/channels.json")
        data = res.json()
        clean_channels = {}
        
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    clean_channels[k] = v
                elif isinstance(v, str):
                    clean_channels[k] = {
                        "channel_id": v,
                        "url": f"https://t.me/{v.replace('@', '')}",
                        "title": "🔗 Join Channel"
                    }
        elif isinstance(data, list):
            for i, v in enumerate(data):
                if isinstance(v, dict):
                    clean_channels[str(i)] = v
                elif isinstance(v, str):
                    clean_channels[str(i)] = {
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
        payload = {
            "channel_id": ch_id,
            "url": url,
            "title": title
        }
        requests.put(f"{FIREBASE_URL}/channels/{clean_key}.json", json=payload)
        return True
    except:
        return False

def remove_channel_from_db(ch_id):
    try:
        clean_key = ch_id.replace("@", "").replace("-", "_").replace(".", "_")
        requests.delete(f"{FIREBASE_URL}/channels/{clean_key}.json")
        return True
    except:
        return False

# --- 🔍 DYNAMIC CHANNEL MEMBERSHIP CHECK ---
def is_joined(user_id):
    channels = get_channels()
    if not channels:
        return True

    for key, ch in channels.items():
        if isinstance(ch, dict):
            ch_id = ch.get("channel_id")
        elif isinstance(ch, str):
            ch_id = ch
        else:
            continue

        if not ch_id:
            continue

        try:
            member = bot.get_chat_member(ch_id, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            pass
    return True

# --- ⌨️ KEYBOARDS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🖥️ Account", "⚡ Referral")
    markup.add("💳 Wallet", "💲 Withdrawal")
    markup.add("SUPPORT 💸")
    markup.add("📊 Status")
    return markup

def join_keyboard():
    markup = types.InlineKeyboardMarkup()
    channels = get_channels()
    
    if not channels:
        markup.add(types.InlineKeyboardButton("🔗 Join Channel 1", url="https://t.me/tbpycofficial"))
    else:
        for key, ch in channels.items():
            if isinstance(ch, dict):
                btn_title = ch.get("title", "🔗 Join Channel")
                btn_url = ch.get("url", "https://t.me/tbpycofficial")
                markup.add(types.InlineKeyboardButton(btn_title, url=btn_url))
        
    markup.add(types.InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership"))
    return markup

# --- 🚀 START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    text_split = message.text.split()
    user_data = get_user(user_id)

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

    welcome_text = """🔒 <b>Access Restricted</b>
━━━━━━━━━━━━━━━━━━━━━
⚠️ <b>You must join all our channels to unlock bot features.</b>

📢 <b>Subscribe to every channel using the buttons below.</b>

✅ <b>After joining all channels, tap the Verify Membership button.</b>"""

    img_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"

    try:
        bot.send_photo(
            user_id,
            photo=img_url,
            caption=welcome_text,
            reply_markup=join_keyboard()
        )
    except Exception:
        bot.send_message(
            user_id,
            welcome_text,
            reply_markup=join_keyboard()
        )

# --- 🔍 VERIFY MEMBERSHIP CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_callback(call):
    user_id = str(call.from_user.id)
    if is_joined(user_id):
        user_data = get_user(user_id)
        
        referrer_id = user_data.get("referred_by")
        if referrer_id and not user_data.get("bonus_claimed"):
            ref_data = get_user(referrer_id)
            if ref_data:
                new_balance = float(ref_data.get("balance", 0)) + 1.0
                new_ref_count = int(ref_data.get("ref_count", 0)) + 1
                update_user(referrer_id, {"balance": new_balance, "ref_count": new_ref_count})
                
                try:
                    bot.send_message(referrer_id, "💰 <b>You have received 1 টাকা for referring a new user!</b>")
                except:
                    pass
            update_user(user_id, {"bonus_claimed": True})

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(
            user_id,
            "🎉 <b>Membership Verified! Welcome to the main menu.</b>",
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined all channels yet! Please join first.", show_alert=True)

# --- 📱 USER MENU HANDLERS ---
@bot.message_handler(func=lambda m: m.text == "🖥️ Account")
def account(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    first_name = message.from_user.first_name or "No Name"
    username = message.from_user.username or "No Username"
    
    balance = user_data.get("balance", 0.0)
    wallet = user_data.get("wallet", "Not Set")

    msg = f"""🙍‍♂️ <b>Your Name:</b> {first_name}
🔥 <b>Username:</b> @{username}
🚀 <b>User ID:</b> <code>{user_id}</code>
💳 <b>Wallet:</b> <code>{wallet}</code>
💰 <b>Balance:</b> {balance} টাকা"""
    bot.send_message(user_id, msg)

@bot.message_handler(func=lambda m: m.text == "⚡ Referral")
def referral(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = user_data.get("ref_count", 0)

    msg = f"""🏅 <b>Per Referral:</b> 1 টাকা

📎 <b>Your Referral Link:</b>
{ref_link}

📊 <b>Your Total Referrals:</b> {ref_count} টি

🚫 <i>Fake and cheat referrals will not be paid</i>"""
    bot.send_message(user_id, msg)

@bot.message_handler(func=lambda m: m.text == "💳 Wallet")
def wallet(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    current_wallet = user_data.get("wallet", "Not Set")

    msg = f"""💳 <b>Current Wallet:</b> <code>{current_wallet}</code>

⚙️ If you want to set or change your wallet, click here: /SetWallet"""
    bot.send_message(user_id, msg)

@bot.message_handler(commands=['SetWallet'])
def set_wallet_prompt(message):
    msg = bot.send_message(message.chat.id, "📝 <b>Please Enter Your Bkash/Nagad Number:</b>")
    bot.register_next_step_handler(msg, save_wallet)

def save_wallet(message):
    user_id = str(message.chat.id)
    wallet_number = message.text.strip()
    update_user(user_id, {"wallet": wallet_number})
    bot.send_message(user_id, f"✅ <b>Wallet successfully updated to:</b> <code>{wallet_number}</code>", reply_markup=main_menu())

# --- 💲 WITHDRAWAL & ADMIN APPROVAL ---
@bot.message_handler(func=lambda m: m.text == "💲 Withdrawal")
def withdraw_prompt(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    balance = float(user_data.get("balance", 0))
    wallet = user_data.get("wallet", "Not Set")

    if wallet == "Not Set":
        bot.send_message(user_id, "😎 Please set your wallet first with /SetWallet.")
        return

    if balance < 10:
        bot.send_message(user_id, f"❌ Minimum withdrawal amount is 10 টাকা.\nYour Balance: {balance} টাকা")
        return

    msg = bot.send_message(user_id, f"💰 <b>Minimum:</b> 10 টাকা\n🚀 <b>Your Balance:</b> {balance} টাকা\n\n📝 আপনি কত টাকা উইথড্র করবেন তা পরিমাণ লিখুন:")
    bot.register_next_step_handler(msg, process_withdraw, balance, wallet)

def process_withdraw(message, balance, wallet):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text.strip())
    except ValueError:
        bot.send_message(user_id, "⚠️ Invalid amount! Please enter numbers only.")
        return

    if amount < 10:
        bot.send_message(user_id, "❌ Minimum withdrawal is 10 টাকা.")
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
    admin_text = f"""🔔 <b>New Withdrawal Request!</b>

🆔 <b>User ID:</b> <code>{user_id}</code>
👤 <b>Username:</b> @{username}
💰 <b>Amount:</b> {amount} টাকা
💳 <b>Wallet:</b> <code>{wallet}</code>
🔖 <b>Trx ID:</b> <code>{w_id}</code>"""
    
    try:
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_markup)
    except:
        pass

    bot.send_message(user_id, f"""Withdrawal Request Successful ✅

💰 <b>Amount:</b> {amount} টাকা
⏳ <b>Payment Status:</b> Pending
💳 <b>Wallet:</b> <code>{wallet}</code>
🔖 <b>Request ID:</b> <code>{w_id}</code>

🔗 <b>Payment Channel:</b> {PAYMENT_CHANNEL}""")

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
    amount = w_data["amount"]
    wallet = w_data["wallet"]
    username = w_data["username"]

    if action == "appr":
        save_withdrawal(w_id, {**w_data, "status": "Approved"})
        bot.edit_message_text(f"{call.message.text}\n\n✅ <b>STATUS: APPROVED & PAID</b>", call.message.chat.id, call.message.message_id)
        
        try:
            bot.send_message(user_id, f"🎉 <b>আপনার {amount} টাকা উইথড্র সফল হয়েছে এবং পেমেন্ট পাঠানো হয়েছে!</b>\n💳 Wallet: <code>{wallet}</code>")
        except:
            pass

        try:
            channel_msg = f"""Withdrawal Completed ✅

🚀 <b>User ID:</b> <code>{user_id}</code>
🔥 <b>Username:</b> @{username}
💰 <b>Amount:</b> {amount} টাকা
⏳ <b>Payment Status:</b> Approved / Paid
💳 <b>Wallet:</b> <code>{wallet}</code>"""
            bot.send_message(PAYMENT_CHANNEL, channel_msg)
        except:
            pass

    elif action == "rej":
        user_info = get_user(user_id)
        current_bal = float(user_info.get("balance", 0))
        update_user(user_id, {"balance": current_bal + amount})
        save_withdrawal(w_id, {**w_data, "status": "Rejected"})

        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>STATUS: REJECTED & REFUNDED</b>", call.message.chat.id, call.message.message_id)

        try:
            bot.send_message(user_id, f"❌ <b>আপনার {amount} টাকা উইথড্র বাতিল করা হয়েছে এবং টাকা রিফান্ড করা হয়েছে।</b>")
        except:
            pass

# --- 👑 ADMIN DYNAMIC CHANNELS ---
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
        bot.send_message(ADMIN_ID, f"✅ চ্যানেল সফলভাবে যুক্ত হয়েছে!\n\n🔹 Title: {ch_title}\n🔹 ID: <code>{ch_id}</code>\n🔹 Link: {ch_url}")
    except:
        bot.send_message(ADMIN_ID, "⚠️ <b>ব্যবহার:</b>\n<code>/addchannel @channel_username https://t.me/link বাটনের_নাম</code>")

@bot.message_handler(commands=['delchannel'])
def admin_del_channel(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    try:
        ch_id = message.text.split()[1]
        remove_channel_from_db(ch_id)
        bot.send_message(ADMIN_ID, f"🗑️ চ্যানেল <code>{ch_id}</code> ডিলিট করা হয়েছে।")
    except:
        bot.send_message(ADMIN_ID, "⚠️ <b>ব্যবহার:</b>\n<code>/delchannel @channel_username</code>")

# --- 👑 OTHER ADMIN COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_help(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    msg = """👑 <b>Admin Control Panel:</b>

📢 <b>চ্যানেল ম্যানেজমেন্ট:</b>
🔹 <code>/addchannel &lt;id&gt; &lt;link&gt; &lt;title&gt;</code> - নতুন চ্যানেল যোগ
🔹 <code>/delchannel &lt;id&gt;</code> - চ্যানেল ডিলিট
🔹 <code>/channels</code> - চ্যানেল লিস্ট

👤 <b>ইউজার কন্ট্রোল:</b>
🔹 <code>/user &lt;id&gt;</code> - ইউজারের ডাটা দেখুন
🔹 <code>/addbal &lt;id&gt; &lt;amount&gt;</code> - ব্যালেন্স দিন
🔹 <code>/cutbal &lt;id&gt; &lt;amount&gt;</code> - ব্যালেন্স কাটুন
🔹 <code>/deluser &lt;id&gt;</code> - ইউজার ডিলিট করুন
🔹 <code>/bcast</code> - মেসেজ ব্রডকাস্ট করুন"""
    bot.send_message(ADMIN_ID, msg)

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
        msg = f"""👤 <b>User Info:</b> <code>{uid}</code>
📝 <b>Name:</b> {u.get('name', 'N/A')}
🔗 <b>Username:</b> @{u.get('username', 'N/A')}
💰 <b>Balance:</b> {u.get('balance', 0)} টাকা
👥 <b>Total Refer:</b> {u.get('ref_count', 0)}
💳 <b>Wallet:</b> <code>{u.get('wallet', 'Not Set')}</code>
🤝 <b>Referred By:</b> <code>{u.get('referred_by', 'None')}</code>"""
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

# --- OTHER BUTTONS ---
@bot.message_handler(func=lambda m: m.text == "SUPPORT 💸")
def support(message):
    msg = """☎️ <b>উইথড্র দেওয়ার ২৪ ঘন্টার মধ্যে পেমেন্ট না পেলে যোগাযোগ করুন:</b>
👤 @Promoter_from_bd

📢 <b>উইথড্র দেওয়ার পর অবশ্যই নক দিবেন:</b> @tbpycofficial"""
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status(message):
    users = get_all_users()
    count = len(users)
    bot.send_message(message.chat.id, f"📊 <b>Total Users:</b> {count}\n🚀 <b>Online Users:</b> {count}")

# --- 🚀 RUN BOT ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is running with Dynamic Admin Channels & Firebase...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)
