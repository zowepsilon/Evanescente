from __future__ import annotations

import functools
import traceback
import random

def debuggable(f):
    @functools.wraps(f)
    async def new(self, ctx, *args, **kwargs):
        try:
            await f(self, ctx, *args, **kwargs)
        except Exception as exc:
            if self.bot.config["debug"] and self.bot.is_dev(ctx.author.id):
                await ctx.send(f"Exception lors de l'exécution: ```\n{traceback.format_exc()}```")
            else:
                raise exc

    return new


def sanitize(text: str) -> str:
    return text \
        .replace("@here", "@​here") \
        .replace("@everyone", "@​everyone") \
        .replace("<@&", "<​@​&​")

cute = ["uwu", ":3", "rawr", "owo", "catgirl", "bébou", "meow", "miaou", "miaw","bae"]
insultes = ["chokbar", "putain", "merde", "fuck", "shit", "ptn","f***","pute","connard","connasse","fdp","bardella"]
tokipona = ["toki ", "pona ", "ala ", " li ", "mute ", "wile", "jan ", "kama ", "waso ", "sina "]

word_chars = "aàâäbcçĉdeéèêëfghiîïjĵklmnoôöpqrstuùûüvwxyÿz-"
word_seps = "'()[]{}\"/,?;:.!`*_"
sep_trans = str.maketrans({c: ' ' for c in word_seps})

def words_of_message(text: str) -> list[str]:
    return [
        word for word in text.lower().translate(sep_trans).split()
        if len(word) > 1 and word[0] != '-' and word[-1] != '-' and all(c in word_chars for c in word)
    ]

class StatCounter:
    def __init__(self, cursor, table_name, predicate):
        self.cursor = cursor
        self.table_name = table_name
        self.predicate = predicate

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                UserId int PRIMARY KEY,
                Count int
            );
        """)

    def on_message(self, message):
        if self.predicate(message.content):
            self.incr(message.author.id)

    def delete_user(self, user_id: int):
        self.cursor.execute(f"""
            DELETE FROM {self.table_name}
            WHERE UserId = ?;
        """, [user_id])

    def incr(self, user_id: int):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, 1)
            ON CONFLICT(UserId)
            DO UPDATE
            SET Count = Count + 1;
        """, [user_id])

    def decr(self, user_id: int):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, 0)
            ON CONFLICT(UserId)
            DO UPDATE
            SET Count = Count - 1;
        """, [user_id])

    def get_rank(self, user_id: int) -> (int, int):
        self.cursor.execute(f"""
            WITH Sorted AS (
                SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                FROM {self.table_name}
            )
            SELECT Rank, Count FROM Sorted
            WHERE UserId = ?;
        """, [user_id])
        
        (rank, message_count) = self.cursor.fetchone()

        return (rank, message_count)

    def get_leaderboard(self, start: int = None, end: int = None) -> list[(int, int, int)]:
        if start is None:
            self.cursor.execute(f"""
                WITH Sorted AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                    FROM {self.table_name}
                )
                SELECT Rank, UserId, Count FROM Sorted
                LIMIT ?;
            """, [end])
        else:
            self.cursor.execute(f"""
                WITH Sorted AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                    FROM {self.table_name}
                )
                SELECT Rank, UserId, Count FROM Sorted
                WHERE Rank BETWEEN ? AND ?
            """, [start, end])

        return self.cursor.fetchall()

class ReacCounter:
    def __init__(self, cursor, table_name):
        self.cursor = cursor
        self.table_name = table_name

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                Emoji VARCHAR(255) PRIMARY KEY,
                Count int
            );
        """)

    def incr(self, emoji: str):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, 1)
            ON CONFLICT(Emoji)
            DO UPDATE
            SET Count = Count + 1;
        """, [emoji])

    def decr(self, emoji: str):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, 0)
            ON CONFLICT(Emoji)
            DO UPDATE
            SET Count = Count - 1;
        """, [emoji])

    def get_rank(self, emoji: str) -> (int, int):
        self.cursor.execute(f"""
            WITH Sorted AS (
                SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                FROM {self.table_name}
            )
            SELECT Rank, Count FROM Sorted
            WHERE Emoji = ?;
        """, [emoji])
        
        (rank, message_count) = self.cursor.fetchone()

        return (rank, message_count)

    def get_leaderboard(self, start: int = None, end: int = None) -> list[(int, str, int)]:
        if start is None:
            self.cursor.execute(f"""
                WITH Sorted AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                    FROM {self.table_name}
                )
                SELECT Rank, Emoji, Count FROM Sorted
                LIMIT ?;
            """, [end])
        else:
            self.cursor.execute(f"""
                WITH Sorted AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                    FROM {self.table_name}
                )
                SELECT Rank, Emoji, Count FROM Sorted
                WHERE Rank BETWEEN ? AND ?
            """, [start, end])

        return self.cursor.fetchall()

