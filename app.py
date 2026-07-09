import re
import os
import random
from datetime import datetime, timedelta
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

word_games = {}

WORD_BANK = [
    "zealand", "target", "rocket", "shadow", "hunter", "galaxy", "thunder", "diamond", "pirate", "winter",
    "summer", "falcon", "dragon", "planet", "matrix", "legend", "oxygen", "random", "victory", "leader",
    "castle", "forest", "orange", "silver", "golden", "danger", "future", "screen", "button", "master",
    "secret", "battle", "friend", "energy", "gaming", "coffee", "school", "doctor", "travel", "market",
    "pencil", "camera", "monkey", "rabbit", "tiger", "island", "bridge", "desert", "signal", "system",
    "memory", "native", "flower", "basket", "window", "mobile", "laptop", "charge", "stream", "chance",
    "wonder", "speech", "answer", "number", "people", "family", "street", "office", "nature", "puzzle",
    "winner", "loser", "bright", "strong", "silent", "simple", "smooth", "purple", "yellow", "magnet",
    "planet", "cosmic", "impact", "storm", "cyber", "venom", "joker", "signal", "strike", "vision",
    "axiom", "chatfight", "premium", "ranking", "message", "telegram", "trigger", "speed", "typing", "leaderboard",
]

WORD_GAME_SECONDS = 600


def today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def week():
    return datetime.utcnow().strftime("%Y-%W")


def get_buttons(active):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"⏺️ 𝐎‌ᴠєꝛᴧʟʟ {'✅' if active=='overall' else ''}",
                callback_data="overall"
            )
        ],
        [
            InlineKeyboardButton(
                f"⏺️ 𝐓‌σᴅᴧʏ {'✅' if active=='today' else ''}",
                callback_data="today"
            ),
            InlineKeyboardButton(
                f"⏺️ 𝐖‌єєᴋ {'✅' if active=='week' else ''}",
                callback_data="week"
            )
        ]
    ])

import random
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from unidecode import unidecode



def normalize_answer(text):
    return re.sub(r"[^a-z0-9]+", "", unidecode(str(text)).lower())


def pick_random_word():
    return random.choice(WORD_BANK).upper()


