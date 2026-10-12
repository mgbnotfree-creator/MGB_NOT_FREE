import asyncio, datetime, time, psutil
from html import escape
from pyrogram.enums import ButtonStyle
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, CallbackQuery
from helper.database import digital_botz
from helper.speedtest import network_speed_label
from config import Config, rkn
from helper.utils import humanbytes
from plugins import __version__ as _bot_version_, __developer__, __database__, __library__, __language__, __programer__
from plugins.web_support import get_status

upgrade_button = InlineKeyboardMarkup([[        
        InlineKeyboardButton('💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ✓', user_id=int(Config.ADMIN), style=ButtonStyle.SUCCESS),
         ],[
        InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="start", style=ButtonStyle.DANGER)
]])

upgrade_trial_button = InlineKeyboardMarkup([[        
        InlineKeyboardButton('💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ✓', user_id=int(Config.ADMIN), style=ButtonStyle.SUCCESS),
         ],[
        InlineKeyboardButton("⏳ ᴛʀɪᴀʟ", callback_data="give_trial", style=ButtonStyle.PRIMARY),
        InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="start", style=ButtonStyle.DANGER)
]])

async def upgrade_view(client, user):
    text = rkn.UPGRADE_PLAN.format(user.mention) if client.uploadlimit else rkn.UPGRADE_PREMIUM.format(user.mention)
    premium = await digital_botz.premium_state(user.id)
    if not premium["has_premium_access"] and not premium["has_free_trial"]:
        return text, upgrade_trial_button
    return text, upgrade_button

