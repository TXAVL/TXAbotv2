from datetime import datetime
from io import BytesIO
import json
import os
import random
from threading import Thread
import time
import requests
from core.bot_sys import is_admin, read_settings, write_settings
from zlapi.models import *
from PIL import Image, ImageDraw
from PIL import Image, ImageDraw, ImageFont

MAX_COINS = "Vo Han"
FLIE_FF = "modules/taixiu/jj.json"

def handle_taixiu_command(client, content, message_object, thread_id, thread_type, author_id):
    try:
        if isinstance(content, list):
            content = ' '.join(content)

        file_path = FLIE_FF

        if not os.path.exists(file_path):
            client.replyMessage(Message(text="💢 Ban can đang ky truoc!"), message_object, thread_id, thread_type)
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Find the user by checking if 'user_id' exists
        user = next((user for user in data if 'user_id' in user and user['user_id'] == author_id), None)
        if not user:
            client.replyMessage(Message(text="💢 Ban can đang ky truoc!"), message_object, thread_id, thread_type)
            return

        # Kiem tra thoi gian đat cuoc
        current_time = datetime.now()
        last_bet_time = datetime.strptime(user.get('last_bet_time', '1970-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S')
        time_difference = (current_time - last_bet_time).total_seconds()

        if time_difference < 60:
            remaining_time = 60 - int(time_difference)
            client.replyMessage(Message(text=f"💢 Ban can đoi {remaining_time} giay nua đe đat cuoc! ⏳"), message_object, thread_id, thread_type)
            return

        args = content.split()
        if len(args) < 3:
            client.replyMessage(Message(text="💢 Cu phap: #taixiu tai/xiu so_tien hoac phan_tram hoac đon_vi"), message_object, thread_id, thread_type)
            return

        bet_type = args[2].lower()
        bet_amount = args[3]

        if bet_type not in ["tai", "xiu"]:
            client.replyMessage(Message(text="💢 Cu phap: #taixiu tai/xiu so_tien hoac phan_tram hoac đon_vi"), message_object, thread_id, thread_type)
            return

        # Kiem tra phan tram va đon vi
        if bet_amount.endswith('%'):  # Đat theo phan tram
            try:
                percent = int(bet_amount[:-1])  # Loai bo dau %
                bet_amount = int(user['coins']) * percent // 100  # Tinh so tien theo phan tram
            except ValueError:
                client.replyMessage(Message(text="💢 Phan tram khong hop le!"), message_object, thread_id, thread_type)
                return
        elif bet_amount.endswith('k') or bet_amount.endswith('m') or bet_amount.endswith('b') or bet_amount.endswith('kb') or bet_amount.endswith('mb') or bet_amount.endswith('bb'):  # Đat theo đon vi (k, m, b)
            unit = bet_amount[-1]
            try:
                number = float(bet_amount[:-1])
                if unit == 'k':
                    bet_amount = int(number * 1000)
                elif unit == 'm':
                    bet_amount = int(number * 1000000)
                elif unit == 'b':
                    bet_amount = int(number * 1000000000)
                elif unit == 'kb':
                    bet_amount = int(number * 1000000000000)
                elif unit == 'mb':
                    bet_amount = int(number * 1000000000000000)
                elif unit == 'bb':
                    bet_amount = int(number * 1000000000000000000)
            except ValueError:
                client.replyMessage(Message(text="💢 Đon vi tien khong hop le!"), message_object, thread_id, thread_type)
                return
        else:  # Neu la so tien truc tiep
            try:
                bet_amount = int(bet_amount)
            except ValueError:
                client.replyMessage(Message(text="💢 So tien khong hop le!"), message_object, thread_id, thread_type)
                return

        # Kiem tra so du cua nguoi choi
        if user['coins'] == "Vo Han":
            user_coins = float('inf')  # Đanh dau vo han
        else:
            user_coins = int(user['coins'])  # Neu khong la vo han, chuyen thanh so nguyen

        if user_coins < bet_amount:
            client.replyMessage(Message(text="💢 Ban khong đu VNĐ đe đat cuoc!"), message_object, thread_id, thread_type)
            return

        # Sinh so xuc xac ngau nhien
        dice = [random.randint(1, 6) for _ in range(3)]  # Tao 3 so ngau nhien tu 1 đen 6 cho 3 vien xuc xac
        total = sum(dice)  # Tinh tong cac gia tri xuc xac
        result = "xiu" if total <= 10 else "tai"  # Xac đinh ket qua dua tren tong

        jackpot = False
        if dice.count(1) == 3 or dice.count(6) == 3:
            jackpot = True
            bet_amount *= 2  # Neu no hu, nhan so tien cuoc len 2 lan

        jackpot_value = bet_amount * 2

        # Gui GIF cho nguoi choi
        gif_path = "modules/taixiu/tx.gif"
        thumbnail_url = "modules/taixiu/background.jpg"
        client.sendLocalGif(gifPath=gif_path, thumbnailUrl=thumbnail_url, thread_id=thread_id, thread_type=thread_type, width=820, height=275, ttl=3000)

        time.sleep(5)  # Correctly using time.sleep(5)

        result_text = f"Ket qua: [{dice[0]} - {dice[1]} - {dice[2]}]\nTong: {total} - {result.upper()}\n"

        # Cap nhat so du sau khi cuoc
        if result == bet_type:
            if user['coins'] != "Vo Han":
                user['coins'] += bet_amount  # Chi cong neu khong phai la "Vo Han"
            if jackpot:
                result_text += f"[{user['user_name']}]\nNo Hu! Ban đa thang {bet_amount} VNĐ. \nSo tien hien tai: {user['coins']} VNĐ."
            else:
                result_text += f"[{user['user_name']}]\nĐa thang {bet_amount} VNĐ.\nSo Du: {user['coins']} VNĐ."
        else:
            if user['coins'] != "Vo Han":
                user['coins'] -= bet_amount  # Chi tru neu khong phai la "Vo Han"
            result_text += f"[{user['user_name']}]\nĐa thua {bet_amount} VNĐ.\nSo Du: {user['coins']} VNĐ."

        result_text += f"\nTien hu hien tai: {jackpot_value} VNĐ 💰"

        # Ve anh xuc xac
        background_image_path = "modules/taixiu/background.jpg"
        background_image = Image.open(background_image_path)
        draw = ImageDraw.Draw(background_image)

        dice_size = 50
        pip_radius = 5

        pip_positions = {
            1: [(25, 25)],
            2: [(10, 10), (40, 40)],
            3: [(10, 10), (25, 25), (40, 40)],
            4: [(10, 10), (10, 40), (40, 10), (40, 40)],
            5: [(10, 10), (10, 40), (40, 10), (40, 40), (25, 25)],
            6: [(10, 10), (10, 25), (10, 40), (40, 10), (40, 25), (40, 40)],
        }

        circle_center = (background_image.width // 2, background_image.height // 2)

        dice_positions = [
            (circle_center[0] - 35, circle_center[1] - 35),
            (circle_center[0] + 35, circle_center[1] - 35),
            (circle_center[0], circle_center[1] + 35)
        ]

        for i, die_value in enumerate(dice):
            rotation_angle = random.randint(0, 360)

            dice_image = Image.new("RGBA", (dice_size, dice_size), (255, 255, 255, 0))
            dice_draw = ImageDraw.Draw(dice_image)

            dice_draw.rectangle([0, 0, dice_size, dice_size], fill="white", outline="black")

            for pip in pip_positions[die_value]:
                pip_x, pip_y = pip
                dice_draw.ellipse([pip_x - pip_radius, pip_y - pip_radius, pip_x + pip_radius, pip_y + pip_radius], fill="black")

            dice_image = dice_image.rotate(rotation_angle, resample=Image.BICUBIC, expand=True)
            background_image.paste(dice_image, (dice_positions[i][0] - dice_image.width // 2,
                                                dice_positions[i][1] - dice_image.height // 2), dice_image)

        merged_image_path = "merged_image.jpg"
        background_image.save(merged_image_path)

        client.sendLocalImage(imagePath=merged_image_path, thread_id=thread_id, thread_type=thread_type, message=Message(text=f"{result_text}"), width=3300, height=1700, ttl=12000)

        # Cap nhat thoi gian cuoc cuoi cung
        user['last_bet_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        client.replyMessage(Message(text=f"💢 Đa xay ra loi: {str(e)}"), message_object, thread_id, thread_type)

def handle_top_command(self, message_object, thread_id, thread_type, author_id):
    try:
        file_path = FLIE_FF

        if not os.path.exists(file_path):
            self.replyMessage(Message(text="💢 Khong co du lieu nguoi dung!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        for user in data:
            try:
                if user.get('coins') == "Vo Han":
                    user['coins'] = float('inf')
                else:
                    user['coins'] = int(user.get('coins', 0))
            except ValueError:
                user['coins'] = 0

        sorted_data = sorted(data, key=lambda x: x['coins'], reverse=True)
        top_players = sorted_data[:10]
        top_message = "🏆 **Top 10 Nguoi Choi Co Nhieu Coin Nhat**\n"
        for idx, player in enumerate(top_players, start=1):
            player_name = player.get('user_name', 'Khong ten')
            coins_display = "Vo han coins" if player['coins'] == float('inf') else f"{player['coins']} coins"
            top_message += f"{idx}. {player_name} - {coins_display}\n"

        self.replyMessage(Message(text=top_message), message_object, thread_id=thread_id, thread_type=thread_type, ttl=30000)

    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi khi lay danh sach top: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)

def handle_taoma_command(self, message, message_object, thread_id, thread_type, author_id):
    try:

        if not is_admin(self, author_id):
            msg = "❌Ban khong phai admin bot!\n"
            self.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=120000)
            return

        args = message.split()
        if len(args) != 4:
            self.replyMessage(Message(text=f"💢 Cu phap: {self.prefix}tx ecode [coins] [luot nhap]"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        coin_amount = int(args[2])
        code_uses = int(args[3])

        if coin_amount <= 0 or code_uses <= 0:
            self.replyMessage(Message(text="💢 So coin hoac so lan nhap khong hop le!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        code = f"code_{random.randint(100000, 999999)}"
        file_path = 'modules/taixiu/codes.json'

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                codes = json.load(f)
        else:
            codes = []

        codes.append({
            'code': code,
            'coin_amount': coin_amount,
            'code_uses': code_uses
        })

        with open(file_path, 'w') as f:
            json.dump(codes, f, indent=4)

        self.replyMessage(Message(text=f"🎉 Ma code cua ban: {code}\nSo coin: {coin_amount}\nSo lan nhap: {code_uses}"), message_object, thread_id=thread_id, thread_type=thread_type)
    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi khi tao ma: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)

def handle_sudung_command(self, message, message_object, thread_id, thread_type, author_id):
    try:
        if len(message.split()) < 3:
            self.replyMessage(Message(text="💢 Ban chua cung cap ma code!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        code = message.split()[2]
        file_path = 'modules/taixiu/codes.json'
        
        if not os.path.exists(file_path):
            self.replyMessage(Message(text="💢 Khong co ma code nao!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        with open(file_path, 'r') as f:
            codes = json.load(f)

        if not codes:
            self.replyMessage(Message(text="💢 Khong co ma code nao!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        code_data = next((code_data for code_data in codes if code_data['code'] == code), None)
        if not code_data:
            self.replyMessage(Message(text="💢 Ma code khong ton tai!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        with open(FLIE_FF, 'r') as f:
            data = json.load(f)

        if not data:
            self.replyMessage(Message(text="💢 Du lieu nguoi dung khong hop le!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return
        
        user = next((user for user in data if user.get('user_id') == author_id), None)
        if not user:
            self.replyMessage(Message(text="💢 Ban chua đang ky!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if code in user['used_codes']:
            self.replyMessage(Message(text="💢 Ban đa su dung ma code nay roi!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if 'code_uses' not in code_data or code_data['code_uses'] <= 0:
            self.replyMessage(Message(text="💢 Ma code nay đa het luot su dung!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        user['coins'] += code_data['coin_amount']
        user['used_codes'].append(code)  

        with open(FLIE_FF, 'w') as f:
            json.dump(data, f, indent=4)

        code_data['code_uses'] -= 1

        with open(file_path, 'w') as f:
            json.dump(codes, f, indent=4)

        self.replyMessage(Message(text=f"🎉 Ban đa su dung ma code thanh cong!\nBan nhan đuoc {code_data['coin_amount']} coins.\nSo coin hien tai: {user['coins']}"), message_object, thread_id=thread_id, thread_type=thread_type)

    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi khi su dung ma: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)

def handle_vitien_command(self, message, message_object, thread_id, thread_type, author_id):
    try:
        file_path = FLIE_FF
        if not os.path.exists(file_path):
            self.replyMessage(Message(text="💢 Ban chua đang ky!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        if not data:
            self.replyMessage(Message(text="💢 Khong co du lieu nguoi dung!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        user = next((user for user in data if user.get('user_id') == author_id), None)

        if not user:
            self.replyMessage(Message(text="💢 Ban chua đang ky!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        user_name = user.get('user_name', 'Nguoi dung')
        coins = user.get('coins', 0)
        bet_coins = int(user.get('bet_coins', 0))  # Đam bao bet_coins la so nguyen
        wins = int(user.get('wins', 0))  # Đam bao wins la so nguyen
        losses = int(user.get('losses', 0))  # Đam bao losses la so nguyen
        registration_date = user.get('registration_date', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

        # Kiem tra va xu ly gia tri "Vo Han"
        if coins == "Vo Han":
            coins_display = "Vo Han Xu"
        else:
            coins = int(coins)  # Chuyen đoi sang so nguyen neu khong phai "Vo Han"
            coins_display = f"{coins:,} Xu"

        self.replyMessage(Message(text=f"🚦Nguoi choi: {user_name}\n"
                                      f"💰 Tai khoan: {coins_display}\n"
                                      f"🪙 So xu đa cuoc: {bet_coins:,} Xu\n"
                                      f"🏆 So lan thang: {wins}\n"
                                      f"😢 So lan thua: {losses}\n"
                                      f"📅 Ngay đang ky: {registration_date}\n"
                                      f"🎮"), 
                           message_object, thread_id=thread_id, thread_type=thread_type)

    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)

def handle_naptien_command(self, message, message_object, thread_id, thread_type, author_id):
    try:
        mentions = message_object.mentions if hasattr(message_object, 'mentions') else []
        if not mentions:
            self.replyMessage(Message(text="💢 Ban can tag nguoi choi đe chuyen tien."), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        mentioned_user_id = mentions[0]['uid']
        amount_str = message.split(" ")[-1]
        
        if not amount_str.isdigit():
            self.replyMessage(Message(text="💢 Vui long nhap so tien hop le."), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        amount = int(amount_str)
        sender_file = FLIE_FF
        with open(sender_file, 'r') as f:
            data = json.load(f)
        
        sender = next((user for user in data if user.get('user_id') == author_id), None)
        if not sender:
            self.replyMessage(Message(text="💢 Ban chua đang ky!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if sender.get('coins', 0) < amount:
            self.replyMessage(Message(text="💢 So du khong đu đe chuyen tien."), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        receiver = next((user for user in data if user.get('user_id') == mentioned_user_id), None)
        if not receiver:
            self.replyMessage(Message(text="💢 Nguoi nhan chua đang ky!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return
        receiver_name = receiver.get('user_name', 'Nguoi nhan')
        sender_name = sender.get('user_name', 'Nguoi gui')

        sender['coins'] -= amount
        receiver['coins'] += amount

        with open(sender_file, 'w') as f:
            json.dump(data, f, indent=4)

        self.replyMessage(Message(text=f"💰 {sender_name} đa chuyen {amount} coins cho {receiver_name}.\nSo tien cua ban hien tai la {sender['coins']} coins.\nSo tien cua nguoi nhan hien tai la {receiver['coins']} coins."), message_object, thread_id=thread_id, thread_type=thread_type)

    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)


def handle_daily_command(self, message, message_object, thread_id, thread_type, author_id):
    try:
        file_path = FLIE_FF
        if not os.path.exists(file_path):
            self.replyMessage(Message(text="💢 Ban can đang ky truoc!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        with open(file_path, 'r') as f:
            data = json.load(f)

        user = next((user for user in data if user.get('user_id') == author_id), None)
        if not user:
            self.replyMessage(Message(text="💢 Ban can đang ky truoc!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        current_date = datetime.now().strftime('%Y-%m-%d')

        if 'last_daily' in user and user['last_daily'] == current_date:
            self.replyMessage(Message(text="💢 Ban đa điem danh hom nay roi!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if user.get('coins') == "Vo Han":
            self.replyMessage(Message(text="💢 Ban đa co so tien vo han, khong the nhan them!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        try:
            user['coins'] = int(user.get('coins', 0))  # Ensure coins is treated as an integer
        except ValueError:
            if user['coins'] == "Vo Han":
                user['coins'] = 0  # Handle "Vo Han" as 0 or reset to default
            else:
                self.replyMessage(Message(text="💢 Đa xay ra loi voi so coin cua ban!"), message_object, thread_id=thread_id, thread_type=thread_type)
                return

        # If MAX_COINS is "Vo Han", bypass the limit check
        if MAX_COINS != "Vo Han" and user['coins'] + 3000 > int(MAX_COINS):
            self.replyMessage(Message(text="💢 So coin cua ban đa đat gioi han toi đa!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        user['coins'] += 3000
        user['last_daily'] = current_date

        self.replyMessage(Message(text=f"🎉 Chuc mung {user.get('user_name', 'Nguoi dung')}! Ban đa điem danh thanh cong va nhan đuoc 3000 coins.\nSo tien hien tai: {user['coins']} coins."), message_object, thread_id=thread_id, thread_type=thread_type)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi khi điem danh: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)


def handle_dangky_command(self, message, message_object, thread_id, thread_type, author_id):
    try:
        file_path = FLIE_FF
        data = []

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []

        if any(user.get('user_id') == author_id for user in data):
            self.replyMessage(
                Message(text="💢 Ban đa đang ky roi!"),
                message_object,
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        user_info = self.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles[author_id].displayName

        user_data = {
            'user_id': author_id,
            'user_name': user_name,
            'coins': 1000,
            'bet_coins': 0,
            'wins': 0,
            'losses': 0,
            'used_codes': []
        }
        data.append(user_data)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        self.replyMessage(
            Message(text=f"🎉 Chuc mung {user_name}! Ban đa đang ky thanh cong va nhan đuoc 1000 coins."),
            message_object,
            thread_id=thread_id,
            thread_type=thread_type
        )

    except Exception as e:
        self.replyMessage(
            Message(text=f"💢 Đa xay ra loi khi đang ky: {str(e)}"),
            message_object,
            thread_id=thread_id,
            thread_type=thread_type
        )

def handle_xoataikhoan_command(self, message, message_object, thread_id, thread_type, author_id):
    try:
        mentions = message_object.mentions if hasattr(message_object, 'mentions') else []
        
        if not mentions:
            self.replyMessage(Message(text="💢 Ban can tag nguoi choi đe xoa tai khoan."), message_object, thread_id=thread_id, thread_type=thread_type)
            return
        mentioned_user_id = mentions[0].get('uid', None)
        if not mentioned_user_id:
            self.replyMessage(Message(text="💢 Khong the xac đinh nguoi choi đuoc tag."), message_object, thread_id=thread_id, thread_type=thread_type)
            return
        
        if not is_admin(self, author_id):
            msg = "❌Ban khong phai admin bot!\n"
            styles = MultiMsgStyle([ 
                MessageStyle(offset=0, length=2, style="color", color="#f38ba8", auto_format=False),
                MessageStyle(offset=2, length=len(msg)-2, style="color", color="#cdd6f4", auto_format=False),
                MessageStyle(offset=0, length=len(msg), style="font", size="13", auto_format=False)
            ])
            self.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
            return
        user_file = FLIE_FF
        with open(user_file, 'r') as f:
            data = json.load(f)
        user_to_delete = next((user for user in data if user.get('user_id') == mentioned_user_id), None)

        if not user_to_delete:
            self.replyMessage(Message(text="💢 Nguoi dung nay khong ton tai trong he thong."), message_object, thread_id=thread_id, thread_type=thread_type)
            return
        data = [user for user in data if user.get('user_id') != mentioned_user_id]

        with open(user_file, 'w') as f:
            json.dump(data, f, indent=4)

        self.replyMessage(Message(text=f"💢 Tai khoan cua {user_to_delete.get('user_name', 'Nguoi choi')} đa đuoc xoa thanh cong."), message_object, thread_id=thread_id, thread_type=thread_type)

    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)

def handle_vohantien_command(self, message, message_object, thread_id, thread_type, author_id):
    try:
        if not is_admin(self, author_id):
            msg = "❌Ban khong phai admin bot!\n"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=2, style="color", color="#f38ba8", auto_format=False),
                MessageStyle(offset=2, length=len(msg)-2, style="color", color="#cdd6f4", auto_format=False),
                MessageStyle(offset=0, length=len(msg), style="font", size="13", auto_format=False)
            ])
            self.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
            return
        
        mentions = message_object.mentions if hasattr(message_object, 'mentions') else []
        if not mentions:
            self.replyMessage(Message(text="💢 Ban can tag nguoi choi đe cap vo han tien."), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        mentioned_user_id = mentions[0].get('uid', None)
        if not mentioned_user_id:
            self.replyMessage(Message(text="💢 Khong the xac đinh nguoi choi đuoc tag."), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        user_file = FLIE_FF
        if not os.path.exists(user_file):
            self.replyMessage(Message(text="💢 Tep du lieu khong ton tai!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        with open(user_file, 'r') as f:
            data = json.load(f)
        existing_user = next((user for user in data if user.get('user_id') == mentioned_user_id), None)
        if not existing_user:
            self.replyMessage(Message(text="💢 Nguoi choi nay chua co tai khoan!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if 'coins' not in existing_user:
            self.replyMessage(Message(text="💢 Du lieu nguoi choi khong hop le!"), message_object, thread_id=thread_id, thread_type=thread_type)
            return
        existing_user['coins'] = "Vo Han"

        with open(user_file, 'w') as f:
            json.dump(data, f, indent=4)
        self.replyMessage(Message(text=f"🎉 Nguoi choi {existing_user['user_name']} đa nhan tien vo han thanh cong! So du hien tai cua ho la: {existing_user['coins']} coins"), message_object, thread_id=thread_id, thread_type=thread_type)

    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)

def list_codes(self, message_object, thread_id, thread_type):
    try:
        file_path = 'modules/taixiu/codes.json'

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                codes = json.load(f)
            
            if codes:
                message_text = "Danh sach cac ma code:\n"
                for code_data in codes:
                    code = code_data.get('code', 'Ma khong xac đinh')
                    coin_amount = code_data.get('coin_amount', 'Khong xac đinh')
                    code_uses = code_data.get('code_uses', 'Khong xac đinh')

                    message_text += f"- Code: {code}\n[So coin: {coin_amount}]\n[So lan nhap: {code_uses}]\n\n"
            else:
                message_text = "💢 Khong co ma code nao đuoc tao!"
        else:
            message_text = "💢 Tep ma code khong ton tai!"

        self.replyMessage(Message(text=message_text), message_object, thread_id=thread_id, thread_type=thread_type)
    except Exception as e:
        self.replyMessage(Message(text=f"💢 Đa xay ra loi khi liet ke ma code: {str(e)}"), message_object, thread_id=thread_id, thread_type=thread_type)

def create_gradient_colors(num_colors):
    return [(random.randint(100, 175), random.randint(100, 180), random.randint(100, 170)) for _ in range(num_colors)]

def interpolate_colors(colors, text_length, change_every):
    gradient = []
    num_segments = len(colors) - 1
    steps_per_segment = (text_length // change_every) + 1
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

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception as e:
        return "Unknown User"
    
def handle_tx_on(bot, thread_id):
    settings = read_settings(bot.uid)
    if "tx" not in settings:
        settings["tx"] = {}
    settings["tx"][thread_id] = True
    write_settings(bot.uid, settings)
    return f"🚦Lenh {bot.prefix}tx đa đuoc Bat 🚀 trong nhom nay ✅"

def handle_tx_off(bot, thread_id):
    settings = read_settings(bot.uid)
    if "tx" in settings and thread_id in settings["tx"]:
        settings["tx"][thread_id] = False
        write_settings(bot.uid, settings)
        return f"🚦Lenh {bot.prefix}tx đa Tat ⭕️ trong nhom nay ✅"
    return "🚦Nhom chua co thong tin cau hinh tx đe ⭕️ Tat 🤗"
    
def handle_tx_command(bot, message_object, author_id, thread_id, thread_type, command):
    def send_response():
        try:

            settings = read_settings(bot.uid)
    
            user_message = command.replace(f"{bot.prefix}tx ", "").strip().lower()
            if user_message == "on":
                if not is_admin(bot, author_id):  
                    response = "❌Ban khong phai admin bot!"
                else:
                    response = handle_tx_on(bot, thread_id)
                bot.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
                return
            elif user_message == "off":
                if not is_admin(bot, author_id):  
                    response = "❌Ban khong phai admin bot!"
                else:
                    response = handle_tx_off(bot, thread_id)
                bot.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
                return
            
            if not (settings.get("tx", {}).get(thread_id, False)):
                return

            parts = command.split()
            commands = "tx"
            if len(parts) == 1:
                response = (
                    f"{get_user_name_by_id(bot, author_id)}\n"
                    f"🧾 Xem danh sach code ({bot.prefix}{commands} lcd)\n"
                    f"♾️ Cong tien vo han(Admin) ({bot.prefix}{commands} max)\n"
                    f"🗑️ Xoa tai khoan(Admin) ({bot.prefix}{commands} remove)\n"
                    f"® Đang ky game ({bot.prefix}{commands} dk)\n"
                    f"🎁 Nhan qua ({bot.prefix}{commands} daily)\n"
                    f"〽️ Chuyen tien ({bot.prefix}{commands} bank)\n"
                    f"💯 Xem so du ({bot.prefix}{commands} sodu)\n"
                    f"🗂️ Tao code(Admin) ({bot.prefix}{commands} ecode)\n"
                    f"💬 Nhap code ({bot.prefix}{commands} code)\n"
                    f"🎯 Xem bang xep hang ({bot.prefix}{commands} bxh)\n"
                    f"💵 Đat cuoc ({bot.prefix}{commands} dat)\n"
                )
            else:
                action = parts[1].lower() 
                
                if action == 'lcd':
                    response = list_codes(bot, message_object, thread_id, thread_type)
                elif action == 'max':
                    response = handle_vohantien_command(bot, command, message_object, thread_id, thread_type, author_id)
                elif action == 'remove':
                    response = handle_xoataikhoan_command(bot, command, message_object, thread_id, thread_type, author_id)             
                elif action == 'dk':
                    response = handle_dangky_command(bot, command, message_object, thread_id, thread_type, author_id)
                elif action == 'daily':
                    response = handle_daily_command(bot, command, message_object, thread_id, thread_type, author_id)
                elif action == 'bank':
                    response = handle_naptien_command(bot, command, message_object, thread_id, thread_type, author_id)
                elif action == 'sodu':
                    response = handle_vitien_command(bot, command, message_object, thread_id, thread_type, author_id)
                elif action == 'ecode':
                    response = handle_taoma_command(bot, command, message_object, thread_id, thread_type, author_id)
                elif action == 'code':
                    response = handle_sudung_command(bot, command, message_object, thread_id, thread_type, author_id)
                elif action == 'bxh':
                    response = handle_top_command(bot, message_object, thread_id, thread_type, author_id)
                elif action == 'dat':
                    response = handle_taixiu_command(bot, command, message_object, thread_id, thread_type, author_id)
                else:
                    response = f"➜ Lenh [{bot.prefix}{commands} {action}] khong đuoc ho tro 🤧"
            
            if response:
                if len(parts) == 1:
                    temp_image_path = create_menu1_image({"response": response}, 1, bot, author_id)
                    bot.sendLocalImage(
                        temp_image_path, thread_id=thread_id, thread_type=thread_type,
                        message=Message(text=response, mention=Mention(author_id, length=len(f"{get_user_name_by_id(bot, author_id)}"), offset=0)), height=500, width=1280, ttl=1200000
                    )
                    os.remove(temp_image_path)
                else:
                    bot.replyMessage(Message(text=response),message_object, thread_id=thread_id, thread_type=thread_type)
        
        except Exception as e:
            print(f"Error: {e}")
            bot.replyMessage(Message(text=f"➜ 🐞 Đa xay ra loi: {e}🤧"), message_object, thread_id=thread_id, thread_type=thread_type)

    thread = Thread(target=send_response)
    thread.start()

def create_menu1_image(command_names, page, bot, author_id):
    
    avatar_url = None

    if author_id:
        user_info = bot.fetchUserInfo(author_id)
        avatar_url = user_info.changed_profiles.get(author_id).avatar

    start_index = (page - 1) * 10
    end_index = start_index + 10
    current_page_commands = list(command_names.items())[start_index:end_index]

    
    numbered_commands = [f"⭐ {i + start_index + 1}. {name} - {desc}" for i, (name, desc) in enumerate(current_page_commands)]

    
    background_dir = "background"
    background_files = [os.path.join(background_dir, f) for f in os.listdir(background_dir) if f.endswith(('.png', '.jpg'))]
    background_path = random.choice(background_files)
    image = Image.open(background_path).convert("RGBA")
    image = image.resize((1280, 500))

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    rect_x0 = (1280 - 1100) // 2
    rect_y0 = (500 - 300) // 2
    rect_x1 = rect_x0 + 1100
    rect_y1 = rect_y0 + 300

    radius = 50
    draw.rounded_rectangle([rect_x0, rect_y0, rect_x1, rect_y1], radius=radius, fill=(255, 255, 255, 200))
    overlay = Image.alpha_composite(image, overlay)
    if avatar_url:
        try:
            avatar_response = requests.get(avatar_url)
            avatar_image = Image.open(BytesIO(avatar_response.content)).convert("RGBA").resize((100, 100))

            gradient_size = 110
            gradient_colors = create_gradient_colors(7)
            gradient_overlay = Image.new("RGBA", (gradient_size, gradient_size), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient_overlay)

            for i, color in enumerate(gradient_colors):
                radius = gradient_size // 2 - i
                gradient_draw.ellipse(
                    (i, i, gradient_size - i, gradient_size - i),
                    outline=color,
                    width=1
                )

            mask = Image.new("L", avatar_image.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 100, 100), fill=255)
            gradient_overlay.paste(avatar_image, (5, 5), mask)

            overlay.paste(gradient_overlay, (rect_x0 + 20, rect_y0 + 100), gradient_overlay)
        except Exception:
            pass

    text_hi = f"Hi {user_info.changed_profiles[author_id].displayName}!" if author_id in user_info.changed_profiles else "Hi Nguoi dung!"
    text_welcome = f"🎊 Chao {user_info.changed_profiles[author_id].displayName}, Toi co the giup gi cho ban?"
    text_bot_info = f"🤖 Bot: {get_user_name_by_id(bot, bot.uid)} 💻 version 1.0.0 🗓️ update 08-01-24"
    text_bot_ready = f"♥️ bot san sang phuc vu"
    font_paci = "arial unicode ms.otf"
    font_emoji = "NotoEmoji-Bold.ttf"
    draw = ImageDraw.Draw(overlay)

    font_hi = ImageFont.truetype(font_paci, size=50) if os.path.exists(font_paci) else ImageFont.load_default()
    font_welcome = ImageFont.truetype(font_paci, size=35) if os.path.exists(font_paci) else ImageFont.load_default()
    font_bot_info = ImageFont.truetype(font_emoji, size=25) if os.path.exists(font_emoji) else ImageFont.load_default()

    x_hi = (1300 - draw.textbbox((0, 0), text_hi, font=font_hi)[2]) // 2
    y_hi = rect_y0 + 10

    gradient_colors_hi = interpolate_colors(create_gradient_colors(5), len(text_hi), 1)
    for i, char in enumerate(text_hi):
        draw.text((x_hi, y_hi), char, font=font_hi, fill=gradient_colors_hi[i])
        x_hi += draw.textbbox((0, 0), char, font=font_hi)[2]

    x_welcome = (1300 - draw.textbbox((0, 0), text_welcome, font=font_welcome)[2]) // 2
    y_welcome = y_hi + 60

    gradient_colors_welcome = interpolate_colors(create_gradient_colors(5), len(text_welcome), 1)
    for i, char in enumerate(text_welcome):
        draw.text((x_welcome, y_welcome), char, font=font_welcome, fill=gradient_colors_welcome[i])
        x_welcome += draw.textbbox((0, 0), char, font=font_welcome)[2]

    x_bot_info = rect_x0 + 130
    y_bot_info = rect_y1 - 60

    gradient_colors_bot_info = interpolate_colors(create_gradient_colors(7), len(text_bot_info), 1)
    current_x = x_bot_info

    for i, char in enumerate(text_bot_info):
        if char in "🤖💻🗓️":
            current_font = font_bot_info
        else:
            current_font = font_welcome

        draw.text((current_x, y_bot_info), char, font=current_font, fill=gradient_colors_bot_info[i])
        char_width = draw.textbbox((0, 0), char, font=current_font)[2]
        current_x += char_width

    y_bot_ready = y_bot_info - 80
    gradient_colors_bot_ready = interpolate_colors(create_gradient_colors(5), len(text_bot_ready), 1)
    current_x_bot_ready = (1300 - draw.textbbox((0, 0), text_bot_ready, font=font_welcome)[2]) // 2

    for i, char in enumerate(text_bot_ready):
        if char in "♥️:3🤗🎉":
            current_font = font_bot_info
        else:
            current_font = font_welcome
        draw.text((current_x_bot_ready, y_bot_ready), char, font=current_font, fill=gradient_colors_bot_ready[i])
        current_x_bot_ready += draw.textbbox((0, 0), char, font=current_font)[2]

    overlay = Image.alpha_composite(image, overlay)
    temp_image_path = "temp_image.png"
    overlay.save(temp_image_path)

    return temp_image_path