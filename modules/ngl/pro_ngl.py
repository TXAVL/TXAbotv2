from zlapi.models import Message, ThreadType
from datetime import datetime
from core.bot_sys import get_user_name_by_id

import threading
import requests
import time
import random
import os

# 📦 Tai user-agent tu file
def load_user_agents():
    file_path = os.path.join(os.path.dirname(__file__), 'user_agents.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("[!] Khong tim thay file user_agents.txt, dung user-agent mac đinh.")
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
        ]

user_agents = load_user_agents()

# 🚀 Ham spam
def ngl_spam(username, count, message):
    success = 0
    bad = 0

    for i in range(count):
        headers = {
            'Host': 'ngl.link',
            'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': random.choice(user_agents),
            'sec-ch-ua-platform': '"Windows"',
            'origin': 'https://ngl.link',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'https://ngl.link/{username}',
            'accept-language': 'en-US,en;q=0.9',
        }

        data = {
            'username': username,
            'question': message,
            'deviceId': 'ABCDEF1234567890',
            'gameSlug': '',
            'referrer': '',
        }

        try:
            res = requests.post('https://ngl.link/api/submit', headers=headers, data=data)
            if res.status_code == 200:
                success += 1
            else:
                bad += 1
        except:
            bad += 1

        time.sleep(1)

    return success, bad


# 🔧 Command /ngl
def handle_ngl_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)
    parts = message.strip().split()

    if len(parts) < 4:
        client.sendMessage(
            Message(text=f"❌ Sai cu phap!\n\n📌 Dung đung dang:\n`/ngl <username> <count> <noi_dung>`\n\nVi du:\n`/ngl userabc 5 Hello tu bot spam!`\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    username = parts[1]

    try:
        count = int(parts[2])
        if count <= 0:
            raise ValueError
    except ValueError:
        client.sendMessage(
            Message(text=f"❌ `count` phai la so nguyen duong!\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    # Gop phan con lai thanh noi dung tin nhan
    spam_text = ' '.join(parts[3:])

    client.sendMessage(
        Message(text=f"🚀 Đang gui `{count}` tin nhan toi `{username}`...\n📝 Noi dung: `{spam_text}`\n⏳ Vui long cho..."),
        thread_id, thread_type
    )

    # Bat đau spam trong thread phu
    def do_spam():
        success, bad = ngl_spam(username, count, spam_text)
        now = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
        result = f"""
        
✨ [ TXA 𝙎𝙋𝘼𝙈 𝙆𝙀𝙏 𝙌𝙐𝘼 ] ✨
━━━━━━━━━━━━━━━━━━━━━━━
👤 Nguoi dung: {user_name}
🎯 Username đich: `{username}`
📨 Gui: `{count}` tin

✅ Thanh cong: `{success}`
❌ That bai: `{bad}`

📝 Noi dung: {spam_text}
🕒 Thoi gian: {now}
━━━━━━━━━━━━━━━━━━━━━━━
📌 *Cam on đa dung bot!*
"""
        client.sendMessage(Message(text=result.strip()), thread_id, thread_type)

    threading.Thread(target=do_spam).start()
