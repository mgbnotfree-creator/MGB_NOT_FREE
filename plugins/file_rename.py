from pyrogram import Client, filters
from pyrogram.enums import ButtonStyle, MessageMediaType, ParseMode
from pyrogram.errors import FloodWait
from pyrogram.file_id import FileId
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix, remove_path
from helper.database import digital_botz
from helper.ffmpeg import change_metadata, get_duration
from config import Config, rkn
import os, time, asyncio, re
from html import escape
import logging

UPLOAD_TEXT = """Uploading Started...."""
DOWNLOAD_TEXT = """Download Started..."""

logger = logging.getLogger(__name__)

app = Client("4gb_FileRenameBot", api_id=Config.API_ID, api_hash=Config.API_HASH, session_string=Config.STRING_SESSION, parse_mode=ParseMode.HTML)

async def upload_files(bot, sender_id, upload_type, file_path, ph_path, caption, duration, rkn_processing):
    try:
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
        if upload_type == "document":
            filw = await bot.send_document(sender_id, document=file_path, thumb=ph_path, caption=caption, progress=progress_for_pyrogram, progress_args=(UPLOAD_TEXT, rkn_processing, time.time()))
        elif upload_type == "video":
            filw = await bot.send_video(sender_id, video=file_path, caption=caption, thumb=ph_path, duration=duration, progress=progress_for_pyrogram, progress_args=(UPLOAD_TEXT, rkn_processing, time.time()))
        elif upload_type == "audio":
            filw = await bot.send_audio(sender_id, audio=file_path, caption=caption, thumb=ph_path, duration=duration, progress=progress_for_pyrogram, progress_args=(UPLOAD_TEXT, rkn_processing, time.time()))
        else:
            return None, f"Unknown upload type: {upload_type}"
        return filw, None
    except Exception as e:
        return None, str(e)