def generate_word_image(word):
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), (3, 3, 6))
    draw = ImageDraw.Draw(img)

    # dark red/black premium background, close to the shared ChatFight style
    for y in range(height):
        ratio = y / height
        r = int(5 + 22 * ratio)
        g = int(2 + 2 * ratio)
        b = int(4 + 6 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for i in range(22):
        offset = i * 28
        odraw.arc(
            (260 + offset, 260 - offset // 3, 1320 + offset, 940 - offset // 2),
            190,
            355,
            fill=(255, 45, 45, 80),
            width=3,
        )
    for i in range(14):
        offset = i * 22
        odraw.arc(
            (-140 + offset, -80 + offset, 460 + offset, 380 + offset),
            20,
            260,
            fill=(255, 55, 55, 70),
            width=3,
        )
    overlay = overlay.filter(ImageFilter.GaussianBlur(0.4))
    img.paste(overlay, (0, 0), overlay)
    draw = ImageDraw.Draw(img)

    try:
        logo_font = ImageFont.truetype("cfont.ttf", 42)
        word_font = ImageFont.truetype("cfont.ttf", 92)
        hint_font = ImageFont.truetype("f.ttf", 24)
    except Exception:
        logo_font = ImageFont.load_default()
        word_font = ImageFont.load_default()
        hint_font = ImageFont.load_default()

    logo_path = os.getenv("WORD_GAME_LOGO_PATH")
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA").resize((92, 92))
            mask = Image.new("L", logo.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 92, 92), fill=255)
            img.paste(logo, (62, 48), mask)
            draw.text((175, 55), "AXIOM", font=logo_font, fill=(255, 255, 255))
            draw.text((175, 105), "CHATFIGHT BOT", font=hint_font, fill=(230, 230, 230))
        except Exception:
            draw.text((70, 55), "AXIOM", font=logo_font, fill=(255, 255, 255))
            draw.text((70, 105), "CHATFIGHT BOT", font=hint_font, fill=(230, 230, 230))
    else:
        draw.text((70, 55), "AXIOM", font=logo_font, fill=(255, 255, 255))
        draw.text((70, 105), "CHATFIGHT BOT", font=hint_font, fill=(230, 230, 230))

    bbox = draw.textbbox((0, 0), word, font=word_font)
    text_w = bbox[2] - bbox[0]
    x = (width - text_w) // 2
    y = 315
    for dx, dy, fill in [(5, 6, (40, 0, 0)), (2, 3, (120, 20, 20)), (0, 0, (255, 255, 255))]:
        draw.text((x + dx, y + dy), word, font=word_font, fill=fill)

    underline_w = min(520, text_w + 60)
    underline_x = (width - underline_w) // 2
    for dot_x in range(underline_x, underline_x + underline_w, 18):
        draw.ellipse((dot_x, y + 110, dot_x + 8, y + 118), fill=(255, 255, 255))

    draw.text((55, 660), "⚡ Be the first to write this word in chat", font=hint_font, fill=(255, 255, 255))

    file_path = f"word_game_{word.lower()}.png"
    img.save(file_path)
    return file_path


async def start_word_game(message):
    word = pick_random_word()
    word_games[message.chat.id] = {
        "word": word,
        "expires_at": datetime.utcnow() + timedelta(seconds=WORD_GAME_SECONDS),
    }
    photo = generate_word_image(word)
    await message.reply_photo(
        photo=photo,
        caption=(
            "<b>ChatFight ⚡</b>\n\n"
            "⚡ Be the first to write the word shown in this photo.\n"
            f"⏱ <b>Time remaining:</b> {WORD_GAME_SECONDS // 60} minutes\n\n"
            " हर game me random word aayega."
        ),
        parse_mode=ParseMode.HTML,
    )


def generate_leaderboard_image(ranking, mode):
    TEXT_WHITE = (255, 255, 255)
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
        smalll_font = ImageFont.truetype("f.ttf", 55)
        count_font = ImageFont.truetype("cfont.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        smalll_font = ImageFont.load_default()
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
        (47, 43),
        "Dev:- Maanav",
        font=small_font,
        fill=TEXT_WHITE
    )

    draw.text(
        (1010, 60),
        mode.upper(),
        font=smalll_font,
        fill=TEXT_WHITE
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
            clean_name = "AxiomUser"
        
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

    text = f"📈 <b>𝐋‌𝐄‌𝐀‌𝐃‌𝐄‌𝐑‌𝐁‌𝐎‌𝐀‌𝐑‌𝐃‌ ({mode.upper()})</b>\n\n"

    total = 0
    for i, (name, user_id, count) in enumerate(ranking[:10], start=1):
        clean_name = re.sub(r"[<>&]", "", name)

        mention = f'<a href="tg://user?id={user_id}">{clean_name}</a>'

        text += f"{i}. {mention} ➜ {count}\n"
        total += count

    text += f"\n✉️ <b>𝐓‌σᴛᴧʟ 𝐌‌єssᴧɢєs:: {total}</b>"

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
"""<tg-emoji emoji-id="5040016479722931047">✨</tg-emoji> <b>𝐖‌єʟᴄσϻє 𝐓‌σ 𝐀‌xɪσϻ 𝐑‌ᴧηᴋɪηɢ 𝐁‌σᴛ <tg-emoji emoji-id="6100570056884752399">💠</tg-emoji> </b>

<b>𝐓‌ꝛᴧᴄᴋ ɢꝛσυᴘ ᴄʜᴧᴛs єᴧsɪʟʏ 📊</b>

<b> <tg-emoji emoji-id="6260304872785059395">🔵</tg-emoji> 𝐂‌σϻϻᴧηᴅs:</b>
• /ranking <b>- sʜσᴡ ʟєᴧᴅєꝛʙσᴧꝛᴅ <tg-emoji emoji-id="6260273356315040975">💀</tg-emoji> </b>
• /wordfight <b>- random word mini-game start karo ⚡</b>
"""     
        ),
        parse_mode=PREMIUM_PARSE,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "☊₊ ᴧᴅᴅ ϻє ᴛσ ʏσυʀ ᴄʜᴧᴛ ₊☊",
                    url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"
                )
            ],
            [
                InlineKeyboardButton("ᴧxɪσϻ υᴘᴅᴧᴛєs ⎘", url="https://t.me/axiombots"),
                InlineKeyboardButton("ᴧxɪσϻ sυᴘᴘσʀᴛ ☏︎", url="https://t.me/axlomm")
            ],
            [
                InlineKeyboardButton("⌯ ᴧxɪσϻ ⌯", url="https://t.me/xomnv"),
                InlineKeyboardButton("🛠️ sσυʀᴄє ᴄσᴅє", url="https://github.com/maanavbaby/AxiomRanking")
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

            if cmd.startswith("/wordfight") or cmd.startswith("/word"):
                await start_word_game(message)
                return

            if cmd.startswith("/ranking"):
                loading = await message.reply_text(
                    "⚡ 𝐅‌єᴛᴄʜɪηɢ ʟєᴧᴅєꝛʙσᴧꝛᴅ ʙʏ 𝐀‌xɪσϻ𝐁‌σᴛ..."
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
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_buttons("overall"),
                    has_spoiler=True
                )
                return

        game = word_games.get(message.chat.id)
        if game and message.text:
            if datetime.utcnow() > game["expires_at"]:
                word_games.pop(message.chat.id, None)
                await message.reply_text("❌ <b>Time's up!</b> /wordfight se naya random word start karo.", parse_mode=ParseMode.HTML)
            elif normalize_answer(message.text) == normalize_answer(game["word"]):
                word_games.pop(message.chat.id, None)
                await users.update_one(
                    {"chat_id": message.chat.id, "user_id": message.from_user.id},
                    {
                        "$inc": {"overall": 5, f"daily.{today()}": 5, f"weekly.{week()}": 5},
                        "$set": {"name": message.from_user.first_name},
                    },
                    upsert=True,
                )
                await message.reply_text(
                    f"💪 <b>Time goal!</b> {message.from_user.mention}\n"
                    "You guessed the word!\n"
                    "+5 points added to leaderboard.",
                    parse_mode=ParseMode.HTML,
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

        user_data = await users.find_one({
            "chat_id": message.chat.id,
            "user_id": message.from_user.id
        })
        
        current = user_data.get("overall", 0)
        
        if current > 0 and current % 100 == 0:
            await message.reply_text(
                f"<b>🎉 𝐂‌σηɢꝛᴧᴛυʟᴧᴛɪσηs</b>  {message.from_user.mention}!\n\n"
                f"<b>𝐘‌συ ᴄσϻᴘʟєᴛєᴅ</b> {current} <b>ϻєssᴧɢєs.</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🔥 𝐕‌ɪєᴡ 𝐑‌ᴧηᴋɪηɢ",
                            callback_data="overall"
                        )
                    ]
                ])
            )
        print(f"Count updated: {message.from_user.first_name}")

    except Exception as e:
        print(f"COUNT ERROR: {e}")


@bot.on_callback_query()
@bot.on_callback_query()
async def callback_handler(_, query):
    try:
        mode = query.data

        await query.answer("Updating Leaderboard By AxiomBot...")

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
                parse_mode=ParseMode.HTML,
                has_spoiler=True
            ),
            reply_markup=get_buttons(mode)
        )

    except Exception as e:
        print(f"CALLBACK ERROR: {e}")


if __name__ == "__main__":
    print("Bot running...")
    bot.run()
