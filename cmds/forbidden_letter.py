import discord
from discord.ext import commands

import random
import re
from unidecode import unidecode

from utils import debuggable

letters = "abcdefghijklmnopqrstuvwxyz"
url_regex = r'https?:\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])'

class ForbiddenLetter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.letter = 'l'

    async def new_letter(self, letter=None):
        if letter:
            self.letter = letter
        else:
            self.letter = random.choice(letters)
        
        forbidden_letter_channel = self.bot.get_channel(
                self.bot.config["forbidden_letter_channel_id"])
        await forbidden_letter_channel.send(
                f"# Nouveau caractère interdit après ce message : `{self.letter}`")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and \
                message.channel.id == self.bot.config["forbidden_letter_channel_id"]:
            no_url_content = re.sub(url_regex, "", message.content)
            normalised_content = unidecode(no_url_content)
            lower_content = normalised_content.lower()
            
            if self.letter in lower_content:
                await message.delete()

    @commands.command()
    @debuggable
    async def new_forbidden_letter(self, ctx, *args):
        if ctx.author.id not in self.bot.config["moderators"]:
            return await ctx.send(":no_entry_sign: You need to be a moderator to do that!")

        if len(args) == 0:
            await self.new_letter()
        else:
            if len(args[0].lower()) == 1:
                await self.new_letter(args[0])
            else:
                await ctx.send(f"`{args[0]}` n'est pas un simple caractère.")


def setup(bot):
    bot.add_cog(ForbiddenLetter(bot))