class WordCounter:
    def __init__(self, cursor, table_name):
        self.cursor = cursor
        self.table_name = table_name

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                Word VARCHAR(255) PRIMARY KEY,
                Count int,
                FirstUserId int
            );
        """)

    def exists(self, word: str) -> bool:
        self.cursor.execute(f"""
            SELECT Count
            FROM {self.table_name}
            WHERE Word = ?;
        """, [word])

        result = self.cursor.fetchone()

        return result is not None and result[0] != 0

    def add_words(self, words: list[str], user_id: int):
        self.cursor.executemany(f"""
            INSERT INTO {self.table_name}
            VALUES(?, 1, ?)
            ON CONFLICT(Word)
            DO UPDATE
            SET Count = Count + 1;
        """, [(w, user_id) for w in words])

    def get_random_word(self) -> str:
        self.cursor.execute(f"""
            SELECT Word FROM {self.table_name}
        """)

        return random.choice(self.cursor.fetchall())[0]

    def get_user_rank(self, user_id: int) -> (int, int):
        self.cursor.execute(f"""
            WITH Counts AS (
                SELECT FirstUserId, COUNT(*) AS WordCount
                FROM {self.table_name}
                GROUP BY FirstUserId
            ),
            Rankings AS (
                SELECT FirstUserId, WordCount,
                       RANK() OVER (ORDER BY WordCount DESC) AS Rank
                FROM Counts
            )
            SELECT Rank, WordCount
            FROM Rankings
            WHERE FirstUserId = ?;
        """, [user_id])

        (rank, count) = self.cursor.fetchone()

        return (rank, count)

    def get_user_leaderboard(self, start: int = None, end: int = None) -> list[(int, int, int)]:
        if start is None:
            self.cursor.execute(f"""
                WITH Counts AS (
                    SELECT FirstUserId, COUNT(*) AS WordCount
                    FROM {self.table_name}
                    GROUP BY FirstUserId
                ),
                Rankings AS (
                    SELECT FirstUserId, WordCount,
                           RANK() OVER (ORDER BY WordCount DESC) AS Rank
                    FROM Counts
                )
                SELECT Rank, FirstUserId, WordCount FROM Rankings
                LIMIT ?;
            """, [end])
        else:
            self.cursor.execute(f"""
                WITH Counts AS (
                    SELECT FirstUserId, COUNT(*) AS WordCount
                    FROM {self.table_name}
                    GROUP BY FirstUserId
                ),
                Rankings AS (
                    SELECT FirstUserId, WordCount,
                           RANK() OVER (ORDER BY WordCount DESC) AS Rank
                    FROM Counts
                )
                SELECT Rank, FirstUserId, WordCount FROM Rankings
                WHERE Rank BETWEEN ? AND ?
            """, [start, end])

        return self.cursor.fetchall()

    def get_word_rank(self, word: str) -> (int, int, int):
        self.cursor.execute(f"""
            WITH Sorted AS (
                SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                FROM {self.table_name}
            )
            SELECT Rank, Count, FirstUserId FROM Sorted
            WHERE Word = ?;
        """, [word])
        
        (rank, count, first_user_id) = self.cursor.fetchone()

        return (rank, count, first_user_id)

    def get_word_leaderboard(self, start: int = None, end: int = None) -> list[(int, str, int, int)]:
        if start is None:
            self.cursor.execute(f"""
                WITH Sorted AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                    FROM {self.table_name}
                )
                SELECT Rank, Word, Count, FirstUserId FROM Sorted
                LIMIT ?;
            """, [end])
        else:
            self.cursor.execute(f"""
                WITH Sorted AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                    FROM {self.table_name}
                )
                SELECT Rank, Word, Count, FirstUserId FROM Sorted
                WHERE Rank BETWEEN ? AND ?
            """, [start, end])

        return self.cursor.fetchall()

    def get_all_words(self) -> list[str]:
        self.cursor.execute(f"""
            SELECT Word FROM {self.table_name}
        """)

        return [word for (word,) in self.cursor.fetchall()]

class NicknameCache:
    def __init__(self, cursor, table_name):
        self.cursor = cursor
        self.table_name = table_name

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                UserId int PRIMARY KEY,
                Name VARCHAR(255)
            );
        """)

    def get_nick(self, user_id: int) -> str:
        self.cursor.execute(f"""
            SELECT Name
            FROM {self.table_name}
            WHERE UserId = ?;
        """, [user_id])
        
        result = self.cursor.fetchone()
        return "<unknown>" if result is None else result[0]

    def set_nick(self, user_id: int, name: str):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, ?)
            ON CONFLICT(UserId)
            DO UPDATE
            SET Name = ?
        """,  [user_id, name, name])

class PenduAccuracyCounter:
    def __init__(self, cursor, table_name):
        self.cursor = cursor
        self.table_name = table_name

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                UserId int PRIMARY KEY,
                CorrectCount int,
                TotalCount int
            );
        """)

    def add_correct_letter(self, user_id: int):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, 1, 1)
            ON CONFLICT(UserId)
            DO UPDATE
            SET
            CorrectCount = CorrectCount + 1,
            TotalCount = TotalCount + 1;
        """, [user_id])

    def add_wrong_letter(self, user_id: int):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, 0, 1)
            ON CONFLICT(UserId)
            DO UPDATE
            SET TotalCount = TotalCount + 1;
        """, [user_id])

    def get_leaderboard(self, start: int = None, end: int = None) -> list[(int, int, int, int, float)]:
        if start is None:
            self.cursor.execute(f"""
                WITH Ratios AS (
                    SELECT *, CAST(CorrectCount AS float) / CAST(TotalCount AS float) AS Accuracy
                    FROM {self.table_name}
                    WHERE TotalCount >= 200
                ), Rankings AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Accuracy DESC) AS Rank, *
                    FROM Ratios
                )
                SELECT Rank, UserId, CorrectCount, TotalCount, Accuracy
                FROM Rankings
                LIMIT ?;

            """, [end])
        else:
            self.cursor.execute(f"""
                WITH Ratios AS (
                    SELECT *, CAST(CorrectCount AS float) / CAST(TotalCount AS float) AS Accuracy
                    FROM {self.table_name}
                    WHERE TotalCount >= 200
                ), Rankings AS (
                    SELECT ROW_NUMBER() OVER (ORDER BY Accuracy DESC) AS Rank, *
                    FROM Ratios
                )
                SELECT Rank, UserId, CorrectCount, TotalCount, Accuracy
                FROM Rankings
                WHERE Rank BETWEEN ? AND ?
            """, [start, end])

        return self.cursor.fetchall()

