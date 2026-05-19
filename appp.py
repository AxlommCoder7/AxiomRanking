import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

dp = Dispatcher()

@dp.message(Command("ss"))
async def start_cmd(message: types.Message):
    await message.answer(
        'bol bhai kya bol rha tha nahi btaunga? <tg-emoji emoji-id="6282977077427702833">🍂</tg-emoji>',
        parse_mode="HTML"
    )

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
