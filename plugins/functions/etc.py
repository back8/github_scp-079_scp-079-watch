# SCP-079-WATCH - Observe and track suspicious spam behaviors
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-WATCH.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
from datetime import datetime
from hashlib import md5
from html import escape
from random import choice, uniform
from re import sub
from string import ascii_letters, digits
from threading import Thread, Timer
from time import localtime, sleep, strftime, time
from typing import Any, Callable, Dict, List, Optional, Union
from unicodedata import normalize

from cryptography.fernet import Fernet
from guess_language import guess_language
from langdetect import detect
from opencc import OpenCC
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, Message, MessageEntity, User
from textblob import TextBlob

from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)

# Init Opencc
converter = OpenCC(config="t2s.json")


def bold(text: Any) -> str:
    # Get a bold text
    result = ""

    try:
        result = str(text).strip()

        if not result:
            return ""

        result = f"<b>{escape(result)}</b>"
    except Exception as e:
        logger.warning(f"Bold error: {e}", exc_info=True)

    return result


def code(text: Any) -> str:
    # Get a code text
    result = ""

    try:
        result = str(text).strip()

        if not result:
            return ""

        result = f"<code>{escape(result)}</code>"
    except Exception as e:
        logger.warning(f"Code error: {e}", exc_info=True)

    return result


def code_block(text: Any) -> str:
    # Get a code block text
    result = ""

    try:
        result = str(text).rstrip()

        if not result:
            return ""

        result = f"<pre>{escape(result)}</pre>"
    except Exception as e:
        logger.warning(f"Code block error: {e}", exc_info=True)

    return result


def crypt_str(operation: str, text: str, key: bytes) -> str:
    # Encrypt or decrypt a string
    result = ""

    try:
        f = Fernet(key)
        text = text.encode("utf-8")

        if operation == "decrypt":
            result = f.decrypt(text)
        else:
            result = f.encrypt(text)

        result = result.decode("utf-8")
    except Exception as e:
        logger.warning(f"Crypt str error: {e}", exc_info=True)

    return result


def delay(secs: int, target: Callable, args: list = None) -> bool:
    # Call a function with delay
    result = False

    try:
        t = Timer(secs, target, args)
        t.daemon = True
        result = t.start() or True
    except Exception as e:
        logger.warning(f"Delay error: {e}", exc_info=True)

    return result


def general_link(text: Union[int, str], link: str) -> str:
    # Get a general link
    result = ""

    try:
        text = str(text).strip()
        link = link.strip()

        if not (text and link):
            return ""

        result = f'<a href="{link}">{escape(text)}</a>'
    except Exception as e:
        logger.warning(f"General link error: {e}", exc_info=True)

    return result


def get_channel_link(message: Union[int, Message]) -> str:
    # Get a channel reference link
    result = ""

    try:
        result = "https://t.me/"

        if isinstance(message, int):
            result += f"c/{str(message)[4:]}"
            return result

        if not message.chat:
            return result

        if message.chat.username:
            result += f"{message.chat.username}"
        else:
            cid = message.chat.id
            result += f"c/{str(cid)[4:]}"
    except Exception as e:
        logger.warning(f"Get channel link error: {e}", exc_info=True)

    return result


def get_entity_text(message: Message, entity: MessageEntity) -> str:
    # Get a message's entity text
    result = ""
    try:
        text = get_text(message)

        if not text or not entity:
            return ""

        offset = entity.offset
        length = entity.length
        text = text.encode("utf-16-le")
        result = text[offset * 2:(offset + length) * 2].decode("utf-16-le")
    except Exception as e:
        logger.warning(f"Get entity text error: {e}", exc_info=True)

    return result


def get_filename(message: Message, normal: bool = False, printable: bool = False, pure: bool = False) -> str:
    # Get file's filename
    result = ""

    try:
        if not message.media:
            return ""

        if message.document and message.document.file_name:
            result = message.document.file_name
        elif message.audio and message.audio.file_name:
            result = message.audio.file_name

        result = t2t(result, normal, printable, pure)
    except Exception as e:
        logger.warning(f"Get filename error: {e}", exc_info=True)

    return result


