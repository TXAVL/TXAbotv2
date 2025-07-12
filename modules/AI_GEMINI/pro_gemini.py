from datetime import datetime, timedelta
import json
from core.bot_sys import *
from zlapi.models import *
import requests
import threading
import re
import random
import math
import heapq
import os
import logging

GEMINI_API_KEY = 'AIzaSyA-zE1aETp-BZEcTO9aIBf8CDkGrI-Ykwo'
last_message_times = {}
conversation_states = {}
default_language = "vi"

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "bạn bí ẩn"

def detect_language(text):
    if re.search(r'[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]', text.lower()):
        return "vi"
    elif re.search(r'[a-zA-Z]', text):
        return "en"
    return default_language

def translate_response(text, target_lang):
    return text  # Giữ nguyên nếu chưa tích hợp dịch

def handle_chat_on(bot, thread_id):
    settings = read_settings(bot.uid)
    if "chat" not in settings:
        settings["chat"] = {}
    settings["chat"][thread_id] = True
    write_settings(bot.uid, settings)
    return "Được rồi, đã bật chat! Giờ thì cùng TXABot khuấy đảo nào! 😎"

def handle_chat_off(bot, thread_id):
    settings = read_settings(bot.uid)
    if "chat" in settings and thread_id in settings["chat"]:
        settings["chat"][thread_id] = False
        write_settings(bot.uid, settings)
        return "Đã tắt chat, buồn thật đấy! Nhưng cần TXABot thì cứ gọi nhé! 😌"
    return "Nhóm này chưa bật chat mà, tắt gì nổi đâu đại ca! 😂"

def handle_chat_command(message, message_object, thread_id, thread_type, author_id, client):
    settings = read_settings(client.uid)
    user_message = message.replace(f"{client.prefix}chat ", "").strip()
    current_time = datetime.now()

    if user_message.lower() == "on":
        if not is_admin(client, author_id):
            response = "❌ Bạn không phải admin bot!"
        else:
            response = handle_chat_on(client, thread_id)
        client.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    elif user_message.lower() == "off":
        if not is_admin(client, author_id):
            response = "❌ Bạn không phải admin bot!"
        else:
            response = handle_chat_off(client, thread_id)
        client.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    if not settings.get("chat", {}).get(thread_id, False):
        return

    # Kiểm tra spam
    if author_id in last_message_times:
        time_diff = current_time - last_message_times[author_id]
        if time_diff < timedelta(seconds=5):
            user_name = get_user_name_by_id(client, author_id)
            client.replyMessage(
                Message(text=f"Ôi {user_name}, từ từ thôi nào! TXABot không phải siêu máy tính đâu nha! 😅\n\n[Hỏi bởi: {user_name}]"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )
            return

    last_message_times[author_id] = current_time
    threading.Thread(target=handle_gemini_chat, args=(user_message, message_object, thread_id, thread_type, author_id, client)).start()

def handle_gemini_chat(user_message, message_object, thread_id, thread_type, author_id, client):
    asker_name = get_user_name_by_id(client, author_id)
    conversation_state = conversation_states.get(thread_id, {'history': []})
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"Bạn là trợ lý AI của người dùng tên {asker_name}, được tạo ra bởi TXA, thời gian hiện tại là {current_time}.\n"
    prompt += "Lịch sử cuộc trò chuyện:\n"
    for item in conversation_state['history'][-10:]:
        prompt += f"{item['role']}: {item['text']}\n"
    prompt += f"user: {user_message}\n>"

    headers = {'Content-Type': 'application/json'}
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    json_data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=json_data, timeout=15)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            for candidate in result['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            reply_text = part['text'].replace("*", "")
                            conversation_state['history'].append({'role': 'user', 'text': user_message})
                            conversation_state['history'].append({'role': 'gemini', 'text': reply_text})
                            conversation_states[thread_id] = conversation_state

                            reply_text += f"\n\n[Hỏi bởi: {asker_name}]"
                            client.replyMessage(
                                Message(text=reply_text),
                                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
                            )
                            return
        else:
            client.replyMessage(
                Message(text=f"Ôi, hệ thống đang bận! Thử lại sau nhé! 😅\n\n[Hỏi bởi: {asker_name}]"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )
    except requests.exceptions.Timeout:
        client.replyMessage(
            Message(text=f"TXABot hơi chậm, chờ chút nha! ⏳\n\n[Hỏi bởi: {asker_name}]"),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        client.replyMessage(
            Message(text=f"Ôi, lỗi rồi: {str(e)} 😓\n\n[Hỏi bởi: {asker_name}]"),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )

# BOT BUILD BY TXA