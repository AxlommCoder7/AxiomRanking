from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

bot = Client(
    "ranking_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["ranking_bot"]
users = db["users"]


def today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def week():
    return datetime.utcnow().strftime("%Y-%W")


@bot.on_message(filters.command("start"))
async def start_cmd(_, message):
    text = """
✨ **Welcome to Axiom Ranking Bot**

Track your group activity with ease 📊

**Available Commands:**
• /ranking - Show group leaderboard

Bot tracks:
• Overall messages
• Daily messages
• Weekly messages
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Channel", url="https://t.me/axiombots"),
                InlineKeyboardButton("Group", url="https://t.me/axlomm")
            ],
            [
                InlineKeyboardButton("Owner", url="https://t.me/xomnv")
            ],
            [
                InlineKeyboardButton("Add To Group", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")
            ]
        ]
    )

    await message.reply_text(
        text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )
    
@bot.on_message(filters.group & ~filters.service)
async def count_msg(_, message):
    if not message.from_user:
        return

    await users.update_one(
        {
            "chat_id": message.chat.id,
            "user_id": message.from_user.id
        },
        {
            "$inc": {
                "overall": 1,
                f"daily.{today()}": 1,
                f"weekly.{week()}": 1
            },
            "$set": {
                "name": message.from_user.first_name
            }
        },
        upsert=True
    )


async def make_board(chat_id, mode):
    data = []

    async for user in users.find({"chat_id": chat_id}):
        if mode == "overall":
            count = user.get("overall", 0)

        elif mode == "today":
            count = user.get("daily", {}).get(today(), 0)

        else:
            count = user.get("weekly", {}).get(week(), 0)

        data.append((user.get("name", "User"), count))

    data.sort(key=lambda x: x[1], reverse=True)

    msg = f"🏆 **Leaderboard • {mode.upper()}**\n\n"

    total = 0
    for i, (name, count) in enumerate(data[:10], start=1):
        msg += f"{i}. {name} ➜ {count}\n"
        total += count

    msg += f"\n📩 Total messages: {total}"
    return msg


def get_buttons(active):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"Today {'✅' if active=='today' else ''}",
                    callback_data="today"
                ),
                InlineKeyboardButton(
                    f"Week {'✅' if active=='week' else ''}",
                    callback_data="week"
                ),
                InlineKeyboardButton(
                    f"Overall {'✅' if active=='overall' else ''}",
                    callback_data="overall"
                )
            ]
        ]
    )


@bot.on_message(filters.command("ranking"))
async def ranking(_, message):
    if message.chat.type not in ["group", "supergroup"]:
        return await message.reply("Use this in groups only.")

    text = await make_board(message.chat.id, "overall")
    await message.reply_text(
        text,
        reply_markup=get_buttons("overall")
    )


@bot.on_callback_query()
async def callbacks(_, query):
    mode = query.data

    if mode not in ["today", "week", "overall"]:
        return

    text = await make_board(query.message.chat.id, mode)

    await query.message.edit_text(
        text,
        reply_markup=get_buttons(mode)
    )
    await query.answer()


async def main():
    await bot.start()
    print("Bot Started Successfully")
    await idle()
    await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
