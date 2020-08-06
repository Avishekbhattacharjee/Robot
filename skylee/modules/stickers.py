import os
import math
import urllib.request as urllib
from PIL import Image
from html import escape

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError

from skylee import dispatcher
from skylee.modules.disable import DisableAbleCommandHandler
from skylee.modules.helper_funcs.alternate import typing_action
import html
from typing import Optional, List
 
import telegram.ext as tg
from telegram import Message, Chat, Update, Bot, ParseMode, User, MessageEntity
from telegram import TelegramError
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html, mention_markdown
 
import skylee.modules.sql.blsticker_sql as sql
from skylee import dispatcher, SUDO_USERS, LOGGER, OWNER_ID
from skylee.modules.disable import DisableAbleCommandHandler
from skylee.modules.helper_funcs.chat_status import can_delete, is_user_admin, user_not_admin, user_admin, \
		bot_can_delete, is_bot_admin
from skylee.modules.helper_funcs.filters import CustomFilters
from skylee.modules.helper_funcs.misc import split_message
from skylee.modules.warns import warn
from skylee.modules.log_channel import loggable
from skylee.modules.sql import users_sql
from skylee.modules.connection import connected
 
from alluka.modules.helper_funcs.alternate import send_message
 

@run_async
@typing_action
def kang(update, context):
    msg = update.effective_message
    user = update.effective_user
    args = context.args
    packnum = 0
    packname = "a" + str(user.id) + "_by_" + context.bot.username
    packname_found = 0
    max_stickers = 120
    while packname_found == 0:
        try:
            stickerset = context.bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = (
                    "a"
                    + str(packnum)
                    + "_"
                    + str(user.id)
                    + "_by_"
                    + context.bot.username
                )
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    kangsticker = "kangsticker.png"
    is_animated = False
    file_id = ""

    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            if msg.reply_to_message.sticker.is_animated:
                is_animated = True
            file_id = msg.reply_to_message.sticker.file_id

        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Yea, I can't kang that.")

        kang_file = context.bot.get_file(file_id)
        if not is_animated:
            kang_file.download("kangsticker.png")
        else:
            kang_file.download("kangsticker.tgs")

        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "😌"

        if not is_animated:
            try:
                im = Image.open(kangsticker)
                maxsize = (512, 512)
                if (im.width and im.height) < 512:
                    size1 = im.width
                    size2 = im.height
                    if im.width > im.height:
                        scale = 512 / size1
                        size1new = 512
                        size2new = size2 * scale
                    else:
                        scale = 512 / size2
                        size1new = size1 * scale
                        size2new = 512
                    size1new = math.floor(size1new)
                    size2new = math.floor(size2new)
                    sizenew = (size1new, size2new)
                    im = im.resize(sizenew)
                else:
                    im.thumbnail(maxsize)
                if not msg.reply_to_message.sticker:
                    im.save(kangsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("kangsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                msg.reply_text(
                    f"Sticker successfully added to [pack](t.me/addstickers/{packname})"
                    + f"\nEmoji is: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN,
                )

            except OSError as e:
                msg.reply_text("I can only kang images m8.")
                print(e)
                return

            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        png_sticker=open("kangsticker.png", "rb"),
                    )
                elif e.message == "Sticker_png_dimensions":
                    im.save(kangsticker, "PNG")
                    context.bot.add_sticker_to_set(
                        user_id=user.id,
                        name=packname,
                        png_sticker=open("kangsticker.png", "rb"),
                        emojis=sticker_emoji,
                    )
                    msg.reply_text(
                        f"Sticker successfully added to [pack](t.me/addstickers/{packname})"
                        + f"\nEmoji is: {sticker_emoji}",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                elif e.message == "Invalid sticker emojis":
                    msg.reply_text("Invalid emoji(s).")
                elif e.message == "Stickers_too_much":
                    msg.reply_text("Max packsize reached. Press F to pay respecc.")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    msg.reply_text(
                        "Sticker successfully added to [pack](t.me/addstickers/%s)"
                        % packname
                        + "\n"
                        "Emoji is:" + " " + sticker_emoji,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                print(e)

        else:
            packname = "animated" + str(user.id) + "_by_" + context.bot.username
            packname_found = 0
            max_stickers = 50
            while packname_found == 0:
                try:
                    stickerset = context.bot.get_sticker_set(packname)
                    if len(stickerset.stickers) >= max_stickers:
                        packnum += 1
                        packname = (
                            "animated"
                            + str(packnum)
                            + "_"
                            + str(user.id)
                            + "_by_"
                            + context.bot.username
                        )
                    else:
                        packname_found = 1
                except TelegramError as e:
                    if e.message == "Stickerset_invalid":
                        packname_found = 1
            try:
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    tgs_sticker=open("kangsticker.tgs", "rb"),
                    emojis=sticker_emoji,
                )
                msg.reply_text(
                    f"Sticker successfully added to [pack](t.me/addstickers/{packname})"
                    + f"\nEmoji is: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        tgs_sticker=open("kangsticker.tgs", "rb"),
                    )
                elif e.message == "Invalid sticker emojis":
                    msg.reply_text("Invalid emoji(s).")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    msg.reply_text(
                        "Sticker successfully added to [pack](t.me/addstickers/%s)"
                        % packname
                        + "\n"
                        "Emoji is:" + " " + sticker_emoji,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                print(e)

    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1]
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "😌"
            urllib.urlretrieve(png_sticker, kangsticker)
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(kangsticker, "PNG")
            msg.reply_photo(photo=open("kangsticker.png", "rb"))
            context.bot.add_sticker_to_set(
                user_id=user.id,
                name=packname,
                png_sticker=open("kangsticker.png", "rb"),
                emojis=sticker_emoji,
            )
            msg.reply_text(
                f"Sticker successfully added to [pack](t.me/addstickers/{packname})"
                + f"\nEmoji is: {sticker_emoji}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(
                    update,
                    context,
                    msg,
                    user,
                    sticker_emoji,
                    packname,
                    packnum,
                    png_sticker=open("kangsticker.png", "rb"),
                )
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("kangsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                msg.reply_text(
                    "Sticker successfully added to [pack](t.me/addstickers/%s)"
                    % packname
                    + "\n"
                    + "Emoji is:"
                    + " "
                    + sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Invalid emoji(s).")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached. Press F to pay respecc.")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text(
                    "Sticker successfully added to [pack](t.me/addstickers/%s)"
                    % packname
                    + "\n"
                    "Emoji is:" + " " + sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN,
                )
            print(e)
    else:
        packs = "Please reply to a sticker, or image to kang it!\nOh, by the way. here are your packs:\n"
        if packnum > 0:
            firstpackname = "a" + str(user.id) + "_by_" + context.bot.username
            for i in range(0, packnum + 1):
                if i == 0:
                    packs += f"[pack](t.me/addstickers/{firstpackname})\n"
                else:
                    packs += f"[pack{i}](t.me/addstickers/{packname})\n"
        else:
            packs += f"[pack](t.me/addstickers/{packname})"
        msg.reply_text(packs, parse_mode=ParseMode.MARKDOWN)
    if os.path.isfile("kangsticker.png"):
        os.remove("kangsticker.png")
    elif os.path.isfile("kangsticker.tgs"):
        os.remove("kangsticker.tgs")


def makepack_internal(
    update,
    context,
    msg,
    user,
    emoji,
    packname,
    packnum,
    png_sticker=None,
    tgs_sticker=None,
):
    name = user.first_name
    name = name[:50]
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        if png_sticker:
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                f"{name}s kang pack" + extra_version,
                png_sticker=png_sticker,
                emojis=emoji,
            )
        if tgs_sticker:
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                f"{name}s animated kang pack" + extra_version,
                tgs_sticker=tgs_sticker,
                emojis=emoji,
            )

    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            msg.reply_text(
                "Your pack can be found [here](t.me/addstickers/%s)" % packname,
                parse_mode=ParseMode.MARKDOWN,
            )
        elif e.message == "Peer_id_invalid" or "bot was blocked by the user":
            msg.reply_text(
                "Contact me in PM first.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Start", url=f"t.me/{context.bot.username}"
                            )
                        ]
                    ]
                ),
            )
        elif e.message == "Internal Server Error: created sticker set not found (500)":
            msg.reply_text(
                "Sticker pack successfully created. Get it [here](t.me/addstickers/%s)"
                % packname,
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    if success:
        msg.reply_text(
            "Sticker pack successfully created. Get it [here](t.me/addstickers/%s)"
            % packname,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        msg.reply_text("Failed to create sticker pack. Possibly due to blek mejik.")


@run_async
def getsticker(update, context):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        context.bot.sendChatAction(chat_id, "typing")
        update.effective_message.reply_text(
            "Hello"
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", Please check the file you requested below."
            "\nPlease use this feature wisely!",
            parse_mode=ParseMode.HTML,
        )
        context.bot.sendChatAction(chat_id, "upload_document")
        file_id = msg.reply_to_message.sticker.file_id
        newFile = context.bot.get_file(file_id)
        newFile.download("sticker.png")
        context.bot.sendDocument(chat_id, document=open("sticker.png", "rb"))
        context.bot.sendChatAction(chat_id, "upload_photo")
        context.bot.send_photo(chat_id, photo=open("sticker.png", "rb"))

    else:
        context.bot.sendChatAction(chat_id, "typing")
        update.effective_message.reply_text(
            "Hello"
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", Please reply to sticker message to get sticker image",
            parse_mode=ParseMode.HTML,
        )


@run_async
@typing_action
def stickerid(update, context):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            "Hello "
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", The sticker id you are replying is :\n <code>"
            + escape(msg.reply_to_message.sticker.file_id)
            + "</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        update.effective_message.reply_text(
            "Hello "
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", Please reply to sticker message to get id sticker",
            parse_mode=ParseMode.HTML,
        )

 
@run_async
def blackliststicker(bot: Bot, update: Update, args: List[str]):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	
		
	conn = connected(bot, update, chat, user.id, need_admin=False)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if chat.type == "private":
			return
		else:
			chat_id = update.effective_chat.id
			chat_name = chat.title
		
	sticker_list = "<b>List black stickers currently in {}:</b>\n".format(chat_name)
 
	all_stickerlist = sql.get_chat_stickers(chat_id)
 
	if len(args) > 0 and args[0].lower() == 'copy':
		for trigger in all_stickerlist:
			sticker_list += "<code>{}</code>\n".format(html.escape(trigger))
	elif len(args) == 0:
		for trigger in all_stickerlist:
			sticker_list += " - <code>{}</code>\n".format(html.escape(trigger))
 
	split_text = split_message(sticker_list)
	for text in split_text:
		if sticker_list == "<b>List black stickers currently in {}:</b>\n".format(chat_name).format(chat_name):
			send_message(update.effective_message, "There is no blacklist sticker in <b>{}</b>!".format(chat_name), parse_mode=ParseMode.HTML)
			return
	send_message(update.effective_message, text, parse_mode=ParseMode.HTML)
 
 
@run_async
@user_admin
def add_blackliststicker(bot: Bot, update: Update):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	words = msg.text.split(None, 1)
 
	conn = connected(bot, update, chat, user.id)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		chat_id = update.effective_chat.id
		if chat.type == "private":
			return
		else:
			chat_name = chat.title
 
	if len(words) > 1:
		text = words[1].replace('https://t.me/addstickers/', '')
		to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
		added = 0
		for trigger in to_blacklist:
			try:
				get = bot.getStickerSet(trigger)
				sql.add_to_stickers(chat_id, trigger.lower())
				added += 1
			except BadRequest:
				send_message(update.effective_message, "Sticker `{}` can not be found!".format(trigger), parse_mode="markdown")
 
		if added == 0:
			return
 
		if len(to_blacklist) == 1:
			send_message(update.effective_message, "Sticker <code>{}</code> added to blacklist stickers in <b>{}</b>!".format(html.escape(to_blacklist[0]), chat_name),
				parse_mode=ParseMode.HTML)
		else:
			send_message(update.effective_message, "<code>{}</code> stickers added to blacklist sticker in <b>{}</b>!".format(added, chat_name), parse_mode=ParseMode.HTML)
	elif msg.reply_to_message:
		added = 0
		trigger = msg.reply_to_message.sticker.set_name
		if trigger == None:
			send_message(update.effective_message, "Sticker is invalid!")
			return
		try:
			get = bot.getStickerSet(trigger)
			sql.add_to_stickers(chat_id, trigger.lower())
			added += 1
		except BadRequest:
			send_message(update.effective_message, "Sticker `{}` can not be found!".format(trigger), parse_mode="markdown")
 
		if added == 0:
			return
 
		send_message(update.effective_message, "Sticker <code>{}</code> added to blacklist stickers in <b>{}</b>!".format(trigger, chat_name), parse_mode=ParseMode.HTML)
	else:
		send_message(update.effective_message, "Tell me what stickers you want to add to the blacklist stickers.")
 
@run_async
@user_admin
def unblackliststicker(bot: Bot, update: Update):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	words = msg.text.split(None, 1)
 
	conn = connected(bot, update, chat, user.id)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		chat_id = update.effective_chat.id
		if chat.type == "private":
			return
		else:
			chat_name = chat.title
 
 
	if len(words) > 1:
		text = words[1].replace('https://t.me/addstickers/', '')
		to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
		successful = 0
		for trigger in to_unblacklist:
			success = sql.rm_from_stickers(chat_id, trigger.lower())
			if success:
				successful += 1
 
		if len(to_unblacklist) == 1:
			if successful:
				send_message(update.effective_message, "Sticker <code>{}</code> deleted from blacklist in <b>{}</b>!".format(html.escape(to_unblacklist[0]), chat_name),
							   parse_mode=ParseMode.HTML)
			else:
				send_message(update.effective_message, "This is not on the blacklist stickers...!")
 
		elif successful == len(to_unblacklist):
			send_message(update.effective_message, "Sticker <code>{}</code> deleted from blacklist in <b>{}</b>!".format(
					successful, chat_name), parse_mode=ParseMode.HTML)
 
		elif not successful:
			send_message(update.effective_message, "None of these stickers exist, so they cannot be removed.".format(
					successful, len(to_unblacklist) - successful), parse_mode=ParseMode.HTML)
 
		else:
			send_message(update.effective_message, "Sticker <code>{}</code> deleted from blacklist. {} did not exist, so it's not deleted.".format(successful, len(to_unblacklist) - successful),
				parse_mode=ParseMode.HTML)
	elif msg.reply_to_message:
		trigger = msg.reply_to_message.sticker.set_name
		if trigger == None:
			send_message(update.effective_message, "Sticker is invalid!")
			return
		success = sql.rm_from_stickers(chat_id, trigger.lower())
 
		if success:
			send_message(update.effective_message, "Sticker <code>{}</code> deleted from blacklist in <b>{}</b>!".format(trigger, chat_name),
							   parse_mode=ParseMode.HTML)
		else:
			send_message(update.effective_message, "{} not found on blacklisted stickers...!".format(trigger))
	else:
		send_message(update.effective_message, "Tell me what stickers you want to add to the blacklist stickers.")
 
@run_async
@loggable
@user_admin
def blacklist_mode(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]
	
 
	conn = connected(bot, update, chat, user.id, need_admin=True)
	if conn:
		chat = dispatcher.bot.getChat(conn)
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if update.effective_message.chat.type == "private":
			send_message(update.effective_message, "You can do this command in groups, not PM")
			return ""
		chat = update.effective_chat
		chat_id = update.effective_chat.id
		chat_name = update.effective_message.chat.title
 
	if args:
		if args[0].lower() == 'off' or args[0].lower() == 'nothing' or args[0].lower() == 'no':
			settypeblacklist = 'turn off'
			sql.set_blacklist_strength(chat_id, 0, "0")
		elif args[0].lower() == 'del' or args[0].lower() == 'delete':
			settypeblacklist = 'left, the message will be deleted'
			sql.set_blacklist_strength(chat_id, 1, "0")
		elif args[0].lower() == 'warn':
			settypeblacklist = 'warned'
			sql.set_blacklist_strength(chat_id, 2, "0")
		elif args[0].lower() == 'mute':
			settypeblacklist = 'muted'
			sql.set_blacklist_strength(chat_id, 3, "0")
		elif args[0].lower() == 'kick':
			settypeblacklist = 'kicked'
			sql.set_blacklist_strength(chat_id, 4, "0")
		elif args[0].lower() == 'ban':
			settypeblacklist = 'banned'
			sql.set_blacklist_strength(chat_id, 5, "0")
		elif args[0].lower() == 'tban':
			if len(args) == 1:
				teks = """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blstickermode tban <timevalue>`.
                                          Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
				send_message(update.effective_message, teks, parse_mode="markdown")
				return
			settypeblacklist = 'temporary banned for {}'.format(args[1])
			sql.set_blacklist_strength(chat_id, 6, str(args[1]))
		elif args[0].lower() == 'tmute':
			if len(args) == 1:
				teks = """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blstickermode tmute <timevalue>`.
                                          Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
				send_message(update.effective_message, teks, parse_mode="markdown")
				return
			settypeblacklist = tl(update.effective_message, 'temporary muted for {}').format(args[1])
			sql.set_blacklist_strength(chat_id, 7, str(args[1]))
		else:
			send_message(update.effective_message, "I only understand off/del/warn/ban/kick/mute/tban/tmute!")
			return
		if conn:
			text = "Blacklist sticker mode changed, will `{}` at *{}*!".format(settypeblacklist, chat_name)
		else:
			text = "Blacklist sticker mode changed, will `{}`!".format(settypeblacklist)
		send_message(update.effective_message, text, parse_mode="markdown")
		return "<b>{}:</b>\n" \
				"<b>Admin:</b> {}\n" \
				"Changed sticker blacklist mode. Will {}.".format(html.escape(chat.title),
																			mention_html(user.id, user.first_name), settypeblacklist)
	else:
		getmode, getvalue = sql.get_blacklist_setting(chat.id)
		if getmode == 0:
			settypeblacklist = "not active"
		elif getmode == 1:
			settypeblacklist = "hapus"
		elif getmode == 2:
			settypeblacklist = "warn"
		elif getmode == 3:
			settypeblacklist = "mute"
		elif getmode == 4:
			settypeblacklist = "kick"
		elif getmode == 5:
			settypeblacklist = "ban"
		elif getmode == 6:
			settypeblacklist = "temporarily banned for {}".format(getvalue)
		elif getmode == 7:
			settypeblacklist = "temporarily muted for {}".format(getvalue)
		if conn:
			text = "Blacklist sticker mode is currently set to *{}* in *{}*.".format(settypeblacklist, chat_name)
		else:
			text = "Blacklist sticker mode is currently set to *{}*.".format(settypeblacklist)
		send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
	return ""
 
@run_async
@user_not_admin
def del_blackliststicker(bot: Bot, update: Update):
	chat = update.effective_chat  # type: Optional[Chat]
	message = update.effective_message  # type: Optional[Message]
	user = update.effective_user
	to_match = message.sticker
	if not to_match:
		return
 
	getmode, value = sql.get_blacklist_setting(chat.id)
 
	chat_filters = sql.get_chat_stickers(chat.id)
	for trigger in chat_filters:
		if to_match.set_name.lower() == trigger.lower():
			try:
				if getmode == 0:
					return
				elif getmode == 1:
					message.delete()
				elif getmode == 2:
					message.delete()
					warn(update.effective_user, chat, "Using sticker '{}' which in blacklist stickers".format(trigger), message, update.effective_user, conn=False)
					return
				elif getmode == 3:
					message.delete()
					bot.restrict_chat_member(chat.id, update.effective_user.id, can_send_messages=False)
					bot.sendMessage(chat.id, "{} muted because using '{}' which in blacklist stickers".format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 4:
					message.delete()
					res = chat.unban_member(update.effective_user.id)
					if res:
						bot.sendMessage(chat.id, "{} kicked because using '{}' which in blacklist stickers".format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 5:
					message.delete()
					chat.kick_member(user.id)
					bot.sendMessage(chat.id, "{} banned because using '{}' which in blacklist stickers".format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 6:
					message.delete()
					bantime = extract_time(message, value)
					chat.kick_member(user.id, until_date=bantime)
					bot.sendMessage(chat.id, "{} banned for {} because using '{}' which in blacklist stickers".format(mention_markdown(user.id, user.first_name), value, trigger), parse_mode="markdown")
					return
				elif getmode == 7:
					message.delete()
					mutetime = extract_time(message, value)
					bot.restrict_chat_member(chat.id, user.id, until_date=mutetime, can_send_messages=False)
					bot.sendMessage(chat.id, "{} muted for {} because using '{}' which in blacklist stickers".format(mention_markdown(user.id, user.first_name), value, trigger), parse_mode="markdown")
					return
			except BadRequest as excp:
				if excp.message == "Message to delete not found":
					pass
				else:
					LOGGER.exception("Error while deleting blacklist message.")
				break
 
 
def __import_data__(chat_id, data):
	# set chat blacklist
	blacklist = data.get('sticker_blacklist', {})
	for trigger in blacklist:
		sql.add_to_blacklist(chat_id, trigger)
 
 
def __migrate__(old_chat_id, new_chat_id):
	sql.migrate_chat(old_chat_id, new_chat_id)
 
 
def __chat_settings__(chat_id, user_id):
	blacklisted = sql.num_stickers_chat_filters(chat_id)
	return "There are `{} `blacklisted stickers.".format(blacklisted)
 
def __stats__():
	return "{} blacklist stickers, across {} chats.".format(sql.num_stickers_filters(), sql.num_stickers_filter_chats())
 

__help__ = """
Kanging Stickers made easy with stickers module!

× /stickerid: Reply to a sticker to me to tell you its file ID.
× /getsticker: Reply to a sticker to me to upload its raw PNG file.
× /kang: Reply to a sticker to add it to your pack.
Blacklist sticker is used to stop certain stickers. Whenever a sticker is sent, the message will be deleted immediately.
*NOTE:* Blacklist stickers do not affect the group admin.
 - /blsticker: See current blacklisted sticker.
*Only admin:*
 - /addblsticker <sticker link>: Add the sticker trigger to the black list. Can be added via reply sticker.
 - /unblsticker <sticker link>: Remove triggers from blacklist. The same newline logic applies here, so you can delete multiple triggers at once.
 - /rmblsticker <sticker link>: Same as above.
 - /blstickermode ban/tban/mute/tmute .
Note:
 - `<sticker link>` can be `https://t.me/addstickers/<sticker>` or just `<sticker>` or reply to the sticker message.
"""

__mod_name__ = "Stickers"
KANG_HANDLER = DisableAbleCommandHandler("kang", kang, pass_args=True, admin_ok=True)
STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
BLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler("blsticker", blackliststicker, pass_args=True, admin_ok=True)
ADDBLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler("addblsticker", add_blackliststicker)
UNBLACKLIST_STICKER_HANDLER = CommandHandler(["unblsticker", "rmblsticker"], unblackliststicker)
BLACKLISTMODE_HANDLER = CommandHandler("blstickermode", blacklist_mode, pass_args=True)
BLACKLIST_STICKER_DEL_HANDLER = MessageHandler(Filters.sticker & Filters.group, del_blackliststicker)
 
dispatcher.add_handler(BLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(ADDBLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(UNBLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(BLACKLISTMODE_HANDLER)
dispatcher.add_handler(BLACKLIST_STICKER_DEL_HANDLER)
dispatcher.add_handler(KANG_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
