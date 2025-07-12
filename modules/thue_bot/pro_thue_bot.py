import colorsys
from datetime import datetime, timedelta
import glob
from io import BytesIO
import logging
import random
import re
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import threading
import json
import os
import emoji
import pytz
import requests
from zlapi.models import *
import sys
from core.bot_sys import admin_cao, is_admin, read_settings
import time

BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "mybot.png")
CONFIG_FILE = "config.json"
logging.basicConfig(level=logging.INFO)

def load_config():
    """Tai du lieu tu config.json."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default_config = {"data": []}
        save_config(default_config)
        return default_config

def save_config(config):
    """Luu du lieu vao config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving config.json: {str(e)}")

def send_message(client, message_object, thread_id, thread_type, text):
    """Gui tin nhan tra loi."""
    client.replyMessage(Message(text=text), message_object, thread_id, thread_type)

def get_user_name_by_id(client, author_id):
    """Lay ten nguoi dung tu client dua tren author_id."""
    try:
        user_info = client.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "Nguoi dung khong ton tai"

def extract_uids_from_mentions(message_object):
    """Trich xuat UID tu cac mentions trong tin nhan."""
    uids = []
    if message_object.mentions:
        uids = [mention['uid'] for mention in message_object.mentions if 'uid' in mention]
    return uids

def parse_time_duration(duration_str):
    """Phan tich chuoi thoi gian (vi du: '1d 5h 30m') thanh so giay."""
    if duration_str.lower() == "all":
        return "all"
    total_seconds = 0
    parts = duration_str.split()
    for part in parts:
        if not part:
            continue
        if part.endswith("d"):
            total_seconds += int(part[:-1]) * 86400
        elif part.endswith("h"):
            total_seconds += int(part[:-1]) * 3600
        elif part.endswith("m"):
            total_seconds += int(part[:-1]) * 60
        else:
            return None
    return total_seconds if total_seconds > 0 else None

