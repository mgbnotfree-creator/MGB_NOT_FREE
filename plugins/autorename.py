from pyrogram import Client, filters
from helper.database import digital_botz
from html import escape

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    user_id = message.from_user.id
    args = message.text.split(" ", 1)
    
    if len(args) < 2:
        return await message.reply_text(
            "<b><u>❌ अशुद्ध फॉर्मेट!</u></b>\n\n"
            "कृपया इस तरह कमांड भेजें:\n"
            "<code>/autorename Ep {episode} - Show Name [1080p]</code>\n\n"
            "💡 <i>ध्यान दें:</i> <code>{episode}</code> लिखना जरूरी है ताकि बोट नंबर खुद-ब-खुद बढ़ा सके।"
        )
    
    format_text = args[1]
    
    # डेटाबेस में फॉर्मेट और ऑटो-रीनेम स्टेटस चालू करें
    await digital_botz.set_auto_name(user_id, format_text)
    await digital_botz.toggle_autorename(user_id, True)
    
    # यदि यूज़र ने पहली बार सेट किया है, तो डिफ़ॉल्ट नंबर 1401 सेट कर दें
    user_data = await digital_botz.get_user_data(user_id)
    if not user_data.get('auto_number'):
        await digital_botz.col.update_one({'_id': user_id}, {'$set': {'auto_number': 1401}})
    
    await message.reply_text(
        f"✅ <b>ऑटो-रीनेम फॉर्मेट सफलतापूर्वक सेट हो गया है!</b>\n\n"
        f"• <b>आपका फॉर्मेट:</b> <code>{escape(format_text)}</code>\n"
        f"• <b>अगला एपिसोड नंबर:</b> <code>1401</code>\n\n"
        f"अब आप कोई भी फाइल भेजेंगे, बोट उसे तुरंत इस फॉर्मेट में रीनेम कर देगा!"
    )
