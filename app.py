import os
import asyncio
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

print("Starting bot file...")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

print("Environment variables loaded successfully")

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

print("MongoDB connected")


def today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def week():
    return datetime.utcnow().strftime("%Y-%W")


@bot.on_message(filters.command("start"))
async def start_cmd(_, message):
    try:
        print("/start command received")

        text = """
✨ **Welcome To Axiom Ranking Bot**

Track group chats easily 📊

Commands:
• /ranking - show leaderboard
"""

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Channel",
                        url="https://t.me/axiombots"
                    ),
                    InlineKeyboardButton(
                        "Group",
                        url="https://t.me/axlomm"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Owner",
                        url="https://t.me/xomnv"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Add To Group",
                        url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"
                    )
                ]
            ]
        )

        await message.reply_text(
            text,
            reply_markup=buttons,
            disable_web_page_preview=True
        )

        print("/start success")

    except Exception as e:
        print(f"START ERROR: {e}")

@bot.on_message(filters.group & ~filters.service)
async def count_messages(_, message):
    try:
        if not message.from_user:
            return

        if message.text:
            cmd = message.text.split()[0].lower()
            if cmd.startswith("/ranking"):
                print("Skipping ranking command count")
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

        print(f"Updated count for {message.from_user.first_name}")

    except Exception as e:
        print(f"COUNT ERROR: {e}")

@bot.on_message(filters.group & filters.text)
async def ranking(_, message):
    try:
        print(
            f"GROUP MESSAGE: {message.text} "
            f"chat={message.chat.id}"
        )

        if not message.text:
            return

        cmd = message.text.split()[0].lower()

        bot_username = (await bot.get_me()).username.lower()

        valid_commands = [
            "/ranking",
            f"/ranking@{bot_username}"
        ]

        if cmd not in valid_commands:
            return

        print("/ranking detected in group")

        text = await build_board(
            message.chat.id,
            "overall"
        )

        await message.reply_text(
            text,
            reply_markup=buttons("overall")
        )

        print("/ranking success in group")

    except Exception as e:
        print(f"GROUP RANK ERROR: {e}")


async def build_board(chat_id, mode):
    try:
        await users.database.client.admin.command("ping")
        ranking = []

        async for user in users.find({"chat_id": chat_id}):
            if mode == "overall":
                count = user.get("overall", 0)

            elif mode == "today":
                count = user.get("daily", {}).get(today(), 0)

            else:
                count = user.get("weekly", {}).get(week(), 0)

            ranking.append(
                (
                    user.get("name", "User"),
                    count
                )
            )

        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )

        text = f"🏆 **Leaderboard ({mode.upper()})**\n\n"

        total = 0
        for i, (name, count) in enumerate(
            ranking[:10],
            start=1
        ):
            text += f"{i}. {name} ➜ {count}\n"
            total += count

        text += f"\n📩 Total Messages: {total}"
        return text

    except Exception as e:
        print(f"BUILD BOARD ERROR: {e}")
        return "Error building ranking."


def buttons(active):
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
    try:
        print("/ranking command triggered")

        text = await build_board(
            message.chat.id,
            "overall"
        )

        await message.reply_text(
            text,
            reply_markup=buttons("overall")
        )

        print("/ranking success")

    except Exception as e:
        print(f"RANKING ERROR: {e}")


@bot.on_callback_query()
async def callbacks(_, query):
    try:
        print(f"Button clicked: {query.data}")

        mode = query.data

        text = await build_board(
            query.message.chat.id,
            mode
        )

        await query.message.edit_text(
            text,
            reply_markup=buttons(mode)
        )

        await query.answer()

        print("Callback success")

    except Exception as e:
        print(f"CALLBACK ERROR: {e}")


if __name__ == "__main__":
    print("Bot Started Successfully")
    bot.run()
