from zlapi.models import Message
import requests
from core.bot_sys import get_user_name_by_id

def handle_reghotmail_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)

    try:
        # Gui yeu cau toi API
        response = requests.get("https://keyherlyswar.x10.mx/api/reghotmail.php")
        
        if response.status_code != 200:
            client.sendMessage(
                Message(text=f"❌ Khong the tao tai khoan Hotmail.\nVui long thu lai sau!\n\n[Ask by: {user_name}]"),
                thread_id, thread_type
            )
            return

        data = response.json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            client.sendMessage(
                Message(text=f"⚠️ Du lieu tra ve khong hop le tu API.\n\n[Ask by: {user_name}]"),
                thread_id, thread_type
            )
            return

        result_message = f"""✅ Tao Hotmail thanh cong!

📧 Email: `{email}`
🔑 Password: `{password}`

[Ask by: {user_name}]
"""
        client.sendMessage(Message(text=result_message), thread_id, thread_type)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Co loi xay ra: {e}\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
