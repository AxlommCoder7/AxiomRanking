import re
import os
import random
from datetime import datetime
from unidecode import unidecode
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont, ImageFilter


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
    width, height = 1280, 720

    # random premium palettes
    palettes = [
        ((8, 12, 30), (18, 45, 80), (0, 240, 255)),      # cyan
        ((20, 8, 30), (60, 20, 80), (255, 0, 180)),      # pink
        ((8, 25, 18), (20, 80, 55), (0, 255, 170)),      # green
        ((15, 10, 35), (40, 25, 90), (180, 100, 255)),   # purple
        ((5, 18, 35), (10, 60, 120), (0, 170, 255)),     # blue
        ((35, 10, 10), (90, 20, 20), (255, 70, 70)),     # red
        ((35, 20, 5), (100, 50, 10), (255, 160, 0)),     # orange
        ((30, 30, 5), (90, 90, 20), (255, 230, 0)),      # yellow
        ((12, 30, 30), (20, 100, 100), (0, 255, 255)),   # aqua
        ((25, 10, 35), (60, 20, 100), (220, 120, 255)),  # violet
        ((30, 15, 25), (90, 30, 70), (255, 100, 200)),   # rose
        ((10, 25, 35), (20, 70, 110), (100, 180, 255)),  # sky blue
        ((8, 12, 30), (18, 45, 80), (0, 240, 255)),
        ((20, 8, 30), (60, 20, 80), (255, 0, 180)),
        ((8, 25, 18), (20, 80, 55), (0, 255, 170)),
        ((15, 10, 35), (40, 25, 90), (180, 100, 255)),
        ((5, 18, 35), (10, 60, 120), (0, 170, 255)),
    ]

    bg1, bg2, accent = random.choice(palettes)

    img = Image.new("RGB", (width, height), bg1)
    draw = ImageDraw.Draw(img)

    # -------- gradient background ----------
    for y in range(height):
        ratio = y / height
        r = int(bg1[0] * (1 - ratio) + bg2[0] * ratio)
        g = int(bg1[1] * (1 - ratio) + bg2[1] * ratio)
        b = int(bg1[2] * (1 - ratio) + bg2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # blur circles
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    for _ in range(8):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(120, 260)

        odraw.ellipse(
            (x, y, x + size, y + size),
            fill=(*accent, 35)
        )

    overlay = overlay.filter(ImageFilter.GaussianBlur(60))
    img.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(img)

    # fonts
    try:
        title_font = ImageFont.truetype("cfont.ttf", 88)
        name_font = ImageFont.truetype("f.ttf", 22)
        small_font = ImageFont.truetype("f.ttf", 26)
        count_font = ImageFont.truetype("cfont.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        count_font = ImageFont.load_default()

    # main glass card
    draw.rounded_rectangle(
        (25, 25, 1255, 695),
        radius=35,
        fill=(5, 10, 25, 180),
        outline=accent,
        width=4
    )

    # top labels
    draw.text(
        (42, 38),
        "Dev:- Maanav",
        font=small_font,
        fill=accent
    )

    draw.text(
        (1030, 40),
        mode.upper(),
        font=small_font,
        fill=accent
    )

    # 3D title
    title = "LEADERBOARD"

    draw.text(
        (315, 60),
        title,
        font=title_font,
        fill=(20, 20, 20)
    )
    draw.text(
        (312, 55),
        title,
        font=title_font,
        fill=(80, 80, 80)
    )
    draw.text(
        (308, 48),
        title,
        font=title_font,
        fill=(255, 255, 255)
    )

    max_count = ranking[0][2] if ranking else 1
    start_y = 180

    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        y = start_y + ((i - 1) * 48)

        # clean first name only
        clean_name = unidecode(str(name)).strip()
        
        # remove symbols but keep spaces
        clean_name = re.sub(r'[^a-zA-Z0-9 ]+', '', clean_name)
        
        # remove extra spaces
        clean_name = " ".join(clean_name.split())
        
        if not clean_name:
            clean_name = "Unknown"
        
        # max 14 chars so fit ho jaye
        clean_name = clean_name[:14]

        # rank
        draw.text(
            (60, y),
            f"{i}.",
            font=name_font,
            fill=(255, 255, 255)
        )

        # user name
        draw.text(
            (120, y),
            clean_name,
            font=name_font,
            fill=(240, 240, 240)
        )

        # bar
        bar_x = 330
        bar_y = y + 8
        full_width = 620
        filled = int((count / max_count) * full_width)

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + full_width, bar_y + 28),
            radius=14,
            fill=(12, 22, 45),
            outline=accent,
            width=2
        )

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + filled, bar_y + 28),
            radius=14,
            fill=accent
        )

        # count box
        draw.rounded_rectangle(
            (1030, y - 1, 1145, y + 34),
            radius=12,
            fill=(10, 25, 50)
        )

        count_x = 1055 if len(str(count)) <= 2 else 1045

        draw.text(
            (count_x, y + 2),
            str(count),
            font=count_font,
            fill=(255, 255, 255)
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

    text += f"\n✉️ **Total Messages: {total}**"
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
