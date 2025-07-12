import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import requests
from datetime import datetime
from urllib.parse import quote_plus

# --- THEM DONG NAY ĐE IMPORT MESSAGE TU ZLAPI ---

from zlapi.models import Message, ThreadType

# --------------------------------------------------

def fetch_image(url, size=None):
    """
    Tai anh tu URL, co the thay đoi kich thuoc.
    """
    if not url:
        return None
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        if size:
            # Su dung Image.LANCZOS thay vi Image.ANTIALIAS (đa bi deprecated)
            img = img.resize(size, Image.LANCZOS)
        return img
    except requests.exceptions.RequestException as e:
        print(f"Loi khi tai anh tu URL ({url}): {e}")
        return None
    except Exception as e:
        print(f"Loi khong xac đinh khi tai anh: {e}")
        return None

def make_circle_avatar(img, size):
    """
    Cat anh thanh hinh tron va resize.
    """
    img = img.convert("RGBA").resize(size, Image.LANCZOS)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    output = ImageOps.fit(img, size, centering=(0.5, 0.5))
    output.putalpha(mask)
    return output

def create_qrbank_image(avatar_url, qr_url, author_name, bank_name, account_number, amount, add_info):
    """
    Tao anh QR Bank gom avatar, ten tac gia, ma QR, va thong tin chuyen khoan.
    """
    W, H = 800, 1400  # Tang chieu cao anh đe chua them thong tin
    bg_color = (240, 248, 255)  # Mau nen nhat, trang nha (AliceBlue)
    header_color = (65, 105, 225) # Mau xanh manh hon (RoyalBlue)
    name_color = (30, 144, 255)  # Mau xanh noi bat cho ten (DodgerBlue)
    detail_color = (70, 70, 70) # Mau xam đam cho chi tiet
    time_color = (120, 120, 120) # Mau xam cho thoi gian

    im = Image.new("RGBA", (W, H), bg_color)
    draw = ImageDraw.Draw(im)

    # Thu tai font, neu khong co thi dung default
    try:
        font_path = "arial.ttf" # Gia đinh font arial nam cung thu muc hoac co san tren he thong
        font_bold_path = "arialbd.ttf" # Font Arial Bold

        font_bold = ImageFont.truetype(font_bold_path, 60)
        font_regular = ImageFont.truetype(font_path, 38)
        font_detail_bold = ImageFont.truetype(font_bold_path, 36) # Font rieng cho chi tiet
        font_small = ImageFont.truetype(font_path, 30)
    except IOError:
        print("Khong tim thay font Arial/Arial Bold, dung font mac đinh.")
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_detail_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Header
    header_text = "THANH TOAN QR"
    bbox_header = draw.textbbox((0, 0), header_text, font=font_bold)
    w, h = bbox_header[2] - bbox_header[0], bbox_header[3] - bbox_header[1]
    draw.text(((W - w) // 2, 40), header_text, font=font_bold, fill=header_color)
    line_y = 40 + h + 15
    draw.line([(W * 0.2, line_y), (W * 0.8, line_y)], fill=header_color, width=5)

    # Avatar
    avatar_size = (200, 200)
    avatar_pos = ((W - avatar_size[0]) // 2, line_y + 40)
    avatar_img = fetch_image(avatar_url, size=avatar_size)
    if avatar_img:
        avatar_circ = make_circle_avatar(avatar_img, avatar_size)
        # Tao bong nhe duoi avatar
        shadow_offset = 10
        shadow_blur = 15
        shadow_color = (0, 0, 0, 120)
        shadow_mask = Image.new("L", (avatar_size[0] + shadow_offset*2, avatar_size[1] + shadow_offset*2), 0)
        draw_shadow_mask = ImageDraw.Draw(shadow_mask)
        draw_shadow_mask.ellipse((shadow_offset, shadow_offset, avatar_size[0] + shadow_offset, avatar_size[1] + shadow_offset), fill=255)
        shadow = Image.new("RGBA", (avatar_size[0] + shadow_offset*2, avatar_size[1] + shadow_offset*2), shadow_color)
        shadow.putalpha(shadow_mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        im.paste(shadow, (avatar_pos[0] - shadow_offset, avatar_pos[1] - shadow_offset), shadow)
        im.paste(avatar_circ, avatar_pos, avatar_circ)
    else:
        draw.ellipse([avatar_pos, (avatar_pos[0] + avatar_size[0], avatar_pos[1] + avatar_size[1])], fill=(200, 200, 200))

    # Ten tac gia
    name_pos_y = avatar_pos[1] + avatar_size[1] + 25
    bbox_name = draw.textbbox((0, 0), author_name, font=font_regular)
    w_name = bbox_name[2] - bbox_name[0]
    draw.text(((W - w_name) // 2, name_pos_y), author_name, font=font_regular, fill=name_color)

    # Thong tin chuyen khoan (TREN QR)
    detail_start_y = name_pos_y + 80

    # Bank Name
    bank_info_text = f"Ngan hang: {bank_name.upper()}"
    bbox_bank = draw.textbbox((0, 0), bank_info_text, font=font_detail_bold)
    w_bank = bbox_bank[2] - bbox_bank[0]
    draw.text(((W - w_bank) // 2, detail_start_y), bank_info_text, font=font_detail_bold, fill=detail_color)
    detail_start_y += 50

    # Account Number
    account_info_text = f"So tai khoan: {account_number}"
    bbox_account = draw.textbbox((0, 0), account_info_text, font=font_detail_bold)
    w_account = bbox_account[2] - bbox_account[0]
    draw.text(((W - w_account) // 2, detail_start_y), account_info_text, font=font_detail_bold, fill=detail_color)
    detail_start_y += 50

    # Amount
    try:
        # Chuyen đoi so tien sang float truoc đe xu ly so lon tot hon, sau đo đinh dang
        formatted_amount = f"So tien: {float(amount):,.0f} VNĐ".replace(",", ".")
    except ValueError:
        formatted_amount = "So tien: Khong hop le"
    
    bbox_amount = draw.textbbox((0, 0), formatted_amount, font=font_detail_bold)
    w_amount = bbox_amount[2] - bbox_amount[0]
    draw.text(((W - w_amount) // 2, detail_start_y), formatted_amount, font=font_detail_bold, fill=detail_color)
    detail_start_y += 50


    # QR Code
    qr_size = (500, 500)
    qr_pos = ((W - qr_size[0]) // 2, detail_start_y + 20)
    qr_img = fetch_image(qr_url, size=qr_size)
    if qr_img:
        # Them border cho QR code
        qr_with_border = Image.new("RGBA", (qr_size[0] + 20, qr_size[1] + 20), (255, 255, 255, 255))
        qr_with_border.paste(qr_img, (10, 10))
        
        # Tao bong cho QR code
        shadow_offset_qr = 15
        shadow_blur_qr = 20
        shadow_color_qr = (0, 0, 0, 100)
        shadow_qr = Image.new("RGBA", (qr_with_border.width + shadow_offset_qr * 2, qr_with_border.height + shadow_offset_qr * 2), (0, 0, 0, 0))
        draw_shadow_qr = ImageDraw.Draw(shadow_qr)
        draw_shadow_qr.rounded_rectangle((shadow_offset_qr, shadow_offset_qr, qr_with_border.width + shadow_offset_qr, qr_with_border.height + shadow_offset_qr), radius=20, fill=shadow_color_qr)
        shadow_qr = shadow_qr.filter(ImageFilter.GaussianBlur(shadow_blur_qr))
        
        im.paste(shadow_qr, (qr_pos[0] - shadow_offset_qr, qr_pos[1] - shadow_offset_qr), shadow_qr)
        im.paste(qr_with_border, qr_pos, qr_with_border)

    else:
        draw.rectangle([qr_pos, (qr_pos[0] + qr_size[0], qr_pos[1] + qr_size[1])], fill=(220, 220, 220))
        text_qr_not_found = "QR code not found"
        bbox_qr_text = draw.textbbox((0, 0), text_qr_not_found, font=font_small)
        w_qr_text = bbox_qr_text[2] - bbox_qr_text[0]
        h_qr_text = bbox_qr_text[3] - bbox_qr_text[1]
        draw.text((qr_pos[0] + (qr_size[0] - w_qr_text) // 2, qr_pos[1] + (qr_size[1] - h_qr_text) // 2), 
                  text_qr_not_found, font=font_small, fill=(100, 100, 100))

    # Noi dung chuyen khoan (DUOI QR)
    content_pos_y = qr_pos[1] + qr_size[1] + 30
    if add_info:
        content_info_text = f"Noi dung: {add_info}"
        bbox_content = draw.textbbox((0, 0), content_info_text, font=font_detail_bold)
        w_content = bbox_content[2] - bbox_content[0]
        draw.text(((W - w_content) // 2, content_pos_y), content_info_text, font=font_detail_bold, fill=detail_color)


    # Thoi gian hien tai (Đua xuong cuoi cung)
    current_time = datetime.now().strftime("%H:%M %d-%m-%Y")
    bbox_time = draw.textbbox((0, 0), current_time, font=font_small)
    w_time = bbox_time[2] - bbox_time[0]
    draw.text(((W - w_time) // 2, H - 60), current_time, font=font_small, fill=time_color)

    return im.convert("RGB")


# Ham xu ly lenh qrbank
def handle_qrbank_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Tang maxsplit đe chua them content va ten chu TK tuy chon
        # '/qrbank [so tai khoan] [ma ngan hang] [so tien] [ten chu TK - tuy chon] [noi dung CK - tuy chon]'
        parts = message.strip().split(maxsplit=6) 
        
        # Kiem tra so luong tham so toi thieu
        if len(parts) < 4: # Toi thieu: lenh, STK, Bank Code, So tien
            client.sendMessage(
                Message(text="Vui long nhap đung cu phap:\n`/qrbank [so tai khoan] [ma ngan hang] [so tien] [ten chu TK - tuy chon] [noi dung CK - tuy chon]`"),
                thread_id, thread_type
            )
            return

        account_number = parts[1]
        bank_code = parts[2].lower()
        amount = parts[3]
        account_name = parts[4] if len(parts) > 4 else ""
        add_info = parts[5] if len(parts) > 5 else ""

        # Kiem tra xem so tien co phai la so hop le khong
        try:
            float(amount)
        except ValueError:
            client.sendMessage(Message(text=f"So tien '{amount}' khong hop le. Vui long nhap so."), thread_id, thread_type)
            return

        bank_codes = {
            "vcb": {"bin": "970436", "name": "VIETCOMBANK"},
            "vietcombank": {"bin": "970436", "name": "VIETCOMBANK"},
            "tcb": {"bin": "970407", "name": "TECHCOMBANK"},
            "techcombank": {"bin": "970407", "name": "TECHCOMBANK"},
            "mb": {"bin": "970422", "name": "MB BANK"},
            "mbbank": {"bin": "970422", "name": "MB BANK"},
            "acb": {"bin": "970416", "name": "ACB"},
            "vib": {"bin": "970441", "name": "VIB"},
            "bidv": {"bin": "970418", "name": "BIDV"},
            "vietinbank": {"bin": "970415", "name": "VIETINBANK"},
            "vtb": {"bin": "970415", "name": "VIETINBANK"},
            "tpbank": {"bin": "970423", "name": "TPBANK"},
            "vpbank": {"bin": "970432", "name": "VPBANK"},
            "agribank": {"bin": "970405", "name": "AGRIBANK"},
            "sacombank": {"bin": "970403", "name": "SACOMBANK"},
            "scb": {"bin": "970429", "name": "SCB"},
            "hdbank": {"bin": "970437", "name": "HDBANK"},
            "ocb": {"bin": "970448", "name": "OCB"},
            "msb": {"bin": "970426", "name": "MSB"},
            "maritimebank": {"bin": "970426", "name": "MSB"},
            "shb": {"bin": "970443", "name": "SHB"},
            "eximbank": {"bin": "970431", "name": "EXIMBANK"},
            "exim": {"bin": "970431", "name": "EXIMBANK"},
            "dongabank": {"bin": "970406", "name": "DONGABANK"},
            "dab": {"bin": "970406", "name": "DONGABANK"},
            "pvcombank": {"bin": "970412", "name": "PVCOMBANK"},
            "gpbank": {"bin": "970408", "name": "GPBANK"},
            "oceanbank": {"bin": "970414", "name": "OCEANBANK"},
            "namabank": {"bin": "970428", "name": "NAMABANK"},
            "seabank": {"bin": "970444", "name": "SEABANK"},
            "vietabank": {"bin": "970425", "name": "VIETABANK"},
            "vietcapitalbank": {"bin": "970425", "name": "VIETABANK"},
            "abbank": {"bin": "970420", "name": "ABBANK"},
            "baovietbank": {"bin": "970427", "name": "BAOVIETBANK"},
            "ncb": {"bin": "970419", "name": "NCB"},
            "saigonbank": {"bin": "970400", "name": "SAIGONBANK"},
            "pgbank": {"bin": "970429", "name": "PGBANK"}, # Luu y: bin nay trung voi SCB, can kiem tra lai neu co xung đot
            "vrb": {"bin": "970450", "name": "VIETRUSSIANBANK"},
            "baca": {"bin": "970409", "name": "BAC A BANK"},
            "kienlongbank": {"bin": "970452", "name": "KIENLONG BANK"},
            "lienpb": {"bin": "970449", "name": "LIENVIETPOSTBANK"},
            "lvpb": {"bin": "970449", "name": "LIENVIETPOSTBANK"},
            "cbbank": {"bin": "970444", "name": "CB BANK"}, # Luu y: bin nay trung voi SEABANK, can kiem tra lai neu co xung đot
            # ... bo sung them neu can
        }

        if bank_code not in bank_codes:
            client.sendMessage(Message(text=f"Ma ngan hang '{bank_code}' khong ho tro hoac khong đung. Vui long kiem tra lai."), thread_id, thread_type)
            return

        bin_code = bank_codes[bank_code]["bin"]
        full_bank_name = bank_codes[bank_code]["name"]

        # Lay avatar & ten user tu client
        user_info = client.fetchUserInfo(author_id) or {}
        uid = user_info.get('uid', author_id)
        # zlapi tra ve thong tin profile trong 'profile' chu khong phai 'changed_profiles'
        profile = user_info.get('profile', {}) 
        avatar_url = profile.get('avatar') or user_info.get('avatar') # Lay avatar tu ca 2 nguon
        author_name = profile.get('name') or user_info.get('name') or "Nguoi dung Zalo" # Lay ten tu ca 2 nguon

        # Tao URL QR code theo API vietqr.io
        encoded_account_name = quote_plus(account_name)
        encoded_add_info = quote_plus(add_info)
        qr_url = (
            f"https://img.vietqr.io/image/{bin_code}-{account_number}-qr_only.jpg"
            f"?accountName={encoded_account_name}&amount={amount}&addInfo={encoded_add_info}"
        )

        print(f"DEBUG: QR URL: {qr_url}") # Đe debug xem URL QR co đung khong

        image = create_qrbank_image(avatar_url, qr_url, author_name, full_bank_name, account_number, amount, add_info)

        path_save = "qrbank_result.jpg"
        image.save(path_save, quality=90)

        # Đam bao client.sendLocalImage nhan đung tham so
        # Neu client cua ban yeu cau 'file_path' thay vi 'path', hay đoi lai
        client.sendLocalImage(path_save, thread_id=thread_id, thread_type=thread_type, width=image.width, height=image.height)

        if os.path.exists(path_save):
            os.remove(path_save)

    except Exception as e:
        # In loi ra console đe debug chi tiet hon
        print(f"Loi trong handle_qrbank_command: {e}")
        import traceback
        traceback.print_exc() # In traceback đay đu
        client.sendMessage(Message(text=f"Đa xay ra loi khi tao QR bank: `{str(e)}`"), thread_id, thread_type)