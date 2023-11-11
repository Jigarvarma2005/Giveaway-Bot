# Author: Jigarvarma2005

import random
import asyncio
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from jvdb import MongoDB
import logging
import pyromod.listen

logging.basicConfig(level=logging.ERROR)

jvbot = Client(name="GiveawayBot", bot_token=Config.BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH)
mydb = MongoDB(Config.MONGO_DB_URI)

async def is_eligible(bot: Client, chatID: int, userID: int):
    if member := await bot.get_chat_member(chatID, userID):
        if member.user.is_bot or member.user.is_deleted:
            return False
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
            member = member.user
            if username := member.username:
                return f"@{username}"
            else:
                return f"{member.mention}"
        else:
            return False
    else:
        return False


async def user_input(msg, text):
    try:
        user_res = await msg.chat.ask(text + "\n\n/skip to use default\n/cancel to cancel giveaway", filters=filters.text & filters.private, timeout=300)
        if user_res := user_res.text:
            if user_res.lower() == "/cancel":
                return "403"
            if user_res.lower() == "/skip":
                return "503"
            else:
                return user_res
    except asyncio.TimeoutError:
        return "403"


@jvbot.on_message(filters.command("source") & filters.private)
async def source_code(bot: Client, message: Message):
    await message.reply_text("**Here is my source code**\n\nhttps://github.com/Jigarvarma2005/Giveaway-Bot",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Developer", url="https://t.me/JVBots")]]
                                                               )
    )


@jvbot.on_message(filters.command("help") & filters.private)
async def help_text(bot: Client, message: Message):
    await message.reply_text("""**Help Menu**

*Channel Commands*
/send id - Send giveaway message
/result id [reply to giveaway msg]- Send giveaway result

*Private Commands*
/gen - Generate giveaway
/delete - Delete giveaway
/my - Get giveaway details

/source - Get source code of bot

@JVBots
""")


@jvbot.on_message(filters.command("start") & filters.private)
async def start(bot: Client, message: Message):
    await message.reply_text("Hi, I'm Giveaway Bot.\nI can help you to create and manage giveaway. Use /help to know how to use me.\n\n@JVBots")


@jvbot.on_message(filters.command("gen") & filters.private)
async def add_giveaway_handler(bot: Client, message: Message):
    is_exist = await mydb.get_giveawayid(message.from_user.id)
    if is_exist != None:
        return await message.reply_text("Giveaway already exist, use /delete to delete giveaway")
    _winners = await user_input(message, "Send me number of winners, default is '1'")
    if _winners == "403":
        return await message.reply_text("Cancelled")
    elif _winners == "503":
        _winners = 1
    try:
        _winners = int(_winners)
    except:
        return await message.reply_text("Number of winners must be a number")

    msg_text = await user_input(message, "Send me Giveaway Message, use {count} to show participated users, default is 'Click below button to participate in giveaway'")
    if msg_text == "403":
        return await message.reply_text("Cancelled")
    elif msg_text == "503":
        msg_text = "Click below button to participate in giveaway"
    else:
        msg_text = msg_text.markdown

    giveaway_text = await user_input(message, "Send me Giveaway Text, use {winners} to show winners, default is 'Giveaway result here, {winners} winners'")
    if giveaway_text == "403":
        return await message.reply_text("Cancelled")
    elif giveaway_text == "503":
        giveaway_text = "Giveaway result here, {winners} winners"
    else:
        giveaway_text = giveaway_text.markdown

    if (await mydb.add_giveaway(message.from_user.id, _winners, msg_text, giveaway_text)):
        await message.reply_text(f"Giveaway added successfully, use `/send {message.from_user.id}` to start giveaway in that chat")
    else:
        await message.reply_text("Failed to add giveaway")


@jvbot.on_message(filters.command("delete") & filters.private)
async def delete_handler(bot: Client, message: Message):
    confirm = await user_input(message, "Are you sure to delete giveaway? YeS to confirm")
    if confirm != "YeS":
        return await message.reply_text("Cancelled")
    if (await mydb.delete_giveawayid(message.from_user.id)):
        await message.reply_text("Giveaway deleted successfully")
    else:
        await message.reply_text("No giveaway found")


