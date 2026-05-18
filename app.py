from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo.rankingbot
users = db.users

app = Client(
    "RankingBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


@app.on_message(filters.group & ~filters.service)
async def track_messages(_, message):
    user = message.from_user
    if not user:
        return

    await users.update_one(
        {
            "chat_id": message.chat.id,
            "user_id": user.id
        },
        {
            "$inc": {
                "overall": 1,
                "today": 1,
                "week": 1
            },
            "$set": {
                "name": user.first_name
            }
        },
        upsert=True
    )


@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    data = users.find(
        {"chat_id": message.chat.id}
    ).sort("overall", -1).limit(10)

    text = "🏆 **LEADERBOARD**\n\n"

    rank = 1
    async for user in data:
        text += f"{rank}. {user['name']} - {user.get('overall', 0)}\n"
        rank += 1

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Today", callback_data="today"),
                InlineKeyboardButton("Week", callback_data="week"),
                InlineKeyboardButton("Overall", callback_data="overall"),
            ],
            [
                InlineKeyboardButton(
                    "Profile",
                    url=f"tg://user?id={message.from_user.id}"
                )
            ]
        ]
    )

    await message.reply_text(text, reply_markup=buttons)


print("Ranking Bot Started...")
app.run()
