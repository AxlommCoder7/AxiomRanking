from pyrogram import Client, filters
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "RankingBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(
        "Hello! Ranking bot is alive ✅\nUse /ranking soon."
    )


print("Bot Started...")
app.run()
