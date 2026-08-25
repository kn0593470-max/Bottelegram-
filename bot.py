import os
import asyncio
import random
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# Thông tin API chung
API_ID = 39485214
API_HASH = 'cd3c7822f740b7b7af660de3cb1c9f9d'

# Danh sách 4 Bot Token của bạn
BOT_TOKENS = [
    '8794826297:AAEQPXXbph-Kk3gQbM5yJWAjjbYlMvJopzE', # Bot 1
    '8991807402:AAG9h73vG6QaMnWWBTiakYePWKwcamsbO1s', # Bot 2
    '8701806868:AAEuz1k-K1eeTkN2Dh3uiM0J17qBrs9fc_E', # Bot 3
    '8315879201:AAHy3Zc1nZr1bSgm4l9dsdzmMwTYZJKj9dU'  # Bot 4
]

# ID được phép sử dụng bot
ADMIN_ID = 7907990385

# Danh sách ngôn chiến của bạn
WAR_WORDS = [
    "óc cặc chạy rồi à =))",
    "Bê đê óc lồn câm nín im re để cha đút cặc vô lồn con gái mẹ mày",
    "Cha nhây với mày tới mai mà ngu à =)",
    "Thằng ngu ảo tưởng đòi làm anh hùng và cái kết =))",
    "lượm cái ngôn m vừa thải ra rồi mua thêm nải chuối với con gà luộc đem lên bàn thờ mà cúng cn mẹ quá cố của m đê =}",
    "Cái con không có địa vị bằng 1 cn súc vật nữa =))",
    "Bị anh cho ngậm đống hành trong mõm r =))",
    "Não bị cha mày cho tàn phế r à =))",
    "Để đầu thai chuyển kiếp thành súc vật =))",
    "Bị cha mày đọa đày xuống diêm la địa phủ =))",
    "sợ bố mà xạo lồn à con =))",
    "Tk não vô sinh ngu ngục quỳ lạy bố đê kiếm ngôn nào sát thương tí dc k =))",
    "Quá khứ hiện tại tương lai của m sẽ xuống cầu y như cái tk cha m =))",
    "Cay quá nên uống nc đái chó cho đỡ cay đi em =))",
    "123 lalala 456 địt cha nhà m =))",
    "Con chó con mèo con ghẹ nhưng tao chỉ thích con mẹ m thôi =))",
    "Ngày anh sinh ra là ngày mày có thêm 1 người bố à =))",
    "m ẳng nqu là t tế mộ cn mẹ m lên t đá/i vô x/ác mẹ m đó tk mồ côi",
    "sao nhìn xanh xao mặt mày hết lên thế kia =}",
    "Không phản bác được à =))",
    "Cha Đức Hot War 2026 🪐 🤪 👈",
    "Óc lồn bại não chạy rồi à =))",
    "Kiki ra đây bố m bón cứt vô mỗm m nè =)"
]

# Quản lý task chạy nền cho từng nhóm
active_tasks = {}

# Khởi tạo 4 client tương ứng với 4 token
clients = []
for i, token in enumerate(BOT_TOKENS):
    session_name = f'bot_session_fix_{i+1}'
    for f in [f'{session_name}.session', f'{session_name}.session-journal']:
        if os.path.exists(f):
            os.remove(f)
    clients.append(TelegramClient(session_name, API_ID, API_HASH))

# Hàm kiểm tra quyền Admin
async def check_admin(event):
    sender_id = event.sender_id
    if sender_id != ADMIN_ID:
        await event.reply("Bố Đức Hot War 2026 🪐🤪👈\nĐòi dùng ké à ccho ngu")
        return False
    return True