@jvbot.on_message(filters.command("my") & filters.private)
async def my_giveaway(bot: Client, message: Message):
    GiveAway = await mydb.get_giveawayid(message.from_user.id)
    if GiveAway != None:
        await message.reply_text("Giveaway is running, /delete to delete giveaway")
        GiveAway = await GiveAway.find_one({"_id": "data"})
        await message.reply_text(f"Winners: {GiveAway['winners']}\n\nMessage: {GiveAway['msg_text']}\n\nGiveaway Text: {GiveAway['giveaway_text']}")
    else:
        await message.reply_text("No giveaway found, /gen to generate giveaway")


@jvbot.on_message(filters.command("result") & ~filters.private)
async def send_giveaway_result(bot: Client, message: Message):
    try:
        usr_id = int(message.text.split(" ",1)[1])
    except:
        return await message.reply_text("send cmd along with giveaway id.\n\neg: /result 837382837")
    giveaway = await mydb.get_giveawayid(usr_id)
    if giveaway != None:
        giveaway = await giveaway.find_one({"_id": "data"})
        if giveaway != None:
            giveaway_users = await mydb.get_giveaway_users(usr_id)
            if giveaway_users != None:
                giveaway_users_count = await mydb.get_giveaway_users_count(usr_id)
                if giveaway_users_count >= giveaway["winners"]:
                    chat_id = message.chat.id
                    replied = message.reply_to_message
                    await bot.send_message(usr_id, "Choosing winners...")
                    await message.delete()
                    winner_text = ""
                    _winners = []
                    i = 1
                    while len(_winners) != giveaway["winners"]:
                        winner = random.choice(giveaway_users)
                        if winner["_id"] == "data":
                            continue
                        if UserMention := await is_eligible(bot, chat_id, winner["_id"]):
                            winner_text += f"{i}. {UserMention}\n"
                            try:
                                await bot.send_message(winner["_id"], f"You won giveaway in {message.chat.title}")
                            except:
                                pass
                            _winners.append(winner["_id"])
                            await bot.send_message(usr_id, f"{i}. {UserMention} won giveaway in {message.chat.title}")
                            i += 1
                        giveaway_users.remove(winner)
                    giveaway_text = giveaway["giveaway_text"].replace("{winners}", winner_text)
                    giveaway_text = giveaway_text.replace("{count}", str(giveaway_users_count))
                    if replied:
                        win_msg = await replied.reply_text(giveaway_text)
                        await bot.edit_message_text(message.chat.id, replied.id, "~~" + replied.text + "~~" + f"\n\n**Winners List**: {win_msg.link}", reply_markup=None)
                    else:
                        await bot.send_message(chat_id, giveaway_text)
                    await mydb.delete_giveawayid(usr_id)
                else:
                    await message.reply_text("Not enough users to choose winners")
            else:
                await message.reply_text("No users participated in giveaway")
        else:
            await message.reply_text("No giveaway data found")
    else:
        await message.reply_text("No giveaway data found")

@jvbot.on_message(filters.command("send") & ~filters.private)
async def send_giveaway(bot: Client, message: Message):
    try:
        usr_id = int(message.text.split(" ",1)[1])
    except:
        return await message.reply_text("send cmd along with giveaway id.\n\neg: /send 837382837")
    replied = message.reply_to_message
    await message.delete()
    giveaway = await mydb.get_giveawayid(usr_id)
    if giveaway != None:
        giveaway = await giveaway.find_one({"_id": "data"})
        if giveaway != None:
            giveaway = giveaway["msg_text"].replace("{count}", "0")
            if replied:
                await replied.reply_text(giveaway, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Participate", callback_data=f"participate_{usr_id}")]]))
            else:
                await bot.send_message(message.chat.id, giveaway, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Participate", callback_data=f"participate_{usr_id}")]]))
        else:
            await message.reply_text("No giveaway data found")
    else:
        await message.reply_text("No giveaway data found")


@jvbot.on_callback_query(filters.regex("participate_"))
async def callback_handler(bot: Client, query: CallbackQuery):
    querydata = int(query.data.split("_")[1])
    userDb = await mydb.add_giveaway_user(querydata, query.from_user.id)
    if userDb != None:
        await query.answer("Participated in giveaway")
        giveaway_data = await userDb.find_one({"_id": "data"})
        if giveaway_data != None:
            count = await userDb.count_documents({})
            giveaway_data = giveaway_data["msg_text"].replace("{count}", str(count))
            await query.message.edit_text(giveaway_data, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Participate", callback_data=f"participate_{querydata}")]]))
    else:
        await query.answer("Already participated in giveaway")

async def startBot():
    await jvbot.start()
    print("Bot Started")
    await idle()
    await jvbot.stop()
    print("Bot Stopped")

jvbot.run(startBot())
