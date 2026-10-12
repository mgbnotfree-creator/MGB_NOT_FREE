from pyrogram.enums import ButtonStyle
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from helper.database import digital_botz
from config import rkn
from html import escape

TRUE = [[InlineKeyboardButton('Metadata On', callback_data='metadata_1', style=ButtonStyle.SUCCESS),
       InlineKeyboardButton('✅', callback_data='metadata_1', style=ButtonStyle.SUCCESS)
       ],[
       InlineKeyboardButton('Set Custom Metadata', callback_data='custom_metadata', style=ButtonStyle.PRIMARY)]]
FALSE = [[InlineKeyboardButton('Metadata Off', callback_data='metadata_0', style=ButtonStyle.DANGER),
        InlineKeyboardButton('❌', callback_data='metadata_0', style=ButtonStyle.DANGER)
       ],[
       InlineKeyboardButton('Set Custom Metadata', callback_data='custom_metadata', style=ButtonStyle.PRIMARY)]]


@Client.on_message(filters.private & filters.command('metadata'))
async def handle_metadata(bot: Client, message: Message):
    RknDev = await message.reply_text("<b>Please Wait...</b>")
    bool_metadata = await digital_botz.get_metadata_mode(message.from_user.id)
    user_metadata = await digital_botz.get_metadata_code(message.from_user.id)
    
    # अगर मेटाडेटा सेट नहीं है तो डिफ़ॉल्ट मैसेज दिखाए
    display_meta = user_metadata if user_metadata else "Not Set"
    
    await RknDev.edit(
        f"<b>Your Current Metadata:</b>\n\n➜ <code>{escape(str(display_meta))}</code>",
        reply_markup=InlineKeyboardMarkup(TRUE if bool_metadata else FALSE)
    )

@Client.on_callback_query(filters.regex('.*?(custom_metadata|metadata).*?'))
async def query_metadata(bot: Client, query: CallbackQuery):
    await query.answer()
    data = query.data
    if data.startswith('metadata_'):
        _bool = data.split('_')[1]
        user_metadata = await digital_botz.get_metadata_code(query.from_user.id)
        display_meta = user_metadata if user_metadata else "Not Set"
        bool_meta = _bool == "1"
        await digital_botz.set_metadata_mode(query.from_user.id, bool_meta=not bool_meta)
        await query.message.edit(f"<b>Your Current Metadata:</b>\n\n➜ <code>{escape(str(display_meta))}</code>", reply_markup=InlineKeyboardMarkup(FALSE if bool_meta else TRUE))
           
    elif data == 'custom_metadata':
        await query.message.reply_text(
            rkn.SEND_METADATA,
            reply_markup=ForceReply(selective=True),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        await query.message.delete()


@Client.on_message(filters.private & filters.reply & filters.text)
async def save_metadata_code(bot: Client, message: Message):
    reply_to = message.reply_to_message
    
    # चेक करें कि क्या यूज़र ने बोट के मैसेज का रिप्लाई किया है
    if not reply_to or not reply_to.from_user or not reply_to.from_user.is_self:
        return
        
    # 100% FIXED: Pyrogram reply_markup हटा देता है, इसलिए हम सिर्फ Text मैच करेंगे
    if not reply_to.text or "Send Your Custom Metadata" not in reply_to.text:
        return
        
    user_input = message.text.strip()
    
    # 100% FIXED AUTO-FORMAT: अगर यूज़र सिर्फ "MGB NOT FREE" भेजे, तो बोट खुद कोड बना लेगा
    if "--change" not in user_input:
        final_metadata = (
            f'--change-title "{user_input}" '
            f'--change-video-title "{user_input}" '
            f'--change-audio-title "{user_input}" '
            f'--change-subtitle-title "{user_input}"'
        )
    else:
        # अगर यूज़र ने खुद पूरा कोड भेजा है, तो उसे वैसे ही रहने दें
        final_metadata = user_input
        
    await digital_botz.set_metadata_code(message.from_user.id, metadata_code=final_metadata)
    
    try:
        await reply_to.delete()
    except:
        pass
        
    await message.reply_text(
        f"<b>✅ Your Metadata Code Set Successfully!</b>\n\n"
        f"<b>Saved As:</b>\n<code>{escape(final_metadata)}</code>"
)
       
