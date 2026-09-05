import os
import asyncio
import random
from aiohttp import web
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# Thông tin API chung
API_ID = 39485214
API_HASH = 'cd3c7822f740b7b7af660de3cb1c9f9d'

# Danh sách 6 Bot Token của bạn
BOT_TOKENS = [
    '8794826297:AAEQPXXbph-Kk3gQbM5yJWAjjbYlMvJopzE', # Bot 1
    '8991807402:AAG9h73vG6QaMnWWBTiakYePWKwcamsbO1s', # Bot 2
    '8701806868:AAEuz1k-K1eeTkN2Dh3uiM0J17qBrs9fc_E', # Bot 3
    '8315879201:AAHy3Zc1nZr1bSgm4l9dsdzmMwTYZJKj9dU', # Bot 4
    '8555969972:AAH0bwmMuwI8BrBUcCn_d4EUWOQEtD7R8I0', # Bot 5
    '8681995389:AAGbNTbkRVFQ2LkUetAP39Q6pSBY_nT8hpI'  # Bot 6
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

# Khởi tạo 6 client tương ứng với 6 token
clients = []
for i, token in enumerate(BOT_TOKENS):
    session_name = f'bot_session_fix_v6_{i+1}'
    for f in [f'{session_name}.session', f'{session_name}.session-journal']:
        if os.path.exists(f):
            os.remove(f)
    clients.append(TelegramClient(session_name, API_ID, API_HASH))

# --- MÁY CHỦ WEB GIẢ LẬP ĐỂ GIỮ RENDER KHÔNG BỊ NGỦ ĐÔNG ---
async def handle_ping(request):
    return web.Response(text="Bot is alive 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"[*] Web server giữ bot đang chạy tại cổng {port}")
# ----------------------------------------------------------

# Hàm xử lý quyền hạn
async def check_permissions(event):
    if event.is_private:
        if event.sender_id == ADMIN_ID:
            return True
        await event.respond("Đã khóa quyền sử dụng của bạn\nGhi chú:\nĐòi ké bot à thằng đú 🤪👈")
        return False
        
    if event.sender_id != ADMIN_ID:
        await event.reply("Bố Đức Hot War 2026 🪐🤪👈\nĐòi dùng ké à ccho ngu")
        return False
        
    return True

# Hàm chạy vòng lặp riêng cho từng bot để spam song song không chờ đợi nhau
async def single_bot_loop(bot_index, client, chat_id, task_type, text_content, target_str):
    while chat_id in active_tasks and active_tasks[chat_id]["running"]:
            try:
                if task_type == "spam":
                    message_to_send = text_content
                else: 
                    random_word = random.choice(WAR_WORDS)
                    message_to_send = f"{random_word}{target_str}"
                    
                await client.send_message(chat_id, message_to_send, parse_mode='markdown')
                
                # Mỗi bot cách nhau 1 giây riêng biệt (6 bot chạy song song sẽ tạo tốc độ cực khủng)
                await asyncio.sleep(1.0)
                
            except FloodWaitError as e:
                print(f"[!] Bot {bot_index+1} bị giới hạn, chờ {e.seconds}s.")
                await asyncio.sleep(e.seconds)
            except Exception:
                await asyncio.sleep(0.5)

async def run_all_bots(chat_id, task_type, text_content, target_str):
    # Khởi chạy đồng thời 6 task cho 6 bot chạy độc lập
    tasks = [
        asyncio.create_task(single_bot_loop(i, clients[i], chat_id, task_type, text_content, target_str))
        for i in range(len(clients))
    ]
    await asyncio.gather(*tasks)

# Lệnh /start hiển thị tính năng cho Admin
@clients[0].on(events.NewMessage(pattern=r'^/start$'))
async def send_menu(event):
    if event.sender_id != ADMIN_ID:
        if event.is_private:
            await event.respond("Đã khóa quyền sử dụng của bạn\nGhi chú:\nĐòi ké bot à thằng đú 🤪👈")
        return
        
    menu_text = (
        "👑 **HỆ THỐNG QUẢN LÝ 6 BOT WAR & SPAM** 👑\n\n"
        "✨ **Danh sách lệnh điều khiển:**\n"
        "👉 `/war [tên hoặc reply]` : 6 bot chiến song song liên tục không ngừng.\n"
        "👉 `/spam [nội dung]` : 6 bot spam song song nội dung cố định.\n"
        "👉 `/stop` : Dừng toàn bộ các tác vụ đang chạy.\n"
        "👉 `/start` : Hiển thị bảng tính năng này.\n\n"
        "🚀 *Trạng thái:* Sẵn sàng càn quét 24/7!"
    )
    await event.reply(menu_text, parse_mode='markdown')

# Lệnh /spam
@clients[0].on(events.NewMessage(pattern=r'^/spam\s+(.+)'))
async def start_spam(event):
    if not await check_permissions(event):
        return
        
    chat_id = event.chat_id
    spam_text = event.pattern_match.group(1).strip()
    
    if chat_id in active_tasks:
        active_tasks[chat_id]["running"] = False
        await asyncio.sleep(0.5)
        
    active_tasks[chat_id] = {"running": True}
    
    await event.delete()
    notif = await clients[0].send_message(chat_id, f"Đã bật 6 bot spam song song, nội dung: \"{spam_text}\"")
    await asyncio.sleep(1.5)
    await notif.delete()
    
    asyncio.create_task(run_all_bots(chat_id, "spam", spam_text, ""))

# Lệnh /war
@clients[0].on(events.NewMessage(pattern=r'^/war(?:\s+(.+))?$'))
async def start_war(event):
    if not await check_permissions(event):
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

    asyncio.create_task(run_all_bots(chat_id, "war", "", target_str))

# Lệnh /stop
@clients[0].on(events.NewMessage(pattern=r'^/stop$'))
async def stop_spam(event):
    if not await check_permissions(event):
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

# Chặn inbox người lạ
@clients[0].on(events.NewMessage(incoming=True))
async def handle_private_messages(event):
    if event.is_private and event.sender_id != ADMIN_ID:
        if not event.raw_text.startswith('/start'):
            await event.respond("Đã khóa quyền sử dụng của bạn\nGhi chú:\nĐòi ké bot à thằng đú 🤪👈")

async def main():
    await start_web_server()
    
    print("Đang kết nối toàn bộ 6 con bot...")
    for i, client in enumerate(clients):
        await client.start(bot_token=BOT_TOKENS[i])
        print(f"-> Bot {i+1} đã sẵn sàng!")
        
    print("Hệ thống 6 bot và Web Server đã hoàn tất!")
    await asyncio.gather(*(client.run_until_disconnected() for client in clients))

if __name__ == '__main__':
    asyncio.run(main())
