from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatAction
from helper.utils import progress_for_pyrogram
import os, asyncio, time
import logging
import gc

logger = logging.getLogger(__name__)

# RAM CONTROL
MAX_CONCURRENT_TASKS = 2
ffmpeg_lock = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

user_audios = {}

# ==========================================
# 🧹 AUTO CLEANER TASK (Storage Saver)
# ==========================================
async def auto_clean_storage():
    while True:
        await asyncio.sleep(3600)
        try:
            folder_path = "downloads"
            if os.path.exists(folder_path):
                current_time = time.time()
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path) and current_time - os.path.getmtime(file_path) > 3600:
                        os.remove(file_path)
            gc.collect()
        except Exception as e:
            pass

# ==========================================
# 🎵 ADVANCED SINGLE AUDIO EDITOR (/edit)
# ==========================================
@Client.on_message(filters.command("edit") & filters.private)
async def advanced_single_edit(client, message):
    if not message.reply_to_message or not (message.reply_to_message.audio or message.reply_to_message.voice):
        return await message.reply_text("⚠️ **एडिट करने के लिए किसी ऑडियो या वॉइस का रिप्लाई करते हुए /edit लिखें।**")
        
    user_id = message.from_user.id
    msg = await message.reply_text("⏳ **Downloading Audio for Editing...**")
    
    if not os.path.isdir("downloads"):
        os.mkdir("downloads")
        
    try:
        file_path = await client.download_media(
            message.reply_to_message,
            file_name=f"downloads/{user_id}_edit.mp3",
            progress=progress_for_pyrogram,
            progress_args=("**📥 Downloading...**", msg, time.time())
        )
        
        user_audios[f"edit_{user_id}"] = file_path
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Bass Boost", callback_data="adv_bass"), InlineKeyboardButton("📢 Vol +50%", callback_data="adv_vol")],
            [InlineKeyboardButton("🚀 Speed Up", callback_data="adv_fast"), InlineKeyboardButton("🐢 Slow Down", callback_data="adv_slow")],
            [InlineKeyboardButton("⏪ Reverse Audio", callback_data="adv_rev")],
            [InlineKeyboardButton("🗑️ Cancel", callback_data="adv_cancel")]
        ])
        
        await msg.edit("✅ **ऑडियो रेडी है!**\n\nआप इसमें कौन सा इफ़ेक्ट (Effect) लगाना चाहते हैं?", reply_markup=buttons)
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")

# ==========================================
# 🎧 DUAL AUDIO EDITOR (/set1 & /set2)
# ==========================================
@Client.on_message(filters.command("set1") & filters.private)
async def set_audio_one(client, message):
    if not message.reply_to_message or not (message.reply_to_message.audio or message.reply_to_message.voice):
        return await message.reply_text("⚠️ **पहली ऑडियो का रिप्लाई करते हुए /set1 लिखें।**")
    
    user_id = message.from_user.id
    if user_id not in user_audios: user_audios[user_id] = {}
    msg = await message.reply_text("⏳ **Downloading Audio 1...**")
    if not os.path.isdir("downloads"): os.mkdir("downloads")
        
    try:
        file_path = await client.download_media(message.reply_to_message, file_name=f"downloads/{user_id}_1.mp3")
        user_audios[user_id]['file1'] = file_path
        await msg.edit("✅ **पहली ऑडियो सेट हो गई!**\nअब दूसरी ऑडियो का रिप्लाई करते हुए `/set2` लिखें।")
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")

@Client.on_message(filters.command("set2") & filters.private)
async def set_audio_two(client, message):
    if not message.reply_to_message or not (message.reply_to_message.audio or message.reply_to_message.voice):
        return await message.reply_text("⚠️ **दूसरी ऑडियो का रिप्लाई करते हुए /set2 लिखें।**")
        
    user_id = message.from_user.id
    if user_id not in user_audios or 'file1' not in user_audios[user_id]:
        return await message.reply_text("⚠️ **पहले /set1 करें!**")
        
    msg = await message.reply_text("⏳ **Downloading Audio 2...**")
    try:
        file_path = await client.download_media(message.reply_to_message, file_name=f"downloads/{user_id}_2.mp3")
        user_audios[user_id]['file2'] = file_path
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎙️ Voice Over (BGM)", callback_data="audio_bgm")],
            [InlineKeyboardButton("🎧 Normal Mix (50-50)", callback_data="audio_mix")],
            [InlineKeyboardButton("🔗 Join (एक के बाद एक)", callback_data="audio_join")],
            [InlineKeyboardButton("🗑️ Cancel", callback_data="audio_cancel")]
        ])
        await msg.edit("✅ **दूसरी ऑडियो भी सेट हो गई!**\nक्या करना है चुनें:", reply_markup=buttons)
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")

