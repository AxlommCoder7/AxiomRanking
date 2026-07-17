"""Enhanced Axiom ChatFight - WITH ALL EXISTING FEATURES + NEW ECONOMY (NO COOLDOWNS)"""

import os
import random
import re
import sqlite3
from datetime import datetime, timedelta
from uuid import uuid4
from pathlib import Path
from typing import Optional, Dict, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from unidecode import unidecode

# ==================== DATABASE & ECONOMY CONFIG ====================
DATABASE_PATH = "axiom_chatfight.db"
WORD_GAME_SECONDS = 600
BASE_REWARD = 10  # Max reward for instant answer
MIN_REWARD = 1
ROB_COOLDOWN_HOURS = 0  # NO COOLDOWN
ROB_SUCCESS_RATE = 0.65
ROB_PERCENTAGE = 0.15
KILL_COOLDOWN_HOURS = 0  # NO COOLDOWN
KILL_COST = 50
TRANSFER_MIN = 10

# ==================== OLD WORD BANK (UNCHANGED) ====================
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
    "axiom", "chatfight", "premium", "ranking", "message", "telegram", "leaderboard", "speed", "power", 
    "black", "Axiom", "OwnerAxiom", "Maanav", "AxiomBots",
    "ability", "academy", "account", "action", "adventure", "airplane", "airport", "alchemy",
    "anchor", "ancient", "android", "angel", "animal", "anthem", "apollo", "archive",
    "arena", "armor", "arrow", "artist", "asteroid", "atomic", "autumn", "avalanche",
    "backpack", "balance", "balloon", "banana", "barcode", "battery", "beacon", "beauty",
    "because", "believe", "bicycle", "binary", "biology", "blanket", "blizzard", "blossom",
    "blueprint", "booster", "border", "borrow", "boulder", "bravery", "breeze", "brother",
    "browser", "builder", "bullet", "butter", "buttoned",
    "cactus", "captain", "carbon", "cargo", "carpet", "cascade", "celestial", "central",
    "champion", "chapter", "charger", "cheetah", "chicken", "chimera", "circle", "citadel",
    "citizen", "classic", "climate", "cloud", "cluster", "comet", "command", "compass",
    "complex", "concept", "connect", "control", "cookie", "coral", "cosmos", "crystal",
    "culture", "current", "custom", "cyclone",
    "dangerous", "daylight", "decoder", "defender", "destiny", "detective", "diamonds",
    "digital", "discovery", "display", "district", "dynamic",
    "eagle", "earth", "echo", "eclipse", "economy", "edition", "element", "emerald",
    "emotion", "empire", "engine", "engineer", "enigma", "episode", "eternal", "evolution",
    "explorer", "express",
    "factory", "fantasy", "feature", "festival", "fighter", "firefly", "firestorm",
    "fitness", "flamingo", "flash", "freedom", "frontier", "fusion", "futuretech",
    "garden", "gateway", "genesis", "genius", "ghost", "glacier", "gladiator", "global",
    "glorious", "gravity", "guardian", "guitar", "gunmetal",
    "hammer", "harmony", "harvest", "hazard", "headline", "heartbeat", "helix", "hero",
    "highway", "history", "holiday", "horizon", "hurricane", "hydrogen",
    "iceberg", "illusion", "imagine", "infinite", "inspire", "instant", "internet",
    "invasion", "ironman", "isotope",
    "jasmine", "javelin", "journey", "justice", "jungle", "juniper",
    "keyboard", "kingdom", "knight", "knowledge",
    "labyrinth", "lantern", "laser", "latitude", "library", "lightning", "limitless",
    "lionheart", "location", "lottery", "lunar",
    "machine", "magical", "manager", "marathon", "marble", "maximum", "mechanic",
    "melody", "meteor", "midnight", "miracle", "mission", "monster", "morning",
    "mountain", "mystery",
    "nebula", "network", "neutron", "nightfall", "nightmare", "nomad", "normal",
    "notebook", "november", "nucleus",
    "oasis", "object", "ocean", "october", "offline", "online", "operator", "oracle",
    "orbit", "origin", "outpost", "overload", "oxygenic",
    "package", "palace", "paradox", "partner", "passion", "pathway", "pattern",
    "pegasus", "penguin", "phoenix", "physics", "picture", "pioneer", "pixel",
    "planetary", "plasma", "player", "pointer", "polygon", "popular", "portal",
    "position", "positive", "predator", "present", "primary", "prism", "process",
    "project", "protect", "protein", "prototype", "python",
    "quantum", "quartz", "question", "quickly",
    "radar", "rainbow", "ranger", "reactor", "reality", "record", "redstone",
    "reflection", "refresh", "relation", "rescue", "respect", "restore",
    "revolution", "rhythm", "river", "robot", "rocketman", "royal",
    "safari", "satellite", "science", "scorpion", "security", "sentence", "shadowed",
    "shark", "shield", "shortcut", "signaler", "silicon", "skyline", "snowfall",
    "software", "soldier", "solution", "spectrum", "spider", "spiral", "spirit",
    "spring", "station", "storage", "strategy", "sunlight", "sunrise", "sunset",
    "supreme", "survival", "swift", "symbol", "symphony", "synergy", "syntax",
    "teacher", "technology", "terminal", "territory", "throne", "thunderbolt",
    "timeline", "tornado", "tracker", "treasure", "triangle", "trinity", "triumph",
    "tropical", "turbine", "turtle",
    "ultimate", "unicorn", "universal", "universe", "upgrade", "utility",
    "vacuum", "valiant", "velocity", "venture", "vertical", "victorious",
    "village", "virtual", "volcano", "voyager",
    "warrior", "waterfall", "waveform", "welcome", "whisper", "wildfire",
    "wildlife", "willpower", "windstorm", "wireless", "wizard", "wonderland",
    "workflow", "workspace",
    "xenon", "xylophone",
    "yesterday", "youngster",
    "zenith", "zeppelin", "zigzag", "zodiac", "zombie", "zone", "zooming", "zircon",
    "alpha", "beta", "gamma", "delta", "omega", "sigma", "nova", "stellar",
    "equinox", "solstice", "aurora", "blackhole", "starship", "moonlight",
    "sunbeam", "starlight", "cosmonaut", "spacecraft", "terraform", "warpdrive",
    "hyperlink", "cyberspace", "datastream", "firewall", "blockchain", "compiler",
    "database", "algorithm", "bandwidth", "bitrate", "download", "upload",
    "keyboarder", "mousepad", "headphone", "microphone", "smartphone",
    "axiomverse", "fightzone", "rankmaster", "chatmaster", "typefast",
    "typingking", "speedrun", "ultraspeed", "megapower", "supernova",
    "darkmatter", "lightyear", "battlezone", "eliteforce", "stormbreaker",
    "ghostmode", "rapidfire", "ultraviolet", "cyberpunk", "codebreaker",
    "dreamscape", "skywalker", "nightwalker", "starborn", "firebrand",
    "moonstone", "ironforge", "silverwing", "goldrush", "crimson", "obsidian",
    "emergence", "evergreen", "mastermind", "brainstorm", "overdrive",
    "unstoppable", "fearless", "relentless", "unstable", "precision",
    "perfection", "dominance", "legendary", "immortal", "invincible"
]