@Client.on_message(filters.private & (filters.audio | filters.document | filters.video))
async def auto_rename_start(bot, message):
    user_id = message.from_user.id
    
    # 100% FIXED: यहाँ फाइल भेजने वाले यूजर का असली नाम (Telegram Name) निकाला जा रहा है
    first_name = message.from_user.first_name or "Unknown"
    last_name = message.from_user.last_name or ""
    sender_name = f"{first_name} {last_name}".strip()
    
    rkn_processing = await message.reply_text("<code>Processing...</code>")
    
    # --- DAILY FILE COUNT LIMIT CHECK ---
    user_data = await digital_botz.get_user_data(user_id)
    if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
        is_premium = await digital_botz.has_premium_access(user_id)
        
        max_limit = user_data.get('uploadlimit', 50) if is_premium else 5
        used = user_data.get('used_limit', 0) if user_data else 0
        
        if used > 5000:
            used = 0
            await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": 0}})
        
        if used >= max_limit:
            plan_type = user_data.get('usertype', 'Paid') if is_premium else 'Free'
            await rkn_processing.delete()
            return await message.reply_text(
                f"❌ <b>Dᴀɪʟʏ Uᴘʟᴏᴀᴅ Lɪᴍɪᴛ Rᴇᴀᴄʜᴇᴅ!</b>\n\n"
                f"• Yᴏᴜʀ Pʟᴀɴ: <b>{plan_type} ({max_limit} Files/Day)</b>\n"
                f"• Tᴏᴅᴀʏ's Uꜱᴀɢᴇ: <b>{used}/{max_limit} files</b>\n\n"
                f"Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴛᴏᴍᴏʀʀᴏᴡ ᴏʀ ᴜᴘɢʀᴀᴅᴇ ʏᴏᴜʀ ᴘʟᴀɴ.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🪪 Uᴘɢʀᴀᴅᴇ Pʟᴀɴꜱ", callback_data="plans", style=ButtonStyle.SUCCESS)]])
            )

    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    # --- DETERMINE FILE NAME & PREFIX/SUFFIX ---
    rkn_file = getattr(message, message.media.value)
    filename = getattr(rkn_file, "file_name", "file.mkv")
    new_name = filename.replace("\\", "/").split("/")[-1]
    
    try:
        prefix = user_data.get('prefix', None)
        suffix = user_data.get('suffix', None)
        new_filename = await add_prefix_suffix(new_name, prefix, suffix)
    except Exception as e:
        return await rkn_processing.edit(f"⚠️ Error in Prefix/Suffix: {escape(str(e))}")

    # --- AUTO DETECT UPLOAD TYPE ---
    if message.media == MessageMediaType.VIDEO:
        upload_type = "video"
    elif message.media == MessageMediaType.AUDIO:
        upload_type = "audio"
    else:
        upload_type = "document"

    file_path = f"Renames/{new_filename}"
    metadata_path = f"Metadata/{new_filename}"
    await rkn_processing.edit("<code>Try To Download....</code>")
    
    if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
        total_used = int(used) + 1
        await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": total_used}}, upsert=True)
        
    try:            
        dl_path = await bot.download_media(message=message, file_name=file_path, progress=progress_for_pyrogram, progress_args=(DOWNLOAD_TEXT, rkn_processing, time.time()))                    
    except Exception as e:
        if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
            used_remove = max(0, int(used))
            await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": used_remove}})
        return await rkn_processing.edit(f"Download Error: {escape(str(e))}")

    # --- AUTO ARTIST / METADATA INJECTION (USER'S OWN NAME) ---
    metadata_mode = True  
    metadata = await digital_botz.get_metadata_code(user_id)
    
    # यहाँ आर्टिस्ट की जगह उस यूज़र का नाम फिक्स किया गया है जो फाइल भेज रहा है
    custom_artist = sender_name
    
    if metadata:
        if "--change-author" not in metadata:
            metadata += f"\n--change-author {custom_artist}"
    else:
        metadata = f"--change-author {custom_artist}"

    await rkn_processing.edit("<b><i>Pʟᴇᴀsᴇ Wᴀɪᴛ...</i></b>\n<b>Aᴅᴅɪɴɢ Aʀᴛɪsᴛ & Mᴇᴛᴀᴅᴀᴛᴀ Tᴏ Fɪʟᴇ....</b>")            
    if await change_metadata(dl_path, metadata_path, metadata):            
        await rkn_processing.edit("Metadata & Artist Added.....")
    else:
        metadata_mode = False

    duration = await get_duration(file_path if os.path.exists(file_path) else dl_path)
    ph_path = None
    c_caption = user_data.get('caption', None)
    c_thumb = user_data.get('file_id', None)
    
    if c_caption:
         try:
             caption = c_caption.format(filename=escape(str(new_filename)), filesize=escape(humanbytes(rkn_file.file_size)), duration=escape(str(convert(duration))))
         except Exception as e:
             if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
                 await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": int(used)}})
             return await rkn_processing.edit(text=f"Caption Error: {escape(str(e))}")             
    else:
         caption = f"<b>{escape(str(new_filename))}</b>"
         
    if (rkn_file.thumbs or c_thumb):
         try:
             if c_thumb:
                 ph_path = await bot.download_media(c_thumb) 
             else:
                 ph_path = await bot.download_media(rkn_file.thumbs[0].file_id)
             if ph_path and os.path.exists(ph_path):
                 with Image.open(ph_path) as img:
                     img.convert("RGB").resize((320, 320), Image.Resampling.LANCZOS).save(ph_path, "JPEG")
         except Exception as e:
             ph_path = None

    final_file_path = metadata_path if metadata_mode and os.path.exists(metadata_path) else file_path
    
    if rkn_file.file_size > 2000 * 1024 * 1024:
        filw, error = await upload_files(app, Config.LOG_CHANNEL, upload_type, final_file_path, ph_path, caption, duration, rkn_processing)
        if error:
            if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
                await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": int(used)}})
            await remove_path(ph_path, file_path, dl_path, metadata_path)
            return await rkn_processing.edit(f"Upload Error: {escape(str(error))}")
        from_chat = filw.chat.id
        mg_id = filw.id
        if Config.BIN_CHANNEL:
            try:
                await bot.copy_message(chat_id=Config.BIN_CHANNEL, from_chat_id=from_chat, message_id=mg_id)
            except Exception:
                pass
        await asyncio.sleep(2)
        await bot.copy_message(message.from_user.id, from_chat, mg_id)
        await bot.delete_messages(from_chat, mg_id)
    else:
        filw, error = await upload_files(bot, message.chat.id, upload_type, final_file_path, ph_path, caption, duration, rkn_processing)
        if error:
            if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
                await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": int(used)}})
            await remove_path(ph_path, file_path, dl_path, metadata_path)
            return await rkn_processing.edit(f"Upload Error: {escape(str(error))}")
        if Config.BIN_CHANNEL:
            try:
                await bot.copy_message(chat_id=Config.BIN_CHANNEL, from_chat_id=filw.chat.id, message_id=filw.id)
            except Exception:
                pass
                
    await remove_path(ph_path, file_path, dl_path, metadata_path)
    return await rkn_processing.edit("Uploaded Successfully....")
