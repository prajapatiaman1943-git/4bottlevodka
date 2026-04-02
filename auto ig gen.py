import os
import random
import string
import time
import names
import requests
import telebot
import re
import threading
from collections import defaultdict

# Color codes for console output (optional)
rd, gn, lgn, yw, lrd, be, pe = '\033[00;31m', '\033[00;32m', '\033[01;32m', '\033[01;33m', '\033[01;31m', '\033[94m', '\033[01;35m'
cn, k, g = '\033[00;36m', '\033[90m', '\033[38;5;130m'
true = f'{rd}[{lgn}+{rd}]{gn} '
false = f'{rd}[{lrd}-{rd}] '
SUCCESS = f'{rd}[{lgn}+{rd}]{gn} '
ERROR = f'{rd}[{lrd}-{rd}]{rd} '

# Telegram Bot Configuration (hardcoded as requested)
TELEGRAM_TOKEN = ""
CHAT_ID = ""  # This is the default chat ID, but the bot will handle any chat

# Proxies: load from proxies.txt, each line format: host:port:username:password
PROXY_LIST = []
PROXY_INDEX = 0
PROXY_LOCK = threading.Lock()

def load_proxies():
    """Load proxies from proxies.txt file if exists."""
    global PROXY_LIST
    try:
        with open("proxies.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    PROXY_LIST.append(line)
        if PROXY_LIST:
            print(f"{true}Loaded {len(PROXY_LIST)} proxies from proxies.txt")
        else:
            print(f"{ERROR}No proxies found in proxies.txt, proceeding without proxy")
    except FileNotFoundError:
        print(f"{ERROR}proxies.txt not found, proceeding without proxy")
        PROXY_LIST = []

def get_next_proxy():
    """Return next proxy in round-robin fashion as a dict for requests."""
    if not PROXY_LIST:
        return None
    with PROXY_LOCK:
        global PROXY_INDEX
        proxy_str = PROXY_LIST[PROXY_INDEX % len(PROXY_LIST)]
        PROXY_INDEX += 1
        # Parse host:port:username:password
        parts = proxy_str.split(":")
        if len(parts) == 4:
            host, port, user, pwd = parts
            proxy_url = f"http://{user}:{pwd}@{host}:{port}"
            return {"http": proxy_url, "https": proxy_url}
        else:
            print(f"{ERROR}Invalid proxy format: {proxy_str}, expected host:port:username:password")
            return None

# User state management for Telegram bot
user_states = defaultdict(dict)  # {chat_id: {'email': str, 'headers': dict, 'signup_code': str, 'state': str}}
# States: 'waiting_email', 'waiting_otp'

# Indian name and username generators (unchanged)
INDIAN_FIRST_NAMES = ["Aarav","Vihaan","Vivaan","Ananya","Diya","Advik","Kabir","Aaradhya","Reyansh","Sai","Arjun","Ishaan","Rudra","Sia","Myra","Ayaan","Shaurya","Anaya","Krisha","Kavya","Rohan","Shreya","Ishita","Yash","Priya","Riya","Rahul","Amit","Sumit","Pooja","Neha","Raj","Simran","Aditya","Krishna","Laksh","Tanvi","Ishika","Ved","Yuvraj","Anushka","Divya","Sanya","Ria","Jay","Virat","Ravindra","Sneha","Nikhil"]
INDIAN_LAST_NAMES = ["Sharma","Verma","Gupta","Kumar","Singh","Patel","Reddy","Rao","Yadav","Jha","Malhotra","Mehta","Choudhary","Thakur","Mishra","Trivedi","Dwivedi","Pandey","Tiwari","Joshi","Desai","Shah","Nair","Menon","Iyer","Khan","Ansari","Sheikh"]
TITLES = ["official","real","the","ig","india","indian","fan","lover","world","zone"]

def generate_indian_username():
    first = random.choice(INDIAN_FIRST_NAMES).lower()
    last = random.choice(INDIAN_LAST_NAMES).lower()
    title = random.choice(TITLES).lower()
    num = random.randint(10, 9999)
    patterns = [
        f"{first}{last}{num}", f"{first}_{last}{num}", f"{first}.{last}{num}",
        f"{first}{num}{last}", f"{title}{first}{last}{num}", f"{first}{last}{title}{num}",
        f"{first}{random.randint(100,999)}", f"{first}{last}{random.randint(1000,9999)}"
    ]
    return random.choice(patterns)

def check_username_availability(username, headers, proxy=None):
    try:
        r = requests.post(
            'https://www.instagram.com/api/v1/users/check_username/',
            headers=headers, data={'username': username}, proxies=proxy, timeout=30
        )
        if r.status_code == 200:
            return r.json().get('available', False)
    except:
        pass
    return False

def show_thinking(message="Processing", duration=4):
    print(f"\n{true}{cn}{message}", end="", flush=True)
    for _ in range(duration):
        time.sleep(1)
        print(".", end="", flush=True)
    print("\n")

def show_ip_info(proxy=None):
    try:
        show_thinking("🌐 Checking your IP", 3)
        ip_data = requests.get("https://ipinfo.io/json", timeout=10, proxies=proxy).json()
        print(f"{true}\x1b[1;36m📍Current IP: {ip_data.get('ip', 'Unknown')}")
        print(f"\x1b[1;91m\x1b[1;100m🌍 Location: {ip_data.get('country')} ({ip_data.get('city')})\n")
    except:
        pass

def get_headers(proxy=None):
    while True:
        try:
            show_thinking("Fetching headers", 2)
            an_agent = f'Mozilla/5.0 (Linux; Android {random.randint(9,13)}; {"".join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111,999)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
            
            r = requests.get('https://www.instagram.com/api/v1/web/accounts/login/ajax/', 
                           headers={'user-agent': an_agent}, timeout=30, proxies=proxy).cookies
            
            resp = requests.get('https://www.instagram.com/', headers={'user-agent': an_agent}, timeout=30, proxies=proxy)
            appid = resp.text.split('APP_ID":"')[1].split('"')[0]
            rollout = resp.text.split('rollout_hash":"')[1].split('"')[0]

            headers = {
                'authority': 'www.instagram.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'cookie': f'dpr=3; csrftoken={r["csrftoken"]}; mid={r["mid"]}; ig_did={r["ig_did"]}',
                'origin': 'https://www.instagram.com',
                'referer': 'https://www.instagram.com/accounts/signup/email/',
                'user-agent': an_agent,
                'x-csrftoken': r["csrftoken"],
                'x-ig-app-id': appid,
                'x-instagram-ajax': rollout,
                'x-web-device-id': r["ig_did"],
            }
            return headers
        except Exception as e:
            print(f"{ERROR} Header Error: {e}")
            time.sleep(3)

def Get_UserName(Headers, proxy=None):
    show_thinking("Generating Indian username", 5)
    for _ in range(25):
        username = generate_indian_username()
        print(f"{true}Checking username: {username} ...")
        if check_username_availability(username, Headers, proxy):
            print(f"{SUCCESS} Username available → {gn}{username}")
            return username
        time.sleep(random.uniform(0.6, 1.5))
    
    fallback = generate_indian_username() + str(random.randint(1000,9999))
    print(f"{yw}[!] Using fallback: {fallback}")
    return fallback

def build_ordered_cookie_string(cdict):
    order = ["mid", "ig_did", "csrftoken", "sessionid", "ds_user_id"]
    parts = []
    for key in order:
        if key in cdict and cdict[key]:
            parts.append(f"{key}={cdict[key]}")
    return '; '.join(parts)

def Send_SMS(Headers, Email, proxy=None):
    try:
        show_thinking("Sending verification code", 8)
        device_id = Headers['cookie'].split('mid=')[1].split(';')[0]
        data = {'device_id': device_id, 'email': Email}
        r = requests.post('https://www.instagram.com/api/v1/accounts/send_verify_email/', 
                         headers=Headers, data=data, timeout=30, proxies=proxy)
        return r.text
    except Exception as e:
        print(f"{ERROR} Send SMS Error: {e}")
        return None

def Validate_Code(Headers, Email, Code, proxy=None):
    try:
        show_thinking("Validating code", 8)
        device_id = Headers['cookie'].split('mid=')[1].split(';')[0]
        data = {'code': Code, 'device_id': device_id, 'email': Email}
        r = requests.post('https://www.instagram.com/api/v1/accounts/check_confirmation_code/', 
                         headers=Headers, data=data, timeout=30, proxies=proxy)
        return r
    except Exception as e:
        print(f"{ERROR} Validate Code Error: {e}")
        return None

def Create_Acc(Headers, Email, SignUpCode, proxy=None):
    try:
        firstname = names.get_first_name()
        UserName = Get_UserName(Headers, proxy)
        Password = firstname.strip() + '@' + str(random.randint(111,999))

        show_thinking("Creating account", 5)

        data = {
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{round(time.time())}:{Password}',
            'email': Email,
            'username': UserName,
            'first_name': firstname,
            'month': random.randint(1, 12),
            'day': random.randint(1, 28),
            'year': random.randint(1990, 2001),
            'client_id': Headers['cookie'].split('mid=')[1].split(';')[0],
            'seamless_login_enabled': '1',
            'tos_version': 'row',
            'force_sign_up_code': SignUpCode,
        }

        response = requests.post(
            'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
            headers=Headers, data=data, timeout=40, proxies=proxy
        )

        if '"account_created":true' in response.text:
            sessionid = response.cookies.get('sessionid')
            csrftoken = Headers.get('x-csrftoken')

            cookie_dict = {
                'sessionid': sessionid,
                'csrftoken': csrftoken,
                'mid': Headers.get('cookie', '').split('mid=')[1].split(';')[0] if 'mid=' in Headers.get('cookie', '') else '',
                'ig_did': Headers.get('cookie', '').split('ig_did=')[1].split(';')[0] if 'ig_did=' in Headers.get('cookie', '') else '',
            }

            cookie_str = build_ordered_cookie_string(cookie_dict)

            print(f"\n{SUCCESS} Account Created Successfully!")
            print(f"{true} Username : {gn}{UserName}")
            print(f"{true} Password : {gn}{Password}")
            print(f"{true} Sessionid : {gn}{sessionid}")

            with open('account_insta.txt', 'a', encoding='utf-8') as f:
                f.write(f"Username: {UserName}\nPassword: {Password}\nEmail: {Email}\nCookies: {cookie_str}\n")
                f.write("-"*80 + "\n\n")

            # Send success message to Telegram
            msg = f"✅ *New Instagram Account Created*\n\n👤 Username: `{UserName}`\n🔑 Password: `{Password}`\n📧 Email: `{Email}`\n\n🍪 Cookies:\n`{cookie_str}`"
            return msg, UserName, Password, cookie_str
        else:
            error_msg = f"❌ *Account creation failed!*\n\nResponse: `{response.text[:200]}`"
            return error_msg, None, None, None
    except Exception as e:
        return f"❌ *Creation Error:* `{str(e)}`", None, None, None

# Telegram bot handlers
bot = telebot.TeleBot('7972037861:AAGQO4xntrYX4AKCfM6xkHpjNo_CekIn0GY')

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'state': 'waiting_email'}
    bot.reply_to(message, "Welcome! Please send me your email address to start creating Instagram accounts.\n\nUse /cancel to abort at any time.")

