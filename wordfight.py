"""Standalone random word-fight mini-game helpers for AxiomRanking.

This file intentionally keeps the feature separate from app.py so the existing
ranking bot code is not touched. Import and wire these helpers from the bot only
when you want to enable the mini-game.
"""

import os
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from unidecode import unidecode

WORD_GAMES = {}
WORD_GAME_SECONDS = 600
WORD_GAME_REWARD = 5

WORD_BANK = [
    "zealand", "target", "rocket", "shadow", "hunter", "galaxy", "thunder", "diamond", "pirate", "winter",
    "summer", "falcon", "dragon", "planet", "matrix", "legend", "oxygen", "random", "victory", "leader",
    "castle", "forest", "orange", "silver", "golden", "danger", "future", "screen", "button", "master",
    "secret", "battle", "friend", "energy", "gaming", "coffee", "school", "doctor", "travel", "market",
    "pencil", "camera", "monkey", "rabbit", "tiger", "island", "bridge", "desert", "signal", "system",
    "memory", "native", "flower", "basket", "window", "mobile", "laptop", "charge", "stream", "chance",
    "wonder", "speech", "answer", "number", "people", "family", "street", "office", "nature", "puzzle",
    "winner", "loser", "bright", "strong", "silent", "simple", "smooth", "purple", "yellow", "magnet",
    "cosmic", "impact", "storm", "cyber", "venom", "joker", "strike", "vision", "typing", "trigger",

    "axiom", "chatfight", "premium", "ranking", "message", "telegram", "leaderboard", "speed", "power", "black",

    "axiom", "chatfight", "premium", "ranking", "message", "telegram", "leaderboard", "speed", "power", 
    "black", "Axiom", "OwnerAxiom", "Maanav", "AxiomBots"

]


def normalize_answer(text: str) -> str:
    """Normalize a chat answer so symbols/case do not block a correct guess."""
    return re.sub(r"[^a-z0-9]+", "", unidecode(str(text)).lower())


def pick_random_word() -> str:
    """Return a new random uppercase challenge word."""
    return random.choice(WORD_BANK).upper()


def _load_font(font_path: str, size: int):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


def _paste_custom_logo(img: Image.Image, draw: ImageDraw.ImageDraw, logo_path: str | None, logo_font, hint_font) -> None:
    if not logo_path or not os.path.exists(logo_path):

        draw.text((70, 55), "AXIOM", font=logo_font, fill=(255, 255, 255))
        draw.text((70, 105), "CHATFIGHT BOT", font=hint_font, fill=(230, 230, 230))

        draw.text((70, 55), "Axiom—chatfight", font=logo_font, fill=(255, 255, 255))
        draw.text((70, 105), "© @AxiomBots", font=hint_font, fill=(230, 230, 230))

        return

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



def _draw_texture(draw: ImageDraw.ImageDraw, width: int, height: int, alpha: int = 24) -> None:
    for _ in range(900):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        shade = random.randint(25, 90)
        draw.point((x, y), fill=(shade, shade, shade, alpha))


def _draw_chalk_doodles(draw: ImageDraw.ImageDraw, width: int, height: int, accent=(255, 225, 150)) -> None:
    white = (245, 240, 230, 210)
    gold = (*accent, 220)

    # corner star/sparkles
    draw.line((0, 52, 155, 0), fill=gold, width=7)
    draw.line((62, 0, 62, 105), fill=gold, width=7)
    draw.polygon([(60, 170), (72, 205), (105, 218), (72, 231), (60, 266), (48, 231), (15, 218), (48, 205)], fill=gold)
    draw.polygon([(725, 600), (738, 633), (770, 646), (738, 659), (725, 692), (712, 659), (680, 646), (712, 633)], fill=gold)

    # chalk circles / loops
    for i in range(3):
        draw.ellipse((-80 + i * 25, 360 + i * 20, 45 + i * 25, 520 + i * 20), outline=white, width=4)
    for i in range(5):
        draw.arc((340 + i * 55, 610 - (i % 2) * 55, 465 + i * 55, 735 - (i % 2) * 55), 180, 520, fill=white, width=3)

    # top doodles
    for x in [250, 310, 370, 430]:
        draw.ellipse((x, random.randint(25, 85), x + 11, random.randint(95, 145)), fill=white)
    for x in [610, 675, 740]:
        draw.ellipse((x, -45, x + 42, 105), outline=white, width=5)
    for x in range(1030, 1260, 42):
        draw.arc((x, 45, x + 75, 105), 180, 360, fill=gold, width=6)

    # right side ladder
    for y in range(195, 445, 38):
        draw.line((1215, y, 1278, y + 5), fill=white, width=3)
    draw.line((1230, 170, 1230, 470), fill=white, width=3)
    draw.line((1268, 165, 1268, 475), fill=white, width=3)

    # lower right scribble
    for i in range(6):
        draw.arc((1110 + i * 7, 590 - i * 9, 1360 - i * 8, 815 - i * 4), 195, 345, fill=gold, width=5)


