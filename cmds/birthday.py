import random
import datetime
import asyncio

import discord
from discord.ext import commands, tasks

from utils import debuggable, BirthdayDb, sanitize

tz = datetime.timezone(datetime.deltatime(hours=2))
check_time = datetime.time(hour=1, minute=40, tzinfo=tz)

class Birthday(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.db = BirthdayDb(self.bot.cursor, "Birthdays")

        self.check_loop.start()

    def cog_unload(self):
        self.check_loop.cancel()

    @tasks.loop(time=check_time)
    async def check_loop(self):
        today = datetime.date.today()

        lucky_ones = self.db.get_birthdays_for_date(today.month, today.day)
        channel = self.bot.get_channel(self.bot.config["birthday_channel"])
        role_id = self.bot.config["birthday_role"]

        tasks = []
        for user_id in lucky_ones:
            tasks.append(channel.send(f"Joyeux anniversaire, <@{user_id}> !"))

        await asyncio.gather(*tasks)

        if len(lucky_ones) != 0:
            await channel.send(f"<@&{role_id}>")

    @commands.command()
    @debuggable
    async def birthday(self, ctx, date: str):
        try:
            day, month, year = map(int, date.split('/'))
            datetime.datetime(year, month, day)
        except ValueError:
            await ctx.send(f"La date `{sanitize(date)}` est invalide. La date doit être de la forme JJ/MM/YYYY.")
            return

        self.db.set_date(ctx.author.id, year, month, day)

        await ctx.send(f"Anniversaire enregistré !")

def setup(bot):
    bot.add_cog(Birthday(bot))
