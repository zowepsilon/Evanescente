import random
import datetime
import asyncio

import discord
from discord.ext import commands, tasks

from utils import debuggable, BirthdayDb, sanitize

tz = datetime.timezone(datetime.timedelta(hours=2))
check_time = datetime.time(hour=10, minute=0, tzinfo=tz)

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
        for (user_id, year) in lucky_ones:
            age = today.year - year
            tasks.append(channel.send(f"Joyeux {age}e anniversaire, <@{user_id}> !"))

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

    @commands.command()
    @debuggable
    async def birthdays(self, ctx, max_rank: int = 10):
        births = self.db.get_all_birthdays()
        today = datetime.date.today()

        bds = [(
            user_id, 
            today.year if (month, day) < (today.month, today.day) else today.year+1,
            month,
            day,
        ) for user_id, year, month, day in births]


        bds.sort(key=lambda x: datetime.date(x[1], x[2], x[3]) - today)

        out = "### Prochains anniversaires\n"
        for (user_id, year, month, day) in bds[:max_rank]:
            name = sanitize(self.bot.nickname_cache.get_nick(user_id))
            out += f"- {name} le {day:02}/{month:02}/{year:04}"

        await ctx.send(out)
            

def setup(bot):
    bot.add_cog(Birthday(bot))
