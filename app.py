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
    ]

    bg1, bg2, accent = random.choice(palettes)

    img = Image.new("RGB", (width, height), bg1)
    draw = ImageDraw.Draw(img)

    # ---------------- background gradient ----------------
    for y in range(height):
        ratio = y / height
        r = int(bg1[0] * (1 - ratio) + bg2[0] * ratio)
        g = int(bg1[1] * (1 - ratio) + bg2[1] * ratio)
        b = int(bg1[2] * (1 - ratio) + bg2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # stars
    for _ in range(250):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        draw.point((x, y), fill=(255, 255, 255))

    # glow circles
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    for _ in range(8):
        x = random.randint(0, width)
        y = random.randint(0, height)
        s = random.randint(150, 320)
        odraw.ellipse(
            (x, y, x + s, y + s),
            fill=(*accent, 35)
        )

    overlay = overlay.filter(ImageFilter.GaussianBlur(80))
    img.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(img)

    # ---------------- fonts ----------------
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 78)
        name_font = ImageFont.truetype("f.ttf", 24)
        small_font = ImageFont.truetype("f.ttf", 26)
        count_font = ImageFont.truetype("arialbd.ttf", 32)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        count_font = ImageFont.load_default()

    # ---------------- outer border ----------------
    draw.rounded_rectangle(
        (20, 20, 1260, 700),
        radius=28,
        fill=(4, 8, 20),
        outline=accent,
        width=3
    )

    # glow corners
    corners = [(20, 20), (1230, 20), (20, 670), (1230, 670)]
    for x, y in corners:
        draw.rectangle((x, y, x + 30, y + 4), fill=accent)
        draw.rectangle((x, y, x + 4, y + 30), fill=accent)

    # ---------------- title box ----------------
    draw.rounded_rectangle(
        (285, 18, 995, 150),
        radius=24,
        fill=(7, 14, 28),
        outline=accent,
        width=3
    )

    title = "LEADERBOARD"

    draw.text((347, 45), title, font=title_font, fill=(25, 25, 25))
    draw.text((343, 40), title, font=title_font, fill=(70, 70, 70))
    draw.text((340, 35), title, font=title_font, fill=(170, 170, 170))
    draw.text((337, 30), title, font=title_font, fill=(255, 255, 255))

    draw.text((565, 118), "PREMIUM", font=small_font, fill=accent)

    # ---------------- left branding ----------------
    draw.text(
        (45, 45),
        "AXIOM\nRANKING",
        font=small_font,
        fill=(255, 255, 255)
    )

    # ---------------- right premium box ----------------
    draw.rounded_rectangle(
        (1035, 30, 1230, 118),
        radius=18,
        fill=(7, 14, 28),
        outline=accent,
        width=2
    )

    draw.text((1070, 48), "AXIOM BOT", font=small_font, fill=(255, 255, 255))
    draw.text((1088, 82), "PREMIUM", font=name_font, fill=accent)

    def medal(rank):
        return {
            1: "🥇",
            2: "🥈",
            3: "🥉"
        }.get(rank, "👤")

    max_count = ranking[0][2] if ranking else 1
    start_y = 195

    # ---------------- rows ----------------
    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        y = start_y + ((i - 1) * 49)

        clean_name = unidecode(str(name)).strip()
        clean_name = re.sub(r'[^a-zA-Z0-9 ]+', '', clean_name)
        clean_name = " ".join(clean_name.split())

        if not clean_name:
            clean_name = "Unknown"

        clean_name = clean_name[:18]

        # row bg
        draw.rounded_rectangle(
            (40, y - 7, 1050, y + 38),
            radius=11,
            fill=(5, 12, 28),
            outline=accent,
            width=1
        )

        # medal
        draw.text(
            (58, y + 2),
            medal(i),
            font=name_font,
            fill=(255, 255, 255)
        )

        # username
        draw.text(
            (120, y + 2),
            clean_name,
            font=name_font,
            fill=(255, 255, 255)
        )

        # bar
        bar_x = 420
        bar_y = y + 6
        full_width = 480
        filled = int((count / max_count) * full_width)

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + full_width, bar_y + 28),
            radius=10,
            fill=(7, 18, 35),
            outline=accent,
            width=1
        )

        for k in range(filled):
            ratio = k / max(filled, 1)
            color = (
                int(accent[0] * (1 - ratio) + 40 * ratio),
                int(accent[1] * (1 - ratio) + 120 * ratio),
                255
            )
            draw.line(
                [(bar_x + k, bar_y + 2), (bar_x + k, bar_y + 26)],
                fill=color
            )

        if filled > 15:
            draw.polygon(
                [
                    (bar_x + filled - 10, bar_y),
                    (bar_x + filled, bar_y),
                    (bar_x + filled - 10, bar_y + 28),
                    (bar_x + filled - 20, bar_y + 28),
                ],
                fill=(255, 255, 255)
            )

        # count box
        draw.rounded_rectangle(
            (1090, y - 2, 1230, y + 34),
            radius=8,
            fill=(5, 12, 28),
            outline=accent,
            width=1
        )

        draw.text(
            (1130, y + 3),
            str(count),
            font=count_font,
            fill=accent
        )

    total_msgs = sum(x[2] for x in ranking)

    # ---------------- bottom panels ----------------
    draw.rounded_rectangle(
        (55, 646, 390, 700),
        radius=14,
        fill=(7, 14, 28),
        outline=accent,
        width=2
    )

    draw.text(
        (85, 662),
        f"TOTAL MSGS: {total_msgs}",
        font=small_font,
        fill=(255, 255, 255)
    )

    draw.rounded_rectangle(
        (450, 646, 820, 700),
        radius=14,
        fill=(7, 14, 28),
        outline=accent,
        width=2
    )

    draw.text(
        (545, 662),
        f"MODE : {mode.upper()}",
        font=small_font,
        fill=accent
    )

    draw.text(
        (1015, 662),
        "POWERED BY AXIOM",
        font=name_font,
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