def get_forward_name(message: Message, normal: bool = False, printable: bool = False, pure: bool = False) -> str:
    # Get forwarded message's origin sender's name
    result = ""

    try:
        if not message.forward_date:
            return ""

        if message.forward_from:
            user = message.forward_from
            result = get_full_name(user, normal, printable, pure)
        elif message.forward_sender_name:
            result = message.forward_sender_name
        elif message.forward_from_chat:
            chat = message.forward_from_chat
            result = chat.title

        result = t2t(result, normal, printable, pure)
    except Exception as e:
        logger.warning(f"Get forward name error: {e}", exc_info=True)

    return result


def get_full_name(user: User, normal: bool = False, printable: bool = False, pure: bool = False) -> str:
    # Get user's full name
    result = ""

    try:
        if not user or user.is_deleted:
            return ""

        result = user.first_name

        if user.last_name:
            result += f" {user.last_name}"

        result = t2t(result, normal, printable, pure)
    except Exception as e:
        logger.warning(f"Get full name error: {e}", exc_info=True)

    return result


def get_int(text: str) -> Optional[int]:
    # Get a int from a string
    result = None

    try:
        result = int(text)
    except Exception as e:
        logger.info(f"Get int error: {e}", exc_info=True)

    return result


def get_lang(text: str) -> str:
    # Get text's language code
    result = ""

    try:
        # Remove unnecessary strings
        chinese_symbols = "～！、，。？￥…×—·．：；“”‘’（）〈〉《》「」『』【】〔〕"
        english_symbols = """`~!@#$%^&*()-=_+[]\\{}|;':",./<>?"""
        special_symbols = "£"
        symbols = chinese_symbols + english_symbols + special_symbols
        text = "".join(t for t in text if t not in symbols and t not in glovar.emoji_set)

        # Avoid short name
        if len(text) < 20:
            text = "".join(t for t in text if t.isprintable())

            if not text.strip():
                return ""

            text = text * (20 // len(text) + 1)

        # Detect
        if not text.strip():
            return ""

        # Init
        recheck = ""

        # Use langdetect, use textblob to recheck
        result = get_lang_langdetect(text)

        if result:
            recheck = get_lang_textblob(text)

        lang_default = glovar.lang_bio | glovar.lang_name | glovar.lang_sticker | glovar.lang_text

        if result and recheck and (result == recheck or recheck not in lang_default):
            return recheck
        elif result:
            return ""

        # Use guess
        result = get_lang_guess(text)
    except Exception as e:
        logger.warning(f"Get lang error: {e}", exc_info=True)

    return result


def get_lang_guess(text: str) -> str:
    # Get language using guess
    result = ""

    try:
        result = guess_language(text)

        if not result or (result != "UNKNOWN" and result in glovar.lang_protect):
            return ""
    except Exception as e:
        logger.info(f"Get lang guess error: {e}", exc_info=True)

    return result


def get_lang_langdetect(text: str) -> str:
    # Get language using langdetect
    result = ""

    try:
        result = detect(text)

        if not result or result in glovar.lang_protect:
            return ""
    except Exception as e:
        logger.info(f"Get lang langdetect error: {e}", exc_info=True)

    return result


def get_lang_textblob(text: str) -> str:
    # Get language using textblob
    result = ""

    try:
        b = TextBlob(text)
        result = b.detect_language()

        if not result or result in glovar.lang_protect:
            return ""
    except Exception as e:
        logger.info(f"Get lang textblob error: {e}", exc_info=True)

    return result


def get_links(message: Message) -> List[str]:
    # Get a message's links
    result = []
    try:
        entities = message.entities or message.caption_entities
        if entities:
            for en in entities:
                if en.type == "url":
                    link = get_entity_text(message, en)
                elif en.url:
                    link = en.url
                else:
                    continue

                link = get_stripped_link(link)

                if not link:
                    continue

                result.append(link)

        reply_markup = message.reply_markup
        if (reply_markup
                and isinstance(reply_markup, InlineKeyboardMarkup)
                and reply_markup.inline_keyboard):
            for button_row in reply_markup.inline_keyboard:
                for button in button_row:
                    if not button:
                        continue

                    if not button.url:
                        continue

                    url = get_stripped_link(button.url)

                    if not url:
                        continue

                    result.append(url)
    except Exception as e:
        logger.warning(f"Get links error: {e}", exc_info=True)

    return result


def get_md5sum(the_type: str, ctx: str) -> str:
    # Get the md5sum of a string or file
    result = ""
    try:
        if not ctx.strip():
            return ""

        if the_type == "file":
            hash_md5 = md5()

            with open(ctx, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

            result = hash_md5.hexdigest()
        elif the_type == "string":
            result = md5(ctx.encode()).hexdigest()
    except Exception as e:
        logger.warning(f"Get md5sum error: {e}", exc_info=True)

    return result


def get_now() -> int:
    # Get time for now
    result = 0

    try:
        result = int(time())
    except Exception as e:
        logger.warning(f"Get now error: {e}", exc_info=True)

    return result


def get_readable_time(secs: int = 0, the_format: str = "%Y%m%d%H%M%S") -> str:
    # Get a readable time string
    result = ""

    try:
        if secs:
            result = datetime.utcfromtimestamp(secs).strftime(the_format)
        else:
            result = strftime(the_format, localtime())
    except Exception as e:
        logger.warning(f"Get readable time error: {e}", exc_info=True)

    return result


def get_report_record(message: Message) -> Dict[str, str]:
    # Get report message's full record
    record = {
        "project": "",
        "origin": "",
        "status": "",
        "uid": "",
        "level": "",
        "rule": "",
        "type": "",
        "game": "",
        "lang": "",
        "length": "",
        "freq": "",
        "score": "",
        "bio": "",
        "name": "",
        "from": "",
        "contact": "",
        "more": "",
        "unknown": ""
    }
    try:
        if not message.text:
            return record

        record_list = message.text.split("\n")
        for r in record_list:
            if re.search(f"^{lang('project')}{lang('colon')}", r):
                record_type = "project"
            elif re.search(f"^{lang('project_origin')}{lang('colon')}", r):
                record_type = "origin"
            elif re.search(f"^{lang('status')}{lang('colon')}", r):
                record_type = "status"
            elif re.search(f"^{lang('user_id')}{lang('colon')}", r):
                record_type = "uid"
            elif re.search(f"^{lang('level')}{lang('colon')}", r):
                record_type = "level"
            elif re.search(f"^{lang('rule')}{lang('colon')}", r):
                record_type = "rule"
            elif re.search(f"^{lang('message_type')}{lang('colon')}", r):
                record_type = "type"
            elif re.search(f"^{lang('message_game')}{lang('colon')}", r):
                record_type = "game"
            elif re.search(f"^{lang('message_lang')}{lang('colon')}", r):
                record_type = "lang"
            elif re.search(f"^{lang('message_len')}{lang('colon')}", r):
                record_type = "length"
            elif re.search(f"^{lang('message_freq')}{lang('colon')}", r):
                record_type = "freq"
            elif re.search(f"^{lang('user_score')}{lang('colon')}", r):
                record_type = "score"
            elif re.search(f"^{lang('user_bio')}{lang('colon')}", r):
                record_type = "bio"
            elif re.search(f"^{lang('user_name')}{lang('colon')}", r):
                record_type = "name"
            elif re.search(f"^{lang('from_name')}{lang('colon')}", r):
                record_type = "from"
            elif re.search(f"^{lang('contact')}{lang('colon')}", r):
                record_type = "contact"
            elif re.search(f"^{lang('more')}{lang('colon')}", r):
                record_type = "more"
            else:
                record_type = "unknown"

            record[record_type] = r.split(f"{lang('colon')}")[-1]
    except Exception as e:
        logger.warning(f"Get report record error: {e}", exc_info=True)

    return record


def get_stripped_link(link: str) -> str:
    # Get stripped link
    result = ""
    try:
        link = link.strip()

        if not link:
            return ""

        result = link.replace("http://", "")
        result = result.replace("https://", "")

        if result and result[-1] == "/":
            result = result[:-1]
    except Exception as e:
        logger.warning(f"Get stripped link error: {e}", exc_info=True)

    return result


def get_text(message: Message, normal: bool = False, printable: bool = True) -> str:
    # Get message's text, including links and buttons
    text = ""
    try:
        if not message:
            return ""

        the_text = message.text or message.caption
        if the_text:
            text += the_text
            entities = message.entities or message.caption_entities
            if entities:
                for en in entities:
                    if not en.url:
                        continue

                    text += f"\n{en.url}"

        reply_markup = message.reply_markup
        if (reply_markup
                and isinstance(reply_markup, InlineKeyboardMarkup)
                and reply_markup.inline_keyboard):
            for button_row in reply_markup.inline_keyboard:
                for button in button_row:
                    if not button:
                        continue

                    if button.text:
                        text += f"\n{button.text}"

                    if button.url:
                        text += f"\n{button.url}"

        if text:
            text = t2t(text, normal, printable)
    except Exception as e:
        logger.warning(f"Get text error: {e}", exc_info=True)

    return text


def lang(text: str) -> str:
    # Get the text
    result = ""
    try:
        result = glovar.lang.get(text, text)
    except Exception as e:
        logger.warning(f"Lang error: {e}", exc_info=True)

    return result


def mention_id(uid: int) -> str:
    # Get a ID mention string
    result = ""

    try:
        result = general_link(f"{uid}", f"tg://user?id={uid}")
    except Exception as e:
        logger.warning(f"Mention id error: {e}", exc_info=True)

    return result


def message_link(message: Message) -> str:
    # Get a message link in a channel
    text = ""
    try:
        mid = message.message_id
        text = f"{get_channel_link(message)}/{mid}"
    except Exception as e:
        logger.warning(f"Message link error: {e}", exc_info=True)

    return text


def random_str(i: int) -> str:
    # Get a random string
    result = ""

    try:
        result = "".join(choice(ascii_letters + digits) for _ in range(i))
    except Exception as e:
        logger.warning(f"Random str error: {e}", exc_info=True)

    return result


def t2t(text: str, normal: bool, printable: bool, pure: bool = False) -> str:
    # Convert the string, text to text
    result = text

    try:
        if not result:
            return ""

        if glovar.normalize and normal:
            for special in ["spc", "spe"]:
                result = "".join(eval(f"glovar.{special}_dict").get(t, t) for t in result)

            result = normalize("NFKC", result)

        if glovar.normalize and normal and "Hans" in glovar.lang:
            result = converter.convert(result)

        if printable:
            result = "".join(t for t in result if t.isprintable() or t in {"\n", "\r", "\t"})

        if pure:
            result = sub(r"""[^\da-zA-Z一-龥.,:'"?!~;()。，？！～@“”]""", "", result)
    except Exception as e:
        logger.warning(f"T2T error: {e}", exc_info=True)

    return result


def thread(target: Callable, args: tuple, kwargs: dict = None, daemon: bool = True) -> bool:
    # Call a function using thread
    result = False

    try:
        t = Thread(target=target, args=args, kwargs=kwargs, daemon=daemon)
        t.daemon = daemon
        result = t.start() or True
    except Exception as e:
        logger.warning(f"Thread error: {e}", exc_info=True)

    return result


def wait_flood(e: FloodWait) -> bool:
    # Wait flood secs
    result = False

    try:
        result = sleep(e.x + uniform(0.5, 1.0)) or True
    except Exception as e:
        logger.warning(f"Wait flood error: {e}", exc_info=True)

    return result