def handle_create_command(message, message_object, thread_id, thread_type, author_id, client):
    def create_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if thread_type != ThreadType.USER:
                cookie = """{"_ga": "GA1.2.103..."}"""
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, lenh nay chi hoat đong voi USER ca nhan inbox rieng, khong hoat đong trong GROUP 🤧\n"
                    f"🚦 Ket ban voi chu Bot va go lenh theo cu phap {client.prefix}mybot create [prefix] [imei] [cookies] đe tao Bot \n"
                    f"🚦 Luu y: Cac thong so prefix imei va cookies JSON phai đe trong ngoac [], neu khong dung prefix thi nhap prefix la None 📌\n"
                    f"🚦 Vi du: {client.prefix}mybot create [{client.prefix}] [ff33af5c-fb...] [{cookie}] ✅\n")

            pattern = r"\[(.*?)\]\s*\[(.*?)\]\s*\[(.*?)\]"
            match = re.search(pattern, message)
            if not match or len(match.groups()) < 3:
                cookies = """{"_ga": "GA1.2.103..."}"""
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, vui long cung cap đu thong so theo cu phap {client.prefix}mybot create [prefix] [imei] [cookies] đe tao Bot 🤖\n"
                    f"🚦 Luu y: Cac thong so imei va cookies JSON phai đe trong ngoac [], neu khong dung prefix thi nhap prefix la None 📌\n"
                    f"🚦 Vi du: {client.prefix}mybot create [{client.prefix}] [ff33af5c-fb...] [{cookies}] ✅\n")

            PREFIX, imei, raw_cookies = match.groups()
            if PREFIX.lower() == "none":
                PREFIX = ""
            raw_cookies = ''.join(c for c in raw_cookies if c.isprintable() and c not in '\n\r\t')
            cookies = None if not raw_cookies else json.loads(raw_cookies) if raw_cookies.startswith('{') and raw_cookies.endswith('}') else None
            if cookies is None and raw_cookies:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, cookies khong hop le! Phai la mot đoi tuong JSON hoan chinh, vi du: {{\"_ga\": \"GA1.2.103...\"}}")
            if not isinstance(cookies, dict) and cookies is not None:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, cookies khong hop le! Phai la mot đoi tuong JSON (dang tu đien). Vi du: {{\"key\": \"value\"}}")
            if not imei.strip():
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, IMEI khong hop le!")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
            if source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot cua ban đa ton tai, khong the tao them!")
            config["data"].append({
                "prefix": PREFIX,
                "session_cookies": cookies,
                "imei": imei,
                "is_main_bot": False,
                "username": source_name,
                "author_id": author_id,
                "status": False
            })
            save_config(config)
            send_message(client, message_object, thread_id, thread_type, f"🚦 Bot cua {source_name} đa đuoc tao thanh cong va đang trong trang thai hoat đong!")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    threading.Thread(target=create_bot_entry, daemon=True).start()

def handle_lock_command(message, message_object, thread_id, thread_type, author_id, client):
    def lock_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
            if not admin_cao(client, author_id):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, ban khong phai admin bot!")
            if thread_type != ThreadType.GROUP:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, lenh nay khong the su dung trong tin nhan rieng!")
            mentioned_uids = extract_uids_from_mentions(message_object)
            if not mentioned_uids:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong tim thay nguoi dung đuoc tag!")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
            for uid in mentioned_uids:
                target_name = get_user_name_by_id(client, uid) if get_user_name_by_id(client, uid) else "Nguoi dung khong ton tai"
                target_bot = None
                for bot in config.get("data", []):
                    if str(bot.get("author_id")) == str(uid):
                        target_bot = bot
                        break
                if not target_bot:
                    send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot cua {target_name} khong ton tai!")
                    continue
                target_bot["status"] = False
                save_config(config)
                send_message(client, message_object, thread_id, thread_type, f"🚦 Bot cua {target_name} đa bi khoa boi {source_name}!")
            time.sleep(5)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    lock_bot_entry()

def handle_unlock_command(message, message_object, thread_id, thread_type, author_id, client):
    def unlock_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
            if not admin_cao(client, author_id):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, ban khong phai admin bot!")
            if thread_type != ThreadType.GROUP:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, lenh nay khong the su dung trong tin nhan rieng!")
            mentioned_uids = extract_uids_from_mentions(message_object)
            if not mentioned_uids:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong tim thay nguoi dung đuoc tag!")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
            for uid in mentioned_uids:
                target_name = get_user_name_by_id(client, uid) if get_user_name_by_id(client, uid) else "Nguoi dung khong ton tai"
                target_bot = None
                for bot in config.get("data", []):
                    if str(bot.get("author_id")) == str(uid):
                        target_bot = bot
                        break
                if not target_bot:
                    send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot cua {target_name} khong ton tai!")
                    continue
                target_bot["status"] = True
                save_config(config)
                send_message(client, message_object, thread_id, thread_type, f"🚦 Bot cua {target_name} đa đuoc mo khoa boi {source_name}!")
            time.sleep(5)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    unlock_bot_entry()

def handle_list_bots_command(message, message_object, thread_id, thread_type, author_id, client):
    def list_bots():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
            bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
            active_bots = []
            now = datetime.now()
            for idx, bot in enumerate(bots, start=1):
                bot_name = bot["username"]
                bot_id = bot["author_id"]
                bot_entry_name = f"🆔 {bot_id}"
                bot_display_name = f"🤖 {bot_name}"
                expiration_time_str = bot.get("het_han", "N/A")
                if expiration_time_str == "N/A":
                    remaining_time_str = "00/00/0000"
                else:
                    expiration_time = datetime.strptime(expiration_time_str, '%d/%m/%Y')
                    if expiration_time > now:
                        delta = expiration_time - now
                        days = delta.days
                        hours = delta.seconds // 3600
                        minutes = (delta.seconds % 3600) // 60
                        remaining_time_str = f"{days} ngay {hours} gio {minutes} phut - {expiration_time_str}"
                    else:
                        remaining_time_str = "Het han"
                bot_entry = f"➜ {idx}.{bot_display_name}\n{bot_entry_name}\n🕑 {remaining_time_str}"
                active_bots.append(bot_entry)
            message_text = "🤖 Danh sach bot ✅\n" + "\n\n".join(active_bots)
            send_message(client, message_object, thread_id, thread_type, message_text)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    threading.Thread(target=list_bots, daemon=True).start()

def handle_del_command(message, message_object, thread_id, thread_type, author_id, client):
    def delete_user_data():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
            if not admin_cao(client, author_id):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, ban khong phai admin bot!")
            if thread_type != ThreadType.GROUP:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, lenh nay khong the su dung trong tin nhan rieng!")
            mentioned_uids = extract_uids_from_mentions(message_object)
            if not mentioned_uids:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong tim thay nguoi dung đuoc tag!")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
            for uid in mentioned_uids:
                target_name = get_user_name_by_id(client, uid) if get_user_name_by_id(client, uid) else "Nguoi dung khong ton tai"
                target_bot = None
                for bot in config.get("data", []):
                    if str(bot.get("author_id")) == str(uid):
                        target_bot = bot
                        break
                if not target_bot:
                    send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot cua {target_name} khong ton tai!")
                    continue
                if target_bot.get("is_main_bot", False):
                    send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, {target_name} la Admin Full Function 🤣")
                    continue
                config["data"] = [bot for bot in config.get("data", []) if str(bot["author_id"]) != str(uid)]
                save_config(config)
                send_message(client, message_object, thread_id, thread_type, f"🚦 Tat ca du lieu cua bot {target_name} đa bi xoa boi {source_name}!")
            time.sleep(5)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    delete_user_data()

def handle_reset_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        config = load_config()
        source_name = get_user_name_by_id(client, author_id)
        source_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(author_id):
                source_bot = bot
                break
        source_name = source_bot["username"] if source_bot else source_name
        if not source_bot:
            return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
        if config is None:
            return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
        if source_bot.get("is_main_bot", False):
            send_message(client, message_object, thread_id, thread_type, f"• 🤖 Bot {source_name} đang tien hanh reset toan bo he thong!")
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            send_message(client, message_object, thread_id, thread_type, f"• 🤖 Bot {source_name} đang tien hanh reset!!")
            time.sleep(5)
            send_message(client, message_object, thread_id, thread_type, f"• 🤖 Bot {source_name} reset thanh cong.")
            os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        source_name = get_user_name_by_id(client, author_id)
        send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, loi xay ra khi reset bot: {str(e)}")

def handle_change_prefix_command(message, message_object, thread_id, thread_type, author_id, client):
    def change_prefix():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
            parts = message.split(maxsplit=2)
            if len(parts) < 3:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, cu phap sai! Vui long nhap đung: ,mybot prefix [new_prefix]")
            new_prefix = parts[2].strip()
            if new_prefix.lower() == "none":
                new_prefix = ""
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
            source_bot["prefix"] = new_prefix
            save_config(config)
            send_message(client, message_object, thread_id, thread_type, f"🚦 Prefix cua bot {source_name} đa đuoc đoi thanh: {new_prefix if new_prefix else 'Khong co prefix'}")
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    change_prefix()

def handle_active_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        config = load_config()
        source_name = get_user_name_by_id(client, author_id)
        source_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(author_id):
                source_bot = bot
                break
        source_name = source_bot["username"] if source_bot else source_name
        if not source_bot:
            return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
        if not admin_cao(client, author_id):
            return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, ban khong phai admin bot!")
        parts = message.split()
        if len(parts) < 3:
            return send_message(client, message_object, thread_id, thread_type,
                f"🚦 {source_name}, cu phap sai! Vui long nhap đung: ,mybot active [thoi gian] [@tag] hoac ,mybot active [@tag] [thoi gian]\n"
                f"📖 Đinh dang: `1d`, `5h`, `30m`, `1d 5h 30m`\n"
                f"💞 Vi du: ,mybot active 1d @Đatt hoac ,mybot active @Đatt 5h")
        mentioned_uids = extract_uids_from_mentions(message_object)
        if not mentioned_uids:
            return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong tim thay nguoi dung đuoc tag!")
        if config is None:
            return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
        
        duration_str = None
        for i, part in enumerate(parts[2:], start=2):
            if parse_time_duration(part) is not None:
                duration_str = part
                break
        if duration_str is None:
            return send_message(client, message_object, thread_id, thread_type,
                f"🚦 {source_name}, thoi gian khong hop le! Đinh dang: `1d`, `5h`, `30m`, `1d 5h 30m`")
        
        duration_seconds = parse_time_duration(duration_str)
        if duration_seconds is None:
            return send_message(client, message_object, thread_id, thread_type,
                f"🚦 {source_name}, thoi gian khong hop le! Đinh dang: `1d`, `5h`, `30m`, `1d 5h 30m`")

        now = datetime.now()
        for uid in mentioned_uids:
            target_name = get_user_name_by_id(client, uid) if get_user_name_by_id(client, uid) else "Nguoi dung khong ton tai"
            target_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(uid):
                    target_bot = bot
                    break
            if not target_bot:
                send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot cua {target_name} khong ton tai!")
                continue
            
            activation_date = now.strftime('%d/%m/%Y')
            expiration_timestamp = now + timedelta(seconds=duration_seconds)
            expiration_date = expiration_timestamp.strftime('%d/%m/%Y')
            
            target_bot["kich_hoat"] = activation_date
            target_bot["het_han"] = expiration_date
            target_bot["status"] = True
            save_config(config)
            
            remaining = expiration_timestamp - now
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            
            send_message(client, message_object, thread_id, thread_type,
                f"• Bot cua {target_name} đang kich hoat boi {source_name}")
            time.sleep(5)
            send_message(client, message_object, thread_id, thread_type,
                f"• Bot cua {target_name} đa đuoc kich hoat thanh cong boi {source_name} vao ngay {activation_date} "
                f"voi thoi gian: {days} ngay {hours} gio {minutes} phut\n"
                f"Bot se tu đong ngung vao ngay {expiration_date}!")
            
            timer = threading.Timer(duration_seconds, deactivate_bot, 
                                  args=(uid, config, client, message_object, thread_id, thread_type))
            timer.start()
            
    except Exception as e:
        source_name = get_user_name_by_id(client, author_id)
        send_message(client, message_object, thread_id, thread_type, f"• {source_name}, đa xay ra loi khi kich hoat bot: {str(e)}")

def deactivate_bot(target_author_id, config, client, message_object, thread_id, thread_type):
    try:
        target_name = get_user_name_by_id(client, target_author_id)
        target_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(target_author_id):
                target_bot = bot
                break
        if not target_bot:
            return send_message(client, message_object, thread_id, thread_type, 
                              f"🚦 Bot cua {target_name} khong ton tai!")
        
        target_bot["status"] = False
        save_config(config)
        send_message(client, message_object, thread_id, thread_type, 
                    f"• Bot cua {target_name} đa het thoi gian hoat đong va đa bi tat!")
    except Exception as e:
        logging.error(f"• Đa xay ra loi khi tat bot: {str(e)}")

def handle_bot_info_command(message, message_object, thread_id, thread_type, author_id, client):
    def get_bot_info():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            
            if source_bot is not None:
                source_name = source_bot.get("username", source_name)
            else:
                return send_message(client, message_object, thread_id, thread_type, 
                                   f"🚦 {source_name}, ban khong co bot!")

            if config is None:
                return send_message(client, message_object, thread_id, thread_type, 
                                   f"🚦 {source_name}, khong the tai cau hinh!")

            mentioned_uids = extract_uids_from_mentions(message_object)
            target_uid = mentioned_uids[0] if mentioned_uids else author_id
            target_name = get_user_name_by_id(client, target_uid) or "Nguoi dung khong ton tai"
            
            target_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(target_uid):
                    target_bot = bot
                    break
            
            if target_bot is None:
                return send_message(client, message_object, thread_id, thread_type, 
                                   f"🚦 {source_name}, bot cua {target_name} khong ton tai!")
            
            if target_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type, 
                                   f"🚦 {source_name}, toi la 🤖 MasterBot full option khong can tra đau 🤣")
            
            bot_id = f"🆔 ID: {target_bot.get('author_id', target_uid)}"
            bot_name = f"🤖 Bot {target_name}"
            prefix = target_bot.get("prefix", "🪰")
            status = target_bot.get("status", False)
            status_text = "Hoat đong ✅" if status else "Tam dung ❌"
            
            now = datetime.now()
            expiration_time_str = target_bot.get("het_han", now.strftime('%d/%m/%Y'))
            try:
                expiration_time = datetime.strptime(expiration_time_str, "%d/%m/%Y")
                if expiration_time > now:
                    delta = expiration_time - now
                    remaining_time = f"{delta.days} ngay {delta.seconds // 3600} gio {(delta.seconds % 3600) // 60} phut"
                else:
                    remaining_time = "Het han"
            except ValueError:
                remaining_time = "Khong xac đinh"

            settings = read_settings(client.uid)
            allowed_thread_ids = settings.get("allowed_thread_ids", [])
            message_parts = [
                f"{bot_name}",
                f"{bot_id}",
                f"📶 Tinh trang: {status_text}",
                f"⏳ Han dung: {remaining_time} - {expiration_time_str}",
                f"➡️ Prefix: {prefix}",
                f"🌀 Group quan ly: {allowed_thread_ids if allowed_thread_ids else 'Chua thiet lap'}"
            ]
            message_text = "\n".join(message_parts)
            
            send_message(client, message_object, thread_id, thread_type, message_text)
        
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, 
                        f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    threading.Thread(target=get_bot_info, daemon=True).start()

def handle_share_command(message, message_object, thread_id, thread_type, author_id, client):
    def share_time():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, ban khong co bot!")
            if not admin_cao(client, author_id):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, ban khong phai admin bot!")
            if thread_type != ThreadType.GROUP:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, lenh nay khong the su dung trong tin nhan rieng!")
            parts = message.split()
            if len(parts) < 3:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, vui long nhap đung cu phap: /mybot share [thoi gian] [@tag bot] hoac /mybot share [@tag bot] [thoi gian]\n"
                    f"📖 Đinh dang: `1d`, `5h`, `30m`, `1d 5h 30m`, `all`\n"
                    f"💞 Vi du: /mybot share 1d @Heoder hoac /mybot share @Heoder all")
            mentioned_uids = extract_uids_from_mentions(message_object)
            if not mentioned_uids:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong tim thay bot đuoc tag!")
            duration_str = None
            for i, part in enumerate(parts[2:], start=2):
                if part.lower() == "all" or parse_time_duration(part) is not None:
                    duration_str = part
                    break
            if duration_str is None:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, thoi gian khong hop le! Đinh dang: `1d`, `5h`, `30m`, `1d 5h 30m`, hoac `all`")
            duration_seconds = parse_time_duration(duration_str)
            if duration_seconds is None:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, thoi gian khong hop le! Đinh dang: `1d`, `5h`, `30m`, `1d 5h 30m`, hoac `all`")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, khong the tai cau hinh!")
            for uid in mentioned_uids:
                target_name = get_user_name_by_id(client, uid) if get_user_name_by_id(client, uid) else "Nguoi dung khong ton tai"
                target_bot = None
                for bot in config.get("data", []):
                    if str(bot.get("author_id")) == str(uid):
                        target_bot = bot
                        break
                if not target_bot:
                    send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot cua {target_name} khong ton tai!")
                    continue
                if source_bot.get("is_main_bot", False):
                    send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot chinh khong the chia se thoi gian!")
                    continue
                now = datetime.now()
                source_expiration = datetime.strptime(source_bot.get("het_han", now.strftime("%d/%m/%Y")), "%d/%m/%Y")
                remaining_seconds = (source_expiration - now).total_seconds()
                if remaining_seconds <= 0:
                    send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot cua ban đa het han, khong the chia se!")
                    continue
                if duration_seconds == "all":
                    duration_seconds = remaining_seconds
                if duration_seconds > remaining_seconds:
                    send_message(client, message_object, thread_id, thread_type,
                        f"🚦 {source_name}, thoi gian chia se vuot qua thoi gian con lai cua bot!")
                    continue
                source_new_expiration = source_expiration - timedelta(seconds=duration_seconds)
                target_expiration = datetime.strptime(target_bot.get("het_han", now.strftime("%d/%m/%Y")), "%d/%m/%Y")
                target_new_expiration = max(target_expiration, now) + timedelta(seconds=duration_seconds)
                source_bot["het_han"] = source_new_expiration.strftime("%d/%m/%Y")
                target_bot["het_han"] = target_new_expiration.strftime("%d/%m/%Y")
                target_bot["status"] = True
                save_config(config)
                source_remaining = source_new_expiration - now
                source_days = source_remaining.days
                source_hours = source_remaining.seconds // 3600
                source_minutes = (source_remaining.seconds % 3600) // 60
                target_remaining = target_new_expiration - now
                target_days = target_remaining.days
                target_hours = target_remaining.seconds // 3600
                target_minutes = (target_remaining.seconds % 3600) // 60
                send_message(client, message_object, thread_id, thread_type,
                    f"🔄 Giao dich thanh cong ✅\n\n"
                    f"📤 {source_name}\n"
                    f"\t➜ Bot Name: {source_name}\n"
                    f"\t➜⌛ Con lai: {source_days} ngay {source_hours} gio {source_minutes} phut - {source_new_expiration.strftime('%d/%m/%Y')}\n"
                    f"———————————————————\n"
                    f"📥 {target_name}\n"
                    f"\t➜ Bot Name: {target_name}\n"
                    f"\t➜⌛ Hien tai: {target_days} ngay {target_hours} gio {target_minutes} phut - {target_new_expiration.strftime('%d/%m/%Y')}"
                )
            time.sleep(5)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đa xay ra loi: {str(e)}")

    threading.Thread(target=share_time, daemon=True).start()