# ==========================================
# ⚙️ FFMPEG PROCESSING ENGINE
# ==========================================
@Client.on_callback_query(filters.regex(r"^(audio_|adv_)"))
async def audio_processing(client, callback_query):
    user_id = callback_query.from_user.id
    action = callback_query.data
    output_file = f"downloads/{user_id}_output.mp3"
    files_to_delete = [output_file]
    
    # Cancel Actions
    if action in ["audio_cancel", "adv_cancel"]:
        if action == "audio_cancel" and user_id in user_audios:
            if 'file1' in user_audios[user_id]: files_to_delete.append(user_audios[user_id]['file1'])
            if 'file2' in user_audios[user_id]: files_to_delete.append(user_audios[user_id]['file2'])
            del user_audios[user_id]
        elif action == "adv_cancel" and f"edit_{user_id}" in user_audios:
            files_to_delete.append(user_audios[f"edit_{user_id}"])
            del user_audios[f"edit_{user_id}"]
            
        for f in files_to_delete:
            if os.path.exists(f): os.remove(f)
        return await callback_query.message.edit("❌ **प्रोसेस कैंसल कर दिया गया है।**")

    await callback_query.message.edit("⚙️ **Advanced Processing Started...**\n*(Please wait...)*")
    
    async with ffmpeg_lock:
        await client.send_chat_action(chat_id=user_id, action=ChatAction.RECORD_AUDIO)
        try:
            cmd = ""
            # --- Single Audio Effects ---
            if action.startswith("adv_"):
                if f"edit_{user_id}" not in user_audios: return await callback_query.message.edit("⚠️ **डेटा एक्सपायर हो गया। फिर से /edit करें।**")
                file1 = user_audios[f"edit_{user_id}"]
                files_to_delete.append(file1)
                
                if action == "adv_bass":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -af "bass=g=15:f=110:w=0.6" -c:a libmp3lame -q:a 2 "{output_file}"'
                elif action == "adv_vol":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -af "volume=1.5" -c:a libmp3lame -q:a 2 "{output_file}"'
                elif action == "adv_fast":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -af "atempo=1.5" -c:a libmp3lame -q:a 2 "{output_file}"'
                elif action == "adv_slow":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -af "atempo=0.75" -c:a libmp3lame -q:a 2 "{output_file}"'
                elif action == "adv_rev":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -af "areverse" -c:a libmp3lame -q:a 2 "{output_file}"'

            # --- Dual Audio Effects ---
            elif action.startswith("audio_"):
                if user_id not in user_audios or 'file2' not in user_audios[user_id]: return await callback_query.message.edit("⚠️ **डेटा नहीं मिला! फिर से /set1 करें।**")
                file1 = user_audios[user_id]['file1']
                file2 = user_audios[user_id]['file2']
                files_to_delete.extend([file1, file2])
                
                if action == "audio_mix":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -i "{file2}" -filter_complex "amix=inputs=2:duration=longest" -c:a libmp3lame -q:a 2 "{output_file}"'
                elif action == "audio_bgm":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -i "{file2}" -filter_complex "[1:a]volume=0.2[a1];[0:a][a1]amix=inputs=2:duration=first" -c:a libmp3lame -q:a 2 "{output_file}"'
                elif action == "audio_join":
                    cmd = f'ffmpeg -threads 1 -y -i "{file1}" -i "{file2}" -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1" -c:a libmp3lame -q:a 2 "{output_file}"'
                
            process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await process.communicate()
            
            if os.path.exists(output_file):
                await callback_query.message.edit("📤 **Uploading your Masterpiece...**")
                await client.send_audio(
                    chat_id=user_id,
                    audio=output_file,
                    caption="✅ **Aᴅᴠᴀɴᴄᴇᴅ Aᴜᴅɪᴏ Eᴅɪᴛɪɴɢ Sᴜᴄᴄᴇssғᴜʟ!**",
                    title="Studio_Edited_Audio",
                    performer=callback_query.from_user.first_name
                )
                await callback_query.message.delete()
            else:
                await callback_query.message.edit("⚠️ **FFmpeg Error:** ऑडियो प्रोसेस नहीं हो पाई।")
                
        except Exception as e:
            await callback_query.message.edit(f"❌ **System Error:** `{e}`")
        finally:
            for f in files_to_delete:
                if os.path.exists(f):
                    try: os.remove(f)
                    except: pass
            if action.startswith("adv_") and f"edit_{user_id}" in user_audios: del user_audios[f"edit_{user_id}"]
            if action.startswith("audio_") and user_id in user_audios: del user_audios[user_id]
            gc.collect()

asyncio.get_event_loop().create_task(auto_clean_storage())
