import re
import os
import random
import asyncio
import logging
import html
from datetime import datetime, timedelta
from pathlib import Path

from datetime import datetime, timedelta

from unidecode import unidecode
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from premium import p, PREMIUM_PARSE
from wordfight import (
    start_game, 
    check_answer, 
    get_user_status,
    buy_shield,
    cmd_balance, 
    cmd_leaderboard, 
    cmd_profile, 
    perform_rob, 
    perform_kill, 
    transfer_coins
)
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ButtonStyle


LOG_FILE = "bot.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("\nStarting The Axiom Chatfight bot...")
logging.info("\nStarting The Axiom Chatfight bot...")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

SESSION_NAME = f"ranking_bot_{os.getpid()}"

SESSION_NAME = f"ranking_bot_{os.getpid()}"

bot = Client(
    SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
    in_memory=True,
    workdir="/tmp"
)

async def get_target_user(message):
    """Reply ya Username/ID se user dhundhne ka function"""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    
    parts = message.text.split()
    if len(parts) > 1:
        try:
            return await bot.get_users(parts[1])
        except Exception:
            return None
    return None
    
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["ranking_bot"]
users = db["users"]
word_settings = db["word_settings"]
scheduler = AsyncIOScheduler()
custom_wordtime_inputs = {}


def today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def week():
    return datetime.utcnow().strftime("%Y-%W")


def parse_duration(value):
    text = str(value).strip().lower().replace(" ", "")
    if not text:
        return None

    units = {
        "s": 1,
        "sec": 1,
        "secs": 1,
        "second": 1,
        "seconds": 1,
        "m": 60,
        "min": 60,
        "mins": 60,
        "minute": 60,
        "minutes": 60,
        "h": 3600,
        "hr": 3600,
        "hour": 3600,
        "hours": 3600,
        "d": 86400,
        "day": 86400,
        "days": 86400,
    }

    match = re.fullmatch(r"(\d+)([a-z]+)", text)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)
    seconds = amount * units.get(unit, 0)

    if seconds < 10 or seconds > 86400 * 30:
        return None

    return seconds


def format_duration(seconds):
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    if seconds % 86400 == 0:
        value = seconds // 86400
        return f"{value} day{'s' if value != 1 else ''}"
    if seconds % 3600 == 0:
        value = seconds // 3600
        return f"{value} hour{'s' if value != 1 else ''}"
    value = seconds // 60
    return f"{value} minute{'s' if value != 1 else ''}"


def get_chat_config_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏱ 10 sec", callback_data="wordtime:10", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("⏱ 1 min", callback_data="wordtime:60", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("⏱ 10 min", callback_data="wordtime:600", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("⏱ 1 hour", callback_data="wordtime:3600", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("⏱ 1 day", callback_data="wordtime:86400", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("✍️ Custom", callback_data="wordtime:custom", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("❌ Off", callback_data="wordtime:off", style=ButtonStyle.DANGER),
        ]
    ])


async def set_wordtime(chat_id, interval_seconds=None):
    now = datetime.utcnow()

    if interval_seconds is None:
        await word_settings.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": False, "updated_at": now}},
            upsert=True
        )
        return "✅ Auto word game band kar diya."

    await word_settings.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "enabled": True,
                "interval_seconds": interval_seconds,
                "next_run": now + timedelta(seconds=interval_seconds),
                "updated_at": now
            }
        },
        upsert=True
    )
    return f"✅ Auto word game set ho gaya. Ab har {format_duration(interval_seconds)} me random word aayega."


async def send_auto_wordfight(chat_id):
    game = start_game(chat_id)
    await bot.send_photo(
        chat_id=chat_id,
        photo=game["photo"],
        caption=game["caption"],
        parse_mode=ParseMode.HTML
    )


