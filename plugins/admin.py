from config import Config
from helper.database import digital_botz
from helper.utils import get_seconds, humanbytes
import os, sys, time, asyncio, logging, datetime, traceback
from zoneinfo import ZoneInfo
from pyrogram.types import Message, LinkPreviewOptions
from pyrogram import Client, filters
from html import escape
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# आपकी परमानेंट एडमिन आईडी
ADMINS = [8853897167]
 
@Client.on_message(filters.command("status") & filters.user(ADMINS))
async def get_stats(bot, message):
    total_users = await digital_botz.total_users_count()
    if bot.premium:
        total_premium_users = await digital_botz.total_premium_users_count()
    else:
        total_premium_users = "Disabled ✅"
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - bot.uptime))    
    start_t = time.time()
    rkn = await message.reply('<b>ᴘʀᴏᴄᴇssɪɴɢ.....</b>')    
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await rkn.edit(text=f"<b>--Bᴏᴛ Sᴛᴀᴛᴜꜱ--</b> \n\n<b>⌚️ Bᴏᴛ Uᴩᴛɪᴍᴇ:</b> {uptime} \n<b>🐌 Cᴜʀʀᴇɴᴛ Pɪɴɢ:</b> <code>{time_taken_s:.3f} ᴍꜱ</code> \n<b>👭 Tᴏᴛᴀʟ Uꜱᴇʀꜱ:</b> <code>{total_users}</code>\n<b>💸 ᴛᴏᴛᴀʟ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs:</b> <code>{total_premium_users}</code>")
 
@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(b, m):
    try:
        await m.reply_document(Config.LOG_FILE)
    except Exception as e:
        await m.reply(str(e))