# 🌈 COLORFUL START MENU BUILDER
def get_start_buttons(client):
    buttons = [
        [
            InlineKeyboardButton('⛩ ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ ⛩', url=f"http://t.me/{client.me.username}?startgroup=true", style=ButtonStyle.DANGER)
        ],
        [
            InlineKeyboardButton('🍬 ꜱᴜᴘᴘᴏʀᴛ 🍬', url='https://t.me/mgbnotfree_creator', style=ButtonStyle.PRIMARY),
            InlineKeyboardButton('🍹 ᴜᴘᴅᴀᴛᴇꜱ 🍹', url='https://t.me/mgbnotfree_creator', style=ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton('🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ 🏩', callback_data='help', style=ButtonStyle.SUCCESS)
        ],
        [
            InlineKeyboardButton('🫧 ᴀʙᴏᴜᴛ ᴍᴇ 🫧', callback_data='about', style=ButtonStyle.PRIMARY),
            InlineKeyboardButton('🪼 ᴏᴡɴᴇʀ 🪼', url='https://t.me/mgbnotfree_creator', style=ButtonStyle.PRIMARY)
        ]
    ]
    if client.premium:
        buttons.append([InlineKeyboardButton('💎 ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ 💎', callback_data='upgrade', style=ButtonStyle.SUCCESS)])
    return buttons

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    start_button = get_start_buttons(client)
    if Config.PIC:
        await message.reply_photo(Config.PIC, caption=rkn.START_TXT.format(user.mention), reply_markup=InlineKeyboardMarkup(start_button))    
    else:
        await message.reply_text(text=rkn.START_TXT.format(user.mention), reply_markup=InlineKeyboardMarkup(start_button), link_preview_options=LinkPreviewOptions(is_disabled=True))

@Client.on_message(filters.private & filters.command('setprefix'))
async def add_prefix(client, message):
    if len(message.command) == 1:
        return await message.reply_text("<b><i>Give The Prefix</i>\n\nExᴀᴍᴩʟᴇ:- <code>/setprefix @mgbnotfree_creator</code></b>")
    prefix = message.text.split(" ", 1)[1]
    RknDev = await message.reply_text("Please Wait ...")
    await digital_botz.set_prefix(message.from_user.id, prefix)
    await RknDev.edit("<b><i>✅ ᴘʀᴇꜰɪx ꜱᴀᴠᴇᴅ</i></b>")

@Client.on_message(filters.private & filters.command('delprefix'))
async def delete_prefix(client, message):
    RknDev = await message.reply_text("Please Wait ...")
    prefix = await digital_botz.get_prefix(message.from_user.id)
    if not prefix:
        return await RknDev.edit("<b><i>😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴘʀᴇꜰɪx</i></b>")
    await digital_botz.set_prefix(message.from_user.id, None)
    await RknDev.edit("<b><i>❌️ ᴘʀᴇꜰɪx ᴅᴇʟᴇᴛᴇᴅ</i></b>")

@Client.on_message(filters.private & filters.command('seeprefix'))
async def see_prefix(client, message):
    RknDev = await message.reply_text("Please Wait ...")
    prefix = await digital_botz.get_prefix(message.from_user.id)
    if prefix:
        await RknDev.edit(f"<b>ʏᴏᴜʀ ᴘʀᴇꜰɪx:-</b>\n\n<code>{escape(str(prefix))}</code>")
    else:
        await RknDev.edit("<b><i>😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴘʀᴇꜰɪx</i></b>")

@Client.on_message(filters.private & filters.command('setsuffix'))
async def add_suffix(client, message):
    if len(message.command) == 1:
        return await message.reply_text("<b><i>Give The Suffix</i>\n\nExᴀᴍᴩʟᴇ:- <code>/setsuffix @mgbnotfree_creator</code></b>")
    suffix = message.text.split(" ", 1)[1]
    RknDev = await message.reply_text("Please Wait ...")
    await digital_botz.set_suffix(message.from_user.id, suffix)
    await RknDev.edit("<b><i>✅ ꜱᴜꜰꜰɪx ꜱᴀᴠᴇᴅ</i></b>")

@Client.on_message(filters.private & filters.command('delsuffix'))
async def delete_suffix(client, message):
    RknDev = await message.reply_text("Please Wait ...")
    suffix = await digital_botz.get_suffix(message.from_user.id)
    if not suffix:
        return await RknDev.edit("<b><i>😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜꜰꜰɪx</i></b>")
    await digital_botz.set_suffix(message.from_user.id, None)
    await RknDev.edit("<b><i>❌️ ꜱᴜꜰꜰɪx ᴅᴇʟᴇᴛᴇᴅ</i></b>")

@Client.on_message(filters.private & filters.command('seesuffix'))
async def see_suffix(client, message):
    RknDev = await message.reply_text("Please Wait ...")
    suffix = await digital_botz.get_suffix(message.from_user.id)
    if suffix:
        await RknDev.edit(f"<b>ʏᴏᴜʀ ꜱᴜꜰꜰɪx:-</b>\n\n<code>{escape(str(suffix))}</code>")
    else:
        await RknDev.edit("<b><i>😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜꜰꜰɪx</i></b>")

@Client.on_message(filters.private & filters.command('setcaption'))
async def add_caption(client, message):
    rkn = await message.reply_text("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</i></b>")
    if len(message.command) == 1:
       return await rkn.edit("<b><i>Gɪᴠᴇ Tʜᴇ Cᴀᴩᴛɪᴏɴ</i>\n\nExᴀᴍᴩʟᴇ:- <code>/setcaption {filename}\n\n💾 Sɪᴢᴇ: {filesize}\n\n⏰ Dᴜʀᴀᴛɪᴏɴ: {duration}</code>\n<b>By: @mgbnotfree_creator</b>")
    caption = message.text.split(" ", 1)[1]
    await digital_botz.set_caption(message.from_user.id, caption=caption)
    await rkn.edit("<b><i>✅ Cᴀᴩᴛɪᴏɴ Sᴀᴠᴇᴅ</i></b>")
   
@Client.on_message(filters.private & filters.command('delcaption'))
async def delete_caption(client, message):
    rkn = await message.reply_text("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</i></b>")
    caption = await digital_botz.get_caption(message.from_user.id)  
    if not caption:
       return await rkn.edit("<b><i>😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Cᴀᴩᴛɪᴏɴ</i></b>")
    await digital_botz.set_caption(message.from_user.id, caption=None)
    await rkn.edit("<b><i>❌️ Cᴀᴩᴛɪᴏɴ Dᴇʟᴇᴛᴇᴅ</i></b>")
                                       
@Client.on_message(filters.private & filters.command('seecaption'))
async def see_caption(client, message):
    rkn = await message.reply_text("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</i></b>")
    caption = await digital_botz.get_caption(message.from_user.id)  
    if caption:
       await rkn.edit(f"<b>Yᴏᴜ'ʀᴇ Cᴀᴩᴛɪᴏɴ:-</b>\n\n<code>{escape(str(caption))}</code>")
    else:
       await rkn.edit("<b><i>😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Cᴀᴩᴛɪᴏɴ</i></b>")

@Client.on_message(filters.private & filters.command('viewthumb'))
async def viewthumb(client, message):
    rkn = await message.reply_text("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</i></b>")
    thumb = await digital_botz.get_thumbnail(message.from_user.id)
    if thumb:
        await client.send_photo(chat_id=message.chat.id, photo=thumb)
        await rkn.delete()
    else:
        await rkn.edit("😔 <b><i>Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Tʜᴜᴍʙɴᴀɪʟ</i></b>") 
		
@Client.on_message(filters.private & filters.command('delthumb'))
async def removethumb(client, message):
    rkn = await message.reply_text("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</i></b>")
    thumb = await digital_botz.get_thumbnail(message.from_user.id)
    if thumb:
        await digital_botz.set_thumbnail(message.from_user.id, file_id=None)
        await rkn.edit("❌️ <b><i>Tʜᴜᴍʙɴᴀɪʟ Dᴇʟᴇᴛᴇᴅ</i></b>")
        return
    await rkn.edit("😔 <b><i>Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Tʜᴜᴍʙɴᴀɪʟ</i></b>")

@Client.on_message(filters.private & filters.photo)
async def addthumbs(client, message):
    rkn = await message.reply_text("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</i></b>")
    await digital_botz.set_thumbnail(message.from_user.id, file_id=message.photo.file_id)                
    await rkn.edit("✅️ <b><i>Tʜᴜᴍʙɴᴀɪʟ Sᴀᴠᴇᴅ</i></b>")

@Client.on_message(filters.private & filters.command("myplan"))
async def myplan(client, message):
    if not client.premium:
        return 
    user_id = message.from_user.id
    user = message.from_user.mention
    premium = await digital_botz.premium_state(user_id)
    if premium["has_premium_access"]:
        data = await digital_botz.get_user(user_id)
        expiry_str_in_ist = data.get("expiry_time")
        time_left_str = expiry_str_in_ist - datetime.datetime.now()
        text = f"ᴜꜱᴇʀ :- {user}\nᴜꜱᴇʀ ɪᴅ :- <code>{user_id}</code>\n"
        if client.uploadlimit:
            user_data = await digital_botz.reset_uploadlimit_access(user_id)
            limit = user_data.get('uploadlimit', 0)
            used = user_data.get('used_limit', 0)
            remain = int(limit) - int(used)
            type = user_data.get('usertype', "Free")
            text += f"ᴘʟᴀɴ :- <code>{escape(str(type))}</code>\nᴅᴀɪʟʏ ᴜᴘʟᴏᴀᴅ ʟɪᴍɪᴛ :- <code>{humanbytes(limit)}</code>\nᴛᴏᴅᴀʏ ᴜsᴇᴅ :- <code>{humanbytes(used)}</code>\nʀᴇᴍᴀɪɴ :- <code>{humanbytes(remain)}</code>\n"
        text += f"ᴛɪᴍᴇ ʟᴇꜰᴛ : {time_left_str}\nᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}"
        await message.reply_text(text)
    else:
        if client.uploadlimit:
            user_data = await digital_botz.get_user_data(user_id)
            limit = user_data.get('uploadlimit', 0)
            used = user_data.get('used_limit', 0)
            remain = int(limit) - int(used)
            type = user_data.get('usertype', "Free")
            text = f"ᴜꜱᴇʀ :- {user}\nᴜꜱᴇʀ ɪᴅ :- <code>{user_id}</code>\nᴘʟᴀɴ :- <code>{escape(str(type))}</code>\nᴅᴀɪʟʏ ᴜᴘʟᴏᴀᴅ ʟɪᴍɪᴛ :- <code>{humanbytes(limit)}</code>\nᴛᴏᴅᴀʏ ᴜsᴇᴅ :- <code>{humanbytes(used)}</code>\nʀᴇᴍᴀɪɴ :- <code>{humanbytes(remain)}</code>\nᴇxᴘɪʀᴇᴅ ᴅᴀᴛᴇ :- ʟɪғᴇᴛɪᴍᴇ\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴛᴀᴋᴇ ᴘʀᴇᴍɪᴜᴍ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ 👇"
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 💸", callback_data='upgrade', style=ButtonStyle.SUCCESS)]]))
        else:
            m=await message.reply_sticker("CAACAgIAAxkBAAIBTGVjQbHuhOiboQsDm35brLGyLQ28AAJ-GgACglXYSXgCrotQHjibHgQ")
            await message.reply_text(f"ʜᴇʏ {user},\n\nʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴀɴʏ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs, ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴛᴀᴋᴇ ᴘʀᴇᴍɪᴜᴍ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ 👇",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 💸", callback_data='upgrade', style=ButtonStyle.SUCCESS)]]))			 
            await asyncio.sleep(2)
            await m.delete()

@Client.on_message(filters.private & filters.command("plans"))
async def plans(client, message):
    if not client.premium:
        return 
    text, markup = await upgrade_view(client, message.from_user)
    await message.reply_text(text=text, reply_markup=markup, link_preview_options=LinkPreviewOptions(is_disabled=True))

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    try:
        await query.answer()
    except Exception:
        pass 
    if data == "start":
        start_button = get_start_buttons(client)
        await query.message.edit_text(
            text=rkn.START_TXT.format(query.from_user.mention),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup = InlineKeyboardMarkup(start_button))
        
    elif data == "help":
        await query.message.edit_text(
            text=rkn.HELP_TXT,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🖼️ ᴛʜᴜᴍʙɴᴀɪʟ", callback_data="thumbnail", style=ButtonStyle.PRIMARY),
                InlineKeyboardButton("📝 ᴄᴀᴘᴛɪᴏɴ", callback_data="caption", style=ButtonStyle.PRIMARY)
                ],[
                InlineKeyboardButton("🖋️ ꜰɪʟᴇ ɴᴀᴍᴇ", callback_data="custom_file_name", style=ButtonStyle.PRIMARY),
                InlineKeyboardButton("🎵 ᴍᴇᴛᴀᴅᴀᴛᴀ", callback_data="custom_metadata", style=ButtonStyle.PRIMARY)
                ],[
                InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="start", style=ButtonStyle.DANGER)
                ]]))         
        
    elif data == "about":
        about_button = [[
        InlineKeyboardButton("💞 ᴜᴘᴅᴀᴛᴇꜱ 💞", url="https://t.me/mgbnotfree_creator", style=ButtonStyle.PRIMARY),
        InlineKeyboardButton("📊 ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ", callback_data="bot_status", style=ButtonStyle.PRIMARY)
        ],[
        InlineKeyboardButton("⚡ ʟɪᴠᴇ ꜱᴛᴀᴛᴜꜱ", callback_data="live_status", style=ButtonStyle.PRIMARY)           
        ]]
        if client.premium:
            about_button[-1].append(InlineKeyboardButton("💎 ᴜᴘɢʀᴀᴅᴇ", callback_data="upgrade", style=ButtonStyle.SUCCESS))
            about_button.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="start", style=ButtonStyle.DANGER)])
        else:
            about_button[-1].append(InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="start", style=ButtonStyle.DANGER))
        await query.message.edit_text(
            text=rkn.ABOUT_TXT.format(client.mention, __developer__, __programer__, __library__, __language__, __database__, _bot_version_),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup(about_button))    
        
    elif data == "upgrade":
        if not client.premium:
            return await query.message.delete()
        text, markup = await upgrade_view(client, query.from_user)
        await query.message.edit_text(text=text, reply_markup=markup, link_preview_options=LinkPreviewOptions(is_disabled=True))

    elif data == "plans":
        if not client.premium:
            return await query.message.delete()
        text, markup = await upgrade_view(client, query.from_user)
        await query.message.edit_text(text=text, reply_markup=markup, link_preview_options=LinkPreviewOptions(is_disabled=True))
           
    elif data == "give_trial":
        if not client.premium:
            return await query.message.delete()
        await query.message.delete()
        free_trial_status = await digital_botz.get_free_trial_status(query.from_user.id)
        if not free_trial_status:            
            await digital_botz.give_free_trial(query.from_user.id)
            new_text = "<b>ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴛʀɪᴀʟ ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ғᴏʀ 𝟷𝟸 ʜᴏᴜʀs.\n\nʏᴏᴜ ᴄᴀɴ ᴜsᴇ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ 𝟷𝟸 ʜᴏᴜʀs ꜰʀᴏᴍ ɴᴏᴡ 😀\n\nआप अब से 𝟷𝟸 घण्टा के लिए निःशुल्क ट्रायल का उपयोग कर सकते हैं 😀</b>"
        else:
            new_text = "<b>🤣 ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ ғʀᴇᴇ ɴᴏᴡ ɴᴏ ᴍᴏʀᴇ ғʀᴇᴇ ᴛʀᴀɪʟ. ᴘʟᴇᴀsᴇ ʙᴜʏ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʜᴇʀᴇ ᴀʀᴇ ᴏᴜʀ 👉 /plans</b>"
        await client.send_message(query.from_user.id, text=new_text)

    elif data == "thumbnail":
        await query.message.edit_text(
            text=rkn.THUMBNAIL,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup([[
             InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="help", style=ButtonStyle.DANGER)]]))

    elif data == "caption":
        await query.message.edit_text(
            text=rkn.CAPTION,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup([[
             InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="help", style=ButtonStyle.DANGER)]]))

    elif data == "custom_file_name":
        await query.message.edit_text(
            text=rkn.CUSTOM_FILE_NAME,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup([[
             InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="help", style=ButtonStyle.DANGER)]]))

    elif data == "bot_status":
        total_users = await digital_botz.total_users_count()
        if client.premium:
            total_premium_users = await digital_botz.total_premium_users_count()
        else:
            total_premium_users = "Disabled ✅"
        uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - client.uptime))
        sent = humanbytes(psutil.net_io_counters().bytes_sent)
        recv = humanbytes(psutil.net_io_counters().bytes_recv)
        speed_label = await network_speed_label()
        await query.message.edit_text(
            text=rkn.BOT_STATUS.format(uptime, total_users, total_premium_users, speed_label, sent, recv),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup([[
             InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="about", style=ButtonStyle.DANGER)]]))

    elif data == "live_status":
        status = await get_status()
        speed_label = await network_speed_label()
        await query.message.edit_text(
            text=rkn.LIVE_STATUS.format(status["uptime"], status["cpu_usage"], status["ram_usage"], status["total_disk"], status["used_disk"], status["disk_usage"], status["free_disk"], status["sent"], status["recv"], speed_label),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup([[
             InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="about", style=ButtonStyle.DANGER)]]))

    elif data == "source_code":
        await query.message.edit_text(
            text=rkn.DEV_TXT,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🖤 ᴍ ɢ ʙ   ᴄ ᴏ ᴅ ᴇ ʀ 🖤", url="https://t.me/mgbnotfree_creator", style=ButtonStyle.PRIMARY)
            ],[
                InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ", callback_data="close", style=ButtonStyle.DANGER),
                InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="about", style=ButtonStyle.PRIMARY)
            ]])
        )

    elif data == "close":
        parent = query.message.reply_to_message
        for target in (query.message, parent):
            if target is None:
                continue
            try:
                await target.delete()
            except Exception:
                pass
        await query.message.continue_propagation()