async def run_wordfight_scheduler():
    now = datetime.utcnow()

    async for setting in word_settings.find({"enabled": True, "next_run": {"$lte": now}}):
        chat_id = setting["chat_id"]
        interval_seconds = setting.get("interval_seconds", 3600)
        next_run = now + timedelta(seconds=interval_seconds)

        try:
            await send_auto_wordfight(chat_id)
            
            # Agar successfully bhej diya, to next_run update karo
            await word_settings.update_one(
                {"chat_id": chat_id},
                {"$set": {"next_run": next_run, "updated_at": now}},
                upsert=True
            )
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Agar error permission ya invalid chat ka hai, to us chat ke liye auto-wordfight band kar do
            if "channel_invalid" in error_str or "forbidden" in error_str or "chat_write" in error_str:
                print(f"⚠️ Auto-disabled wordfight for chat {chat_id} (Bot kicked or no permissions).")
                await word_settings.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"enabled": False, "updated_at": now}}
                )
            else:
                # Baaki errors ke liye sirf log karo, next_run update karo
                print(f"AUTO WORDFIGHT ERROR ({chat_id}): {e}")
                await word_settings.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"next_run": next_run, "updated_at": now}},
                    upsert=True
                )


async def is_authorized_config_user(message):
    if OWNER_ID and message.from_user.id == OWNER_ID:
        return True

    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        status = str(member.status).lower()
        return "administrator" in status or "creator" in status or "owner" in status
    except Exception as e:
        logging.exception("AUTH CHECK ERROR: %s", e)
        return False


