from zlapi.models import Message
import requests
import time
from core.bot_sys import get_user_name_by_id

des = {
    'version': "1.2.0",
    'credits': "Hoang Thanh Tung",
    'description': "Spam ket ban FF bang API LK-TEAM, gui 10 lan",
    'power': "✅ Ai cung dung duoc"
}

def handle_kb_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)
    parts = message.strip().split()

    if len(parts) < 2:
        client.sendMessage(
            Message(text=f"❌ Thieu UID!\n\n📌 **Cach dung:**\n`/spamff <uid>`\nVi du: `/spamff 12345678`\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    uid = parts[1]
    url = f"https://spam-fr-lk-team.vercel.app/send_requests?uid={uid}"

    # 👇 Gui thong bao truoc khi spam
    client.sendMessage(
        Message(text=f"⏳ Đang gui 10 lan spam đen UID `{uid}`...\n[Ask by: {user_name}]"),
        thread_id, thread_type
    )

    total_success = 0
    total_failed = 0
    total_tokens = 0
    last_message = ""
    status_codes = []

    for i in range(10):  # 👈 Lap 10 lan
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            total_success += data.get("success_count", 0)
            total_failed += data.get("failed_count", 0)
            total_tokens += data.get("tokens_attempted_with_regions", 0)
            last_message = data.get("message", "")
            status_codes.append(str(data.get("status_code", "N/A")))
        except Exception:
            total_failed += 1
        time.sleep(0.5)  # ⏱ Delay nhe tranh bi rate-limit

    msg = (
        f"📤 **SPAM UID `{uid}` HOAN TAT (10 lan)**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Tong thanh cong: `{total_success}`\n"
        f"❌ Tong that bai: `{total_failed}`\n"
        f"🌍 Tong vung thu: `{total_tokens}`\n"
        f"📝 Phan hoi cuoi: {last_message or 'Khong co'}\n"
        f"📦 Ma phan hoi: `{', '.join(status_codes)}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[Ask by: {user_name}]"
    )

    client.sendMessage(Message(text=msg), thread_id, thread_type)
