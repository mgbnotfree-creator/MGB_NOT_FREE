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

@Client.on_message(filters.private & (filters.audio | filters.document | filters.video))
async def rename_start(client, message):
    user_id  = message.from_user.id
    rkn_file = getattr(message, message.media.value)
    filename = getattr(rkn_file, "file_name", "file.mkv")

    # --- DAILY FILE COUNT LIMIT CHECK ---
    user_data = await digital_botz.get_user_data(user_id)
    if getattr(client, "premium", True) and getattr(client, "uploadlimit", True):
        is_premium = await digital_botz.has_premium_access(user_id)
        
        # Fetching precise limit from database (5 for free, 50/100 for premium)
        max_limit = user_data.get('uploadlimit', 50) if is_premium else 5
        used_count = user_data.get('used_limit', 0) if user_data else 0
        
        # 100% FIXED: Agar database me purana byte size (jaise 38588947) hai, to use reset kar do
        if used_count > 5000:
            used_count = 0
            await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": 0}})
        
        if used_count >= max_limit:
            plan_type = user_data.get('usertype', 'Paid') if is_premium else 'Free'
            return await message.reply_text(
                f"❌ <b>Dᴀɪʟʏ Uᴘʟᴏᴀᴅ Lɪᴍɪᴛ Rᴇᴀᴄʜᴇᴅ!</b>\n\n"
                f"• Yᴏᴜʀ Pʟᴀɴ: <b>{plan_type} ({max_limit} Files/Day)</b>\n"
                f"• Tᴏᴅᴀʏ's Uꜱᴀɢᴇ: <b>{used_count}/{max_limit} files</b>\n\n"
                f"Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴛᴏᴍᴏʀʀᴏᴡ ᴏʀ ᴜᴘɢʀᴀᴅᴇ ʏᴏᴜʀ ᴘʟᴀɴ.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🪪 Uᴘɢʀᴀᴅᴇ Pʟᴀɴꜱ", callback_data="plans", style=ButtonStyle.SUCCESS)]])
            )

    # --- FULLY AUTOMATIC DEFAULT NAME FLOW (No Command / No Manual Typing Needed) ---
    new_name = filename or "file.mkv"
    new_name = new_name.replace("\\", "/").split("/")[-1]
    
    button = [[InlineKeyboardButton("📁 Dᴏᴄᴜᴍᴇɴᴛ", callback_data = "upload#document", style=ButtonStyle.PRIMARY)]]
    if message.media == MessageMediaType.VIDEO:
        button.append([InlineKeyboardButton("🎥 Vɪᴅᴇᴏ", callback_data = "upload#video", style=ButtonStyle.PRIMARY)])
    elif message.media == MessageMediaType.AUDIO:
        button.append([InlineKeyboardButton("🎵 Aᴜᴅɪᴏ", callback_data = "upload#audio", style=ButtonStyle.PRIMARY)])
    elif message.media == MessageMediaType.DOCUMENT:
        button.append([InlineKeyboardButton("🎥 Vɪᴅᴇᴏ", callback_data = "upload#video", style=ButtonStyle.PRIMARY)])
            
    await message.reply_text(
        text=f"<b>Fɪʟᴇ Dᴇᴛᴇᴄᴛᴇᴅ!</b>\n<b>• Dᴇꜰᴀᴜʟᴛ Nᴀᴍᴇ :-</b><code>{escape(str(new_name))}</code>\n\n<b>Sᴇʟᴇᴄᴛ Tʜᴇ Oᴜᴛᴩᴜᴛ Tyᴩᴇ 👇</b>",
        reply_markup=InlineKeyboardMarkup(button)
    )

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

@Client.on_callback_query(filters.regex("upload#"), group=-5)
async def upload_doc(bot, update):
    await update.answer()
    rkn_processing = await update.message.edit("<code>Processing...</code>")
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
    user_id = int(update.message.chat.id) 
    
    text_content = update.message.text
    if "Dᴇꜰᴀᴜʟᴛ Nᴀᴍᴇ :-" in text_content:
        new_filename_ = text_content.split("Dᴇꜰᴀᴜʟᴛ Nᴀᴍᴇ :-")[1].split("\n")[0].strip()
    elif "Fɪʟᴇ Nᴀᴍᴇ :-" in text_content:
        new_filename_ = text_content.split("Fɪʟᴇ Nᴀᴍᴇ :-")[1].split("\n")[0].strip()
    elif ":-" in text_content:
        new_filename_ = text_content.split(":-")[1].split("\n")[0].strip()
    else:
        new_filename_ = "file.mkv"

    user_data = await digital_botz.get_user_data(user_id)
    try:
        prefix = user_data.get('prefix', None)
        suffix = user_data.get('suffix', None)
        new_filename = await add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await rkn_processing.edit(f"⚠️ Error in Prefix/Suffix: {escape(str(e))}")
    
    file = update.message.reply_to_message
    if not file or not file.media:
        return await rkn_processing.edit("⚠️ Original file missing.")
        
    media = getattr(file, file.media.value)
    file_path = f"Renames/{new_filename}"
    metadata_path = f"Metadata/{new_filename}"
    await rkn_processing.edit("<code>Try To Download....</code>")
    
    # +1 Count Logic fixed to avoid crash with DB
    used = user_data.get('used_limit', 0) if user_data else 0
    if used > 5000:
        used = 0
    
    if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
        total_used = int(used) + 1
        await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": total_used}}, upsert=True)
        
    try:            
        dl_path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=(DOWNLOAD_TEXT, rkn_processing, time.time()))                    
    except Exception as e:
        if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
            used_remove = max(0, int(used))
            await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": used_remove}})
        return await rkn_processing.edit(f"Download Error: {escape(str(e))}")

    metadata_mode = True  
    metadata = await digital_botz.get_metadata_code(user_id)
    if metadata:
        if "--change-author" not in metadata:
            metadata += "\n--change-author @Digital_Botz"
    else:
        metadata = "--change-author @Digital_Botz"

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
             caption = c_caption.format(filename=escape(str(new_filename)), filesize=escape(humanbytes(media.file_size)), duration=escape(str(convert(duration))))
         except Exception as e:
             if getattr(bot, "premium", True) and getattr(bot, "uploadlimit", True):
                 await digital_botz.col.update_one({"_id": user_id}, {"$set": {"used_limit": int(used)}})
             return await rkn_processing.edit(text=f"Caption Error: {escape(str(e))}")             
    else:
         caption = f"<b>{escape(str(new_filename))}</b>\n\n<b>User:</b> {escape(str(update.from_user.first_name))}\n<b>User ID:</b> <code>{user_id}</code>"
         
    if (media.thumbs or c_thumb):
         try:
             if c_thumb:
                 ph_path = await bot.download_media(c_thumb) 
             else:
                 ph_path = await bot.download_media(media.thumbs[0].file_id)
             if ph_path and os.path.exists(ph_path):
                 with Image.open(ph_path) as img:
                     img.convert("RGB").resize((320, 320), Image.Resampling.LANCZOS).save(ph_path, "JPEG")
         except Exception as e:
             ph_path = None

    upload_type = update.data.split("#")[1]
    final_file_path = metadata_path if metadata_mode and os.path.exists(metadata_path) else file_path
    
    if media.file_size > 2000 * 1024 * 1024:
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
        await bot.copy_message(update.from_user.id, from_chat, mg_id)
        await bot.delete_messages(from_chat, mg_id)
    else:
        filw, error = await upload_files(bot, update.message.chat.id, upload_type, final_file_path, ph_path, caption, duration, rkn_processing)
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
        
