import os
import json
import random
import logging
import threading
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pytz
from datetime import datetime
from core.bot_sys import get_user_name_by_id, is_admin, read_settings, write_settings
from zlapi.models import *
from zlapi._message import Message
import pytz

# Cấu hình autosend
autosend_enabled = False
time_messages = {
    "06:00": "Chào buổi sáng! Hãy bắt đầu một ngày mới tràn đầy năng lượng.",
    "07:00": "Đã đến giờ uống cà phê! Thưởng thức một tách cà phê nhé.",
    "08:00": "Đi học thôi nào :3",
    "10:00": "Chúc bạn một buổi sáng hiệu quả! Đừng quên nghỉ ngơi.",
    "11:00": "Chỉ còn một giờ nữa là đến giờ nghỉ trưa. Hãy chuẩn bị nhé!",
    "12:00": "Giờ nghỉ trưa! Thời gian để nạp năng lượng.",
    "13:00": "Chúc bạn buổi chiều làm việc hiệu quả.",
    "13:15": "Chúc bạn đi làm việc vui vẻ",
    "14:00": "Đến giờ làm việc rồi",
    "15:00": "Một buổi chiều vui vẻ! Đừng quên đứng dậy và vận động.",
    "17:00": "Chuẩn bị hết giờ làm việc rồi nè!",
    "17:50": "Kết thúc một ngày làm việc! Hãy thư giãn.",
    "18:00": "Chào buổi tối! Thời gian để thư giãn sau một ngày dài. Đi tắm luôn đc r đấy!",
    "19:00": "Thời gian cho bữa tối! Hãy thưởng thức bữa ăn ngon miệng.",
    "21:00": "Một buổi tối tuyệt vời! Hãy tận hưởng thời gian bên gia đình.",
    "22:00": "Sắp đến giờ đi ngủ! Hãy chuẩn bị cho một giấc ngủ ngon.",
    "23:00": "Cất điện thoại đi ngủ thôi nào thức đêm không tốt đâu!",
    "00:00": "BOT AUTO chúc các cạu ngủ ngon nhó",
    "09:00": "Buổi đi học đầy tự tin",
    "09:30": "Tới giờ trả bài rồi",
}

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

def start_auto(bot):
    try:
        if not autosend_enabled:
            logging.info("Autosend is disabled - skipping")
            return
            
        listvd = "https://raw.githubusercontent.com/nguyenductai206/list/refs/heads/main/listvideo.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        
        current_time = datetime.now(vn_tz).strftime('%H:%M')
        logging.info(f"Checking autosend at {current_time}")
        
        if current_time in time_messages:
            logging.info(f"Matched time {current_time} - preparing to send message")
            response = requests.get(listvd, headers=headers)
            response.raise_for_status()
            urls = response.json()
            video_url = random.choice(urls)
            thumbnail_url = "https://f55-zpg-r.zdn.vn/jpg/866067064496219315/acc5444f5c38e466bd29.jpg"
            duration = '1000000000000000000000000000000000'
            caption = f"[SendTask {current_time}]\n{time_messages[current_time]}"
            logging.info(f"Sending video: {video_url} with caption: {caption}")
            bot.sendVideo(video_url, thumbnail_url, duration, caption=caption)
            logging.info("Message sent successfully")
        else:
            logging.info(f"No message scheduled for {current_time}")
    except Exception as e:
        logging.error(f"Lỗi khi gửi tin nhắn tự động: {str(e)}", exc_info=True)
    finally:
        if autosend_enabled:
            logging.info("Scheduling next check in 10 seconds")
            threading.Timer(10, start_auto, args=[bot]).start()

def handle_autosend_on(bot, thread_id):
    settings = read_settings(bot.uid)
    if "autosend" not in settings:
        settings["autosend"] = {}
    settings["autosend"][thread_id] = True
    write_settings(bot.uid, settings)
    return f"🚦Lệnh {bot.prefix}autosend đã được Bật 🚀 trong nhóm này ✅"

def handle_autosend_off(bot, thread_id):
    settings = read_settings(bot.uid)
    if "autosend" in settings and thread_id in settings["autosend"]:
        settings["autosend"][thread_id] = False
        write_settings(bot.uid, settings)
        return f"🚦Lệnh {bot.prefix}autosend đã Tắt ⭕️ trong nhóm này ✅"
    return "🚦Nhóm chưa có thông tin cấu hình autosend để ⭕️ Tắt 🤗"

def handle_autosend_command(message, message_object, thread_id, thread_type, author_id, bot):
    try:
        if not isinstance(message, str):
            raise ValueError("Message phải là chuỗi")
            
        from core.bot_sys import is_admin
        
        user_message = message.replace(f"{bot.prefix}autosend", "").strip().lower()
        
        if user_message == "on":
            if not is_admin(bot, author_id):
                response = "❌Bạn không phải admin bot!"
            else:
                response = handle_autosend_on(bot, thread_id)
                threading.Thread(target=start_auto, args=[bot]).start()
        elif user_message == "off":
            if not is_admin(bot, author_id):
                response = "❌Bạn không phải admin bot!"
            else:
                response = handle_autosend_off(bot, thread_id)
        else:
            response = f"ℹ️ Sử dụng: {bot.prefix}autosend on/off"
        
        bot.replyMessage(Message(text=response), 
                        thread_id=thread_id, 
                        thread_type=thread_type, 
                        replyMsg=message_object, 
                        ttl=10000)
        
        # Update global autosend_enabled based on settings
        settings = read_settings(bot.uid)
        global autosend_enabled
        autosend_enabled = any(v for k, v in settings.get("autosend", {}).items())
        
    except Exception as e:
        error_msg = f"❌ Lỗi khi xử lý autosend: {str(e)}"
        bot.replyMessage(Message(text=error_msg), 
                        thread_id=thread_id,
                        thread_type=thread_type,
                        replyMsg=message_object,
                        ttl=15000)
