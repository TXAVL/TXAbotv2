import colorsys
from datetime import datetime
import glob
from io import BytesIO
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pytz
import requests
from core.bot_sys import get_user_name_by_id, is_admin, read_settings, write_settings
from zlapi.models import *

BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "or.png")

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
            f"💞 Chao mung đen menu Share Code 💌",
            f"{bot.prefix}share on/off: 🚀 Bat/Tat tinh nang",
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

        right_icons = ["💌", "📩", "📬", "📮", "📦", "📫", "📭"]
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

def handle_share_on(bot, thread_id):
    settings = read_settings(bot.uid)
    if "share" not in settings:
        settings["share"] = {}
    settings["share"][thread_id] = True
    write_settings(bot.uid, settings)
    return f"🚦Lenh {bot.prefix}share đa đuoc Bat 🚀 trong nhom nay ✅"

def handle_share_off(bot, thread_id):
    settings = read_settings(bot.uid)
    if "share" in settings and thread_id in settings["share"]:
        settings["share"][thread_id] = False
        write_settings(bot.uid, settings)
        return f"🚦Lenh {bot.prefix}share đa Tat ⭕️ trong nhom nay ✅"
    return "🚦Nhom chua co thong tin cau hinh share đe ⭕️ Tat 🤗"

def handle_share_command(self, message, message_object, thread_id, author_id, thread_type):

    settings = read_settings(self.uid)
    
    user_message = message.replace(f"{self.prefix}share ", "").strip().lower()
    if user_message == "on":
        if not is_admin(self, author_id):  
            response = "❌Ban khong phai admin bot!"
        else:
            response = handle_share_on(self, thread_id)
        self.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object, ttl=10000)
        return
    elif user_message == "off":
        if not is_admin(self, author_id):  
            response = "❌Ban khong phai admin bot!"
        else:
            response = handle_share_off(self, thread_id)
        self.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object, ttl=10000)
        return
    
    if not (settings.get("share", {}).get(thread_id, False)):
        return

    bot_name = get_user_name_by_id(self, self.uid)
    time_update = "12-07-25"

    contents = {
        'art': {
            'url': "https://link4m.com/zynR1ry0",
            'author': bot_name,
            'update_date': time_update,
            'features': "Ve text art 3 chu cai khong dau",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Dung lenh !art [xxx] [emoji] Vi du: !art tot 🍉"
            ]
        },
        'bot_info': {
            'url': "https://link4m.com/E6bYAj",
            'author': bot_name,
            'update_date': time_update,
            'features': "Quan ly nhom\n📎 Đinh kem: Su dung kem voi file setting.json\n🔗 File setting.json: https://link4m.com/jinRErv",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Dung lenh !bot on vao nhom muon Bat bot",
                "3 [Buoc 3] Dung lenh !bot setup on đe cau hinh noi quy nhom",
                "4 [Buoc 4] Dung lenh !bot noiquy đe ap noi quy cho nhom"
            ]
        },
        'chui_khanh_tai': {
            'url': "https://link4m.com/vIrILZA",
            'author': bot_name,
            'update_date': time_update,
            'features': "Tao 2 luong gui tin nhan chui Khanh va Tai No cam 2 Bot tele đe lay cap thong tin anh em. Dung api tele no chui nguoc lai no",
            'notes': [
                "1 [Buoc 1] Mo file va run chi the thoi"
            ]
        },
        'kickall': {
            'url': "https://link4m.com/IvWCPjQf",
            'author': bot_name,
            'update_date': time_update,
            'features': "Kick all member, suy nghi sang suot truoc khi su dung nhe",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Dung lenh !kickall Pha kick toan bo member. Đieu kien la phai cam key vang hoac bac"
            ]
        },
        'reaction': {
            'url': "https://link4m.com/9ZqSAyMf",
            'author': bot_name,
            'update_date': time_update,
            'features': "Tha cam xuc all tin nhan",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Run"
            ]
        },
        'var': {
            'url': "https://link4m.com/6UslPHh",
            'author': bot_name,
            'update_date': time_update,
            'features': "Tinh nang đi var",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Co 3 lenh var, stop va kickall"
            ]
        },
        'color': {
            'url': "https://link4m.com/NOuwq",
            'author': bot_name,
            'update_date': time_update,
            'features': "Tao Color chu mau Gradient (chi 77 ky tu gioi han cua Zalo, vuot qua 77 ky tu goi thuong khong đoi mau)",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie. Tim dong imei va session_cookies lan luot thay bang imei va cookie cua minh",
                "2 [Buoc 2] Dung lenh /color Noi dung đoi mau"
            ]
        },
        'fake_hack': {
            'url': "https://link4m.com/SNoB7",
            'author': bot_name,
            'update_date': time_update,
            'features': "Fake hack by A Sin. Đoi ten, avtar, chan toan bo danh sach ban! ⚠️ Canh bao: Tuyet đoi khong su dung đoi voi nguoi thieu hieu biet",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Run file la lum"
            ]
        },
        'group': {
            'url': "https://link4m.com/ong2UsCV",
            'author': bot_name,
            'update_date': time_update,
            'features': "Xem thong tin nhom",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie. Tim dong imei va session_cookies lan luot thay bang imei va cookie cua minh",
                "2 [Buoc 2] Dung lenh /gr"
            ]
        },
        'info': {
            'url': "https://link4m.com/9ZqSAyMf",
            'author': bot_name,
            'update_date': time_update,
            'features': "Tha cam xuc all tin nhan",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Run"
            ]
        },
        'infoadv3': {
            'url': "https://link4m.com/XULfcD",
            'author': bot_name,
            'update_date': time_update,
            'features': "Thong tin tac gia\n🔗 Link folder:https://link4m.com/reAlLD",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Thuc muc anime đe ngang hang voi file infoad.py. Sau đo copy cac anh yeu thich vao thu muc anime"
                "3 [Buoc 2] Chay lenh !infoad"
            ]
        },
        'nhai_theo': {
            'url': "https://link4m.com/9W7ql",
            'author': bot_name,
            'update_date': time_update,
            'features': "Nhai theo tin nhan text cua nguoi khac",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Dung lenh !nhai on đe bat, !nhai off đe tat"
            ]
        },
        'voice': {
            'url': "https://link4m.com/qC4roZ7a",
            'author': bot_name,
            'update_date': time_update,
            'features': "Chuyen Text sang Voice",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Cai thu vien pip install gtts"
                "3 [Buoc 3] Run va dung lenh !vi"
            ]
        },
        'welcome': {
            'url': "https://link4m.com/aQAQ6qsi",
            'author': bot_name,
            'update_date': time_update,
            'features': "Chao mung thanh vien ra vao nhom",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Chon nhom can bat welcome. Go lenh !wl on đe bat che đo welcome. Tat bang lenh !wl off"
            ]
        },
        'welcome2': {
            'url': "https://link4m.com/f6to3r",
            'author': bot_name,
            'update_date': time_update,
            'features': "Chao mung thanh vien ra vao nhom V2\n🔗 Link Font va toan bo file: https://link4m.com/KAKasDdS",
            'notes': [
                "1 [Buoc 1] Thay imei va cookie",
                "2 [Buoc 2] Cai thu vien pip install pillow, pip install emoji Run file chinh welcome2.py Thu muc Font, file va welcome2.py đat ngang hang nhau"
                "3 [Buoc 3] Chon nhom can bat welcome. Go lenh !wl on đe bat che đo welcome. Tat bang lenh !wl off"
            ]
        }
        
    }

    content_parts = message.strip().split(" ", 1)
    if len(content_parts) < 2:
        error_message = {
            f"🚦Tong hop code đuoc share\n":
            f"➜ art\n"
            f"➜ bot_info\n"
            f"➜ chui_khanh_tai\n"
            f"➜ color\n"
            f"➜ fake_hack\n"
            f"➜ group\n"
            f"➜ info\n"
            f"➜ infoadv3\n"
            f"➜ kickall\n"
            f"➜ nhai_theo\n"
            f"➜ reaction\n"
            f"➜ var\n"
            f"➜ voice\n"
            f"➜ welcome\n"
            f"➜ welcome2\n"
            f"🚦 Vi du {self.prefix}share info ✅"
                        }
        os.makedirs(CACHE_PATH, exist_ok=True)
    
        image_path = generate_menu_image(self, author_id, thread_id, thread_type)
        if not image_path:
            self.sendMessage("❌ Khong the tao anh menu!", thread_id, thread_type)
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
        
        self.sendReaction(message_object, random.choice(reaction), thread_id, thread_type)
        self.sendLocalImage(
            imagePath=image_path,
            message=Message(text=error_message, mention=Mention(author_id, length=len(f"{get_user_name_by_id(self, author_id)}"), offset=0)),
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

    name = content_parts[1].strip()

    share_info = contents.get(name)
    commands = f"{self.prefix}share"

    if not share_info:
        error_message = Message(text=f"Lenh [{commands} {name}] khong đuoc ho tro 🤧.")
        self.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    notes_formatted = "\n".join([f"   {i+1} {note}" for i, note in enumerate(share_info['notes'])])

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    share_message = Message(
        text=(
            f"🚦Chi tiet Code {name}\n"
            f"👨‍💻 Tac gia: {share_info['author']}\n"
            f"🔄 Cap nhat: {share_info['update_date']}\n"
            f"🚀 Tinh nang: {share_info['features']}\n"
            f"📌 Luu y:\n"
            f"{notes_formatted}\n"
            f"🚦 Link code share: {share_info['url']}\n"
        )
    )

    self.replyMessage(share_message, message_object, thread_id, thread_type)