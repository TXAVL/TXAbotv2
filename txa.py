import os
import io
import time
import json
import math
import queue
from colorama import Fore, Back, Style
import random
import logging
from queue import Queue
import tempfile
import threading
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

# Thu vien ben ngoai
import requests

from modules.group.pro_group import handle_group_command
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageFilter, ImageEnhance
from bs4 import BeautifulSoup
from colorama import Style, init
import pyfiglet

# Zalo Bot va Core
from zlapi import ZaloAPI
from zlapi.models import Message, ThreadType
from core.bot_sys import *

# Command Modules
from modules.ff.pro_ff import handle_ff_command

from modules.ngl.pro_ngl import handle_ngl_command

from modules.qrbank.pro_qrbank import handle_qrbank_command


from modules.ff.pro_spamff import handle_kb_command

# from modules.save.pro_save import handle_save_command

from modules.attack.pro_attack import handle_attack_command

from modules.stkxp.pro_stkxp import handle_stkxp_command

from modules.reghotmail.pro_reghotmail import handle_reghotmail_command
from modules.doff.pro_doff import handle_doff_command
from modules.autosend.pro_autosend import handle_autosend_command
from modules.AI_GEMINI.pro_gemini import handle_chat_command
from modules.anhgai.pro_anhgai import handle_anhgai_command
from modules.cauthinh.pro_thinh import handle_tha_thinh_command
from modules.creat_menu.menu_or import handle_menu_or_commands
from modules.creat_menu.menu_zl import handle_menu_zl_command
from modules.creat_menu.pro_hiden import handle_hiden_commands
from modules.creat_menu.pro_menu import handle_menu_commands
from modules.dhbc.pro_dhbc import handle_dhbc_command
from modules.func_allan.pro_allan import command_allan_for_link, command__allan_cd
from modules.func_disbox.pro_disbox import handle_disbox
from modules.func_friend.pro_friend import addallfriongr, addfrito, blockto, removefrito, unblockto
from modules.func_giavang.pro_giavang import handle_gia_vang_command
from modules.func_kickall.pro_kickall import kick_member_group
from modules.func_leave.pro_leave import handle_leave_group_command
from modules.func_make.make import handle_make_command
from modules.func_meme.pro_meme import meme
from modules.func_mst.mst import mst
from modules.func_news.pro_news import news
from modules.func_phatnguoi.pro_phatnguoi import phatnguoi
from modules.func_pin.pro_pin import handle_pro_pin
from modules.func_pixi.pro_pixi import pixitimkiem
from modules.func_share.pro_share import handle_share_command
from modules.func_spam_call.pro_spamcall import handle_spamcall_command
from modules.func_spamsms.pro_spamsms import handle_sms_command
from modules.func_src.pro_src import src
from modules.func_stk.pro_stk import handle_stk_command
from modules.func_tygia.pro_tygia import handle_hoan_doi_command
from modules.func_war.allwar import handle_allwar_command
from modules.get_link.pro_getlink import handle_getlink_command
from modules.get_voice.pro_getvoice import handle_getvoice_command
from modules.join_gr.join import handle_join_command
from modules.join_gr.join1 import handle_join1_command
from modules.nhac_scl.pro_nhac import handle_nhac_command
from modules.taixiu.pro_taixiu import handle_tx_command
from modules.text.pro_text import handle_create_image_command
from modules.thue_bot.pro_thue_bot import handle_thuebot_command
from modules.translate.pro_dich import handle_translate_command
from modules.vdgai.pro_vdgai import handle_vdgai_command
from modules.weather.pro_weather import handle_weather_command


message_count = {}
def send_random_sticker(bot, thread_id, thread_type):
    with open('auto_sticker.json', 'r', encoding='utf-8') as file:
        stickers = json.load(file)
    sticker = random.choice(stickers)
    bot.sendSticker(sticker['stickerType'], sticker['stickerId'], sticker['cateId'], thread_id, thread_type)

def auto_stk(bot, message_object, author_id, thread_id, thread_type):
    settings = read_settings(bot.uid)
    if settings.get('auto_sticker', {}).get(thread_id, False) and thread_id in settings.get('allowed_thread_ids', []):
        if thread_id not in message_count:
            message_count[thread_id] = 0
        message_count[thread_id] += 1
        if message_count[thread_id] >= random.randint(10,11):
            send_random_sticker(bot, thread_id, thread_type)
            message_count[thread_id] = 0


current_word = None
wrong_attempts = 0
correct_attempts = 0
timeout_thread = None
timeout_duration = 30
current_player = None
used_words = set()
game_active = False
leaderboard = {}
leaderboard_file = "leaderboard.json"
words = []

def load_words():
    global words
    try:
        with open('words.txt', 'r', encoding='utf-8') as file:
            words = [line.strip() for line in file if line.strip()]
        return words
    except FileNotFoundError:
        words = []
        return words

words = load_words()

def load_leaderboard(uid):
    global leaderboard
    data_file_path = f"{uid}_{leaderboard_file}"
    try:
        with open(data_file_path, 'r', encoding='utf-8') as f:
            leaderboard = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard = {}

