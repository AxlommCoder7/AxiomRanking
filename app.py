import re
import os
import random
from datetime import datetime
from unidecode import unidecode
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from premium import p, PREMIUM_PARSE
from pyrogram import Client, filters
from pyrogram.enums import ParseMode


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
    parse_mode=ParseMode.HTML
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
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import random, re
    from unidecode import unidecode

    width, height = 1280, 720

    palettes = [
        ((8, 12, 30), (18, 45, 80), (0, 240, 255)),
        ((20, 8, 30), (60, 20, 80), (255, 0, 180)),
        ((8, 25, 18), (20, 80, 55), (0, 255, 170)),
        ((15, 10, 35), (40, 25, 90), (180, 100, 255)),
        ((5, 18, 35), (10, 60, 120), (0, 170, 255)),
        ((35, 10, 10), (90, 20, 20), (255, 70, 70)),
        ((35, 20, 5), (100, 50, 10), (255, 160, 0)),
        ((30, 30, 5), (90, 90, 20), (255, 230, 0)),
        ((12, 30, 30), (20, 100, 100), (0, 255, 255)),
        ((25, 10, 35), (60, 20, 100), (220, 120, 255)),
    ]

    bg1, bg2, accent = random.choice(palettes)

    img = Image.new("RGB", (width, height), bg1)
    draw = ImageDraw.Draw(img)

    # ---------------- BACKGROUND ----------------
    for y in range(height):
        ratio = y / height
        r = int(bg1[0] * (1 - ratio) + bg2[0] * ratio)
        g = int(bg1[1] * (1 - ratio) + bg2[1] * ratio)
        b = int(bg1[2] * (1 - ratio) + bg2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # stars/grid texture
    for _ in range(250):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(255, 255, 255))

    # blur glow circles
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    for _ in range(8):
        x = random.randint(0, width)
        y = random.randint(0, height)
        s = random.randint(150, 300)
        odraw.ellipse((x, y, x+s, y+s), fill=(*accent, 40))

    overlay = overlay.filter(ImageFilter.GaussianBlur(80))
    img.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(img)

    # ---------------- FONTS ----------------
    try:
        title_font = ImageFont.truetype("cfont.ttf", 90)
        name_font = ImageFont.truetype("f.ttf", 25)
        small_font = ImageFont.truetype("f.ttf", 26)
        count_font = ImageFont.truetype("cfont.ttf", 34)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        count_font = ImageFont.load_default()

    # ---------------- MAIN OUTER ----------------
    draw.rounded_rectangle(
        (25, 25, 1255, 695),
        radius=28,
        fill=(4, 8, 20),
        outline=accent,
        width=3
    )

    # glow corners
    for x, y in [(25,25),(1225,25),(25,665),(1225,665)]:
        draw.rectangle((x, y, x+30, y+4), fill=accent)
        draw.rectangle((x, y, x+4, y+30), fill=accent)

    # ---------------- TITLE BOX ----------------
    draw.rounded_rectangle(
        (300, 20, 980, 145),
        radius=20,
        fill=(6, 12, 24),
        outline=accent,
        width=3
    )

    title = "LEADERBOARD"

    # 3D metallic text
    draw.text((352, 42), title, font=title_font, fill=(20,20,20))
    draw.text((348, 38), title, font=title_font, fill=(90,90,90))
    draw.text((344, 32), title, font=title_font, fill=(255,255,255))

    draw.text((560, 118), "PREMIUM", font=small_font, fill=accent)

    # left logo
    draw.text((45, 45), "AXIOM\nRANKING", font=small_font, fill=(255,255,255))

    # right premium box
    draw.rounded_rectangle(
        (1035, 35, 1230, 120),
        radius=16,
        fill=(6,12,24),
        outline=accent,
        width=2
    )
    draw.text((1070, 48), "AXIOM BOT", font=small_font, fill=(255,255,255))
    draw.text((1088, 82), "PREMIUM", font=name_font, fill=accent)

    def medal(rank):
        return {1:"🥇",2:"🥈",3:"🥉"}.get(rank, "👤")

    max_count = ranking[0][2] if ranking else 1
    start_y = 190

    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        y = start_y + ((i-1)*48)

        clean_name = unidecode(str(name)).strip()
        clean_name = re.sub(r'[^a-zA-Z0-9 ]+', '', clean_name)
        clean_name = " ".join(clean_name.split())[:18] or "Unknown"

        # row bg
        draw.rounded_rectangle(
            (45, y-8, 1035, y+34),
            radius=10,
            fill=(5, 12, 28),
            outline=accent,
            width=1
        )

        draw.text((60, y), medal(i), font=name_font, fill=(255,255,255))
        draw.text((120, y), clean_name, font=name_font, fill=(255,255,255))

        # bar bg
        bar_x = 430
        full_width = 470
        filled = int((count / max_count) * full_width)

        draw.rounded_rectangle(
            (bar_x, y+4, bar_x+full_width, y+26),
            radius=8,
            fill=(10,20,40),
            outline=accent,
            width=1
        )

        # 3d gradient bar
        for k in range(filled):
            ratio = k / max(filled,1)
            color = (
                int(accent[0]*(1-ratio)+20*ratio),
                int(accent[1]*(1-ratio)+80*ratio),
                int(accent[2]*(1-ratio)+255*ratio)
            )
            draw.line(
                [(bar_x+k, y+5), (bar_x+k, y+25)],
                fill=color
            )

        draw.polygon([
            (bar_x+filled, y+4),
            (bar_x+filled+10, y+4),
            (bar_x+filled, y+26),
            (bar_x+filled-10, y+26)
        ], fill=(255,255,255))

        # count box
        draw.rounded_rectangle(
            (1080, y-3, 1215, y+30),
            radius=8,
            fill=(5,12,28),
            outline=accent,
            width=1
        )
        draw.text((1110, y), str(count), font=count_font, fill=accent)

    total = sum(x[2] for x in ranking)

    # bottom panels
    draw.rounded_rectangle(
        (55, 640, 390, 690),
        radius=14,
        fill=(6,12,24),
        outline=accent,
        width=2
    )
    draw.text((85, 653), f"TOTAL MSGS: {total}", font=small_font, fill=(255,255,255))

    draw.rounded_rectangle(
        (450, 640, 820, 690),
        radius=14,
        fill=(6,12,24),
        outline=accent,
        width=2
    )
    draw.text((540, 653), f"MODE : {mode.upper()}", font=small_font, fill=accent)

    draw.text((1010, 653), "POWERED BY AXIOM", font=name_font, fill=(255,255,255))

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


