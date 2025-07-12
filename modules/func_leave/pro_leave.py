import time
from core.bot_sys import admin_cao
from zlapi.models import *

def handle_leave_group_command(message, message_object, thread_id, thread_type, author_id, client):
    if not admin_cao(client, author_id):
        client.replyMessage(Message(text="❌ Ban khong phai admin bot!"), 
                           message_object, thread_id=thread_id, 
                           thread_type=thread_type, ttl=100000)
        return

    try:
        farewell_msg = "🚦Tam biet moi nguoi! Hen gap lai nhe! 👋😊"
        client.replyMessage(Message(text=farewell_msg), 
                           message_object, thread_id=thread_id, 
                           thread_type=thread_type, ttl=120000)
        time.sleep(1)
        client.leaveGroup(thread_id, silent=True)

    except ZaloAPIException as e:
        error_msg = f"❌ Loi khi roi nhom: {str(e)}"
        client.replyMessage(Message(text=error_msg), 
                           message_object, thread_id=thread_id, 
                           thread_type=thread_type, ttl=86400000)
    except Exception as e:
        error_msg = f"❌ Loi khong xac đinh: {str(e)}"
        client.replyMessage(Message(text=error_msg), 
                           message_object, thread_id=thread_id, 
                           thread_type=thread_type, ttl=86400000)