def save_leaderboard(uid):
    data_file_path = f"{uid}_{leaderboard_file}"
    try:
        with open(data_file_path, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")

def save_word_to_file(word):
    try:
        with open('words.txt', 'a', encoding='utf-8') as file:
            file.write(f"\n{word}")
        if word not in words:
            words.append(word)
    except Exception as e:
        print(f"Error saving word: {e}")

def remove_word_from_file(word):
    global words
    if word in words:
        try:
            with open('words.txt', 'r', encoding='utf-8') as file:
                lines = file.readlines()
            with open('words.txt', 'w', encoding='utf-8') as file:
                for line in lines:
                    if line.strip() != word:
                        file.write(line)
            words = load_words()
            return True
        except Exception as e:
            print(f"Error removing word: {e}")
    return False

def reset_game():
    global current_word, wrong_attempts, correct_attempts, timeout_thread, current_player, used_words, game_active
    if timeout_thread and timeout_thread.is_alive():
        timeout_thread.cancel()
    
    current_word = None
    wrong_attempts = 0
    correct_attempts = 0
    timeout_thread = None
    current_player = None
    used_words.clear()
    game_active = False

def handle_timeout(bot, message_object, thread_id, thread_type):
    global game_active
    if not game_active:
        return
    bot.sendReaction(message_object, "❌", thread_id, thread_type)
    bot.replyMessage(Message(text="➜ ❌ Ban đa het thoi gian tra loi! Tro choi ket thuc."), 
                    message_object, thread_id=thread_id, thread_type=thread_type)
    reset_game()

def start_timeout(bot, message_object, thread_id, thread_type):
    global timeout_thread, game_active
    if timeout_thread and timeout_thread.is_alive():
        timeout_thread.cancel()
    game_active = True
    timeout_thread = threading.Timer(timeout_duration, lambda: handle_timeout(bot, message_object, thread_id, thread_type))
    timeout_thread.start()

def fetch_webpage(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching webpage: {str(e)}")
        return None

def get_wikipedia_info(search_term):
    base_url = "https://vi.wikipedia.org/wiki/"
    search_url = base_url + search_term.replace(" ", "_")
    
    page_content = fetch_webpage(search_url)
    if not page_content:
        return {"Loi": "Khong the lay thong tin tu Wikipedia."}

    soup = BeautifulSoup(page_content, "html.parser")
    image_url = "Khong tim thay anh"
    infobox = soup.find("table", {"class": "infobox"})
    
    if infobox:
        image_tag = infobox.find("img")
        if image_tag and "src" in image_tag.attrs:
            image_url = "https:" + image_tag["src"]

    info = {}
    if infobox:
        rows = infobox.find_all("tr")
        for row in rows:
            header = row.find("th")
            data = row.find("td")
            if header and data:
                links = data.find_all("a", href=True)
                if links:
                    info[header.text.strip()] = [f"https://vi.wikipedia.org{link['href']}" for link in links]
                else:
                    info[header.text.strip()] = data.text.strip()

    paragraphs = soup.find_all("p")
    content = "\n\n".join([p.text.strip() for p in paragraphs[:2] if p.text.strip()])

    return {
        "Hinh anh": image_url,
        "Thong tin": info,
        "Mo ta": content
    }

def check_word(player_word, last_part):
    if not player_word or not last_part:
        return False
    if player_word in words and player_word.split()[0] == last_part:
        return True
    wiki_info = get_wikipedia_info(player_word)
    if "Loi" not in wiki_info and wiki_info["Mo ta"]:
        if player_word.split()[0] == last_part:
            save_word_to_file(player_word)
            return True
    return False

def update_leaderboard(bot, user_id, user_name, words_used):
    global leaderboard
    load_leaderboard(bot.uid)
    
    if user_id not in leaderboard:
        leaderboard[user_id] = {"name": user_name, "score": 0, "correct_answers": 0}
    
    leaderboard[user_id]["score"] += words_used
    leaderboard[user_id]["correct_answers"] += words_used
    leaderboard[user_id]["name"] = user_name
    
    save_leaderboard(bot.uid)
    return leaderboard[user_id]

def get_user_rank(bot, user_id):
    load_leaderboard(bot.uid)
    if not leaderboard or user_id not in leaderboard:
        return None
    
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1]["score"], reverse=True)
    for rank, (uid, _) in enumerate(sorted_leaderboard, 1):
        if uid == user_id:
            return rank
    return None

def handle_victory(bot, message_object, author_id, thread_id, thread_type):
    user_name = get_user_name_by_id(bot, author_id)
    words_used = correct_attempts
    user_data = update_leaderboard(bot, author_id, user_name, words_used)
    user_rank = get_user_rank(bot, author_id)
    
    message = f"🚦 {user_name}\n"
    message += "🎈 Xin chuc mung ban đa chien thang!\n"
    message += f"💯 Khich le: +{words_used} 🍫\n"
    message += f"🏅 Thanh tich: {words_used} tu\n"
    
    if user_rank and user_rank <= 10:
        medal_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medal_emojis.get(user_rank, f"{user_rank}")
        message += f"🎉 Ban đa lap ky luc moi đung {medal} trong BXH!"
    
    bot.replyMessage(Message(text=message, mention=Mention(author_id, length=len(user_name), offset=3)), 
                    message_object, thread_id=thread_id, thread_type=thread_type)
    reset_game()

def handle_defeat(bot, message_object, author_id, thread_id, thread_type):
    user_name = get_user_name_by_id(bot, author_id)
    correct_answers = correct_attempts
    
    if correct_answers > 0:
        user_data = update_leaderboard(bot, author_id, user_name, correct_answers)
        user_rank = get_user_rank(bot, author_id)
    else:
        user_rank = None
    
    message = f"🚦 {user_name}\n"
    message += "😢 Ban đa sai qua nhieu lan. Thua roi!\n"
    message += f"🎖️ Thanh tich: {correct_answers} tu\n"
    
    if user_rank and user_rank <= 10:
        medal_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medal_emojis.get(user_rank, f"{user_rank}")
        message += f"🎉 Ban đa lap ky luc moi đung {medal} trong BXH!"
    
    bot.replyMessage(Message(text=message, mention=Mention(author_id, length=len(user_name), offset=3)), 
                    message_object, thread_id=thread_id, thread_type=thread_type)
    reset_game()

def handle_wrong_attempt(bot, message_object, thread_id, thread_type):
    global wrong_attempts
    wrong_attempts += 1
    for _ in range(wrong_attempts):
        bot.sendReaction(message_object, "❌", thread_id, thread_type)
    if wrong_attempts >= 3:
        handle_defeat(bot, message_object, current_player, thread_id, thread_type)
        return True
    return False

def get_leaderboard_display(bot):
    load_leaderboard(bot.uid)
    
    if not leaderboard:
        return "🚦 BXH 🏅 Top Game Noi Tu:\n➜ Chua co du lieu xep hang!"
    
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1]["score"], reverse=True)
    
    display_text = "🚦 BXH 🏅 Top 10 Game Noi Tu:\n"
    medals = ["🥇", "🥈", "🥉"] + [f"{i}" for i in range(4, 11)]
    
    for i, (user_id, data) in enumerate(sorted_leaderboard[:10], 1):
        medal = medals[i-1]
        name = data["name"]
        score = data["score"]
        display_text += f"➜ {medal} {name} - {score} tu\n"
    
    return display_text.strip()

def nt_bxh(bot, message_object, thread_id, thread_type):
    display_text = get_leaderboard_display(bot)
    bot.replyMessage(Message(text=display_text), 
                    message_object, thread_id=thread_id, thread_type=thread_type)

def process_valid_word(bot, message_object, author_id, thread_id, thread_type, player_word):
    global current_word, wrong_attempts, correct_attempts, used_words
    player_last_part = player_word.split()[-1]
    used_words.add(player_word)
    
    next_word = next(
        (word for word in words 
         if word.split()[0] == player_last_part
         and word not in used_words 
         and len(word.split()) == 2),
        None
    )
    
    if next_word:
        current_word = next_word
        used_words.add(next_word)
        wrong_attempts = 0
        correct_attempts += 1
        
        for _ in range(correct_attempts):
            bot.sendReaction(message_object, "✅", thread_id, thread_type)
        
        response = f"{get_user_name_by_id(bot, author_id)} {next_word}"
        start_timeout(bot, message_object, thread_id, thread_type)
        bot.replyMessage(Message(text=response, mention=Mention(author_id, length=len(f"{get_user_name_by_id(bot, author_id)}"), offset=0)), 
                       message_object, thread_id=thread_id, thread_type=thread_type)
    else:
        handle_victory(bot, message_object, author_id, thread_id, thread_type)