async def run_git_pull():
    process = await asyncio.create_subprocess_exec(
        "git",
        "pull",
        "--ff-only",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await process.communicate()
    output = stdout.decode(errors="replace").strip()
    return process.returncode, output or "No output"


def trim_output(text, limit=3500):
    if len(text) <= limit:
        return text
    return text[-limit:]


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
import asyncio
import logging
import html
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from unidecode import unidecode


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
        title_font = ImageFont.truetype("f.ttf", 88)
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
• /chatconfig <b>- auto word game settings panel ⚙️</b>

• /logs <b>- bot logs file</b>
• /gitpull <b>- server pe git pull</b>


• /wordfight <b>- random word game start karo ⚡</b>

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


# ==================== SIMPLE REPLY-ONLY ECONOMY COMMANDS ====================
async def get_target_user(message):
    """Sirf reply se user dhundhne ka function"""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None

@bot.on_message(filters.command("bal"))
async def balance_cmd(_, message):
    target = await get_target_user(message)
    if not target:
        return await message.reply_text("❌ Kisi ke message ko reply karke /bal likho!")
    
    me = await bot.get_me()
    if target.is_bot and target.id != me.id:
        return await message.reply_text(" Dusre bots ka balance check nahi kar sakte!")

    text = cmd_balance(target.id, target.first_name)
    await message.reply_text(text, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("top"))
async def top_cmd(_, message):
    text = cmd_leaderboard(10)
    await message.reply_text(text, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("protect") | filters.command("shield"))
async def shield_cmd(_, message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text(
            "️ <b>Protection Shield Shop</b>\n\n"
            "1️ <b>1 Day Shield</b> - 500 coins\n"
            "2️⃣ <b>2 Days Shield</b> - 1500 coins\n"
            "3️⃣ <b>3 Days Shield</b> - 3000 coins\n\n"
            "Usage: <code>/protect 1d</code> | <code>/protect 2d</code> | <code>/protect 3d</code>",
            parse_mode=ParseMode.HTML
        )
    days_input = parts[1].lower()
    if days_input == "1d": days = 1
    elif days_input == "2d": days = 2
    elif days_input == "3d": days = 3
    else:
        return await message.reply_text("❌ Invalid format! Use:\n<code>/protect 1d</code>\n<code>/protect 2d</code>\n<code>/protect 3d</code>", parse_mode=ParseMode.HTML)
    result = buy_shield(message.from_user.id, days)
    await message.reply_text(result["message"], parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("status") | filters.command("mystatus"))
async def status_cmd(_, message):
    text = get_user_status(message.from_user.id)
    await message.reply_text(text, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("profile"))
async def profile_cmd(_, message):
    target = await get_target_user(message)
    if not target:
        return await message.reply_text("❌ Kisi ke message ko reply karke /profile likho!")
    
    me = await bot.get_me()
    if target.is_bot and target.id != me.id:
        return await message.reply_text(" Dusre bots ka profile check nahi kar sakte!")

    text = cmd_profile(message.from_user.id, target.id)
    await message.reply_text(text, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("rob"))
async def rob_cmd(_, message):
    target = await get_target_user(message)
    if not target:
        return await message.reply_text("❌ Kisi ke message ko reply karke /rob likho!")
    if target.id == message.from_user.id:
        return await message.reply_text("❌ Khud ko rob nahi kar sakte!")
    
    me = await bot.get_me()
    if target.is_bot and target.id != me.id:
        return await message.reply_text(" Dusre bots ko rob nahi kar sakte!")

    result = perform_rob(message.from_user.id, target.id)
    target_name = await get_target_display_name(target)
    final_msg = f"🎯 <b>Target: {target_name}</b>\n\n{result['message']}"
    await message.reply_text(final_msg, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("kill"))
async def kill_cmd(_, message):
    target = await get_target_user(message)
    if not target:
        return await message.reply_text("❌ Kisi ke message ko reply karke /kill likho!")
    if target.id == message.from_user.id:
        return await message.reply_text(" Khud ko kill nahi kar sakte!")
    
    me = await bot.get_me()
    if target.is_bot and target.id != me.id:
        return await message.reply_text(" Dusre bots ko kill nahi kar sakte!")

    result = perform_kill(message.from_user.id, target.id)
    target_name = await get_target_display_name(target)
    final_msg = f"💀 <b>Target: {target_name}</b>\n\n{result['message']}"
    await message.reply_text(final_msg, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("give") | filters.command("transfer"))
async def transfer_cmd(_, message):
    target = await get_target_user(message)
    if not target:
        return await message.reply_text("❌ Kisi ke message ko reply karke /give <amount> likho!")
    
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❌ Amount nahi diya! Example: Reply karke /give 100")
    
    try:
        amount = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ Amount number hona chahiye!")
    
    if target.id == message.from_user.id:
        return await message.reply_text("❌ Khud ko transfer nahi kar sakte!")
    
    me = await bot.get_me()
    if target.is_bot and target.id != me.id:
        return await message.reply_text(" Dusre bots ko transfer nahi kar sakte!")
    
    result = transfer_coins(message.from_user.id, target.id, amount)
    target_name = await get_target_display_name(target)
    final_msg = f"💸 <b>Target: {target_name}</b>\n\n{result['message']}"
    await message.reply_text(final_msg, parse_mode=ParseMode.HTML)


@bot.on_message(filters.group & ~filters.service)
async def count_messages(_, message):
    try:
        if not message.from_user:
            return

        if message.text:
            cmd = message.text.split()[0].lower()

            if cmd.startswith("/logs"):
                if not await is_authorized_config_user(message):
                    await message.reply_text("❌ Sirf owner/admin logs dekh sakta hai.")
                    return

                logging.info("/logs requested by %s in %s", message.from_user.id, message.chat.id)
                log_path = Path(LOG_FILE)
                if not log_path.exists():
                    log_path.write_text("No logs yet.\n")

                await message.reply_document(
                    document=str(log_path),
                    caption="📄 Bot logs"
                )
                return

            if cmd.startswith("/gitpull"):
                if not await is_authorized_config_user(message):
                    await message.reply_text("❌ Sirf owner/admin git pull chala sakta hai.")
                    return

                loading = await message.reply_text("🔄 Git pull chal raha hai...")
                code, output = await run_git_pull()
                logging.info("/gitpull by %s in %s returned %s: %s", message.from_user.id, message.chat.id, code, output)
                status = "✅" if code == 0 else "❌"
                await loading.edit_text(
                    f"{status} <b>git pull --ff-only</b> finished with code <code>{code}</code>\n\n"
                    f"<pre>{html.escape(trim_output(output))}</pre>",
                    parse_mode=ParseMode.HTML
                )
                return

            custom_key = (message.chat.id, message.from_user.id)
            custom_expires_at = custom_wordtime_inputs.get(custom_key)
            if custom_expires_at and datetime.utcnow() > custom_expires_at:
                custom_wordtime_inputs.pop(custom_key, None)
                custom_expires_at = None

            if custom_expires_at:
                interval_seconds = parse_duration(message.text)

                if not interval_seconds:
                    await message.reply_text(
                        "❌ Galat time. Aise likho: <code>10 s</code>, <code>10 m</code>, <code>10 h</code>, <code>1 d</code>",
                        parse_mode=ParseMode.HTML
                    )
                    return

                custom_wordtime_inputs.pop(custom_key, None)
                text = await set_wordtime(message.chat.id, interval_seconds)
                await message.reply_text(text)
                return

            if cmd.startswith("/chatconfig"):
                await message.reply_text(
                    "⚙️ <b>Chat Config</b>\n\nAuto random word game ka timer select karo:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_chat_config_buttons()
                )
                return

            if cmd.startswith("/wordfight") or cmd.startswith("/word"):
                game = start_game(message.chat.id)
                await message.reply_photo(
                    photo=game["photo"],
                    caption=game["caption"],
                    parse_mode=ParseMode.HTML
                )
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

        if message.text:
            word_result = check_answer(
                message.chat.id, 
                message.from_user.id, 
                message.from_user.first_name, 
                message.text
            )

            if word_result["status"] == "dead":
                await message.reply_text(word_result["message"], parse_mode=ParseMode.HTML)
                return

            if word_result["status"] == "expired":
                await message.reply_text(
                    "❌ <b>Time's up!</b> /wordfight se naya random word start karo.",
                    parse_mode=ParseMode.HTML
                )
                return

            elif word_result["status"] == "correct":
                await users.update_one(
                    {
                        "chat_id": message.chat.id,
                        "user_id": message.from_user.id
                    },
                    {
                        "$inc": {
                            "overall": word_result["reward"],
                            f"daily.{today()}": word_result["reward"],
                            f"weekly.{week()}": word_result["reward"]
                        },
                        "$set": {
                            "name": message.from_user.first_name
                        }
                    },
                    upsert=True
                )
                await message.reply_text(word_result["message"], parse_mode=ParseMode.HTML)
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
                            callback_data="overall",
                            style=ButtonStyle.SUCCESS,
                        )
                    ]
                ])
            )
        print(f"Count updated: {message.from_user.first_name}")

    except Exception as e:
        logging.exception("COUNT ERROR: %s", e)
        print(f"COUNT ERROR: {e}")