def handle_update_command(message, message_object, thread_id, thread_type, author_id, client):
    def update_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, 
                    f"🚦 {source_name}, ban khong co bot đe cap nhat!")
            
            if thread_type != ThreadType.USER:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, lenh nay chi hoat đong voi USER ca nhan inbox rieng, khong hoat đong trong GROUP 🤧\n"
                    f"🚦 Go lenh theo cu phap {client.prefix}mybot update [imei] [cookies JSON] đe cap nhat Bot 🤖\n"
                    f"🚦 Luu y: Cac thong so imei va cookies JSON phai đe trong ngoac [] 📌\n"
                    f"🚦 Vi du: {client.prefix}mybot update [ff33af5c-fb...] [{{\"_ga\": \"GA1.2.103\"}}] ✅")

            import re
            pattern = r"\[(.*?)\]\s*\[(.*?)\]"
            match = re.search(pattern, message)
            if not match or len(match.groups()) < 2:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, vui long cung cap đu thong so theo cu phap {client.prefix}mybot update [imei] [cookies JSON] đe cap nhat Bot 🤖\n"
                    f"🚦 Luu y: Cac thong so imei va cookies JSON phai đe trong ngoac [] 📌\n"
                    f"🚦 Vi du: {client.prefix}mybot update [ff33af5c-fb...] [{{\"_ga\": \"GA1.2.103\"}}] ✅")

            imei, raw_cookies = match.groups()
            raw_cookies = ''.join(c for c in raw_cookies if c.isprintable() and c not in '\n\r\t')
            cookies = None if not raw_cookies else json.loads(raw_cookies) if raw_cookies.startswith('{') and raw_cookies.endswith('}') else None

            if cookies is None and raw_cookies:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, cookies khong hop le! Phai la mot đoi tuong JSON hoan chinh, vi du: {{\"_ga\": \"GA1.2.103\"}}")
            if not isinstance(cookies, dict) and cookies is not None:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, cookies khong hop le! Phai la mot đoi tuong JSON (dang tu đien). Vi du: {{\"key\": \"value\"}}")

            if not imei.strip():
                return send_message(client, message_object, thread_id, thread_type, 
                    f"🚦 {source_name}, IMEI khong hop le!")

            source_bot["imei"] = imei
            source_bot["session_cookies"] = cookies
            save_config(config)
            
            send_message(client, message_object, thread_id, thread_type, 
                f"🚦 Bot cua {source_name} đa đuoc cap nhat thanh cong!\n"
                f"➜ IMEI moi: {imei}\n"
                f"➜ Cookies moi: {json.dumps(cookies) if cookies else 'Khong co cookies'}")
        
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, 
                f"🚦 {source_name}, đa xay ra loi khi cap nhat bot: {str(e)}")

    threading.Thread(target=update_bot_entry, daemon=True).start()

def handle_setbox_command(message, message_object, thread_id, thread_type, author_id, client):
    def set_box_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, 
                    f"➜ {source_name}, ban khong co bot đe thiet lap box quan ly!")
  
            if not admin_cao(client, author_id):
                return send_message(client, message_object, thread_id, thread_type, 
                    f"❌ {source_name}, ban khong phai admin bot đe su dung lenh nay!")
            
            if thread_type != ThreadType.GROUP:
                return send_message(client, message_object, thread_id, thread_type,
                    f"➜ {source_name}, lenh nay chi hoat đong trong GROUP, khong hoat đong trong tin nhan rieng!")

            box_id = thread_id
            source_bot["box_id"] = box_id
            save_config(config)
            
            send_message(client, message_object, thread_id, thread_type, 
                f"➜ Successfuly!\n"
                f"➜ ID Box: {box_id}\n"
                f"➜ Nguoi thiet lap: {source_name}")
        
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, 
                f"➜ {source_name}, đa xay ra loi khi thiet lap box quan ly: {str(e)}")

    threading.Thread(target=set_box_entry, daemon=True).start()