WORD_GAMES = {}

# ==================== DATABASE FUNCTIONS (UNCHANGED) ====================
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 100,
        total_earned INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        fastest_time REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_rob TIMESTAMP,
        last_killed TIMESTAMP,
        last_kill TIMESTAMP,
        shield_expiry TIMESTAMP,
        is_dead INTEGER DEFAULT 0,
        death_expiry TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS game_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, chat_id INTEGER, word TEXT, reward INTEGER, 
        time_taken REAL, percentage_earned REAL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user INTEGER, to_user INTEGER, amount INTEGER, type TEXT, 
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, username: str = None) -> dict:
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, username, balance, total_earned) VALUES (?, ?, 100, 0)", 
                  (user_id, username))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in c.description]
        return dict(zip(columns, row))
    return None

def update_user_balance(user_id: int, amount: int):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ?, total_earned = total_earned + ? WHERE user_id = ?", 
              (amount, amount if amount > 0 else 0, user_id))
    conn.commit()
    conn.close()

def record_game(user_id: int, chat_id: int, word: str, reward: int, time_taken: float, percentage: float):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO game_history (user_id, chat_id, word, reward, time_taken, percentage_earned) 
                 VALUES (?, ?, ?, ?, ?, ?)""", (user_id, chat_id, word, reward, time_taken, percentage))
    c.execute("""UPDATE users SET games_played = games_played + 1, games_won = games_won + 1,
                 fastest_time = CASE WHEN fastest_time = 0 OR ? < fastest_time THEN ? ELSE fastest_time END 
                 WHERE user_id = ?""", (time_taken, time_taken, user_id))
    conn.commit()
    conn.close()

# ==================== TIME-BASED REWARD CALCULATION (UNCHANGED) ====================
def calculate_time_based_reward(time_taken: float, total_time: int = WORD_GAME_SECONDS) -> Tuple[int, float]:
    percentage = ((total_time - time_taken) / total_time) * 100
    
    if time_taken <= 10:
        reward = 10
    elif time_taken <= 180:
        reward = 7
    elif time_taken <= 300:
        reward = 5
    elif time_taken <= 480:
        reward = 3
    else:
        reward = max(1, int(10 * (percentage / 100)))
    
    return reward, round(percentage, 2)

# ==================== ECONOMY FUNCTIONS (NO COOLDOWNS) ====================
def can_rob(user_id: int) -> Tuple[bool, str]:
    # NO COOLDOWN - Always allow
    return True, ""

def can_kill(user_id: int) -> Tuple[bool, str]:
    user = get_or_create_user(user_id)
    if user['balance'] < KILL_COST:
        return False, f"Need {KILL_COST} coins (have {user['balance']})"
    # NO COOLDOWN - Always allow if has balance
    return True, ""

def is_user_dead(user_id: int) -> Tuple[bool, str]:
    # DEATH STATE DISABLED - Always alive
    return False, ""

def perform_rob(attacker_id: int, victim_id: int) -> dict:
    attacker = get_or_create_user(attacker_id)
    victim = get_or_create_user(victim_id)
    
    # Shield check
    has_shield, shield_msg = check_shield(victim_id)
    if has_shield:
        return {"success": False, "message": f"🛡️ Victim has protection shield! ({shield_msg})"}
    
    if victim['balance'] < 10:
        return {"success": False, "message": "❌ Victim too poor!"}
    
    rob_amount = max(int(victim['balance'] * ROB_PERCENTAGE), 10)
    
    if random.random() > ROB_SUCCESS_RATE:
        penalty = min(20, attacker['balance'])
        update_user_balance(attacker_id, -penalty)
        update_user_balance(victim_id, penalty)
        return {"success": False, "message": f"❌ Rob failed! Lost {penalty} coins!"}
    
    update_user_balance(attacker_id, rob_amount)
    update_user_balance(victim_id, -rob_amount)
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (from_user, to_user, amount, type) VALUES (?, ?, ?, 'rob')", 
              (victim_id, attacker_id, rob_amount))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"✅ Robbed {rob_amount} coins!"}

def perform_kill(killer_id: int, victim_id: int) -> dict:
    if killer_id == victim_id:
        return {"success": False, "message": "❌ Khud ko kill nahi kar sakte!"}
    
    killer = get_or_create_user(killer_id)
    victim = get_or_create_user(victim_id)
    
    can_do, msg = can_kill(killer_id)
    if not can_do:
        return {"success": False, "message": msg}
    
    # Check if victim has shield
    has_shield, shield_msg = check_shield(victim_id)
    if has_shield:
        return {"success": False, "message": f"🛡️ Victim has protection shield! ({shield_msg})"}
    
    # Random reward between 120 and 180
    reward = random.randint(120, 180)
    update_user_balance(killer_id, reward)
    
    return {
        "success": True, 
        "message": f"💀 KILLED!\n💰 You earned: {reward} coins"
    }

def transfer_coins(from_id: int, to_id: int, amount: int) -> dict:
    sender = get_or_create_user(from_id)
    if amount < TRANSFER_MIN:
        return {"success": False, "message": f"❌ Min transfer: {TRANSFER_MIN}"}
    if sender['balance'] < amount:
        return {"success": False, "message": f"❌ Insufficient balance ({sender['balance']})"}
    
    update_user_balance(from_id, -amount)
    update_user_balance(to_id, amount)
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (from_user, to_user, amount, type) VALUES (?, ?, ?, 'transfer')", 
              (from_id, to_id, amount))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"✅ Transferred {amount} coins!"}

def get_leaderboard(limit: int = 10) -> list:
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""SELECT user_id, username, balance, total_earned, games_won, games_played 
                 FROM users ORDER BY balance DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_stats(user_id: int) -> Optional[dict]:
    user = get_or_create_user(user_id)
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""SELECT word, reward, time_taken, percentage_earned FROM game_history 
                 WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5""", (user_id,))
    recent = c.fetchall()
    c.execute("""SELECT COUNT(*), SUM(amount) FROM transactions 
                 WHERE from_user = ? OR to_user = ?""", (user_id, user_id))
    tx = c.fetchone()
    conn.close()
    return {"user": user, "recent_games": recent, "total_tx": tx[0] or 0} if user else None

