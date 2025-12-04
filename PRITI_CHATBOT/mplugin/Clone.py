import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from pyrogram.errors import AccessTokenExpired, AccessTokenInvalid

from config import API_ID, API_HASH, OWNER_ID
from PRITI_CHATBOT import PRITI_CHATBOT as app, save_clonebot_owner, CLONE_OWNERS
from PRITI_CHATBOT import db as mongodb


CLONES = set()
clonebotdb = mongodb.clonebotdb
cloneownerdb = mongodb.cloneownerdb


###############################################
# 1) BLOCK CLONE ON CLONE-BOTS → REDIRECT TO MAIN BOT
###############################################
@app.on_message(filters.command(["clone", "host", "deploy"]))
async def block_clone_on_clonebots(client, message):

    # MAIN BOT username
    main_bot = "PritiChatbot"

    # profile photo fetch
    try:
        p = await app.get_profile_photos(main_bot, limit=1)
        pic = p[0].file_id if p else None
    except:
        pic = None

    caption = (
        "🚫 **Cloning is disabled on clone bots.**\n\n"
        "👉 Please use the main bot to clone your bot.\n"
        f"🔗 **@{main_bot}**"
    )

    btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✨ Go to Main Bot", url=f"https://t.me/{main_bot}?start=start")]]
    )

    if pic:
        await message.reply_photo(photo=pic, caption=caption, reply_markup=btn)
    else:
        await message.reply_text(caption, reply_markup=btn)

    return  # STOP HERE; NO CLONING IN CLONE BOTS


###############################################
# 2) REAL CLONE SYSTEM (ONLY IN MAIN BOT)
###############################################
@Client.on_message(filters.command(["clone", "host", "deploy"]) & filters.user(int(OWNER_ID)))
async def clone_system(client, message):
    # This handler ONLY works for main bot + OWNER
    if len(message.command) <= 1:
        return await message.reply_text(
            "**Send bot token after /clone.**\nExample: `/clone 1234:ABCD`"
        )

    bot_token = message.text.split(maxsplit=1)[1].strip()
    mi = await message.reply_text("Checking token…")

    try:
        ai = Client(
            bot_token, API_ID, API_HASH,
            bot_token=bot_token,
            plugins=dict(root="PRITI_CHATBOT/mplugin")
        )
        await ai.start()
        bot = await ai.get_me()

    except (AccessTokenExpired, AccessTokenInvalid):
        return await mi.edit_text("❌ Invalid bot token")

    except Exception as e:
        logging.exception(e)
        return await mi.edit_text(f"❌ Error: `{e}`")

    user_id = message.from_user.id

    await save_clonebot_owner(bot.id, user_id)

    try:
        await ai.set_bot_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Help menu"),
            BotCommand("ping", "Check bot ping"),
            BotCommand("id", "Get your user ID"),
            BotCommand("stats", "Bot statistics"),
            BotCommand("gcast", "Broadcast message"),
            BotCommand("chatbot", "Enable or disable chatbot"),
            BotCommand("status", "Chatbot status"),
            BotCommand("shayri", "Send random shayri"),
            BotCommand("repo", "Get bot source code"),
        ])
    except:
        pass

    details = {
        "bot_id": bot.id,
        "user_id": user_id,
        "token": bot_token,
        "name": bot.first_name,
        "username": bot.username,
    }

    await clonebotdb.insert_one(details)
    CLONES.add(bot.id)

    await mi.edit_text(
        f"✅ **Bot @{bot.username} cloned successfully!**\n\n"
        "Delete using: `/delclone <token>`"
    )


###############################################
# 3) NORMAL USER COMMANDS KEEP WORKING
###############################################

@Client.on_message(filters.command("cloned"))
async def list_cloned(client, message):
    bots = await clonebotdb.find().to_list(length=None)
    if not bots:
        return await message.reply_text("No bots cloned yet.")

    txt = f"**Total Cloned Bots: {len(bots)}**\n\n"
    for b in bots:
        txt += f"• **{b['name']}** — @{b['username']}\n"

    await message.reply_text(txt)


@Client.on_message(filters.command(["delclone", "deleteclone"]))
async def delete_clone(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/delclone <token>`")

    token = message.text.split(maxsplit=1)[1]
    bot = await clonebotdb.find_one({"token": token})

    if not bot:
        return await message.reply_text("❌ Bot not found")

    caller = message.from_user.id
    owner = bot["user_id"]

    if caller != owner and caller != int(OWNER_ID):
        return await message.reply_text("❌ You can't delete this bot")

    await clonebotdb.delete_one({"token": token})
    CLONES.discard(bot["bot_id"])

    await message.reply_text("✅ Clone removed successfully.")


###############################################
# 4) OWNER — Delete All
###############################################
@Client.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all(client, message):
    await clonebotdb.delete_many({})
    CLONES.clear()
    await message.reply_text("🗑 All clones deleted.")