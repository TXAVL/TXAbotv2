import requests
import subprocess
import json
import urllib.parse
import os
from io import BytesIO
from PIL import Image, ImageDraw
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from zlapi._threads import ThreadType
from zlapi.models import Message
import requests
import json
import urllib.parse
import io
from PIL import Image
from removebg import RemoveBg

class BackgroundRemover:
    def __init__(self, api_key):
        self.rmbg = RemoveBg(api_key, "error.log")

    def remove_background_from_url(self, img_url):
        try:
            output_file_name = 'no-bg.png'
            self.rmbg.remove_background_from_img_url(img_url, new_file_name=output_file_name)
            return output_file_name
        except Exception as e:
            print(f"Loi khi xoa nen tu URL: {e}")
            return None

def handle_stkxp_command(message, message_object, thread_id, thread_type, author_id, client):
    if message_object.quote:
        attach = message_object.quote.attach
        if attach:
            try:
                attach_data = json.loads(attach)
            except json.JSONDecodeError:
                client.sendMessage(Message(text="Du lieu anh khong hop le."), thread_id=thread_id, thread_type=thread_type)
                return
            image_url = attach_data.get('hdUrl') or attach_data.get('href')
            if not image_url:
                client.sendMessage(Message(text="Khong tim thay URL anh."), thread_id=thread_id, thread_type=thread_type)
                return
            image_url = image_url.replace('/jxl', '/jpg').replace('.jxl', '.jpg')
            image_url = urllib.parse.unquote(image_url)
            if is_valid_image_url(image_url):
                remover = BackgroundRemover("DjYwh19heAXUpcGTPCkkq1Z5")
                output_file_name = remover.remove_background_from_url(image_url)
                if output_file_name:
                    uploaded_url = upload_to_uguu(output_file_name)
                    if uploaded_url:
                        try:
                            client.sendCustomSticker(
                                staticImgUrl=uploaded_url,
                                animationImgUrl=None,
                                thread_id=thread_id,
                                thread_type=thread_type
                            )
                            client.sendMessage(Message(text="Sticker đa đuoc tao!"), thread_id=thread_id, thread_type=thread_type, ttl=1800000)
                        except Exception as e:
                            client.sendMessage(Message(text=f"Khong the gui sticker: {str(e)}"), thread_id=thread_id, thread_type=thread_type)
                    else:
                        client.sendMessage(Message(text="Khong the tai anh len."), thread_id=thread_id, thread_type=thread_type, ttl=120000)
                else:
                    client.sendMessage(Message(text="Khong the xoa nen."), thread_id=thread_id, thread_type=thread_type, ttl=120000)
            else:
                client.sendMessage(Message(text="URL khong phai la anh hop le."), thread_id=thread_id, thread_type=thread_type, ttl=120000)
        else:
            client.sendMessage(Message(text="Khong co anh nao đuoc reply."), thread_id=thread_id, thread_type=thread_type, ttl=120000)
    else:
        client.sendMessage(Message(text="Hay reply vao anh can tao sticker."), thread_id=thread_id, thread_type=thread_type, ttl=120000)

def is_valid_image_url(url):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return any(url.lower().endswith(ext) for ext in valid_extensions)

def upload_to_uguu(file_path):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with open(file_path, 'rb') as file:
            files = {'files[]': file}
            response = requests.post("https://uguu.se/upload", files=files, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result["files"][0]["url"]
    except Exception as e:
        print(f"Loi khi upload file len Uguu: {e}")
    return None
def send_response(client, thread_id, thread_type, text, ttl=10000):
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="10", auto_format=False),
        MessageStyle(offset=0, length=len(text), style="bold", auto_format=False)
    ])
    styled_message = Message(text=text, style=style)
    client.sendMessage(styled_message, thread_id, thread_type, ttl=ttl)