# ==================== DEATH & SHIELD SYSTEM (DEATH DISABLED) ====================
def check_shield(user_id: int) -> Tuple[bool, str]:
    user = get_or_create_user(user_id)
    if not user.get('shield_expiry'):
        return False, ""
    
    shield_expiry = datetime.fromisoformat(user['shield_expiry'])
    if datetime.utcnow() < shield_expiry:
        remaining = shield_expiry - datetime.utcnow()
        days = remaining.days
        hours = remaining.seconds // 3600
        return True, f"{days}d {hours}h"
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET shield_expiry = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return False, ""

def buy_shield(user_id: int, days: int) -> dict:
    costs = {1: 500, 2: 1500, 3: 3000}
    if days not in costs:
        return {"success": False, "message": "❌ Invalid days! Use 1, 2, or 3."}
    
    cost = costs[days]
    user = get_or_create_user(user_id)
    if user['balance'] < cost:
        return {"success": False, "message": f"❌ Insufficient balance! Need {cost} coins (have {user['balance']})"}
    
    update_user_balance(user_id, -cost)
    expiry = datetime.utcnow() + timedelta(days=days)
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET shield_expiry = ? WHERE user_id = ?", (expiry.isoformat(), user_id))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"🛡️ Shield activated for {days} day(s)!\n💰 Cost: {cost} coins\n⏰ Valid until: {expiry.strftime('%Y-%m-%d %H:%M')}"}

