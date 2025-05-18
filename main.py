import json
import time
import datetime
import os

import sqlite3

import discord
from discord.ext import commands

from utils import NicknameCache, WordCounter

intents = discord.Intents.all()

class Bot(commands.Bot):
    SOURCE = os.path.dirname(os.path.realpath(__file__))

    CONFIG_PATH = "config.json"
    DEFAULT_CONFIG_PATH = SOURCE + "/default_config.json"
    
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

        self.db = sqlite3.connect(self.config["database"])
        self.db.autocommit = True
        self.cursor = self.db.cursor()

        self.nickname_cache = NicknameCache(self.cursor, "NicknameCache")
        self.word_counter = WordCounter(self.cursor, "WordCounts")

        self.startup_time = time.gmtime()
        self.reload_time = time.gmtime()

        super().__init__(
            command_prefix=commands.when_mentioned_or(self.config["prefix"]),
            intents=intents
        )

        for m in modules:
            self.load_extension(m)
        
    def run(self):
        print("Launching bot...")

        os.makedirs(self.config["run_dir"], exist_ok=True)
        os.chdir(self.config["run_dir"])

        super().run(self.config["secrets"]["discord"])
        
        print("\nSaving data...")

        with open(self.CONFIG_PATH, mode='w') as f:
            json.dump(self.config, f, indent=4)
        
        print("Stopped bot!")
    
    def is_dev(self, user_id: int):
        return user_id in self.config["developers"]

bot = Bot(modules=(
    "cmds.admin",
    "cmds.chat",
    "cmds.code",
    "cmds.dev",
    "cmds.help",
    "cmds.misc",
    "cmds.pendu",
    "cmds.sanity",
    "cmds.starboard",
    "cmds.stats",
    "cmds.typst",
))

bot.run()
