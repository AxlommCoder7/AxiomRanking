import os
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

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
db = mongo["rankingbot"]
collection = db["messages"]


def get_today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_week():
    return datetime.utcnow().strftime("%Y-%U")


@bot.on_message(filters.group & ~filters.service)
async def count_messages(client, message):
    if not message.from_user:
        return

    await collection.update_one(
        {
            "chat_id": message.chat.id,
            "user_id": message.from_user.id
        },
        {
            "$inc": {
                "overall": 1,
                f"today.{get_today()}": 1,
                f"week.{get_week()}": 1
            },
            "$set": {
                "name": message.from_user.first_name
            }
        },
        upsert=True
    )


async def get_ranking(chat_id, mode="overall"):
    users = []
    async for user in collection.find({"chat_id": chat_id}):
        if mode == "overall":
            count = user.get("overall", 0)
        elif mode == "today":
            count = user.get("today", {}).get(get_today(), 0)
        else:
            count = user.get("week", {}).get(get_week(), 0)

        users.append((user.get("name", "User"), count))

    users.sort(key=lambda x: x[1], reverse=True)

    text = f"🏆 **Leaderboard ({mode.title()})**\n\n"
    for i, (name, count) in enumerate(users[:10], 1):
        text += f"{i}. {name} - {count}\n"

    return text


def keyboard(active):
    return InlineKeyboardMarkup([
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
    ])


@bot.on_message(filters.command("ranking") & filters.group)
async def ranking(client, message):
    text = await get_ranking(message.chat.id, "overall")
    await message.reply_text(
        text,
        reply_markup=keyboard("overall")
    )


@bot.on_callback_query()
async def callbacks(client, query):
    mode = query.data
    text = await get_ranking(query.message.chat.id, mode)

    await query.message.edit_text(
        text,
        reply_markup=keyboard(mode)
    )
    await query.answer()


async def main():
    await bot.start()
    print("Bot Started Successfully")
    await idle()
    await bot.stop()


bot.run(main())