def get_user_status(user_id: int) -> str:
    user = get_or_create_user(user_id)
    has_shield, shield_time = check_shield(user_id)
    
    text = f"👤 <b>Your Status</b>\n\n"
    text += f"💰 Balance: {user['balance']} coins\n"
    text += f"🎮 Games: {user['games_won']}/{user['games_played']} wins\n"
    text += f"⚡ Fastest: {user['fastest_time']:.1f}s\n\n"
    
    if has_shield:
        text += f"🛡️ <b>Shield Active</b>\n"
        text += f"⏰ Protected for: {shield_time}\n"
        text += f"✅ You are safe from kills and robs!"
    else:
        text += f"🟢 <b>State: ALIVE</b>\n"
        text += f"⚔️ No cooldowns! You can kill/rob freely!"
    
    return text


# ==================== OLD HELPER FUNCTIONS (UNCHANGED) ====================
def normalize_answer(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", unidecode(str(text)).lower())

def pick_random_word() -> str:
    return random.choice(WORD_BANK).upper()

def _load_font(font_path: str, size: int):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def _paste_custom_logo(img: Image.Image, draw: ImageDraw.ImageDraw, logo_path: str | None, logo_font, hint_font) -> None:
    if not logo_path or not os.path.exists(logo_path):
        draw.text((70, 55), "Axiom—chatfight", font=logo_font, fill=(255, 255, 255))
        draw.text((70, 105), "© @AxiomBots", font=hint_font, fill=(230, 230, 230))
        return
    
    try:
        logo = Image.open(logo_path).convert("RGBA").resize((92, 92))
        mask = Image.new("L", logo.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 92, 92), fill=255)
        img.paste(logo, (62, 48), mask)
        draw.text((70, 55), "Axiom—chatfight", font=logo_font, fill=(255, 255, 255))
        draw.text((70, 105), "© @AxiomBots", font=hint_font, fill=(230, 230, 230))
    except Exception:
        draw.text((70, 55), "Axiom—chatfight", font=logo_font, fill=(255, 255, 255))
        draw.text((70, 105), "© @AxiomBots", font=hint_font, fill=(230, 230, 230))

def _draw_texture(draw: ImageDraw.ImageDraw, width: int, height: int, alpha: int = 24) -> None:
    for _ in range(900):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        shade = random.randint(25, 90)
        draw.point((x, y), fill=(shade, shade, shade, alpha))

