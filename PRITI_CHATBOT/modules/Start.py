import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import OWNER_ID
from PRITI_CHATBOT import PRITI_CHATBOT as app

# --- Bot username here ---
MAIN_BOT_USERNAME = "PritiChatBot"   # <-- Change if needed
MAIN_BOT_CLONE_URL = f"https://t.me/{MAIN_BOT_USERNAME}?start=clone"

# --- Bot DP (Replace with your bot DP URL) ---
CLONE_IMG = "https://te.legra.ph/file/4d3887bf3b7955daeb849.jpg"   # <-- replace with your bot dp url


# ============================
#  BLOCK CLONE SYSTEM HERE
# ============================

@app.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_block(client, message):

    await message.reply_photo(
        photo=CLONE_IMG,
        caption=(
            "**🚫 Cloning Not Allowed Here!**\n\n"
            "This is a *Cloned Bot*, cloning is only allowed in the **Main Bot**.\n\n"
            "👉 Click the button below to clone your own bot."
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🤖 Go To Clone", url=MAIN_BOT_CLONE_URL
                    )
                ]
            ]
        )
    )