def handle_thuebot_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        content = message.strip().split()
        if len(content) < 2:
            msg = "".join([
                f"🤖 Tao Bot ({client.prefix}mybot create)\n"
                f"🔄 Khoi đong lai Bot ({client.prefix}mybot rs)\n"
                f"➡️ Danh sach Bot ({client.prefix}mybot list)\n"
                f"🔒 Khoa/Mo khoa Bot ({client.prefix}mybot lock/unlock @bot)\n"
                f"📟 Đoi lenh dung Bot ({client.prefix}mybot prefix [prefix]/@bot)\n"
                f"🤝 Share ngay su dung (d=ngay, h=gio, m=phut) ({client.prefix}mybot share)\n"
                f"🗑️ Xoa Bot ({client.prefix}mybot del @bot)\n"
                f"🚀 Kich hoat thoi gian su dung Bot(OA) ({client.prefix}mybot active @bot [days])\n"
                f"♨️ Xem thong tin Bot minh hoac Bot nguoi khac ({client.prefix}mybot info/@bot)\n"
                f"🔧 Cap nhat IMEI va Cookies ({client.prefix}mybot update [imei] [cookies JSON])\n"
                f"📬 Thiet lap Box quan ly Bot(OA) ({client.prefix}mybot setbox)\n"
            ])
            os.makedirs(CACHE_PATH, exist_ok=True)
    
            image_path = generate_menu_image(client, author_id, thread_id, thread_type)
            if not image_path:
                client.sendMessage("❌ Khong the tao anh menu!", thread_id, thread_type)
                return

            reaction = [
                "❌", "🤧", "🐞", "😊", "🔥", "👍", "💖", "🚀",
                "😍", "😂", "😢", "😎", "🙌", "💪", "🌟", "🍀",
                "🎉", "🦁", "🌈", "🍎", "⚡", "🔔", "🎸", "🍕",
                "🏆", "📚", "🦋", "🌍", "⛄", "🎁", "💡", "🐾",
                "😺", "🐶", "🐳", "🦄", "🌸", "🍉", "🍔", "🎄",
                "🎃", "👻", "☃️", "🌴", "🏀", "⚽", "🎾", "🏈",
                "🚗", "✈️", "🚢", "🌙", "☀️", "⭐", "⛅", "☔",
                "⌛", "⏰", "💎", "💸", "📷", "🎥", "🎤", "🎧",
                "🍫", "🍰", "🍩", "☕", "🍵", "🍷", "🍹", "🥐",
                "🐘", "🦒", "🐍", "🦜", "🐢", "🦀", "🐙", "🦈",
                "🍓", "🍋", "🍑", "🥥", "🥐", "🥪", "🍝", "🍣",
                "🎲", "🎯", "🎱", "🎮", "🎰", "🧩", "🧸", "🎡",
                "🏰", "🗽", "🗼", "🏔️", "🏝️", "🏜️", "🌋", "⛲",
                "📱", "💻", "🖥️", "🖨️", "⌨️", "🖱️", "📡", "🔋",
                "🔍", "🔎", "🔑", "🔒", "🔓", "📩", "📬", "📮",
                "💢", "💥", "💫", "💦", "💤", "🚬", "💣", "🔫",
                "🩺", "💉", "🩹", "🧬", "🔬", "🔭", "🧪", "🧫",
                "🧳", "🎒", "👓", "🕶️", "👔", "👗", "👠", "🧢",
                "🦷", "🦴", "👀", "👅", "👄", "👶", "👩", "👨",
                "🚶", "🏃", "💃", "🕺", "🧘", "🏄", "🏊", "🚴",
                "🍄", "🌾", "🌻", "🌵", "🌿", "🍂", "🍁", "🌊",
                "🛠️", "🔧", "🔨", "⚙️", "🪚", "🪓", "🧰", "⚖️",
                "🧲", "🪞", "🪑", "🛋️", "🛏️", "🪟", "🚪", "🧹"
            ]
            
            client.sendReaction(message_object, random.choice(reaction), thread_id, thread_type)
            client.sendLocalImage(
                imagePath=image_path,
                message=Message(text=msg, mention=Mention(author_id, length=len(f"{get_user_name_by_id(client, author_id)}"), offset=0)),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1920,
                height=600,
                ttl=240000
            )
            
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"❌ Loi khi xoa anh: {e}")
            return

        if len(content) >= 2:
            command = content[1].lower()
        handlers = {
            'create': handle_create_command,
            'lock': handle_lock_command,
            'unlock': handle_unlock_command,
            'list': handle_list_bots_command,
            'del': handle_del_command,
            'rs': handle_reset_command,
            'prefix': handle_change_prefix_command,
            'active': handle_active_command,
            'info': handle_bot_info_command,
            'share': handle_share_command,
            'update': handle_update_command,
            'setbox': handle_setbox_command
        }
        if command in handlers:
            handlers[command](message, message_object, thread_id, thread_type, author_id, client)
        else:
            send_message(client, message_object, thread_id, thread_type, f"➜ Lenh [mybot {command}] khong đuoc ho tro 🤧")
    except Exception as e:
        send_message(client, message_object, thread_id, thread_type, f"➜ 🐞 Đa xay ra loi: {e}🤧")

