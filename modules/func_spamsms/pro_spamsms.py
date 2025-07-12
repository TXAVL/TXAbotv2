from core.bot_sys import admin_cao
from zlapi.models import *
import datetime
import os
import subprocess

last_sms_times = {}
current_processing_number = None
cooldown = 300

def handle_sms_command(message, message_object, thread_id, thread_type, author_id, client):
    global current_processing_number

    try:
        if not admin_cao(client, author_id):
            client.replyMessage(
                Message(text="❌ Ban khong co quyen su dung lenh nay!"),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000
            )
            return

        parts = message.strip().split()
        if len(parts) < 3:
            client.replyMessage(
                Message(text='🚫 Vui long nhap so đien thoai va so lan spam.'),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000
            )
            return

        attack_phone_number = parts[1]
        try:
            number_of_times = int(parts[2])
        except ValueError:
            client.replyMessage(
                Message(text='❌ So lan spam phai la so nguyen hop le!'),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000
            )
            return

        if not (attack_phone_number.isnumeric() and len(attack_phone_number) == 10):
            client.replyMessage(
                Message(text='❌ So đien thoai khong hop le! Phai đung 10 chu so.'),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000
            )
            return

        if current_processing_number:
            client.replyMessage(
                Message(text=f"⏳ Vui long đoi so {current_processing_number} xu ly xong truoc khi thuc hien tiep!"),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000
            )
            return

        # Gioi han so lan spam cho nguoi dung binh thuong (đang bo ADMIN, nen ap dung cho tat ca)
        if number_of_times > 10:
            client.replyMessage(
                Message(text="🚫 Nguoi dung chi đuoc spam toi đa 10 lan!"),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000
            )
            return

        current_time = datetime.datetime.now()

        if author_id in last_sms_times and (current_time - last_sms_times[author_id]).total_seconds() < cooldown:
            remaining = int(cooldown - (current_time - last_sms_times[author_id]).total_seconds())
            client.replyMessage(
                Message(text=f"⏳ Vui long đoi {remaining} giay truoc khi spam tiep!"),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000
            )
            return

        last_sms_times[author_id] = current_time
        current_processing_number = attack_phone_number

        masked_number = f"{attack_phone_number[:3]}***{attack_phone_number[-3:]}"
        time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")

        msg_start = f"""
/-li   Đang spam SMS & Call  
📱  So đien thoai:  {masked_number} 
⏰  Thoi gian gui:  {time_str}  
♻️  So lan gui:  {number_of_times} 
⏳  Thoi gian cho:  0 giay
👱  Nguoi quan ly:  NGUOI DUNG
"""
        mention = Mention(author_id, length=len("Nguoi quan ly"), offset=0)
        style = MultiMsgStyle([MessageStyle(style="color", color="#4caf50", length=len(msg_start), offset=0)])

        client.replyMessage(
            Message(text=msg_start.strip(), style=style, mention=mention),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=8000)

        process = subprocess.Popen(
            ["python3", os.path.join(os.getcwd(), "smsv2.py"), attack_phone_number, str(number_of_times)]
        )
        process.wait()

        msg_end = f"""
/-li   Spam SMS & Call hoan tat  
📱  So đien thoai:  {masked_number} 
⏰  Thoi gian gui:  {time_str}  
♻️  So lan gui:  {number_of_times}  
⏳  Thoi gian cho:  0 giay 
👱  Nguoi quan ly:  NGUOI DUNG
"""
        client.replyMessage(
            Message(text=msg_end.strip(), style=style, mention=mention),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000)

        current_processing_number = None

    except Exception as e:
        client.replyMessage(
            Message(text=f"⚠️ Co loi xay ra: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=10000
        )