@bot.on_callback_query()
async def callback_handler(_, query):
    try:
        data = query.data

        if data.startswith("wordtime:"):
            value = data.split(":", 1)[1]

            if value == "custom":
                custom_wordtime_inputs[(query.message.chat.id, query.from_user.id)] = datetime.utcnow() + timedelta(minutes=2)
                await query.answer("Custom time bhejo")
                await query.message.reply_text(
                    "✍️ Custom time bhejo. Example:\n"
                    "<code>10 s</code>\n"
                    "<code>10 m</code>\n"
                    "<code>10 h</code>\n"
                    "<code>1 d</code>",
                    parse_mode=ParseMode.HTML
                )
                return

            if value == "off":
                text = await set_wordtime(query.message.chat.id, None)
            else:
                text = await set_wordtime(query.message.chat.id, int(value))

            await query.answer("Saved")
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_chat_config_buttons()
            )
            return

        mode = data

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
        logging.exception("CALLBACK ERROR: %s", e)
        print(f"CALLBACK ERROR: {e}")


if __name__ == "__main__":
    scheduler.add_job(run_wordfight_scheduler, "interval", seconds=5, max_instances=1)
    scheduler.start()
    print("The Axiom Chatfight Bot started Successfully...")
    logging.info("The Axiom Chatfight Bot started Successfully...")
    bot.run()
