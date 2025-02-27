from __future__ import annotations

import functools
import traceback

def debuggable(f):
    @functools.wraps(f)
    async def new(self, ctx, *args, **kwargs):
        try:
            await f(self, ctx, *args, **kwargs)
        except Exception as exc:
            if self.bot.config["debug"] and ctx.author.id == self.bot.config["owner"]:
                await ctx.send(f"Exception lors de l'exécution: ```\n{traceback.format_exc()}```")

    return new

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

    def get_leaderboard(self, limit: int = 20) -> list[(int, int, int)]:
        self.cursor.execute(f"""
            WITH Sorted AS (
                SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                FROM {self.table_name}
            )
            SELECT Rank, UserId, Count FROM Sorted
            LIMIT ?;
        """, [limit])

        return self.cursor.fetchall()