def _draw_chalk_doodles(draw: ImageDraw.ImageDraw, width: int, height: int, accent=(255, 225, 150)) -> None:
    white = (245, 240, 230, 210)
    gold = (*accent, 220)
    draw.line((0, 52, 155, 0), fill=gold, width=7)
    draw.line((62, 0, 62, 105), fill=gold, width=7)
    draw.polygon([(60, 170), (72, 205), (105, 218), (72, 231), (60, 266), (48, 231), (15, 218), (48, 205)], fill=gold)
    draw.polygon([(725, 600), (738, 633), (770, 646), (738, 659), (725, 692), (712, 659), (680, 646), (712, 633)], fill=gold)
    for i in range(3):
        draw.ellipse((-80 + i * 25, 360 + i * 20, 45 + i * 25, 520 + i * 20), outline=white, width=4)
    for i in range(5):
        draw.arc((340 + i * 55, 610 - (i % 2) * 55, 465 + i * 55, 735 - (i % 2) * 55), 180, 520, fill=white, width=3)
    for x in [250, 310, 370, 430]:
        draw.ellipse((x, random.randint(25, 85), x + 11, random.randint(95, 145)), fill=white)
    for x in [610, 675, 740]:
        draw.ellipse((x, -45, x + 42, 105), outline=white, width=5)
    for x in range(1030, 1260, 42):
        draw.arc((x, 45, x + 75, 105), 180, 360, fill=gold, width=6)
    for y in range(195, 445, 38):
        draw.line((1215, y, 1278, y + 5), fill=white, width=3)
    draw.line((1230, 170, 1230, 470), fill=white, width=3)
    draw.line((1268, 165, 1268, 475), fill=white, width=3)
    for i in range(6):
        draw.arc((1110 + i * 7, 590 - i * 9, 1360 - i * 8, 815 - i * 4), 195, 345, fill=gold, width=5)

def _draw_word_background(width: int, height: int) -> Image.Image:
    style = random.randint(0, 9)
    img = Image.new("RGB", (width, height), (4, 4, 6))
    draw = ImageDraw.Draw(img)
    
    palettes = [
        ((5, 5, 8), (32, 5, 6), (255, 55, 55)),
        ((3, 9, 18), (2, 42, 75), (0, 210, 255)),
        ((8, 4, 18), (48, 12, 82), (205, 90, 255)),
        ((3, 20, 14), (4, 70, 50), (0, 255, 165)),
        ((16, 10, 2), (92, 48, 5), (255, 190, 70)),
        ((5, 5, 5), (28, 28, 28), (255, 225, 150)),
        ((10, 8, 18), (16, 22, 45), (80, 145, 255)),
        ((20, 4, 17), (75, 5, 42), (255, 80, 180)),
        ((2, 16, 20), (4, 65, 75), (80, 255, 240)),
        ((18, 16, 10), (54, 48, 34), (245, 240, 220)),
    ]
    bg1, bg2, accent = palettes[style]
    
    for y in range(height):
        ratio = y / height
        draw.line([(0, y), (width, y)], fill=(
            int(bg1[0] * (1 - ratio) + bg2[0] * ratio),
            int(bg1[1] * (1 - ratio) + bg2[1] * ratio),
            int(bg1[2] * (1 - ratio) + bg2[2] * ratio),
        ))
    
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

# ==================== OLD generate_word_image (UNCHANGED) ====================
def generate_word_image(word: str, output_dir: str = ".", logo_path: str | None = None) -> str:
    width, height = 1280, 720
    img = _draw_word_background(width, height)
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
    file_path = Path(output_dir) / f"word_game_{normalize_answer(word)}_{uuid4().hex[:8]}.png"
    img.save(file_path)
    return str(file_path)

# ==================== OLD start_game (UNCHANGED) ====================
def start_game(chat_id: int, output_dir: str = ".", logo_path: str | None = None) -> dict:
    word = pick_random_word()
    WORD_GAMES[chat_id] = {
        "word": word,
        "start_time": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(seconds=WORD_GAME_SECONDS),
    }
    photo = generate_word_image(word, output_dir=output_dir, logo_path=logo_path)
    return {
        "word": word,
        "photo": photo,
        "caption": (
            "<b>Axiom—chatfight ⚡</b>\n\n"
            "⚡ Be the first to write the word shown in this photo.\n"
            f"⏱ <b>Time remaining:</b> {WORD_GAME_SECONDS // 60} minutes\n"
            f"💰 <b>Max Reward:</b> 10 coins (faster = more!)\n\n"
        ),
        "expires_at": WORD_GAMES[chat_id]["expires_at"],
    }

