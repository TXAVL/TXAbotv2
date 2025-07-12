from zlapi.models import Message, ThreadType
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import requests
import os
import tempfile

def fetch_image(url, timeout=60):
    """Tải ảnh từ url với timeout"""
    try:
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print(f"Fetch image lỗi: {e}")
        return None

def draw_text_wrapped(draw, text, position, font, max_width, line_spacing=3, fill=(0,0,0)):
    """Vẽ text xuống dòng khi vượt quá max_width"""
    x, y = position
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            line = test_line
        else:
            if line: 
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.getbbox(line)[3] - font.getbbox(line)[1] + line_spacing

def handle_group_command(message, message_object, thread_id, thread_type, author_id, bot):
    try:
        group = bot.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id)
        if not group:
            bot.replyMessage(Message(text="Không tìm thấy thông tin nhóm!"), message_object, thread_id, thread_type)
            return

        avatar_url = group.fullAvt if group.fullAvt else None
        avatar_img = fetch_image(avatar_url) if avatar_url else None

        # Tăng kích thước ảnh để chữ thoải mái hơn
        width, height = 1100, 700  
        bg_color = (255, 255, 255)
        image = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        font_path = "BeVietnamPro-SemiBold.ttf"
        if not os.path.isfile(font_path):
            font_path = None
        font_title = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()
        font_text = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()

        padding = 30
        avatar_size = 180
        text_start_x = avatar_size + padding * 2
        current_y = padding - 10

        if avatar_img:
            avatar_img = avatar_img.resize((avatar_size, avatar_size))
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            image.paste(avatar_img, (padding, padding), mask)

        group_name = group.name or "Không tên"
        draw.text((text_start_x, current_y), group_name, font=font_title, fill=(30, 30, 30))
        current_y += font_title.getbbox(group_name)[3] - font_title.getbbox(group_name)[1] + 15

        desc = group.desc or "Không có mô tả"
        draw_text_wrapped(draw, f"Mô tả: {desc}", (text_start_x, current_y), font_text, max_width=width - text_start_x - padding, fill=(70,70,70))
        current_y += (font_text.getbbox(desc)[3] - font_text.getbbox(desc)[1]) * (desc.count('\n')+1) + 40

        info_lines = []
        info_lines.append(f"ID nhóm: {group.groupId}")

        creator_name = "Không xác định"
        try:
            creator_name = bot.fetchUserInfo(group.creatorId).changed_profiles[group.creatorId].zaloName
        except:
            pass
        info_lines.append(f"Trưởng nhóm: {creator_name}")

        # Bỏ phó nhóm nên không lấy adminIds

        info_lines.append(f"Tổng thành viên: {group.totalMember}")

        create_ts = group.createdTime
        try:
            create_time_str = datetime.fromtimestamp(create_ts / 1000).strftime("%H:%M %d/%m/%Y")
        except:
            create_time_str = "Không xác định"
        info_lines.append(f"Thời gian tạo: {create_time_str}")

        key_translation = {
            'blockName': 'Chặn đổi tên & avatar nhóm',
            'signAdminMsg': 'Ghim tin nhắn từ chủ/pho nhóm',
            'addMemberOnly': 'Chỉ chủ/phó thêm thành viên',
            'setTopicOnly': 'Cho phép members ghim tin nhắn, ghi chú, bình chọn',
            'enableMsgHistory': 'Bật lịch sử tin nhắn',
            'lockCreatePost': 'Khóa tạo ghi chú, nhắc hẹn',
            'lockCreatePoll': 'Khóa tạo cuộc thăm dò',
            'joinAppr': 'Chế độ phê duyệt thành viên',
            'bannFeature': 'Tính năng cấm',
            'dirtyMedia': 'Nội dung nhạy cảm',
            'banDuration': 'Thời gian cấm',
            'lockSendMsg': 'Khóa gửi tin nhắn',
            'lockViewMember': 'Khóa xem thành viên'
        }
        setting = getattr(group, "setting", {})
        setting_lines = []

        for key, label in key_translation.items():
            val = setting.get(key, 0)
            if val == 1:
                status_text = "Bật"
                status_color = (0, 150, 0)  # xanh lá
            else:
                status_text = "Tắt"
                status_color = (200, 0, 0)  # đỏ

            # Vẽ label
            draw.text((text_start_x, current_y), f"{label}: ", font=font_text, fill=(0,0,0))
            # Vẽ trạng thái bật/tắt sát bên
            label_bbox = draw.textbbox((text_start_x, current_y), f"{label}: ", font=font_text)
            status_x = label_bbox[2] + 5
            draw.text((status_x, current_y), status_text, font=font_text, fill=status_color)
            current_y += font_text.getbbox(label)[3] - font_text.getbbox(label)[1] + 8

        # Lưu ảnh tạm rồi gửi
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            image.convert("RGB").save(tmp_file.name, format="JPEG", quality=90)
            tmp_path = tmp_file.name

        bot.replyMessage(
            Message(text=f"📄 Thông tin nhóm: {group_name}"),
            message_object,
            thread_id=thread_id,
            thread_type=thread_type
        )

        bot.sendLocalImage(
            tmp_path,
            thread_id=thread_id,
            thread_type=thread_type
        )

        os.remove(tmp_path)

    except Exception as e:
        print(f"Lỗi xử lý lệnh nhóm: {e}")
        bot.replyMessage(Message(text="❌ Lỗi xử lý lệnh nhóm, thử lại sau!"), message_object, thread_id, thread_type)