@bot.message_handler(commands=['cancel'])
def cancel(message):
    chat_id = message.chat.id
    user_states.pop(chat_id, None)
    bot.reply_to(message, "Operation cancelled. Send /start to begin again.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()
    state_data = user_states.get(chat_id, {})
    state = state_data.get('state', '')

    if state == 'waiting_email':
        # User sent email
        email = text
        # Basic email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            bot.reply_to(message, "Invalid email format. Please try again or /cancel.")
            return
        # Update state
        state_data['email'] = email
        state_data['state'] = 'waiting_otp'
        user_states[chat_id] = state_data

        # Get headers and send verification code
        bot.reply_to(message, f"Processing email `{email}`...", parse_mode='Markdown')
        proxy = get_next_proxy()  # Use a proxy for this operation
        headers = get_headers(proxy)
        state_data['headers'] = headers
        state_data['proxy'] = proxy

        # Send SMS
        send_resp = Send_SMS(headers, email, proxy)
        if send_resp and '"email_sent":true' in send_resp:
            bot.reply_to(message, f"📧 Verification code sent to `{email}`.\nPlease reply with the 6-digit code.", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"Failed to send verification code. Error: `{send_resp[:100]}`\nPlease check email or try again.", parse_mode='Markdown')
            user_states.pop(chat_id, None)

    elif state == 'waiting_otp':
        # User sent OTP
        code = text
        if not code.isdigit() or len(code) != 6:
            bot.reply_to(message, "Invalid OTP. Please send a 6-digit code or /cancel.")
            return

        # Validate OTP
        email = state_data['email']
        headers = state_data['headers']
        proxy = state_data.get('proxy')
        validate_resp = Validate_Code(headers, email, code, proxy)
        if validate_resp and validate_resp.status_code == 200 and 'status":"ok' in validate_resp.text:
            signup_code = validate_resp.json().get('signup_code')
            bot.reply_to(message, "✅ OTP verified. Creating account...")
            # Create account
            msg, username, password, cookies = Create_Acc(headers, email, signup_code, proxy)
            if username:
                bot.send_message(chat_id, msg, parse_mode='Markdown')
                # After success, ask if user wants another account with same email or new
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton("Same Email", callback_data="same"))
                markup.add(telebot.types.InlineKeyboardButton("New Email", callback_data="new"))
                markup.add(telebot.types.InlineKeyboardButton("Cancel", callback_data="cancel"))
                bot.send_message(chat_id, "What would you like to do next?", reply_markup=markup)
                # Keep state but mark as waiting for choice
                state_data['state'] = 'waiting_choice'
                user_states[chat_id] = state_data
            else:
                bot.reply_to(message, msg, parse_mode='Markdown')
                user_states.pop(chat_id, None)
        else:
            bot.reply_to(message, f"Invalid OTP. Please try again or /cancel.\nResponse: `{validate_resp.text[:100] if validate_resp else 'None'}`", parse_mode='Markdown')
    elif state == 'waiting_choice':
        # Should not happen via text, handled by callback
        pass
    else:
        bot.reply_to(message, "Unknown state. Please /start again.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    state_data = user_states.get(chat_id, {})
    if state_data.get('state') != 'waiting_choice':
        bot.answer_callback_query(call.id, "Operation expired. Please /start again.")
        return
    choice = call.data
    if choice == "same":
        email = state_data['email']
        bot.edit_message_text(f"Creating another account with same email `{email}`...", chat_id, call.message.message_id, parse_mode='Markdown')
        # Reuse existing headers? Need fresh headers for new account
        # Use a new proxy (rotate)
        proxy = get_next_proxy()
        headers = get_headers(proxy)
        # Resend SMS
        send_resp = Send_SMS(headers, email, proxy)
        if send_resp and '"email_sent":true' in send_resp:
            bot.send_message(chat_id, f"📧 Verification code sent to `{email}`.\nPlease reply with the 6-digit code.", parse_mode='Markdown')
            # Update state
            state_data['state'] = 'waiting_otp'
            state_data['headers'] = headers
            state_data['proxy'] = proxy
            user_states[chat_id] = state_data
        else:
            bot.send_message(chat_id, f"Failed to send verification code. Error: `{send_resp[:100]}`\nPlease try again.", parse_mode='Markdown')
            user_states.pop(chat_id, None)
    elif choice == "new":
        bot.edit_message_text("Please send the new email address.", chat_id, call.message.message_id)
        state_data['state'] = 'waiting_email'
        user_states[chat_id] = state_data
    elif choice == "cancel":
        bot.edit_message_text("Operation cancelled. Send /start to begin again.", chat_id, call.message.message_id)
        user_states.pop(chat_id, None)
    bot.answer_callback_query(call.id)

def main():
    load_proxies()
    print(f"{true}Telegram Bot started. Waiting for messages...")
    # Optionally show IP info using a random proxy if available
    if PROXY_LIST:
        proxy = get_next_proxy()
        show_ip_info(proxy)
    else:
        show_ip_info()
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()