class SanityDb:
    def __init__(self, cursor, table_name):
        self.cursor = cursor
        self.table_name = table_name

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                TargetUserId int,
                VoterUserId int,
                Level int,
                PRIMARY KEY (TargetUserId, VoterUserId)
            );
        """)

    def change_entry(self, target_user_id: int, voter_user_id: int, level: int):
        self.cursor.execute(f"""
            INSERT OR REPLACE INTO {self.table_name}
            VALUES(?, ?, ?)
        """, [target_user_id, voter_user_id, level])
    
    def get_sanity(self, user_id: int) -> (float, int):
        self.cursor.execute(f"""
            SELECT Level FROM {self.table_name}
            WHERE TargetUserId = ?
        """, [user_id])

        entries = self.cursor.fetchall()
        
        return sum(e[0] for e in entries) / len(entries), len(entries)
    
    def delete_entry(self, target_user_id: int, voter_user_id: int):
        self.cursor.execute(f"""
            DELETE FROM {self.table_name}
            WHERE
            TargetUserId = ?
            VoterUserId = ?
        """, [target_user_id, voter_user_id])


class BirthdayDb:
    def __init__(self, cursor, table_name):
        self.cursor = cursor
        self.table_name = table_name

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                UserId int PRIMARY KEY,
                Year int,
                Month int,
                Day int
            );
        """)

    def get_birthdays_for_date(self, month: int, day: int) -> list[int]:
        self.cursor.execute(f"""
            SELECT UserId
            FROM {self.table_name}
            WHERE Month = ?, Day = ?
        """, [month, day])
        
        return self.cursor.fetchall()

    def set_date(self, user_id: int, year: int, month: int, day: int):
        self.cursor.execute(f"""
            INSERT INTO {self.table_name}
            VALUES(?, ?, ?, ?)
            ON CONFLICT(UserId)
            DO UPDATE
            SET Year = ?, Month = ?, Day = ?
        """,  [user_id, year, month, day, year, month, day])

    def get_all_birthdays(self) -> list[(int, int, int, int)]:
        self.cursor.execute(f"SELECT * FROM {self.table_name}")

        return self.cursor.fetchall()