# ==================== UPDATED check_answer (NO DEAD CHECK) ====================
def check_answer(chat_id: int, user_id: int, username: str, answer: str) -> dict:
    game = WORD_GAMES.get(chat_id)
    if not game:
        return {"status": "no_game", "reward": 0}
    
    if datetime.utcnow() > game["expires_at"]:
        WORD_GAMES.pop(chat_id, None)
        return {"status": "expired", "reward": 0, "word": game["word"]}
    
    if normalize_answer(answer) != normalize_answer(game["word"]):
        return {"status": "wrong", "reward": 0}
    
    time_taken = (datetime.utcnow() - game["start_time"]).total_seconds()
    reward, percentage = calculate_time_based_reward(time_taken)
    
    update_user_balance(user_id, reward)
    record_game(user_id, chat_id, game["word"], reward, time_taken, percentage)
    
    WORD_GAMES.pop(chat_id, None)
    
    if time_taken < 60:
        time_str = f"{time_taken:.1f} seconds"
    else:
        mins = int(time_taken // 60)
        secs = int(time_taken % 60)
        time_str = f"{mins}m {secs}s"
    
    return {
        "status": "correct",
        "reward": reward,
        "word": game["word"],
        "time_taken": time_taken,
        "percentage": percentage,
        "message": (
            f"✅ <b>Correct!</b>\n"
            f"⏱ Time: {time_str}\n"
            f"⚡ Speed: {percentage}%\n"
            f"💰 Reward: +{reward} coins\n"
            f"Great job!"
        )
    }

# ==================== COMMAND HELPER FUNCTIONS (UNCHANGED) ====================
def cmd_balance(user_id: int, username: str = None) -> str:
    user = get_or_create_user(user_id, username)
    if not user:
        return "❌ User not found!"
    
    return (
        f"💵 <b>Balance:</b> {user['balance']} coins\n"
        f"📈 <b>Total Earned:</b> {user['total_earned']} coins\n"
        f"🎮 <b>Games:</b> {user['games_won']}/{user['games_played']} wins\n"
        f"⚡ <b>Fastest:</b> {user['fastest_time']:.1f}s"
    )

def cmd_leaderboard(limit: int = 10) -> str:
    top = get_leaderboard(limit)
    if not top:
        return "📊 No users yet!"
    
    text = "🏆 <b>Top Players</b>\n\n"
    for rank, (uid, uname, bal, earned, won, played) in enumerate(top, 1):
        medal = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else "🔹"
        name = uname or f"User {uid}"
        text += f"{medal} <b>#{rank}</b> {name}\n"
        text += f"   💰 {bal} coins | 🎯 {won}/{played} wins\n\n"
    
    return text

def cmd_profile(user_id: int, target_id: int = None) -> str:
    if target_id is None:
        target_id = user_id
    
    stats = get_user_stats(target_id)
    if not stats:
        return "❌ User not found!"
    
    user = stats['user']
    name = user['username'] or f"User {user['user_id']}"
    
    win_rate = 0
    if user['games_played'] > 0:
        win_rate = (user['games_won'] / user['games_played']) * 100
    
    text = (
        f"👤 <b>Profile: {name}</b>\n\n"
        f"💰 <b>Balance:</b> {user['balance']} coins\n"
        f"📈 <b>Total Earned:</b> {user['total_earned']} coins\n\n"
        f"🎮 <b>Games:</b>\n"
        f"   Played: {user['games_played']}\n"
        f"   Won: {user['games_won']}\n"
        f"   Win Rate: {win_rate:.1f}%\n"
        f"   ⚡ Fastest: {user['fastest_time']:.1f}s\n\n"
        f"💸 <b>Transactions:</b> {stats['total_tx']}\n"
    )
    
    if stats['recent_games']:
        text += "\n🕹 <b>Recent Games:</b>\n"
        for word, reward, time_taken, pct in stats['recent_games'][:3]:
            text += f"   • {word}: +{reward} ({pct}% speed)\n"
    
    return text

# Initialize database when module loads
init_database()
