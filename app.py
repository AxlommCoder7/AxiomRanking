from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
MONGO_URL = os.environ["MONGO_URL"]

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["ranking_bot"]
users = db["users"]

app = Client(
    "rankingbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


def get_today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_week():
    return datetime.utcnow().strftime("%Y-%U")


@app.on_message(filters.group & ~filters.service)
async def count_messages(client, message):
    if not message.from_user:
        return

    user = message.from_user
    chat_id = message.chat.id
    today = get_today()
    week = get_week()

    await users.update_one(
        {
            "chat_id": chat_id,
            "user_id": user.id
        },
        {
            "$inc": {
                "overall": 1,
                f"daily.{today}": 1,
                f"weekly.{week}": 1
            },
            "$set": {
                "name": user.first_name
            }
        },
        upsert=True
    )


async def generate_ranking(chat_id, mode):
    ranking = []

    async for user in users.find({"chat_id": chat_id}):
        count = 0

        if mode == "overall":
            count = user.get("overall", 0)

        elif mode == "today":
            count = user.get("daily", {}).get(get_today(), 0)

        elif mode == "week":
            count = user.get("weekly", {}).get(get_week(), 0)

        ranking.append((user.get("name", "User"), count))

    ranking.sort(key=lambda x: x[1], reverse=True)

    text = f"🏆 **TOP 10 - {mode.upper()}**\n\n"

    for i, (name, count) in enumerate(ranking[:10], start=1):
        text += f"{i}. {name} ➜ {count}\n"

    return text


@app.on_message(filters.command("ranking") & filters.group)
async def ranking_command(client, message):
    text = await generate_ranking(message.chat.id, "overall")

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Today", callback_data="rank_today"),
                InlineKeyboardButton("Week", callback_data="rank_week"),
                InlineKeyboardButton("Overall", callback_data="rank_overall")
            ]
        ]
    )

    await message.reply_text(text, reply_markup=buttons)


@app.on_callback_query()
async def callbacks(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id

    if data == "rank_today":
        text = await generate_ranking(chat_id, "today")

    elif data == "rank_week":
        text = await generate_ranking(chat_id, "week")

    elif data == "rank_overall":
        text = await generate_ranking(chat_id, "overall")

    else:
        return

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Today", callback_data="rank_today"),
                InlineKeyboardButton("Week", callback_data="rank_week"),
                InlineKeyboardButton("Overall", callback_data="rank_overall")
            ]
        ]
    )

    await callback_query.message.edit_text(
        text,
        reply_markup=buttons
    )


print("Ranking Bot Started...")
app.run()
