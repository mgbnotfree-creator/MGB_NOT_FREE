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

ADMINS = [8853897167]
 
@Client.on_message(filters.command("status") & filters.user(ADMINS))
async def get_stats(bot, message):
    total_users = await digital_botz.total_users_count()
    if getattr(bot, "premium", True):
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

@Client.on_message(filters.private & filters.command("givepro"))
async def add_premium(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("❌ <b>Aap is command ko use nahi kar sakte! Yeh sirf Admin ke liye hai.</b>")

    try:
        if len(message.command) < 4:
            return await message.reply_text("<b>Usage :</b>\n<code>/givepro user_id Pro 1 month</code>\n<i>or</i>\n<code>/givepro user_id UltraPro 1 month</code>")
        
        # 100% FIXED: Integer User ID and Case-Insensitive Plan Check
        user_id = int(message.command[1].strip())
        plan_type_input = message.command[2].lower().strip()
        
        if plan_type_input == "pro":
            limit = 50  # Pro: 50 files per day
            p_type = "Pro"
        elif plan_type_input in ["ultrapro", "ultra"]:
            limit = 100 # UltraPro: 100 files per day
            p_type = "UltraPro"
        else:
            return await message.reply_text("❌ Invalid Plan Type. Please use <code>Pro</code> or <code>UltraPro</code>.")
        
        time_string = " ".join(message.command[3:])
        time_zone = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")
        
        try:
            user = await client.get_users(user_id)
            mention = user.mention
        except Exception:
            mention = f"User {user_id}"

        seconds = await get_seconds(time_string)
        if seconds <= 0:
            return await message.reply_text("❌ Invalid time format! Use e.g., <code>1 month</code>, <code>7 days</code>")
        
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        
        # 100% FIXED: Yahan error-free MongoDB update logic lagaya gaya hai
        await digital_botz.col.update_one(
            {"_id": user_id},
            {"$set": {
                "expiry_time": expiry_time,
                "uploadlimit": limit,
                "usertype": p_type
            }},
            upsert=True
        )
        
        expiry_str_in_ist = expiry_time.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
        
        msg_text = (
            f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n"
            f"👤 ᴜꜱᴇʀ : {mention}\n"
            f"⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n"
            f"ᴘʟᴀɴ :- <code>{p_type}</code>\n"
            f"📊 ᴅᴀɪʟʏ ʟɪᴍɪᴛ :- <code>{limit} Files/Day</code>\n"
            f"⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{escape(str(time_string))}</code>\n\n"
            f"⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n"
            f"⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}"
        )
        
        await message.reply_text(msg_text, link_preview_options=LinkPreviewOptions(is_disabled=True))
        
        try:
            user_msg = (
                f"👋 ʜᴇʏ {mention},\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\nᴇɴᴊᴏʏ !! ✨🎉\n\n"
                f"⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{escape(str(time_string))}</code>\n"
                f"ᴘʟᴀɴ :- <code>{p_type}</code>\n"
                f"📊 ᴅᴀɪʟʏ ʟɪᴍɪᴛ :- <code>{limit} Files/Day</code>\n"
                f"⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n"
                f"⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}"
            )
            await client.send_message(chat_id=user_id, text=user_msg, link_preview_options=LinkPreviewOptions(is_disabled=True))
        except Exception:
            pass

    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b>\n<code>{escape(str(e))}</code>")

@Client.on_message(filters.command("removepremium") & filters.user(ADMINS))
async def remove_premium(bot, message):
    if len(message.command) == 2:
        user_id = int(message.command[1].strip())
        try:
            user = await bot.get_users(user_id)
            mention = user.mention
        except Exception:
            mention = f"User {user_id}"
        
        # FIXED: remove premium par free limit (5) set ki gai hai taaki user block na ho
        await digital_botz.col.update_one(
            {"_id": user_id},
            {"$set": {
                "expiry_time": None,
                "uploadlimit": 5, 
                "usertype": "Free"
            }}
        )
        
        await message.reply_text(f"ʜᴇʏ {mention}, ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ.")
        try:
            await bot.send_message(chat_id=user_id, text=f"<b>ʜᴇʏ {mention},\n\n✨ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ᴛᴏ ᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ\n\nᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʟᴀɴ ʜᴇʀᴇ /myplan</b>")
        except Exception:
            pass
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ : /removepremium ᴜꜱᴇʀ ɪᴅ")

@Client.on_message(filters.private & filters.command("restart") & filters.user(ADMINS))
async def restart_bot(b, m):
    rkn = await b.send_message(text="<b>🔄 ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ. ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛɪɴɢ.....</b>", chat_id=m.chat.id)
    os.execl(sys.executable, sys.executable, *sys.argv)
 