def start_new_game(bot, message_object, author_id, thread_id, thread_type):
    global current_word, current_player, used_words, game_active
    if not words:
        bot.replyMessage(Message(text="➜ ❌ File words.txt khong chua tu nao!"), 
                       message_object, thread_id=thread_id, thread_type=thread_type)
        return
    current_word = random.choice(words)
    used_words.add(current_word)
    current_player = author_id
    game_active = True
    response = f"➜ Tu khoi đau: '{current_word}'\n"
    start_timeout(bot, message_object, thread_id, thread_type)
    bot.replyMessage(Message(text=response), message_object,
                   thread_id=thread_id, thread_type=thread_type)

def nt_check(bot, message_object, author_id, thread_id, thread_type, message):
    parts = message.strip().split()
    if len(parts) < 3 or parts[1].lower() != "check":
        bot.replyMessage(Message(text="➜ Cu phap khong đung! Su dung: /nt check <tu>"), 
                        message_object, thread_id=thread_id, thread_type=thread_type)
        return
    
    search_term = " ".join(parts[2:])
    wiki_info = get_wikipedia_info(search_term)
    
    if "Loi" in wiki_info or not wiki_info["Mo ta"]:
        response = f"➜ Tu '{search_term}' khong đuoc tim thay tren Wikipedia hoac khong co nghia ro rang."
    else:
        response = (
            f"➜ Ket qua cho '{search_term}':\n"
            f"📝 Mo ta: {wiki_info['Mo ta'][:200]}...\n"
            f"🖼️ Hinh anh: {wiki_info['Hinh anh']}\n"
            f"🔗 Link: https://vi.wikipedia.org/wiki/{search_term.replace(' ', '_')}"
        )
        if search_term not in words:
            save_word_to_file(search_term)
            response += f"\n✅ Đa them '{search_term}' vao danh sach tu vung!"

    bot.replyMessage(Message(text=response), message_object, 
                    thread_id=thread_id, thread_type=thread_type)

def nt_add(bot, message_object, author_id, thread_id, thread_type, message):
    parts = message.strip().split()
    if len(parts) < 3 or parts[1].lower() != "add":
        bot.replyMessage(Message(text="➜ Cu phap khong đung! Su dung: /nt add <tu>"), 
                        message_object, thread_id=thread_id, thread_type=thread_type)
        return
    
    new_word = " ".join(parts[2:])
    if new_word in words:
        response = f"🚦 {get_user_name_by_id(bot, author_id)} Tu '{new_word}' đa ton tai trong tu đien! ⚠️"
    else:
        save_word_to_file(new_word)
        response = f"🚦 {get_user_name_by_id(bot, author_id)} Đa them tu '{new_word}' vao tu đien thanh cong! ✅"
    
    bot.replyMessage(Message(text=response, mention=Mention(author_id, length=len(f"{get_user_name_by_id(bot, author_id)}"), offset=3)), 
                    message_object, thread_id=thread_id, thread_type=thread_type)

def nt_del(bot, message_object, author_id, thread_id, thread_type, message):
    parts = message.strip().split()
    if len(parts) < 3 or parts[1].lower() != "del":
        bot.replyMessage(Message(text="➜ Cu phap khong đung! Su dung: /nt del <tu>"), 
                        message_object, thread_id=thread_id, thread_type=thread_type)
        return
    
    word_to_remove = " ".join(parts[2:])
    if remove_word_from_file(word_to_remove):
        response = f"🚦 Đa xoa tu '{word_to_remove}' khoi tu đien ✅"
    else:
        response = f"➜ Tu '{word_to_remove}' khong co trong tu đien 🤧"
    
    bot.replyMessage(Message(text=response), message_object, 
                    thread_id=thread_id, thread_type=thread_type)

def nt_go(bot, message_object, author_id, thread_id, thread_type, message):
    global current_word, wrong_attempts, current_player, used_words, game_active
    message_text = message.strip()
    
    if message_text.startswith(f"{bot.prefix}nt bxh"):
        return nt_bxh(bot, message_object, thread_id, thread_type)
    elif message_text.startswith(f"{bot.prefix}nt check"):
        return nt_check(bot, message_object, author_id, thread_id, thread_type, message)
    elif message_text.startswith(f"{bot.prefix}nt add"):
        return nt_add(bot, message_object, author_id, thread_id, thread_type, message)
    elif message_text.startswith(f"{bot.prefix}nt del"):
        return nt_del(bot, message_object, author_id, thread_id, thread_type, message)
    elif message_text == f"{bot.prefix}nt":
        return show_menu(bot, message_object, message, author_id, thread_id, thread_type)

    if not game_active or current_player is None:
        return start_new_game(bot, message_object, author_id, thread_id, thread_type)
    
    if game_active and author_id != current_player:
        return

    if author_id != current_player:
        return
    
    player_word = message_text.replace(f"{bot.prefix}nt", "").strip()
    if len(player_word.split()) != 2:
        if handle_wrong_attempt(bot, message_object, thread_id, thread_type):
            return
        start_timeout(bot, message_object, thread_id, thread_type)
        return
    
    if player_word in used_words:
        if handle_wrong_attempt(bot, message_object, thread_id, thread_type):
            return
        start_timeout(bot, message_object, thread_id, thread_type)
        return
    
    last_part = current_word.split()[-1]
    if not check_word(player_word, last_part):
        if handle_wrong_attempt(bot, message_object, thread_id, thread_type):
            return
        start_timeout(bot, message_object, thread_id, thread_type)
        return
    
    if timeout_thread and timeout_thread.is_alive():
        timeout_thread.cancel()
    
    process_valid_word(bot, message_object, author_id, thread_id, thread_type, player_word)

def show_menu(bot, message_object, message, author_id, thread_id, thread_type):
    content = message.strip().split()
    message_text = message.strip()
    if message_text.startswith(f"{bot.prefix}nt"):
        if len(content) == 1:
            menu_nt = {
                f"{bot.prefix}nt go": "🔠 Bat đau game",
                f"{bot.prefix}nt check [tu vung]": "✅ Kiem tra y nghia tu vung",
                f"{bot.prefix}nt bxh": "🏆 Top 10 BXH",
                f"{bot.prefix}nt add [tu vung]": "✚ Them tu vung (BMT)",
                f"{bot.prefix}nt del [tu vung]": "🗑️ Xoa tu vung"
            }
            temp_image_path, menu_message = create_menu_nt_image(menu_nt, bot, author_id)
            bot.sendLocalImage(
                temp_image_path, thread_id=thread_id, thread_type=thread_type,
                message=Message(text=menu_message), height=500, width=1280
            )
            os.remove(temp_image_path)
            return

def create_gradient_colors(num_colors: int) -> List[Tuple[int, int, int]]:
    return [(random.randint(80, 220), random.randint(80, 220), random.randint(80, 220)) 
            for _ in range(num_colors)]

