import json
from time import time
import datetime

import discord
from discord.ext import commands


intents = discord.Intents.all()

class Bot(commands.Bot):
    __version__ = '1.0'

    CONFIG_PATH = "config.json"
    DEFAULT_CONFIG_PATH = "default_config.json"
    
    def __init__(self, modules=()):
        print("Loading configuration...")
        no_default_config = False
        try:
            with open(self.DEFAULT_CONFIG_PATH, mode='r') as f:
                self.config = json.load(f)
        except FileNotFoundError as e:
            print("Warning: Could not find default config!")
            no_default_config = True

        try:
            with open(self.CONFIG_PATH, mode='r') as f:
                self.config.update(json.load(f))
        except FileNotFoundError:
            if no_default_config:
                raise FileNotFoundError("you must provide at least a configuration or a default configuration")
            else:
                print("Warning: Could not find config!")

        super().__init__(
            command_prefix=commands.when_mentioned_or(self.config["prefix"]),
            intents=intents
        )

        for m in modules:
            self.load_extension(m)
        
    def run(self):
        print("Launching bot...")

        super().run(self.config["secrets"]["discord"])
        
        print("\nSaving data...")

        with open(self.CONFIG_PATH, mode='w') as f:
            json.dump(self.config, f, indent=4)
        
        print("Stopped bot!")
    
    def is_dev(self, user_id: int):
        print(self.config["developers"])
        return user_id in self.config["developers"] 

bot = Bot(modules=(
    "cmds.misc",
    "cmds.admin",
    "cmds.help",
    "cmds.dev",
    "cmds.fun",
    "cmds.stats"
))

bot.run()
