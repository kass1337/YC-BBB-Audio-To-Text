import re
from decode import Decoder
from telebot.async_telebot import AsyncTeleBot
import os
import asyncio
import aiofiles
API_TOKEN = os.environ['TELEGRAM_TOKEN']
bot = AsyncTeleBot(API_TOKEN)
TIMEOUT = 14400
VALID_URL_RE = re.compile(
    r'''(?x)
            (?P<website>https?://[^/]+)/playback/presentation/
            (?P<version>[\d\.]+)/
            (playback.html\?.*?meetingId=)?
            (?P<id>[0-9a-f\-]+)
        '''
)

decoder = Decoder()


def is_valid_url(url):
    obj = re.match(VALID_URL_RE, url)
    return obj is not None


@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    if is_valid_url(message.text):
        await bot.reply_to(message, "Начали")
        result = await decoder.decode(message.text)
        try:
            async with aiofiles.open(result, mode='rb') as file:
                await bot.send_document(message.chat.id, file, timeout=TIMEOUT)
                await file.close()
        except Exception:
            await bot.reply_to(message, result)
    else:
        await bot.reply_to(message, "Неправильная ссылка на запись из BBB")

asyncio.run(bot.polling(non_stop=True))
