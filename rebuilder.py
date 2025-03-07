import discord
import sqlite3

from utils import NicknameCache, WordCounter, StatCounter, ReacCounter
from utils import cute, insultes, tokipona, words_of_message

class DatabaseRebuilder:
    def __init__(self, db_path: str):
        self.database = sqlite3.connect(db_path)
        self.database.autocommit = True
        self.cursor = self.database.cursor()

        self.nickname_cache = NicknameCache(self.cursor, "NicknameCache")
        self.word_counter = WordCounter(self.cursor, "WordCounts")

        self.counters = {
            "message": StatCounter(self.cursor, "MessageCounts", lambda msg: True),
            "feur": StatCounter(self.cursor, "FeurCounts", lambda msg: "feur" in msg.lower()),
            "bouboubou": StatCounter(self.cursor, "BouboubouCounts", lambda msg: "bouboubou" in msg.lower()),
            "quoicoubeh": StatCounter(self.cursor, "QuoicoubehCounts", lambda msg: "quoicoubeh" in msg.lower()),
            "cute": StatCounter(self.cursor, "CuteCounts", lambda msg: any(w in msg.lower() for w in cute)),
            "insulte": StatCounter(self.cursor, "InsulteCounts", lambda msg: any(w in msg.lower() for w in insultes)),
            "tokipona": StatCounter(self.cursor, "TokiPonaCounts", lambda msg: any(w in msg.lower() for w in tokipona)),
        }

        self.reac_counter = ReacCounter(self.cursor, "ReactionCounts")

    def process_message(self, message):
        if message.author.bot or len(message.content) == 0 or message.content[0] == '?':
            return

        for (_, c) in self.counters.items():
            c.on_message(message)

        words = words_of_message(message.content)
        self.word_counter.add_words(words, message.author.id)

        for reaction in message.reactions:
            if isinstance(reaction.emoji, str):
                self.reac_counter.incr(reaction.emoji)
            elif isinstance(reaction.emoji, discord.Emoji):
                self.reac_counter.incr(str(reaction.emoji))