def interpolate_colors(colors: List[Tuple[int, int, int]], text_length: int, change_every: int) -> List[Tuple[int, int, int]]:
    gradient = []
    num_segments = len(colors) - 1
    steps_per_segment = max((text_length // change_every) + 1, 1)

    for i in range(num_segments):
        for j in range(steps_per_segment):
            if len(gradient) < text_length:
                ratio = j / steps_per_segment
                interpolated_color = (
                    int(colors[i][0] * (1 - ratio) + colors[i + 1][0] * ratio),
                    int(colors[i][1] * (1 - ratio) + colors[i + 1][1] * ratio),
                    int(colors[i][2] * (1 - ratio) + colors[i + 1][2] * ratio)
                )
                gradient.append(interpolated_color)

    while len(gradient) < text_length:
        gradient.append(colors[-1])
    return gradient[:text_length]

def is_emoji(character: str) -> bool:
    return character in emoji.EMOJI_DATA

def draw_text_with_emoji(draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
                        font: ImageFont.FreeTypeFont, emoji_font: ImageFont.FreeTypeFont,
                        gradient_colors: List[Tuple[int, int, int]]) -> int:
    current_x = position[0]
    y = position[1]
    gradient = interpolate_colors(gradient_colors, len(text), 1)
    
    for i, char in enumerate(text):
        try:
            selected_font = emoji_font if is_emoji(char) else font
            font_size = selected_font.size
            offset_y = y - (font_size // 4) if is_emoji(char) else y
            
            draw.text((current_x, offset_y), char, 
                     fill=tuple(gradient[i]), 
                     font=selected_font)
            
            text_bbox = draw.textbbox((current_x, offset_y), char, font=selected_font)
            text_width = text_bbox[2] - text_bbox[0]
            current_x += text_width + (2 if is_emoji(char) else 0)
            
        except Exception as e:
            print(f"Loi khi ve ky tu '{char}': {e}")
            continue
    
    return current_x

def create_menu_nt_image(command_names, bot, author_id, nt_status=True):
    avatar_url = bot.fetchUserInfo(author_id).changed_profiles.get(author_id).avatar
    current_page_commands = list(command_names.items())
    numbered_commands = [f"{name}: {desc}" for name, desc in current_page_commands]
    menu_message = f"{get_user_name_by_id(bot, author_id)}\n" + "\n".join(numbered_commands)

    background_dir = "background"
    background_path = random.choice([os.path.join(background_dir, f) 
                                   for f in os.listdir(background_dir) 
                                   if f.endswith(('.png', '.jpg'))])
    image = Image.open(background_path).convert("RGBA").resize((1280, 500))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    rect_x0, rect_y0, rect_x1, rect_y1 = (1280 - 1100) // 2, (500 - 300) // 2, \
                                        (1280 - 1100) // 2 + 1100, (500 - 300) // 2 + 300
    draw.rounded_rectangle([rect_x0, rect_y0, rect_x1, rect_y1], radius=50, 
                         fill=(255, 255, 255, 200))

    if avatar_url:
        try:
            avatar_image = Image.open(BytesIO(requests.get(avatar_url).content)).convert("RGBA").resize((100, 100))
            gradient_size = 110
            gradient_colors = create_gradient_colors(7)
            gradient_overlay = Image.new("RGBA", (gradient_size, gradient_size), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient_overlay)
            
            for i, color in enumerate(gradient_colors):
                gradient_draw.ellipse((i, i, gradient_size - i, gradient_size - i), 
                                    outline=color, width=1)
            
            mask = Image.new("L", avatar_image.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 100, 100), fill=255)
            gradient_overlay.paste(avatar_image, (5, 5), mask)
            overlay.paste(gradient_overlay, (rect_x0 + 20, rect_y0 + 100), gradient_overlay)
        except Exception as e:
            print(f"Loi khi xu ly avatar: {e}")

    text_hi = f"Hi, {get_user_name_by_id(bot, author_id)}"
    text_welcome = f"🎊 Chao mung đen voi menu 🔠 game noi tu"
    text_nt_status = f"{bot.prefix}nt on/off: bat/tat tinh nang"
    text_bot_ready = f"♥️ bot san sang phuc vu"
    text_bot_info = f"🤖 Bot: {get_user_name_by_id(bot, bot.uid)} 💻 version 2.0 🗓️ update 08-01-24"

    font_path = "arial unicode ms.otf"
    emoji_font_path = "NotoEmoji-Bold.ttf"
    
    font_hi = ImageFont.truetype(font_path, size=50) if os.path.exists(font_path) else ImageFont.load_default()
    font_welcome = ImageFont.truetype(font_path, size=35) if os.path.exists(font_path) else ImageFont.load_default()
    font_nt = ImageFont.truetype(font_path, size=40) if os.path.exists(font_path) else ImageFont.load_default()
    emoji_font = ImageFont.truetype(emoji_font_path, size=35) if os.path.exists(emoji_font_path) else ImageFont.load_default()

    total_height = 300
    line_spacing = total_height // 5
    center_x = 1280 // 2

    y_pos = rect_y0 + 10
    draw_text_with_emoji(draw, text_hi, (center_x - 200, y_pos),
                        font_hi, emoji_font, create_gradient_colors(5))
    
    y_pos += line_spacing
    draw_text_with_emoji(draw, text_welcome, (center_x - 370, y_pos), 
                        font_welcome, emoji_font, create_gradient_colors(5))
    
    y_pos += line_spacing
    draw_text_with_emoji(draw, text_nt_status, (center_x - 250, y_pos), 
                        font_nt, emoji_font, create_gradient_colors(5))
    
    y_pos += line_spacing
    draw_text_with_emoji(draw, text_bot_ready, (center_x - 250, y_pos), 
                        font_welcome, emoji_font, create_gradient_colors(5))
    
    y_pos += line_spacing - 10
    draw_text_with_emoji(draw, text_bot_info, (center_x - 460, y_pos), 
                        font_welcome, emoji_font, create_gradient_colors(7))

    final_image = Image.alpha_composite(image, overlay)
    temp_image_path = "nt_menu.png"
    final_image.save(temp_image_path)
    
    return temp_image_path, menu_message

user_selection_data = {}
session = requests.Session()
BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "donghua.png")

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

        greeting_name = "Chủ Nhân" if str(author_id) == is_admin else user_name

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
            f"💞 Chào mừng đến vs menu 3d donghua 🐉",
            f"{bot.prefix}donghua on/off: 🚀 Bật/Tắt tính năng",
            "😁 Bot Sẵn Sàng Cống Hiến 🖤",
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

        right_icons = ["🐉", "🐳", "🐲"]
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

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception as e:
        return "Unknown User"
    
def tim_kiem_yanhh3d(bot, message_object, author_id, thread_id, thread_type, message_lower, message):
    try:
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            response = (
                f"{get_user_name_by_id(bot, author_id)}\n"
                f"{bot.prefix}donghua [tu khoa]: .\n"
                f"{bot.prefix}donghua bxh: .\n"
                f"💞 Vi du: {bot.prefix}donghua tu tutien  ✅\n"
            )
            os.makedirs(CACHE_PATH, exist_ok=True)
    
            image_path = generate_menu_image(bot, author_id, thread_id, thread_type)
            if not image_path:
                bot.sendMessage("❌ Khong the tao anh menu!", thread_id, thread_type)
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
            
            bot.sendReaction(message_object, random.choice(reaction), thread_id, thread_type)
            bot.sendLocalImage(
                imagePath=image_path,
                message=Message(text=response, mention=Mention(author_id, length=len(f"{get_user_name_by_id(bot, author_id)}"), offset=0)),
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
            return  # Them return đe tranh loi tiep tuc xu ly

        tu_khoa = parts[1].strip().lower()
        if tu_khoa == "bxh":
            send_bxh(bot, thread_id, thread_type, message_object, author_id)
            return

        url = "https://yanhh3d.vip/ajax/search/suggest"
        params = {"ajaxSearch": "1", "keysearch": tu_khoa}
        headers = {"User-Agent": "Mozilla/5.0"}
        response = session.get(url, params=params, headers=headers)
        data = response.json()
        html_data = data.get("data", "")
        soup = BeautifulSoup(html_data, "html.parser")
        items = soup.find_all("a")

        if not items:
            bot.replyMessage(
                Message(text="❌ Khong tim thay ket qua nao."),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )
            return

        danh_sach = []
        for a_tag in items:
            title = a_tag.get("title")
            ep_span = a_tag.find("span", class_="ep-search")
            so_tap = ep_span.get_text(strip=True) if ep_span else "Khong ro"
            url_phim = a_tag.get('href')
            img_tag = a_tag.find("img")
            avatar_url = img_tag.get("src") if img_tag else ""
            danh_sach.append((title, so_tap, url_phim, avatar_url)) 

        user_selection_data[author_id] = {
            "state": "waiting_for",
            "next_step": "handle_user_selection",
            "danh_sach": danh_sach
        }

        set_timeout(author_id, bot, message_object, thread_id, thread_type)

        danh_sach_text = "\n".join(
            [f"➜ {i}. {title} ({so_tap})" for i, (title, so_tap, _, _) in enumerate(danh_sach, 1)]
        )

        custom_message = (
            f"🚦{get_user_name_by_id(bot, author_id)}\n"
            f"🔎 Danh sách phim hoạt hình 3D '{tu_khoa}' tìm được\n"
            f"🧮 Tổng: {len(danh_sach)} phim\n"
            "🌀 Nguồn: yanhh3d.tv\n\n"
            f"{danh_sach_text}\n"
            "🎯 Nhập số tương ứng để chọn phim (30s)\n"
            "🚦 Nhập 0 để hủy"
        )

        anh_path = ve_anh_danh_sach(danh_sach, tu_khoa)
        bot.sendLocalImage(
            imagePath=anh_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=custom_message),
            height=440,
            width=1365,
            ttl=30000
        )
        os.remove(anh_path)

        if message == "0":
            bot.replyMessage(
                Message(text="❌ Ban đa huy lua chon."),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )
            user_selection_data.pop(author_id, None)  
            return

    except Exception as e:
        bot.replyMessage(
            Message(text=f"❌ Đa xay ra loi khi tim kiem: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
        )

def set_timeout(author_id, bot, message_object, thread_id, thread_type):
    def cancel_selection():
        if author_id in user_selection_data and user_selection_data[author_id]["state"] == "waiting_for":
            del user_selection_data[author_id]
            bot.replyMessage(
                Message(text="⏰ Het thoi gian phan hoi. Vui long thu lai tu đau."),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )
    timer = threading.Timer(30.0, cancel_selection)
    timer.start()


def ve_anh_danh_sach(danh_sach, tu_khoa):
    width = 1365
    item_height = 130
    padding = 20
    row_count = (len(danh_sach) + 1) // 2
    height = padding * 2 + row_count * item_height

    bg_path = random.choice([f for f in os.listdir("background") if f.endswith(('.jpg', '.png'))])
    bg_image = Image.open(f"background/" + bg_path).resize((width, height))
    img = ImageEnhance.Brightness(bg_image).enhance(0.3)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial unicode ms.otf", 36)
        font_item = ImageFont.truetype("arial unicode ms.otf", 28)
        font_small = ImageFont.truetype("arial unicode ms.otf", 24)
    except:
        font_title = font_item = font_small = ImageFont.load_default()

    def draw_circle_avatar(pos, avatar_url, size=90):
        try:
            response = requests.get(avatar_url)
            avatar = Image.open(BytesIO(response.content)).resize((size, size)).convert("RGBA")
        except:
            avatar = Image.new("RGBA", (size, size), (255, 255, 255, 255))

        mask = Image.new("L", (size, size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, size, size), fill=255)

        border = Image.new("RGBA", (size + 10, size + 10), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.ellipse((0, 0, size + 10, size + 10), fill=(255, 0, 255, 255))
        border.paste(avatar, (5, 5), mask=mask)
        img.paste(border, pos, mask=border)

    for i, (title, so_tap, url_phim, avatar_url) in enumerate(danh_sach):
        row = i // 2
        col = i % 2
        x = padding + col * (width // 2)
        y = padding + row * item_height

        draw.rounded_rectangle((x, y, x + width // 2 - padding, y + item_height - 10), radius=20, fill=(0, 0, 0, 100))
        draw_circle_avatar((x + 10, y + 10), avatar_url)
        draw.text((x + 110, y + 10), title, font=font_item, fill=(200, 150, 255))
        draw.text((x + 110, y + 50), so_tap, font=font_small, fill=(255, 255, 255))
        draw.text((x + 110, y + 80), "yanhh3d.vip", font=font_small, fill=(200, 200, 200))
        draw.text((x + width // 2 - 60, y + 10), str(i + 1), font=font_item, fill=(180, 180, 180))

    with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        img.save(tmp.name)
        return tmp.name


def handle_user_selection(bot, message_object, author_id, thread_id, thread_type, message):
    try:
        user_data = user_selection_data.get(author_id)
        if not user_data or user_data.get("next_step") != "handle_user_selection":
            return

        danh_sach = user_data.get('danh_sach', [])

        if message.strip() == "0":
            bot.replyMessage(
                Message(text="❌ Ban đa huy lua chon."),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )
            user_selection_data.pop(author_id, None)
            return

        if not message.isdigit():
            bot.replyMessage(
                Message(text="❌ Vui long nhap so hop le tuong ung voi phim."),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )
            return

        chon = int(message)
        if chon < 1 or chon > len(danh_sach):
            bot.replyMessage(
                Message(text="❌ Lua chon khong hop le. Vui long nhap so trong danh sach."),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )
            return

        lua_chon = danh_sach[chon - 1]
        ten_phim, tap, url_phim = lua_chon[:3]

        user_selection_data[author_id] = {
            "state": "waiting_for",
            "next_step": "handle_episode_selection",
            "url_phim": url_phim,
            "ten_phim": ten_phim,
            "tap": tap
        }

        set_timeout(author_id, bot, message_object, thread_id, thread_type)

        bot.replyMessage(
            Message(text=f"🍿 Ban đa chon: {ten_phim}\n🔖 Danh sach tap: [{tap}]\n\nVui long nhap so tap ban muon xem.\n🚦 Nhap 0 đe huy chon"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=30000
        )

    except Exception as e:
        bot.replyMessage(
            Message(text=f"❌ Đa xay ra loi: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
        )
 
        

def handle_episode_selection(bot, message_object, author_id, thread_id, thread_type, message):
  
    try:
        user_data = user_selection_data.get(author_id)
        if message == "0":
            bot.replyMessage(
                Message(text="❌ Ban đa huy lua chon."),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )
            user_selection_data.pop(author_id, None) 
            return
       
        # bot.replyMessage(
        #         Message(text=f"Chay toi buoc chon tap phim"),
        #         message_object, thread_id=thread_id, thread_type=thread_type
        # )
        try:
            chon_tap = int(message)
      
            url_phim = user_data["url_phim"]
            ten_phim = user_data["ten_phim"]
            tap= user_data["tap"]
            max_tap = 27
            if chon_tap > max_tap and chon_tap < 1:
                bot.replyMessage(
                    Message(text=f"❌ Tap phim khong hop le. Vui long chon lai tu 1 đen {max_tap}."), message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000)
                return
            url_tap = f"{url_phim.strip('/')}/tap-{chon_tap}"

            bot.replyMessage(
                Message(text=f"🍿 Ban đa chon tap {chon_tap} cua phim '{ten_phim}'.\n🎥 URL: {url_tap}"),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
            )

            
            get_fb_source(bot, url_tap, message_object, thread_id, thread_type)
            user_selection_data.pop(author_id, None)
        except ValueError:
           pass
    except Exception as e:
        bot.replyMessage(
            Message(text=f"❌ Đa xay ra loi: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
        )



def get_fb_source(bot, url_tap, message_object, thread_id, thread_type):
    try:
        response = session.get(url_tap)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        
        og_image = soup.find("meta", property="og:image")
        thumbnail_url = og_image["content"] if og_image else "https://default-thumbnail-url.com/thumbnail.jpg"
        
        scripts = soup.find_all('script')

        for script in scripts:
            script_content = script.string
            if not script_content:
                continue

            checklink_matches = re.findall(r'\$checkLink\d+\s*=\s*"([^"]+)"', script_content)
            for link in checklink_matches:
                if "yanhh3d" in link:
                    process_yanhh3d(bot, link, message_object, thread_id, thread_type, thumbnail_url)
                    return

        bot.replyMessage(
            Message(text="❌ loi roi."),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
        )

    except Exception as e:
        bot.replyMessage(
            Message(text=f"❌ Loi khi xu ly: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
        )

def process_yanhh3d(bot, url, message_object, thread_id, thread_type, thumbnail_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        match = re.search(r'var cccc = "(https://[^"]+\.mp4[^"]*)"', response.text)
        if match:
            video_url = match.group(1)
            download_video(bot, video_url, thumbnail_url, message_object, thread_id, thread_type)
        else:
            pass
    except Exception as e:
        bot.replyMessage(
            Message(text=f"❌ Loi khi truy cap link: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
        )

def download_video(bot, video_url, thumbnail_url, message_object, thread_id, thread_type):
    try:
        duration = 100
        final_duration = 600 if duration > 600 else duration

        bot.sendRemoteVideo(
            videoUrl=video_url,
            thumbnailUrl=thumbnail_url,  
            duration=final_duration,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1280,
            height=720,
            message=Message(text=""),
            ttl=1000000
        )

    except Exception as e:
        bot.replyMessage(
            Message(text=f"❌ Loi khi gui video: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=100000
        )




def upload_to_uguuu(file_path):
    try:
        print(f"➜   Đang upload file len GoFile: {file_path}")
        
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post("https://store1.gofile.io/uploadFile", files=files)

        print(f"➜   Phan hoi tu GoFile: {response.text}")
        result = response.json()
        
        if result["status"] == "ok":
            uploaded_url = result["data"]["downloadPage"]
            print(f"➜   Upload thanh cong: {uploaded_url}")
            return uploaded_url
        else:
            print("➜   Upload that bai:", result.get("message"))
            return None

    except Exception as e:
        print(f"➜   Loi khi upload file len GoFile: {e}")
        return None



def ve_anh_bxh(items):
    width = 1365
    item_height = 130
    padding = 20
    row_count = (len(items) + 1) // 2
    height = padding * 2 + row_count * item_height

    bg_path = random.choice([f for f in os.listdir("background") if f.endswith(('.jpg', '.png'))])
    bg_image = Image.open(f"background/{bg_path}").resize((width, height))
    img = ImageEnhance.Brightness(bg_image).enhance(0.3)
    draw = ImageDraw.Draw(img)

    try:
        font_item = ImageFont.truetype("arial unicode ms.otf", 28)
        font_small = ImageFont.truetype("arial unicode ms.otf", 24)
    except:
        font_item = font_small = ImageFont.load_default()

    for i, item in enumerate(items):
        rank = item['rank']
        name = item['name']
        episode = item['episode']
        avatar_url = item['avatar_url']

        row = i // 2
        col = i % 2
        x = padding + col * (width // 2)
        y = padding + row * item_height

        draw.rounded_rectangle((x, y, x + width // 2 - padding, y + item_height - 10), radius=20, fill=(0, 0, 0, 100))

        try:
            response = requests.get(avatar_url)
            avatar = Image.open(BytesIO(response.content)).resize((90, 90)).convert("RGBA")
        except:
            avatar = Image.new("RGBA", (90, 90), (255, 255, 255, 255))

        mask = Image.new("L", (90, 90), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 90, 90), fill=255)

        border = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.ellipse((0, 0, 100, 100), fill=(255, 0, 255, 255))
        border.paste(avatar, (5, 5), mask=mask)

        img.paste(border, (x + 10, y + 10), mask=border)
        draw.text((x + 110, y + 10), f"{rank}. {name}", font=font_item, fill=(200, 150, 255))
        draw.text((x + 110, y + 50), episode, font=font_small, fill=(255, 255, 255))
        draw.text((x + width // 2 - 60, y + 10), str(rank), font=font_item, fill=(180, 180, 180))

    with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        img.save(tmp.name)
        return tmp.name

def send_bxh(bot, thread_id, thread_type, message_object, author_id):
    try:
        url = "https://yanhh3d.vip/moi-cap-nhat"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        ranking_section = soup.select_one("#top-viewed-day")
        items = ranking_section.select("li.item-top") if ranking_section else []
        if not items:
            bot.replyMessage(
                Message(text="❌ Khong tim thay BXH nao."),
                message_object, thread_id=thread_id, thread_type=thread_type
            )
            return

        bxh_list = []
        for item in items:
            rank = item.select_one(".film-number span").text.strip() if item.select_one(".film-number span") else ""
            name = item.select_one(".film-name a").text.strip() if item.select_one(".film-name a") else ""
            episode = item.select_one(".fd-infor span").text.strip() if item.select_one(".fd-infor span") else ""
            link = item.select_one(".film-name a")["href"] if item.select_one(".film-name a") else ""
            img_tag = item.select_one("img")
            avatar_url = img_tag["data-src"] if img_tag and img_tag.has_attr("data-src") else img_tag["src"] if img_tag and img_tag.has_attr("src") else ""
            
            bxh_list.append({
                'rank': rank,
                'name': name,
                'episode': episode,
                'link': link,
                'avatar_url': avatar_url
            })

        user_name = get_user_name_by_id(bot, author_id)
        text_bxh = f"🚦{user_name}\n🚦Top {len(bxh_list)} bang xep hang phim hoat hinh 3D cap nhat moi nhat\n📅 Vao luc: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n🌀Nguon: yanhh3d.vip\n\n"

        for item in bxh_list:
            text_bxh += f"{item['rank']}. {item['name']} ({item['episode']})\n🔗 {item['link']}\n"

        image_path = ve_anh_bxh(bxh_list[:10])
        bot.sendLocalImage(
            imagePath=image_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=text_bxh),
            height=440,
            width=1365,
            ttl=1200000
        )
        os.remove(image_path)

    except Exception as e:
        bot.replyMessage(
            Message(text=f"❌ Loi khi lay BXH: {str(e)}"),
            message_object, thread_id=thread_id, thread_type=thread_type
        )

init(autoreset=True)
colors = [
    "FF9900", "FFFF33", "33FFFF", "FF99FF", "FF3366", 
    "FFFF66", "FF00FF", "66FF99", "00CCFF", "FF0099", 
    "FF0066", "0033FF", "FF9999", "00FF66", "00FFFF", 
    "CCFFFF", "8F00FF", "FF00CC", "FF0000", "FF1100", 
    "FF3300"
]

def hex_to_ansi(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'\033[38;2;{r};{g};{b}m'

text = "Cmeii Cte"
xb = pyfiglet.figlet_format(text)
print(xb)

class bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None, prefix='', is_main_bot=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.is_main_bot = is_main_bot
        self.prefix = prefix
        self.imei = imei
        self.session_cookies = session_cookies
        self.secret_key = secret_key
        self.api_key = api_key
        self.group_info_cache = {}
        self.last_sms_times = {}
        handle_bot_admin(self)
        self.Group = False
        self.is_spamming = False
        self.spam_thread = None
        self.spam_lock = threading.Lock()
        self.spam_content = ""
        self.link_removal_enabled = False
        self.banned_word_removal_enabled = False
        self.message_queue = Queue()
        self.worker_thread = threading.Thread
        self.users = {}
        self.promotion_active = False
        self.promotion_discount = 0.5
        self.current_color = "#BBDF32"
        self.current_size = "15"
        self.hidden_accounts = set()
        self.hidden_notifications = {}
        self.data_file = {}
        self.list_group = []
        self.loan_allowed = {}
        self.previous_members = {}
        self.latest_member = {}
        self.last_check_time = {}
        self.pending_login_requests = {}
        self.message_counts = {}
        self.command_usage_count = {}
        self.used_codes = {}
        self.allowed_groups = set()
        self.stop_event = threading.Event()
        self.version ="2.1"
        self.date_update ='13-07-25'
        self.me_name = self.fetchAccountInfo().profile.displayName
        self.group_info_cache = {}
        all_group = self.fetchAllGroups()
        allowed_thread_ids = list(all_group.gridVerMap.keys())
        initialize_group_info(self, allowed_thread_ids)
        start_member_check_thread(self,allowed_thread_ids)

    def onEvent(self, event_data, event_type):
        try:
            handle_event(self, event_data, event_type)
        except Exception as e:
            logger.error(f"🚦 Loi khi xu ly su kien: {e}")

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            settings = read_settings(self.uid)
            allowed_thread_ids = settings.get('allowed_thread_ids', [])
            admin_bot = settings.get("admin_bot", [])
            banned_users = settings.get("banned_users", [])
            chat_user = (thread_type == ThreadType.USER)
            is_main_bot = self.is_main_bot
            prefix = self.prefix
            allowed_thread_ids = get_allowed_thread_ids(self)

            if author_id in banned_users:
                return

            if not (author_id in admin_bot or thread_id in allowed_thread_ids or chat_user):
                return

            if thread_id in allowed_thread_ids and thread_type == ThreadType.GROUP and not is_admin(self, author_id):
                handle_check_profanity(self, author_id, thread_id, message_object, thread_type, message)
                
            message_text = message.text if isinstance(message, Message) else str(message)
            message_lower = message_text.lower()
            author_info = self.fetchUserInfo(author_id).changed_profiles.get(author_id, {})
            author_name = author_info.get('zaloName', 'đeo xac đinh')
            group_info = self.fetchGroupInfo(thread_id)
            group_name = group_info.gridInfoMap.get(thread_id, {}).get('name', 'N/A')
            current_time = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime())
            colors_selected = random.sample(colors, 8)
            print(f"{hex_to_ansi(colors_selected[1])}{Style.BRIGHT}│- Message: {message_text}{Style.RESET_ALL}")
            print(f"{hex_to_ansi(colors_selected[2])}{Style.BRIGHT}│- ID NGUOI DUNG: {author_id}{Style.RESET_ALL}")
            print(f"{hex_to_ansi(colors_selected[6])}{Style.BRIGHT}│- TEN NGUOI DUNG: {author_name}{Style.RESET_ALL}")
            print(f"{hex_to_ansi(colors_selected[3])}{Style.BRIGHT}│- ID NHOM: {thread_id}{Style.RESET_ALL}")
            print(f"{hex_to_ansi(colors_selected[4])}{Style.BRIGHT}│- TEN NHOM: {group_name}{Style.RESET_ALL}")
            print(f"{hex_to_ansi(colors_selected[5])}{Style.BRIGHT}│- TYPE: {thread_type}{Style.RESET_ALL}")
            print(f"{hex_to_ansi(colors_selected[7])}{Style.BRIGHT}│- THOI GIAN NHAN ĐUOC: {current_time}{Style.RESET_ALL}")
            if message_text.startswith(f"{prefix}nt go"):
                nt_go(self, message_object, author_id, thread_id, thread_type, message_text[len(f"{prefix}nt go"):].strip())
            elif message_text.startswith(f"{prefix}nt"):
                nt_go(self, message_object, author_id, thread_id, thread_type, message_text)
            elif current_word is not None: 
                nt_go(self, message_object, author_id, thread_id, thread_type, message_lower)

            elif message_lower.startswith(f"{prefix}sms"):
                handle_sms_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}stkxp"):
                handle_stkxp_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}group"):
                handle_group_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}qrbank"):
                handle_qrbank_command(message, message_object, thread_id, thread_type, author_id, self)
            # elif message_lower.startswith(f"{prefix}save"):
            #     handle_save_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}ff"):
                handle_ff_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}spamff"):
                handle_spamff_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}attack"):
                handle_attack_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}reghotmail"):
                handle_reghotmail_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}doff"):
                handle_doff_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}news"):
                news(self, message_object, author_id, thread_id, thread_type, message)
           
            elif message_lower.startswith(f"{prefix}call"):
                handle_spamcall_command(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}tygia"):
                handle_hoan_doi_command(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}giavang"):
                handle_gia_vang_command(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}mybot") and is_main_bot:
                handle_thuebot_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}war"):
                handle_allwar_command(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}share"):
                handle_share_command(self, message, message_object, thread_id, author_id, thread_type)
            elif message_lower.startswith(f"{prefix}scl"):
                handle_nhac_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}make"):
                handle_make_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}getvoice"):
                handle_getvoice_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}chat"):
                handle_chat_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}ngl"):
                handle_ngl_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}bot"):
                handle_bot_command(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}st"):
                handle_create_image_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}girl"):
                handle_anhgai_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}vdgirl"):
                handle_vdgai_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}menu"):
                handle_menu_commands(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}or"):
                handle_menu_or_commands(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}weather"):
                handle_weather_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}bc"):
                handle_dhbc_command(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}dich"):
                handle_translate_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}tx"):
                handle_tx_command(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}leave"):
                handle_leave_group_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}love"):
                handle_tha_thinh_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}ngl"):
                handle_ngl_thinh_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}autosend"):
                handle_autosend_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}zl"):
                handle_menu_zl_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}hiden"):
                handle_hiden_commands(message, thread_id, thread_type, author_id, self, message_object)
            elif message_lower.startswith(f"{prefix}disbox"):
                handle_disbox(self, thread_id, author_id, thread_type, message_object)
            elif message_lower.startswith(f"{prefix}spam"):
                handle_join_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}join"):
                handle_join1_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}kickall"):
                kick_member_group(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}meme"):
                meme(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}src"):
                src(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}pin"):
                handle_pro_pin(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}phatnguoi"):
                phatnguoi(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}mst"):
                mst(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}getlink"):
                handle_getlink_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}blockfri"):
                blockto(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}unlockfri"):
                unblockto(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}addfri"):
                addfrito(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}rmfri"):
                removefrito(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}addallfri"):
                addallfriongr(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}pix"):
                pixitimkiem(self, message_object, author_id, thread_id, thread_type, message)
            elif message_lower.startswith(f"{prefix}lmao"):
                command_allan_for_link(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}all"):
                command__allan_cd(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}sk"):
                handle_stk_command(message, message_object, thread_id, thread_type, author_id, self)
            elif message_lower.startswith(f"{prefix}donghua"):
                tim_kiem_yanhh3d(self, message_object, author_id, thread_id, thread_type, message_lower, message)
            elif author_id in user_selection_data and message.strip().isdigit() and user_selection_data.get(author_id)['next_step'] == "handle_user_selection":
                handle_user_selection(self, message_object, author_id, thread_id, thread_type, message)
            elif author_id in user_selection_data and message.strip().isdigit() and user_selection_data.get(author_id)['next_step'] == "handle_episode_selection":
                handle_episode_selection(self, message_object, author_id, thread_id, thread_type, message)
            auto_stk(self, message_object, author_id, thread_id, thread_type)
        except Exception as e:
            print(f"[MAIN]Loi trong main: {e}")
      