@Client.on_message(filters.private & filters.command("addpremium"))
async def add_premium(client, message):
    # Security Check: Agar bhejne wala admin nahi hai, toh rok do
    if message.from_user.id not in ADMINS:
        return await message.reply_text("❌ <b>Aap is command ko use nahi kar sakte! Yeh sirf Admin ke liye hai.</b>")

    if not client.premium:
        return await message.reply_text("premium mode disabled ✅")
    
    if client.uploadlimit:
        if len(message.command) < 4:
            return await message.reply_text("Usage : /addpremium user_id Plan_Type (e.g... <code>Pro</code>, <code>UltraPro</code>) time (e.g., '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year')")
        
        user_id = int(message.command[1])
        plan_type = message.command[2]
        if plan_type not in ["Pro", "UltraPro"]:
            return await message.reply_text("Invalid Plan Type. Please use 'Pro' or 'UltraPro'.")
        
        time_string = " ".join(message.command[3:])
        time_zone = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")
        user = await client.get_users(user_id)
        
        if plan_type == "Pro":
            limit = 107374182400
            type = "Pro"
        elif plan_type == "UltraPro":
            limit = 1073741824000
            type = "UltraPro"

        seconds = await get_seconds(time_string)
        if seconds <= 0:
            return await message.reply_text("Invalid time format. Please use <code>/addpremium user_id 1 year 1 month 1 day 1 min 10 s</code>")
        
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time}
        await digital_botz.add_premium(user_id, user_data, limit, type)
        
        user_data = await digital_botz.get_user_data(user_id)
        limit = user_data.get('uploadlimit', 0)
        type = user_data.get('usertype', "Free")
        data = await digital_botz.get_user(user_id)
        expiry = data.get("expiry_time")
        expiry_str_in_ist = expiry.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
        
        await message.reply_text(f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\nᴘʟᴀɴ :- <code>{type}</code>\nᴅᴀɪʟʏ ᴜᴘʟᴏᴀᴅ ʟɪᴍɪᴛ :- <code>{humanbytes(limit)}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{escape(str(time_string))}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", link_preview_options=LinkPreviewOptions(is_disabled=True))
        
        await client.send_message(
            chat_id=user_id,
            text=f"👋 ʜᴇʏ {user.mention},\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\nᴇɴᴊᴏʏ !! ✨🎉\n\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{escape(str(time_string))}</code>\nᴘʟᴀɴ :- <code>{type}</code>\nᴅᴀɪʟʏ ᴜᴘʟᴏᴀᴅ ʟɪᴍɪᴛ :- <code>{humanbytes(limit)}</code>\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", link_preview_options=LinkPreviewOptions(is_disabled=True)              
        )
    else:
        if len(message.command) < 3:
            return await message.reply_text("Usage : /addpremium user_id time (e.g., '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year')")
        user_id = int(message.command[1])
        time_string = " ".join(message.command[2:])
        time_zone = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")
        user = await client.get_users(user_id)        
        seconds = await get_seconds(time_string)
        if seconds <= 0:
            return await message.reply_text("Invalid time format. Please use <code>/addpremium user_id 1 year 1 month 1 day 1 min 10 s</code>")
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time}
        await digital_botz.add_premium(user_id, user_data)
        data = await digital_botz.get_user(user_id)
        expiry = data.get("expiry_time")
        expiry_str_in_ist = expiry.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
        await message.reply_text(f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{escape(str(time_string))}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", link_preview_options=LinkPreviewOptions(is_disabled=True))
        await client.send_message(
                chat_id=user_id,
                text=f"👋 ʜᴇʏ {user.mention},\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\nᴇɴᴊᴏʏ !! ✨🎉\n\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{escape(str(time_string))}</code>\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", link_preview_options=LinkPreviewOptions(is_disabled=True)
            )

@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(bot, message):
    if not bot.premium:
        return await message.reply_text("premium mode disabled ✅")
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await bot.get_users(user_id)
        if await digital_botz.has_premium_access(user_id):
            await digital_botz.remove_premium(user_id)
            await message.reply_text(f"ʜᴇʏ {user.mention}, ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ.")
            await bot.send_message(chat_id=user_id, text=f"<b>ʜᴇʏ {user.mention},\n\n✨ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ᴛᴏ ᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ\n\nᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʟᴀɴ ʜᴇʀᴇ /myplan</b>")
        else:
            await message.reply_text("ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ !\nᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ, ɪᴛ ᴡᴀꜱ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ɪᴅ ?")
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ : /removepremium ᴜꜱᴇʀ ɪᴅ")


@Client.on_message(filters.private & filters.command("restart") & filters.user(ADMINS))
async def restart_bot(b, m):
    rkn = await b.send_message(text="<b>🔄 ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ. ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛɪɴɢ.....</b>", chat_id=m.chat.id)
    failed = 0
    success = 0
    deactivated = 0
    blocked = 0
    start_time = time.time()
    total_users = await digital_botz.total_users_count()
    all_users = await digital_botz.get_all_users()
    async for user in all_users:
        try:
            restart_msg = f"ʜᴇʏ, {(await b.get_users(user['_id'])).mention}\n\n<b>🔄 ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ. ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛɪɴɢ.....\n\n✅️ ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛᴇᴅ. ɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴍᴇ.</b>"
            await b.send_message(user['_id'], restart_msg)
            success += 1
        except InputUserDeactivated:
            deactivated +=1
            await digital_botz.delete_user(user['_id'])
        except UserIsBlocked:
            blocked +=1
            await digital_botz.delete_user(user['_id'])
        except FloodWait as e:
            await asyncio.sleep(e.value)
            failed += 1
        except PeerIdInvalid:
            failed += 1
        except Exception:
            failed += 1
        try:
            await rkn.edit(f"<u>ʀᴇsᴛᴀʀᴛ ɪɴ ᴩʀᴏɢʀᴇꜱꜱ:</u>\n\n• ᴛᴏᴛᴀʟ ᴜsᴇʀs: {total_users}\n• sᴜᴄᴄᴇssғᴜʟ: {success}\n• ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: {blocked}\n• ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: {deactivated}\n• ᴜɴsᴜᴄᴄᴇssғᴜʟ: {failed}")
        except FloodWait as e:
            await asyncio.sleep(e.value)
    completed_restart = datetime.timedelta(seconds=int(time.time() - start_time))
    await rkn.edit(f"ᴄᴏᴍᴘʟᴇᴛᴇᴅ ʀᴇsᴛᴀʀᴛ: {completed_restart}\n\n• ᴛᴏᴛᴀʟ ᴜsᴇʀs: {total_users}\n• sᴜᴄᴄᴇssғᴜʟ: {success}\n• ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: {blocked}\n• ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: {deactivated}\n• ᴜɴsᴜᴄᴄᴇssғᴜʟ: {failed}")
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.private & filters.command("ban") & filters.user(ADMINS))
async def ban(c: Client, m: Message):
    if len(m.command) == 1:
        return await m.reply_text("Usage: <code>/ban user_id ban_duration ban_reason</code>")
    try:
        user_id = int(m.command[1])
        ban_duration = int(m.command[2])
        ban_reason = ' '.join(m.command[3:])
        await c.send_message(user_id, f"You are banned for {ban_duration} day(s). Reason: {ban_reason}")
        await digital_botz.ban_user(user_id, ban_duration, ban_reason)
        await m.reply_text(f"User {user_id} banned successfully.")
    except Exception as e:
        await m.reply_text(f"Error: {escape(str(e))}")

@Client.on_message(filters.private & filters.command("unban") & filters.user(ADMINS))
async def unban(c: Client, m: Message):
    if len(m.command) == 1:
        return await m.reply_text("Usage: <code>/unban user_id</code>")
    try:
        user_id = int(m.command[1])
        await c.send_message(user_id, "Your ban was lifted!")
        await digital_botz.remove_ban(user_id)
        await m.reply_text(f"User {user_id} unbanned successfully.")
    except Exception as e:
        await m.reply_text(f"Error: {escape(str(e))}")

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_handler(bot: Client, m: Message):
    broadcast_msg = m.reply_to_message
    sts_msg = await m.reply_text("Bʀᴏᴀᴅᴄᴀꜱᴛ Sᴛᴀʀᴛᴇᴅ..!") 
    done, success, failed = 0, 0, 0
    total_users = await digital_botz.total_users_count()
    async for user in digital_botz.get_all_users():
        try:
            await broadcast_msg.copy(chat_id=int(user['_id']))
            success += 1
        except Exception:
            failed += 1
        done += 1
        if not done % 20:
            await sts_msg.edit(f"Progress: {done}/{total_users}\nSuccess: {success}\nFailed: {failed}")
    await sts_msg.edit(f"Broadcast Completed!\nSuccess: {success}\nFailed: {failed}")
