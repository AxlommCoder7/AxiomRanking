import re
import os
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont

print("Starting bot...")

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


def get_buttons(active):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"⏺️ Overall {'✅' if active=='overall' else ''}",
                callback_data="overall"
            )
        ],
        [
            InlineKeyboardButton(
                f"⏺️ Today {'✅' if active=='today' else ''}",
                callback_data="today"
            ),
            InlineKeyboardButton(
                f"⏺️ Week {'✅' if active=='week' else ''}",
                callback_data="week"
            )
        ]
    ])

def generate_leaderboard_image(ranking, mode):
    width = 1280
    height = 720

    img = Image.new("RGB", (width, height), (8, 12, 25))
    draw = ImageDraw.Draw(img)

    cyan = (0, 255, 255)
    white = (255, 255, 255)
    blue = (0, 180, 255)
    gray = (120, 130, 160)

    try:
        title_font = ImageFont.truetype("arial.ttf", 70)
        text_font = ImageFont.truetype("arial.ttf", 32)
        small_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.text((360, 40), "LEADERBOARD", font=title_font, fill=cyan)
    draw.text((30, 20), "AXIOM RANKING", font=small_font, fill=blue)
    draw.text((1040, 20), "PREMIUM", font=small_font, fill=cyan)

    max_count = ranking[0][2] if ranking else 1

    start_y = 160

    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        y = start_y + ((i - 1) * 48)

        clean_name = re.sub(r'[^a-zA-Z0-9 ]', '', name)[:12]

        draw.text(
            (60, y),
            f"{i}. {clean_name}",
            font=text_font,
            fill=white
        )

        bar_x = 300
        bar_y = y + 8
        bar_width = int((count / max_count) * 700)

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + 700, bar_y + 28),
            radius=14,
            outline=(30, 60, 100),
            width=2
        )

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + bar_width, bar_y + 28),
            radius=14,
            fill=blue
        )

        draw.text(
            (1020, y),
            str(count),
            font=text_font,
            fill=cyan
        )

    draw.text(
        (40, 670),
        f"MODE: {mode.upper()}",
        font=small_font,
        fill=gray
    )

    file_path = "leaderboard.png"
    img.save(file_path)
    return file_path

async def build_board(chat_id, mode):
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
                user.get("user_id"),
                count
            )
        )

    ranking.sort(key=lambda x: x[2], reverse=True)

    text = f"📈 **LEADERBOARD ({mode.upper()})**\n\n"

    total = 0
    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        clean_name = re.sub(r'[\[\]\(\)_*`]', '', name)
        mention = f"[{clean_name}](tg://user?id={user_id})"
    
        text += f"{i}. {mention} ➜ {count}\n"
        total += count

    text += f"\n✉️ Total Messages: {total}"
    return text, ranking


@bot.on_message(filters.command("start"))
async def start_cmd(_, message):
    await message.reply_text(
        """✨ **Welcome To Axiom Ranking Bot**

Track group chats easily 📊

Commands:
• /ranking - show leaderboard
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Channel", url="https://t.me/axiombots"),
                InlineKeyboardButton("Group", url="https://t.me/axlomm")
            ],
            [
                InlineKeyboardButton("Owner", url="https://t.me/xomnv")
            ],
            [
                InlineKeyboardButton(
                    "Add To Group",
                    url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"
                )
            ]
        ])
    )


@bot.on_message(filters.group & ~filters.service)
async def count_messages(_, message):
    try:
        if not message.from_user:
            return

        if message.text:
            cmd = message.text.split()[0].lower()

            if cmd.startswith("/ranking"):
                print("Ranking command detected inside count handler")

                text, ranking = await build_board(
                    message.chat.id,
                    "overall"
                )
                
                photo = generate_leaderboard_image(
                    ranking,
                    "overall"
                )
                
                await message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=get_buttons("overall")
                )
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

        print(f"Count updated: {message.from_user.first_name}")

    except Exception as e:
        print(f"COUNT ERROR: {e}")


@bot.on_callback_query()
async def callback_handler(_, query):
    try:
        mode = query.data
        text, ranking = await build_board(
            query.message.chat.id,
            mode
        )
        
        photo = generate_leaderboard_image(
            ranking,
            mode
        )
        
        await query.message.delete()
        
        await query.message.reply_photo(
            photo=photo,
            caption=text,
            reply_markup=get_buttons(mode)
        )
        await query.answer()

    except Exception as e:
        print(f"CALLBACK ERROR: {e}")


if __name__ == "__main__":
    print("Bot running...")
    bot.run()
