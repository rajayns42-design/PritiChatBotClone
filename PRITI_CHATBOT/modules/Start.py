import logging
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid

from config import API_ID, API_HASH, OWNER_ID
from PRITI_CHATBOT import PRITI_CHATBOT as app, save_clonebot_owner, CLONE_OWNERS
from PRITI_CHATBOT import db as mongodb

CLONES = set()
cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb


# =========================
#  USER SIDE /clone BLOCKED
# =========================
@Client.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):

    # ===== GET MAIN BOT DP ======
    try:
        photos = await app.get_profile_photos("PritiChatbot", limit=1)
        dp = photos[0].file_id if photos else None
    except:
        dp = None

    btn = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 GO TO CLONE", url="https://t.me/PritiChatbot?start=clone")]
        ]
    )

    caption = (
        "🤖 **Clone Available Only On Main Bot**\n\n"
        "⚠️ You cannot clone from a cloned bot.\n"
        "👉 Click the button below to clone your bot safely!"
    )

    if dp:
        return await message.reply_photo(dp, caption=caption, reply_markup=btn)
    else:
        return await message.reply_text(caption, reply_markup=btn)


# =========================
#  OWNER MAIN CLONE SYSTEM
# =========================
# ONLY owner / clone owners can actually clone
@app.on_message(filters.command(["clone", "host", "deploy"]) & filters.user([int(OWNER_ID), *CLONE_OWNERS]))
async def owner_clone_system(client, message):

    if len(message.command) <= 1:
        return await message.reply_text("Usage:\n`/clone <BOT_TOKEN>`")

    bot_token = message.text.split(maxsplit=1)[1].strip()
    msg = await message.reply_text("🔎 Checking token...")

    try:
        ai = Client(bot_token, API_ID, API_HASH, bot_token=bot_token,
                    plugins=dict(root="PRITI_CHATBOT/mplugin"))
        await ai.start()
        bot = await ai.get_me()

        user_id = message.from_user.id
        await save_clonebot_owner(bot.id, user_id)

        await ai.set_bot_commands([
            BotCommand("start", "Start bot"),
            BotCommand("help", "Help menu"),
            BotCommand("ping", "Bot alive?"),
            BotCommand("stats", "Bot stats"),
            BotCommand("gcast", "Global broadcast"),
            BotCommand("chatbot", "AI Chatbot"),
            BotCommand("repo", "Source code"),
        ])

    except (AccessTokenExpired, AccessTokenInvalid):
        return await msg.edit("❌ Invalid bot token.")
    except Exception as e:
        exist = await clonebotdb.find_one({"token": bot_token})
        if exist:
            return await msg.edit("⚠️ This bot is already cloned.")
        logging.exception(e)
        return await msg.edit(f"❌ Error:\n`{e}`")

    # store
    details = {
        "bot_id": bot.id,
        "user_id": user_id,
        "name": bot.first_name,
        "username": bot.username,
        "token": bot_token,
    }

    await clonebotdb.insert_one(details)
    CLONES.add(bot.id)

    return await msg.edit(
        f"✅ **Bot @{bot.username} cloned successfully!**\n"
        f"Use `/delclone {bot_token}` to delete."
    )


# =========================
#  /CLONED (USER → OWN BOTS ONLY)
# =========================
@app.on_message(filters.command("cloned"))
async def user_cloned(client, message):

    user_id = message.from_user.id

    # OWNER SEES ALL
    if user_id == int(OWNER_ID):
        bots = await clonebotdb.find().to_list(None)
        if not bots:
            return await message.reply_text("No bots cloned yet.")

        text = "🤖 **All Cloned Bots:**\n\n"
        for b in bots:
            text += f"• @{b['username']} — Owner `{b['user_id']}`\n"
        return await message.reply_text(text)

    # USER SEES ONLY THEIR OWN
    bots = await clonebotdb.find({"user_id": user_id}).to_list(None)
    if not bots:
        return await message.reply_text("You haven't cloned any bot yet.")

    text = "🤖 **Your Cloned Bots:**\n\n"
    for b in bots:
        text += f"• @{b['username']}\n"

    await message.reply_text(text)


# =========================
#   DELETE CLONE (User delete own)
# =========================
@app.on_message(filters.command(["delclone", "delcloned"]))
async def delete_cloned_bot(client, message):

    if len(message.command) < 2:
        return await message.reply_text("Usage:\n`/delclone <TOKEN_OR_USERNAME>`")

    query = message.text.split(maxsplit=1)[1].replace("@", "").strip()
    bot = await clonebotdb.find_one({"$or": [{"token": query}, {"username": query}]})

    if not bot:
        return await message.reply_text("❌ No such cloned bot found.")

    user_id = message.from_user.id

    if user_id != bot["user_id"] and user_id != int(OWNER_ID):
        return await message.reply_text("❌ You are not allowed to delete this bot.")

    await clonebotdb.delete_one({"_id": bot["_id"]})
    CLONES.discard(bot["bot_id"])

    return await message.reply_text(f"✅ Deleted cloned bot @{bot['username']}")


# =========================
# OWNER: DELETE ALL
# =========================
@app.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all(client, message):

    await clonebotdb.delete_many({})
    CLONES.clear()
    return await message.reply_text("🗑 All cloned bots deleted.")


# END OF FILE