# Hàm chạy vòng lặp gửi tin nhắn nền không bị ngắt
async def run_loop(chat_id, task_type, text_content, target_str):
    bot_index = 0
    while chat_id in active_tasks and active_tasks[chat_id]["running"]:
        try:
            current_client = clients[bot_index]
            
            if task_type == "spam":
                message_to_send = text_content
                sleep_time = 2.0
            else: # war
                random_word = random.choice(WAR_WORDS)
                message_to_send = f"{random_word}{target_str}"
                sleep_time = 0.2 # 1 giây 5 câu
                
            await current_client.send_message(chat_id, message_to_send, parse_mode='markdown')
            
            # Xoay vòng liên tục: 0 -> 1 -> 2 -> 3 -> 0
            bot_index = (bot_index + 1) % len(clients)
            await asyncio.sleep(sleep_time)
            
        except FloodWaitError as e:
            print(f"[!] Bot {bot_index+1} bị FloodWait, phải đợi {e.seconds} giây.")
            await asyncio.sleep(e.seconds)
        except Exception as ex:
            # Nếu bot này lỗi, tự động chuyển sang bot tiếp theo không dừng vòng lặp
            bot_index = (bot_index + 1) % len(clients)
            await asyncio.sleep(0.5)

# Lệnh /spam
@clients[0].on(events.NewMessage(pattern=r'^/spam\s+(.+)'))
async def start_spam(event):
    if event.is_private or not await check_admin(event):
        return
        
    chat_id = event.chat_id
    spam_text = event.pattern_match.group(1).strip()
    
    # Nếu nhóm đang chạy cái khác thì dừng trước
    if chat_id in active_tasks:
        active_tasks[chat_id]["running"] = False
        await asyncio.sleep(0.5)
        
    active_tasks[chat_id] = {"running": True}
    
    await event.delete()
    notif = await clients[0].send_message(chat_id, f"Đã bật spam liên tục 4 bot, nội dung: \"{spam_text}\"")
    await asyncio.sleep(1.5)
    await notif.delete()
    
    # Chạy vòng lặp nền
    asyncio.create_task(run_loop(chat_id, "spam", spam_text, ""))

# Lệnh /war
@clients[0].on(events.NewMessage(pattern=r'^/war(?:\s+(.+))?$'))
async def start_war(event):
    if event.is_private or not await check_admin(event):
        return
        
    chat_id = event.chat_id
    target = event.pattern_match.group(1)
    if target:
        target = target.strip()
    else:
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            sender = await reply_msg.get_sender()
            if sender and sender.username:
                target = f"@{sender.username}"
            elif sender and sender.first_name:
                target = f"[{sender.first_name}](tg://user?id={sender.id})"
        
    target_str = f" {target}" if target else ""
    
    # Nếu nhóm đang chạy cái khác thì dừng trước
    if chat_id in active_tasks:
        active_tasks[chat_id]["running"] = False
        await asyncio.sleep(0.5)
        
    active_tasks[chat_id] = {"running": True}
    
    await event.delete()
    try:
        init_msg = f"Bố Đức Hot War 2026 🪐 🤪{target_str}"
        await clients[0].send_message(chat_id, init_msg, parse_mode='markdown')
    except Exception:
        pass

    # Chạy vòng lặp nền
    asyncio.create_task(run_loop(chat_id, "war", "", target_str))

# Lệnh dừng
@clients[0].on(events.NewMessage(pattern=r'^/stop$'))
async def stop_spam(event):
    if event.is_private or not await check_admin(event):
        return
        
    chat_id = event.chat_id
    if chat_id in active_tasks:
        active_tasks[chat_id]["running"] = False
        del active_tasks[chat_id]
        
    await event.delete()
    try:
        notif = await clients[0].send_message(chat_id, "Đã dừng hoàn toàn các tác vụ!")
        await asyncio.sleep(1.5)
        await notif.delete()
    except Exception:
        pass

async def main():
    print("Đang kết nối toàn bộ 4 con bot...")
    for i, client in enumerate(clients):
        await client.start(bot_token=BOT_TOKENS[i])
        print(f"-> Bot {i+1} đã sẵn sàng!")
        
    print("Hệ thống đã sẵn sàng chiến liên tục không nghĩ! Chỉ ID 7907990385 mới dùng được.")
    await asyncio.gather(*(client.run_until_disconnected() for client in clients))

await main()
