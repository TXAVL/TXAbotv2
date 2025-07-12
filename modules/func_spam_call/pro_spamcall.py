import threading
import time
from core.bot_sys import admin_cao, get_user_name_by_id, read_settings
from zlapi.models import *

def extract_uids_from_mentions(message_object):
    uids = []
    if message_object.mentions:
        uids = [mention['uid'] for mention in message_object.mentions if 'uid' in mention]
    return uids

def handle_spamcall_command(bot, message_object, author_id, thread_id, thread_type, command):
    def call():
        try:
            if not admin_cao(bot, author_id):
                bot.replyMessage(Message(text="❌ Ban khong phai admin bot!"), 
                                 message_object, thread_id=thread_id, 
                                 thread_type=thread_type, ttl=100000)
                return

            parts = command.split()
            if len(parts) < 3:
                bot.replyMessage(Message(text="❌ Sai cu phap! Dung: -call [so lan] [uid] hoac -call [so lan] + tag nguoi dung"), 
                                 message_object, thread_id=thread_id, 
                                 thread_type=thread_type, ttl=100000)
                return

            # Lay so lan goi
            try:
                spam_count = int(parts[1])
                if spam_count <= 0 or spam_count > 100:
                    raise ValueError
            except ValueError:
                bot.replyMessage(Message(text="❌ So lan phai la so nguyen duong tu 1 đen 100."), 
                                 message_object, thread_id=thread_id, 
                                 thread_type=thread_type, ttl=100000)
                return

            # Lay UID tu lenh hoac mentions
            target_ids = extract_uids_from_mentions(message_object)
            if not target_ids:
                try:
                    target_ids = [int(parts[2])]
                except:
                    bot.replyMessage(Message(text="❌ UID khong hop le hoac chua tag nguoi dung!"), 
                                     message_object, thread_id=thread_id, 
                                     thread_type=thread_type, ttl=100000)
                    return

            # Lay ten nguoi dung
            target_names = []
            for target_id in target_ids:
                user_name = get_user_name_by_id(bot, target_id)
                if user_name:
                    target_names.append(user_name)

            if not target_names:
                bot.replyMessage(Message(text="❌ Khong tim thay nguoi dung hop le!"), 
                                 message_object, thread_id=thread_id, 
                                 thread_type=thread_type, ttl=100000)
                return

            # Thong bao bat đau
            targets_str = ", ".join(target_names)
            bot.replyMessage(Message(text=f"📞 Bat đau goi {spam_count} lan đen: {targets_str}"), 
                             message_object, thread_id=thread_id, 
                             thread_type=thread_type, ttl=100000)

            # Gui cuoc goi
            for target_id in target_ids:
                for i in range(spam_count):
                    callid_random = bot.TaoIDCall()
                    bot.sendCall(target_id, callid_random)
                    time.sleep(2)

            # Thong bao hoan thanh
            bot.replyMessage(Message(text=f"✅ Đa goi {spam_count} lan đen {targets_str}"), 
                             message_object, thread_id=thread_id, 
                             thread_type=thread_type, ttl=100000)

        except Exception as e:
            bot.replyMessage(Message(text=f"🐞 Loi: {str(e)}"), 
                             message_object, thread_id=thread_id, 
                             thread_type=thread_type, ttl=100000)

    try:
        thread = threading.Thread(target=call)
        thread.daemon = True
        thread.start()
    except Exception as e:
        bot.replyMessage(Message(text=f"🐞 Loi khi tao thread: {str(e)}"), 
                         message_object, thread_id=thread_id, 
                         thread_type=thread_type, ttl=100000)
