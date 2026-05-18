from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
MONGO_URL = os.environ["MONGO_URL"]

app = Client(
    "rankingbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo.rankingbot
users = db.users


def today_key():
    return datetime.utcnow().strftime("%Y-%m-%d")


def week_key():
    return datetime.utcnow().strftime("%Y-%W")


@app.on_message(filters.group & ~filters.service)
async def message_counter(_, message):
    if not message.from_user:
        return

    user = message.from_user
    chat_id = message.chat.id

    await users.update_one(
        {"chat_id": chat_id, "user_id": user.id},
        {
            "$inc": {
                "overall": 1,
                f"today.{today_key()}": 1,
                f"week.{week_key()}": 1
            },
            "$set": {
                "name": user.first_name
            }
        },
        upsert=True
    )


async def build_ranking(chat_id, mode):
    ranking = []

    async for user in users.find({"chat_id": chat_id}):
        count = 0

        if mode == "overall":
            count = user.get("overall", 0)

        elif mode == "today":
            count = user.get("today", {}).get(today_key(), 0)

        elif mode == "week":
            count = user.get("week", {}).get(week_key(), 0)

        ranking.append((user.get("name", "User"), count))

    ranking.sort(key=lambda x: x[1], reverse=True)

    text = f"🏆 **LEADERBOARD ({mode.upper()})**\n\n"

    total = 0
    for i, (name, count) in enumerate(ranking[:10], start=1):
        text += f"{i}. {name} ➜ {count}\n"
        total += count

    text += f"\n📩 Total messages: {total}"
    return text


def buttons(active="overall"):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"Today {'✅' if active == 'today' else ''}",
                    callback_data="today"
                ),
                InlineKeyboardButton(
                    f"Week {'✅' if active == 'week' else ''}",
                    callback_data="week"
                ),
                InlineKeyboardButton(
                    f"Overall {'✅' if active == 'overall' else ''}",
                    callback_data="overall"
                )
            ]
        ]
    )


@app.on_message(filters.command("ranking") & filters.group)
async def ranking(_, message):
    text = await build_ranking(message.chat.id, "overall")
    await message.reply_text(
        text,
        reply_markup=buttons("overall")
    )


@app.on_callback_query()
async def callback_handler(_, query):
    mode = query.data
    if mode not in ["today", "week", "overall"]:
        return

    text = await build_ranking(query.message.chat.id, mode)

    await query.message.edit_text(
        text,
        reply_markup=buttons(mode)
    )

    await query.answer()


print("Ranking Bot Started...")
app.run()