@bot.on_message(filters.command("test"))
async def test(_, message):
    await message.reply_text(p(
        f'Premium test <tg-emoji emoji-id="6260064483465502441">❤️‍🔥</tg-emoji>'
    )),
    parse_mode=PREMIUM_PARSE
    

@bot.on_message(filters.command("start"))
async def start_cmd(_, message):
    await message.reply_text(
        p(
"""<tg-emoji emoji-id="5040016479722931047">✨</tg-emoji> <b>Welcome To Axiom Ranking Bot <tg-emoji emoji-id="6100570056884752399">💠</tg-emoji> </b>

<b>Track group chats easily 📊</b>

<b> <tg-emoji emoji-id="6260304872785059395">🔵</tg-emoji> Commands:</b>
• /ranking <b>- show leaderboard <tg-emoji emoji-id="6260273356315040975">💀</tg-emoji> </b>
"""     
        ),
        parse_mode=PREMIUM_PARSE,
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
                loading = await message.reply_text(
                    "⚡ Fetching leaderboard by Axiom Bots..."
                )
            
                text, ranking = await build_board(
                    message.chat.id,
                    "overall"
                )
            
                photo = generate_leaderboard_image(
                    ranking,
                    "overall"
                )
            
                await loading.delete()
            
                await message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=get_buttons("overall"),
                    has_spoiler=True
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
@bot.on_callback_query()
async def callback_handler(_, query):
    try:
        mode = query.data

        await query.answer("Updating...")

        text, ranking = await build_board(
            query.message.chat.id,
            mode
        )

        photo = generate_leaderboard_image(
            ranking,
            mode
        )

        await bot.edit_message_media(
            chat_id=query.message.chat.id,
            message_id=query.message.id,
            media=InputMediaPhoto(
                media=photo,
                caption=text,
                has_spoiler=True
            ),
            reply_markup=get_buttons(mode)
        )

    except Exception as e:
        print(f"CALLBACK ERROR: {e}")


if __name__ == "__main__":
    print("Bot running...")
    bot.run()
