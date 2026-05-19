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
    bot_token=BOT_TOKEN
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

    img = Image.new("RGB", (width, height), (4, 8, 20))
    draw = ImageDraw.Draw(img)

    # colors
    bg_panel = (8, 18, 38)
    cyan = (0, 240, 255)
    blue = (0, 140, 255)
    white = (255, 255, 255)
    gray = (140, 160, 190)
    dark_bar = (10, 28, 55)

    # fonts from uploaded files
    try:
        title_font = ImageFont.truetype("cfont.ttf", 88)
        name_font = ImageFont.truetype("f.ttf", 30)
        small_font = ImageFont.truetype("f.ttf", 22)
        count_font = ImageFont.truetype("cfont.ttf", 28)
    except Exception as e:
        print(f"FONT ERROR: {e}")
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        count_font = ImageFont.load_default()

    # main card
    draw.rounded_rectangle(
        (25, 25, 1255, 695),
        radius=35,
        fill=bg_panel,
        outline=(0, 100, 200),
        width=4
    )

    # watermark logo style
    draw.text(
        (40, 40),
        "Dev:- Maanav",
        font=small_font,
        fill=(0, 120, 180)
    )

    draw.text(
        (990, 42),
        "",
        font=small_font,
        fill=cyan
    )

    # shadow title
    draw.text(
        (318, 58),
        "LEADERBOARD",
        font=title_font,
        fill=(0, 60, 90)
    )

    draw.text(
        (310, 50),
        "LEADERBOARD",
        font=title_font,
        fill=white
    )

    max_count = ranking[0][2] if ranking else 1
    start_y = 180

    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        y = start_y + ((i - 1) * 48)

        clean_name = re.sub(r'[^a-zA-Z0-9 ]', '', name)[:14]

        # rank
        draw.text(
            (65, y),
            f"{i}.",
            font=name_font,
            fill=white
        )

        # user name
        draw.text(
            (130, y),
            clean_name,
            font=name_font,
            fill=white
        )

        bar_x = 350
        bar_y = y + 8
        full_width = 620
        filled = int((count / max_count) * full_width)

        # background bar
        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + full_width, bar_y + 28),
            radius=14,
            fill=dark_bar,
            outline=(0, 90, 180),
            width=2
        )

        # filled bar
        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + filled, bar_y + 28),
            radius=14,
            fill=blue
        )

        # value box
        draw.rounded_rectangle(
            (1020, y - 1, 1135, y + 34),
            radius=12,
            fill=(8, 35, 70)
        )

        draw.text(
            (1052, y + 2),
            str(count),
            font=count_font,
            fill=cyan
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