def get_dominant_color(image_path):
    try:
        if not os.path.exists(image_path):
            print(f"File anh khong ton tai: {image_path}")
            return (0, 0, 0)

        img = Image.open(image_path).convert("RGB")
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        pixels = img.getdata()

        if not pixels:
            print(f"Khong the lay du lieu pixel tu anh: {image_path}")
            return (0, 0, 0)

        r, g, b = 0, 0, 0
        for pixel in pixels:
            r += pixel[0]
            g += pixel[1]
            b += pixel[2]
        total = len(pixels)
        if total == 0:
            return (0, 0, 0)
        r, g, b = r // total, g // total, b // total
        return (r, g, b)

    except Exception as e:
        print(f"Loi khi phan tich mau noi bat: {e}")
        return (0, 0, 0)

def get_contrasting_color(base_color, alpha=255):
    r, g, b = base_color[:3]
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return (255, 255, 255, alpha) if luminance < 0.5 else (0, 0, 0, alpha)

def random_contrast_color(base_color):
    r, g, b, _ = base_color
    box_luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    if box_luminance > 0.5:
        r = random.randint(0, 50)
        g = random.randint(0, 50)
        b = random.randint(0, 50)
    else:
        r = random.randint(200, 255)
        g = random.randint(200, 255)
        b = random.randint(200, 255)
    
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    s = min(1.0, s + 0.9)
    v = min(1.0, v + 0.7)
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    text_luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    if abs(text_luminance - box_luminance) < 0.3:
        if box_luminance > 0.5:
            r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v * 0.4))
        else:
            r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v * 1.7))
    
    return (int(r * 255), int(g * 255), int(b * 255), 255)