def _draw_word_background(width: int, height: int) -> Image.Image:
    style = random.randint(0, 9)
    img = Image.new("RGB", (width, height), (4, 4, 6))
    draw = ImageDraw.Draw(img)

    palettes = [
        ((5, 5, 8), (32, 5, 6), (255, 55, 55)),       # red wave
        ((3, 9, 18), (2, 42, 75), (0, 210, 255)),      # blue neon
        ((8, 4, 18), (48, 12, 82), (205, 90, 255)),    # purple
        ((3, 20, 14), (4, 70, 50), (0, 255, 165)),     # green
        ((16, 10, 2), (92, 48, 5), (255, 190, 70)),    # amber
        ((5, 5, 5), (28, 28, 28), (255, 225, 150)),    # chalkboard
        ((10, 8, 18), (16, 22, 45), (80, 145, 255)),   # night grid
        ((20, 4, 17), (75, 5, 42), (255, 80, 180)),    # magenta
        ((2, 16, 20), (4, 65, 75), (80, 255, 240)),    # teal
        ((18, 16, 10), (54, 48, 34), (245, 240, 220)), # paper dark
    ]
    bg1, bg2, accent = palettes[style]

    for y in range(height):
        ratio = y / height
        draw.line(
            [(0, y), (width, y)],
            fill=(
                int(bg1[0] * (1 - ratio) + bg2[0] * ratio),
                int(bg1[1] * (1 - ratio) + bg2[1] * ratio),
                int(bg1[2] * (1 - ratio) + bg2[2] * ratio),
            ),
        )

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    if style == 0:
        for i in range(22):
            offset = i * 28
            odraw.arc((260 + offset, 260 - offset // 3, 1320 + offset, 940 - offset // 2), 190, 355, fill=(*accent, 80), width=3)
        for i in range(14):
            offset = i * 22
            odraw.arc((-140 + offset, -80 + offset, 460 + offset, 380 + offset), 20, 260, fill=(*accent, 70), width=3)
    elif style == 1:
        for x in range(-120, width, 95):
            odraw.line((x, 0, x + 360, height), fill=(*accent, 45), width=2)
        for y in range(80, height, 85):
            odraw.line((0, y, width, y + 40), fill=(*accent, 40), width=2)
    elif style == 2:
        for _ in range(16):
            x = random.randint(-120, width)
            y = random.randint(-80, height)
            size = random.randint(130, 360)
            odraw.ellipse((x, y, x + size, y + size), outline=(*accent, 75), width=4)
    elif style == 3:
        for _ in range(55):
            x = random.randint(0, width)
            y = random.randint(0, height)
            odraw.polygon([(x, y - 18), (x + 18, y), (x, y + 18), (x - 18, y)], outline=(*accent, 85))
    elif style == 4:
        for i in range(0, width, 70):
            odraw.arc((i - 120, 510, i + 190, 800), 200, 340, fill=(*accent, 95), width=5)
        for _ in range(28):
            x = random.randint(0, width)
            odraw.line((x, 0, x - 120, 170), fill=(*accent, 55), width=3)
    elif style == 5:
        _draw_chalk_doodles(odraw, width, height, accent)
    elif style == 6:
        for x in range(0, width, 80):
            odraw.line((x, 0, x, height), fill=(*accent, 45), width=1)
        for y in range(0, height, 80):
            odraw.line((0, y, width, y), fill=(*accent, 45), width=1)
        for _ in range(80):
            x = random.randint(0, width)
            y = random.randint(0, height)
            odraw.ellipse((x, y, x + 3, y + 3), fill=(*accent, 160))
    elif style == 7:
        for i in range(18):
            odraw.rounded_rectangle((80 + i * 45, 70 + i * 14, 1260 - i * 18, 650 - i * 12), radius=35, outline=(*accent, 50), width=4)
    elif style == 8:
        for i in range(26):
            y = i * 35
            odraw.line((0, y, width, y + random.randint(-45, 45)), fill=(*accent, 45), width=3)
        for _ in range(20):
            x = random.randint(0, width)
            y = random.randint(0, height)
            odraw.arc((x, y, x + 150, y + 100), 20, 320, fill=(*accent, 80), width=3)
    else:
        for _ in range(36):
            x = random.randint(-50, width)
            y = random.randint(-50, height)
            odraw.rectangle((x, y, x + random.randint(70, 160), y + random.randint(30, 90)), outline=(*accent, 45), width=3)
        _draw_chalk_doodles(odraw, width, height, accent)

    overlay = overlay.filter(ImageFilter.GaussianBlur(0.35))
    img.paste(overlay, (0, 0), overlay)

    texture = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    _draw_texture(ImageDraw.Draw(texture), width, height)
    img.paste(texture, (0, 0), texture)
    return img


def generate_word_image(word: str, output_dir: str = ".", logo_path: str | None = None) -> str:
    """Generate a random ChatFight-style challenge image and return its path."""
    width, height = 1280, 720
    img = _draw_word_background(width, height)
    draw = ImageDraw.Draw(img)

    logo_font = _load_font("cfont.ttf", 42)
    word_font = _load_font("cfont.ttf", 92)

    draw.text((175, 55), "Axiom—chatfight", font=logo_font, fill=(255, 255, 255))
    draw.text((175, 105), "© @AxiomBots ", font=hint_font, fill=(230, 230, 230))


def generate_word_image(word: str, output_dir: str = ".", logo_path: str | None = None) -> str:
    """Generate the black ChatFight-style challenge image and return its path."""
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), (3, 3, 6))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        draw.line([(0, y), (width, y)], fill=(int(5 + 22 * ratio), int(2 + 2 * ratio), int(4 + 6 * ratio)))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for i in range(22):
        offset = i * 28
        odraw.arc((260 + offset, 260 - offset // 3, 1320 + offset, 940 - offset // 2), 190, 355, fill=(255, 45, 45, 80), width=3)
    for i in range(14):
        offset = i * 22
        odraw.arc((-140 + offset, -80 + offset, 460 + offset, 380 + offset), 20, 260, fill=(255, 55, 55, 70), width=3)
    img.paste(overlay.filter(ImageFilter.GaussianBlur(0.4)), (0, 0), overlay)
    draw = ImageDraw.Draw(img)

    logo_font = _load_font("f.ttf", 42)
    word_font = _load_font("f.ttf", 92)

    hint_font = _load_font("f.ttf", 24)

    _paste_custom_logo(img, draw, logo_path or os.getenv("WORD_GAME_LOGO_PATH"), logo_font, hint_font)

    word = word.upper()
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

    draw.text((55, 660), "Be the first to write this word in chat", font=hint_font, fill=(255, 255, 255))

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    file_path = Path(output_dir) / f"word_game_{normalize_answer(word)}.png"
    img.save(file_path)
    return str(file_path)


def start_game(chat_id: int, output_dir: str = ".", logo_path: str | None = None) -> dict:
    """Create a new game for a chat and return word/photo/caption metadata."""
    word = pick_random_word()
    WORD_GAMES[chat_id] = {
        "word": word,
        "expires_at": datetime.utcnow() + timedelta(seconds=WORD_GAME_SECONDS),
    }
    photo = generate_word_image(word, output_dir=output_dir, logo_path=logo_path)
    return {
        "word": word,
        "photo": photo,
        "caption": (

            "<b>ChatFight ⚡</b>\n\n"
            "⚡ Be the first to write the word shown in this photo.\n"
            f"⏱ <b>Time remaining:</b> {WORD_GAME_SECONDS // 60} minutes\n\n"

        ),
        "expires_at": WORD_GAMES[chat_id]["expires_at"],
    }


def check_answer(chat_id: int, answer: str) -> dict:
    """Check an answer for a chat and return the result without touching old bot code."""
    game = WORD_GAMES.get(chat_id)
    if not game:
        return {"status": "no_game", "reward": 0}

    if datetime.utcnow() > game["expires_at"]:
        WORD_GAMES.pop(chat_id, None)
        return {"status": "expired", "reward": 0, "word": game["word"]}

    if normalize_answer(answer) == normalize_answer(game["word"]):
        WORD_GAMES.pop(chat_id, None)
        return {"status": "correct", "reward": WORD_GAME_REWARD, "word": game["word"]}

    return {"status": "wrong", "reward": 0}
