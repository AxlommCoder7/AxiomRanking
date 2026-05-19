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
    from PIL import Image, ImageDraw, ImageFont
    import os

    TEMPLATE = "ranking_1.png"

    img = Image.open(TEMPLATE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    try:
        name_font = ImageFont.truetype("f.ttf", 34)
        count_font = ImageFont.truetype("cfont.ttf", 42)
        mode_font = ImageFont.truetype("cfont.ttf", 42)
        total_font = ImageFont.truetype("cfont.ttf", 42)
    except:
        name_font = ImageFont.load_default()
        count_font = ImageFont.load_default()
        mode_font = ImageFont.load_default()
        total_font = ImageFont.load_default()

    max_count = ranking[0][2] if ranking else 1

    # rows positions based on template
    start_y = 286
    gap = 92

    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        y = start_y + (i - 1) * gap

        # clean username
        clean_name = str(name).replace("\n", " ").strip()
        clean_name = clean_name[:18]

        # username
        draw.text(
            (325, y),
            clean_name,
            font=name_font,
            fill=(255, 255, 255)
        )

        # count
        draw.text(
            (2245, y),
            str(count),
            font=count_font,
            fill=(0, 230, 255)
        )

        # progress bar
        bar_x = 960
        bar_y = y + 10
        bar_w = 980
        bar_h = 52

        filled = int((count / max_count) * bar_w)

        # bar fill
        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + filled, bar_y + bar_h),
            radius=12,
            fill=(0, 170, 255)
        )

    total = sum(x[2] for x in ranking)

    # total msgs
    draw.text(
        (260, 1445),
        f"{total:,}",
        font=total_font,
        fill=(0, 230, 255)
    )

    # mode
    draw.text(
        (1180, 1445),
        mode.upper(),
        font=mode_font,
        fill=(0, 230, 255)
    )

    output = "leaderboard.png"
    img.save(output)
    return output

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