CONFIG_FILE = "config.json"
lock = threading.Lock()

def save_json(filename: str, data: Dict) -> None:
    """Ghi du lieu vao file JSON voi xu ly loi"""
    with lock:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Loi khi luu du lieu vao {filename}: {e}")
            raise

def load_json(filename: str) -> Dict:
    """Đoc du lieu tu file JSON voi xu ly loi"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"Khong tim thay tep {filename}. Tao du lieu mac đinh")
        default_data = {"data": []}
        save_json(filename, default_data)
        return default_data
    except json.JSONDecodeError:
        logging.error(f"Khong the giai ma JSON tu {filename}")
        default_data = {"data": []}
        save_json(filename, default_data)
        return default_data
    except Exception as e:
        logging.error(f"Loi khong xac đinh khi đoc {filename}: {e}")
        return {"data": []}

def save_username_to_config(username: str, author_id: str) -> None:
    try:
        with lock:
            data = load_json(CONFIG_FILE)
            
            if "data" not in data:
                data["data"] = []
                
            existing_user = next((user for user in data["data"] if user.get('username') == username), None)
            if not existing_user:
                data["data"].append({
                    "username": username,
                    "author_id": author_id,
                    "status": True
                })
                save_json(CONFIG_FILE, data)
                logging.info(f"Đa luu {username} vao config")
    except Exception as e:
        logging.error(f"Loi khi luu username va author_id vao config.json: {e}")

def run_bot(
    imei: str,
    session_cookies: Dict,
    prefix: str,
    is_main_bot: bool,
    username: Optional[str] = None,
    author_id: Optional[str] = None,
    status: Optional[bool] = None
) -> None:
    try:
        if status is False:
            logging.info(f"Bot {username} bi vo hieu hoa (status: {status})")
            return

        if not isinstance(session_cookies, dict) or not session_cookies:
            logging.error(f"Cookie phien khong hop le cho {username}")
            return

        prefix = prefix if prefix else "None"
        
        client = bot('</>', '</>', imei=imei, session_cookies=session_cookies, 
                    prefix=prefix, is_main_bot=is_main_bot)

        if username and author_id:
            save_username_to_config(username, author_id)

        bot_type = "chinh" if is_main_bot else "phu"
        logging.info(f"Khoi đong bot {bot_type} - Ten: {username}, prefix: {prefix}")
        
        client.listen(run_forever=True, delay=0, thread=True)

    except Exception as e:
        logging.error(f"Loi khi chay bot {username}: {e}")

def start_threads(data: List[Dict]) -> None:
    threads = []

    for item in data:
        try:
            imei = item.get("imei", "Unknown_IMEI")
            session_cookies = item.get("session_cookies", {})
            prefix = item.get("prefix", "")
            is_main_bot = item.get("is_main_bot", False)
            username = item.get("username")
            author_id = item.get("author_id")
            status = item.get("status", True)

            if not username or not author_id:
                logging.warning(f"Thieu username hoac author_id trong config: {item}")
                continue

            thread = threading.Thread(
                target=run_bot,
                args=(imei, session_cookies, prefix, is_main_bot, username, author_id, status)
            )
            threads.append(thread)
            thread.start()

        except Exception as e:
            logging.error(f"Loi khi tao thread cho bot {username}: {e}")

    for thread in threads:
        try:
            thread.join()
        except Exception as e:
            logging.error(f"Loi khi join thread: {e}")

def main():
    """Ham chinh đe chay chuong trinh"""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        data = load_json(CONFIG_FILE)
        
        if "data" not in data:
            logging.error("Khong tim thay truong 'data' trong JSON")
            return
            
        if not data["data"]:
            logging.warning("Khong co du lieu bot nao trong config")
            return
            
        start_threads(data["data"])
        
    except Exception as e:
        logging.error(f"Loi trong qua trinh khoi đong: {e}")

if __name__ == "__main__":
    main()