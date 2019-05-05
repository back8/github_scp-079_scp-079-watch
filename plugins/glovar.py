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
import pickle
from configparser import RawConfigParser
from os import mkdir
from os.path import exists
from shutil import rmtree
from threading import Lock
from typing import Dict, List, Set

# Enable logging
logger = logging.getLogger(__name__)

# Init

all_commands: List[str] = ["status", "version"]

default_user_status: Dict[str, Set[int]] = {
    "ban": set(),
    "delete": set()
}

file_ids: Dict[str, Set[str]] = {
    "ban": set(),
    "delete": set()
}
# file_ids = {
#     "ban": {"file_id"},
#     "delete": {"file_id"}
# }

lock_image: Lock = Lock()

lock_text: Lock = Lock()

receivers_status: List[str] = ["CAPTCHA", "LANG", "NOFLOOD", "NOPORN", "NOSPAM", "MANAGE", "RECHECK"]

sender = "WATCH"

version: str = "0.0.1"

watch_ids: Dict[str, Dict[int, int]] = {
    "ban": {},
    "delete": {}
}
# watch_ids = {
#     "ban": {
#         12345678: 0
#     },
#     "delete": {
#         12345678: 0
#     }
# }

# Read data from config.ini

# [basic]
prefix: List[str] = []
prefix_str: str = "/!"

# [bots]
captcha_id: int = 0
clean_id: int = 0
lang_id: int = 0
noflood_id: int = 0
noporn_id: int = 0
nospam_id: int = 0
user_id: int = 0
warn_id: int = 0

# [channels]
hide_channel_id: int = 0
watch_channel_id: int = 0

# [custom]
limit_ban: int = 0
limit_delete: int = 0
reset_day: str = ""
time_ban: int = 0
time_delete: int = 0
time_new: int = 0

# [encrypt]
key: str = ""
password: str = ""

# [o5]
o5_1_id: int = 0

try:
    config = RawConfigParser()
    config.read("config.ini")
    # [basic]
    prefix = list(config["basic"].get("prefix", prefix_str))
    # [bots]
    captcha_id = int(config["bots"].get("captcha_id", captcha_id))
    clean_id = int(config["bots"].get("clean_id", clean_id))
    lang_id = int(config["bots"].get("lang_id", lang_id))
    noflood_id = int(config["bots"].get("noflood_id", noflood_id))
    noporn_id = int(config["bots"].get("noporn_id", noporn_id))
    nospam_id = int(config["bots"].get("nospam_id", nospam_id))
    user_id = int(config["bots"].get("user_id", user_id))
    warn_id = int(config["bots"].get("warn_id", warn_id))
    # [channels]
    hide_channel_id = int(config["channels"].get("hide_channel_id", hide_channel_id))
    watch_channel_id = int(config["channels"].get("watch_channel_id", watch_channel_id))
    # [custom]
    limit_ban = int(config["custom"].get("limit_ban", limit_ban))
    limit_delete = int(config["custom"].get("limit_delete", limit_delete))
    reset_day = config["custom"].get("reset_day", reset_day)
    time_ban = int(config["custom"].get("time_ban", time_ban))
    time_delete = int(config["custom"].get("time_delete", time_delete))
    time_new = int(config["custom"].get("time_new", time_new))
    # [encrypt]
    key = config["encrypt"].get("key", key)
    password = config["encrypt"].get("password", password)
    # [o5]
    o5_1_id = int(config["o5"].get("o5_1_id", o5_1_id))
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (prefix == []
        or captcha_id == 0
        or clean_id == 0
        or lang_id == 0
        or noflood_id == 0
        or noporn_id == 0
        or nospam_id == 0
        or user_id == 0
        or warn_id == 0
        or hide_channel_id == 0
        or watch_channel_id == 0
        or limit_ban == 0
        or limit_delete == 0
        or reset_day in {"", "[DATA EXPUNGED]"}
        or time_ban == 0
        or time_delete == 0
        or time_new == 0
        or key in {"", "[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}
        or o5_1_id == 0):
    raise SystemExit('No proper settings')

bot_ids: Set[int] = {captcha_id, clean_id, lang_id, noflood_id, noporn_id, nospam_id, user_id, warn_id}

# Load data from pickle

# Init dir
try:
    rmtree("tmp")
except Exception as e:
    logger.info(f"Remove tmp error: {e}")

for path in ["data", "tmp"]:
    if not exists(path):
        mkdir(path)

# Init ids variables

bad_ids: Dict[str, Set[int]] = {
    "channels": set(),
    "users": set()
}
# bad_ids = {
#     "channels": {-10012345678},
#     "users": {12345678}
# }

except_ids: Dict[str, Set[int]] = {
    "channels": set(),
    "users": set()
}
# except_ids = {
#     "channels": {-10012345678},
#     "users": {12345678}
# }

user_ids: Dict[int, Dict[str, Set[int]]] = {}
# user_ids = {
#     12345678: {
#         "ban": set(),
#         "delete": set()
#     }
# }

# Init data variables

# Load data
file_list: List[str] = ["bad_ids", "except_ids", "user_ids"]
for file in file_list:
    try:
        try:
            if exists(f"data/{file}") or exists(f"data/.{file}"):
                with open(f"data/{file}", 'rb') as f:
                    locals()[f"{file}"] = pickle.load(f)
            else:
                with open(f"data/{file}", 'wb') as f:
                    pickle.dump(eval(f"{file}"), f)
        except Exception as e:
            logger.error(f"Load data {file} error: {e}")
            with open(f"data/.{file}", 'rb') as f:
                locals()[f"{file}"] = pickle.load(f)
    except Exception as e:
        logger.critical(f"Load data {file} backup error: {e}")
        raise SystemExit("[DATA CORRUPTION]")

# Start program
copyright_text = (f"SCP-079-WATCH v{version}, Copyright (C) 2019 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)