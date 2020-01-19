# functions.py | function definitions
# Copyright (C) 2019  EraserBird, person_v1.32, hmmm

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import contextlib
import difflib
import os
import pickle
import random
import string
import time
import urllib.parse
from functools import partial
from io import BytesIO
from mimetypes import guess_all_extensions, guess_extension

import discord
from PIL import Image

from data import (GenericError, database, logger)
async def channel_setup(ctx):
    """Sets up a new discord channel.
    
    `ctx` - Discord context object
    """
    logger.info("checking channel setup")
    if database.exists(f"channel:{str(ctx.channel.id)}"):
        logger.info("channel data ok")
    else:
        database.hmset(
            f"channel:{str(ctx.channel.id)}", {
                "bird": "",
                "answered": 1,
                "prevJ": 20,
                "prevB": ""
            }
        )
        # true = 1, false = 0, index 0 is last arg, prevJ is 20 to define as integer
        logger.info("channel data added")
        await ctx.send("Ok, setup! I'm all ready to use!")


async def user_setup(ctx):
    """Sets up a new discord user for score tracking.
    
    `ctx` - Discord context object
    """
    logger.info("checking user data")
    if database.zscore("users:global", str(ctx.author.id)) is not None:
        logger.info("user global ok")
    else:
        database.zadd("users:global", {str(ctx.author.id): 0})
        logger.info("user global added")
        await ctx.send("Welcome <@" + str(ctx.author.id) + ">!")

    #Add streak
    if (database.zscore("streak:global", str(ctx.author.id)) is not None) and (
            database.zscore("streak.max:global", str(ctx.author.id)) is not None):
        logger.info("user streak in already")
    else:
        database.zadd("streak:global", {str(ctx.author.id): 0})
        database.zadd("streak.max:global",{str(ctx.author.id): 0})
        logger.info("added streak")


def error_skip(ctx):
    """Skips the current bird.
    
    Passed to send_bird() as on_error to skip the bird when an error occurs to prevent error loops.
    """
    logger.info("ok")
    database.hset(f"channel:{str(ctx.channel.id)}", "bird", "")
    database.hset(f"channel:{str(ctx.channel.id)}", "answered", "1")


def score_increment(ctx, amount: int):
    """Increments the score of a user by `amount`.

    `ctx` - Discord context object\n
    `amount` (int) - amount to increment by, usually 1
    """
    logger.info(f"incrementing score by {amount}")
    database.zincrby("score:global", amount, str(ctx.channel.id))
    database.zincrby("users:global", amount, str(ctx.author.id))


def owner_check(ctx) -> bool:
    """Check to see if the user is the owner of the bot."""
    owners = set(str(os.getenv("ids")).split(","))
    return str(ctx.author.id) in owners


def spellcheck(worda, wordb, cutoff=3):
    """Checks if two words are close to each other.
    
    `worda` (str) - first word to compare
    `wordb` (str) - second word to compare
    `cutoff` (int) - allowed difference amount
    """
    worda = worda.lower()
    wordb = wordb.lower()
    shorterword = min(worda, wordb, key=len)
    if worda != wordb:
        if len(list(difflib.Differ().compare(worda, wordb))) - len(shorterword) >= cutoff:
            return False
    return True