def download_avatar(avatar_url, save_path=os.path.join(CACHE_PATH, "user_avatar.png")):
    if not avatar_url:
        return None
    try:
        resp = requests.get(avatar_url, stream=True, timeout=5)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return save_path
    except Exception as e:
        print(f"❌ Loi tai avatar: {e}")
    return None

def generate_menu_image(bot, author_id, thread_id, thread_type):
    images = glob.glob(os.path.join(BACKGROUND_PATH, "*.jpg")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.png")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.jpeg"))
    if not images:
        print("❌ Khong tim thay anh trong thu muc background/")
        return None

    image_path = random.choice(images)

    try:
        size = (1920, 600)
        final_size = (1280, 380)
        bg_image = Image.open(image_path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=7))
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        dominant_color = get_dominant_color(image_path)
        r, g, b = dominant_color
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

        box_colors = [
            (255, 20, 147, 90),
            (128, 0, 128, 90),
            (0, 100, 0, 90),
            (0, 0, 139, 90),
            (184, 134, 11, 90),
            (138, 3, 3, 90),
            (0, 0, 0, 90)
        ]

        box_color = random.choice(box_colors)

        box_x1, box_y1 = 90, 60
        box_x2, box_y2 = size[0] - 90, size[1] - 60
        draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=75, fill=box_color)

        font_arial_path = "arial unicode ms.otf"
        font_emoji_path = "emoji.ttf"
        
        try:
            font_text_large = ImageFont.truetype(font_arial_path, size=76)
            font_text_big = ImageFont.truetype(font_arial_path, size=68)
            font_text_small = ImageFont.truetype(font_arial_path, size=64)
            font_text_bot = ImageFont.truetype(font_arial_path, size=58)
            font_time = ImageFont.truetype(font_arial_path, size=56)
            font_icon = ImageFont.truetype(font_emoji_path, size=60)
            font_icon_large = ImageFont.truetype(font_emoji_path, size=175)
            font_name = ImageFont.truetype(font_emoji_path, size=60)
        except Exception as e:
            print(f"❌ Loi tai font: {e}")
            font_text_large = ImageFont.load_default(size=76)
            font_text_big = ImageFont.load_default(size=68)
            font_text_small = ImageFont.load_default(size=64)
            font_text_bot = ImageFont.load_default(size=58)
            font_time = ImageFont.load_default(size=56)
            font_icon = ImageFont.load_default(size=60)
            font_icon_large = ImageFont.load_default(size=175)
            font_name = ImageFont.load_default(size=60)

        def draw_text_with_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 250), shadow_offset=(2, 2)):
            x, y = position
            draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=fill)

        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        vietnam_now = datetime.now(vietnam_tz)
        hour = vietnam_now.hour
        formatted_time = vietnam_now.strftime("%H:%M")
        time_icon = "🌤️" if 6 <= hour < 18 else "🌙"
        time_text = f" {formatted_time}"
        time_x = box_x2 - 250
        time_y = box_y1 + 10
        
        box_rgb = box_color[:3]
        box_luminance = (0.299 * box_rgb[0] + 0.587 * box_rgb[1] + 0.114 * box_rgb[2]) / 255
        last_lines_color = (255, 255, 255, 220) if box_luminance < 0.5 else (0, 0, 0, 220)

        time_color = last_lines_color

        if time_x >= 0 and time_y >= 0 and time_x < size[0] and time_y < size[1]:
            try:
                icon_x = time_x - 75
                icon_color = random_contrast_color(box_color)
                draw_text_with_shadow(draw, (icon_x, time_y - 8), time_icon, font_icon, icon_color)
                draw.text((time_x, time_y), time_text, font=font_time, fill=time_color)
            except Exception as e:
                print(f"❌ Loi ve thoi gian len anh: {e}")
                draw_text_with_shadow(draw, (time_x - 75, time_y - 8), "⏰", font_icon, (255, 255, 255, 255))
                draw.text((time_x, time_y), " ??;??", font=font_time, fill=time_color)

        user_info = bot.fetchUserInfo(author_id) if author_id else None
        user_name = "Unknown"
        if user_info and hasattr(user_info, 'changed_profiles') and author_id in user_info.changed_profiles:
            user = user_info.changed_profiles[author_id]
            user_name = getattr(user, 'name', None) or getattr(user, 'displayName', None) or f"ID_{author_id}"

        greeting_name = "Chu Nhan" if str(author_id) == is_admin else user_name

        emoji_colors = {
            "🎵": random_contrast_color(box_color),
            "😁": random_contrast_color(box_color),
            "🖤": random_contrast_color(box_color),
            "💞": random_contrast_color(box_color),
            "🤖": random_contrast_color(box_color),
            "💻": random_contrast_color(box_color),
            "📅": random_contrast_color(box_color),
            "🎧": random_contrast_color(box_color),
            "🌙": random_contrast_color(box_color),
            "🌤️": (200, 150, 50, 255)
        }

        text_lines = [
            f"Hi, {greeting_name}",
            f"💞 Chao Ban, toi co the giup gi cho ban a?",
            f"@Quan ly bot cua ban 🚀 ",
            "😁 Bot San Sang Phuc 🖤",
            f"🤖Bot: {bot.me_name} 💻Version: {bot.version} 📅Update {bot.date_update}"
        ]

        color1 = random_contrast_color(box_color)
        color2 = random_contrast_color(box_color)
        while color1 == color2:
            color2 = random_contrast_color(box_color)
        text_colors = [
            color1,
            color2,
            last_lines_color,
            last_lines_color,
            last_lines_color
        ]

        text_fonts = [
            font_text_large,
            font_text_big,
            font_text_bot,
            font_text_bot,
            font_text_small
        ]

        line_spacing = 85
        start_y = box_y1 + 10

        avatar_url = user_info.changed_profiles[author_id].avatar if user_info and hasattr(user_info, 'changed_profiles') and author_id in user_info.changed_profiles else None
        avatar_path = download_avatar(avatar_url)
        if avatar_path and os.path.exists(avatar_path):
            avatar_size = 200
            try:
                avatar_img = Image.open(avatar_path).convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                border_size = avatar_size + 10
                rainbow_border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
                draw_border = ImageDraw.Draw(rainbow_border)
                steps = 360
                for i in range(steps):
                    h = i / steps
                    r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                    draw_border.arc([(0, 0), (border_size-1, border_size-1)], start=i, end=i + (360 / steps), fill=(int(r * 255), int(g * 255), int(b * 255), 255), width=5)
                avatar_y = (box_y1 + box_y2 - avatar_size) // 2
                overlay.paste(rainbow_border, (box_x1 + 40, avatar_y), rainbow_border)
                overlay.paste(avatar_img, (box_x1 + 45, avatar_y + 5), mask)
            except Exception as e:
                print(f"❌ Loi xu ly avatar: {e}")
                draw.text((box_x1 + 60, (box_y1 + box_y2) // 2 - 140), "🐳", font=font_icon, fill=(0, 139, 139, 255))
        else:
            draw.text((box_x1 + 60, (box_y1 + box_y2) // 2 - 140), "🐳", font=font_icon, fill=(0, 139, 139, 255))

        current_line_idx = 0
        for i, line in enumerate(text_lines):
            if not line:
                current_line_idx += 1
                continue

            parts = []
            current_part = ""
            for char in line:
                if ord(char) > 0xFFFF:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                    parts.append(char)
                else:
                    current_part += char
            if current_part:
                parts.append(current_part)

            total_width = 0
            part_widths = []
            current_font = font_text_bot if i == 4 else text_fonts[i]
            for part in parts:
                font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
                width = draw.textbbox((0, 0), part, font=font_to_use)[2]
                part_widths.append(width)
                total_width += width

            max_width = box_x2 - box_x1 - 300
            if total_width > max_width:
                font_size = int(current_font.getbbox("A")[3] * max_width / total_width * 0.9)
                if font_size < 60:
                    font_size = 60
                try:
                    current_font = ImageFont.truetype(font_arial_path, size=font_size) if os.path.exists(font_arial_path) else ImageFont.load_default(size=font_size)
                except Exception as e:
                    print(f"❌ Loi đieu chinh font size: {e}")
                    current_font = ImageFont.load_default(size=font_size)
                total_width = 0
                part_widths = []
                for part in parts:
                    font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
                    width = draw.textbbox((0, 0), part, font=font_to_use)[2]
                    part_widths.append(width)
                    total_width += width

            text_x = (box_x1 + box_x2 - total_width) // 2
            text_y = start_y + current_line_idx * line_spacing + (current_font.getbbox("A")[3] // 2)

            current_x = text_x
            for part, width in zip(parts, part_widths):
                if any(ord(c) > 0xFFFF for c in part):
                    emoji_color = emoji_colors.get(part, random_contrast_color(box_color))
                    draw_text_with_shadow(draw, (current_x, text_y), part, font_icon, emoji_color)
                    if part == "🤖" and i == 4:
                        draw_text_with_shadow(draw, (current_x, text_y - 5), part, font_icon, emoji_color)
                else:
                    if i < 2:
                        draw_text_with_shadow(draw, (current_x, text_y), part, current_font, text_colors[i])
                    else:
                        draw.text((current_x, text_y), part, font=current_font, fill=text_colors[i])
                current_x += width
            current_line_idx += 1

        right_icons = ["🎧"]
        right_icon = random.choice(right_icons)
        icon_right_x = box_x2 - 225
        icon_right_y = (box_y1 + box_y2 - 180) // 2
        draw_text_with_shadow(draw, (icon_right_x, icon_right_y), right_icon, font_icon_large, emoji_colors.get(right_icon, (80, 80, 80, 255)))

        final_image = Image.alpha_composite(bg_image, overlay)
        final_image = final_image.resize(final_size, Image.Resampling.LANCZOS)
        os.makedirs(os.path.dirname(OUTPUT_IMAGE_PATH), exist_ok=True)
        final_image.save(OUTPUT_IMAGE_PATH, "PNG", quality=95)
        print(f"✅ Anh menu đa đuoc luu: {OUTPUT_IMAGE_PATH}")
        return OUTPUT_IMAGE_PATH

    except Exception as e:
        print(f"❌ Loi xu ly anh menu: {e}")
        return None