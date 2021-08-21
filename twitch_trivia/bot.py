import logging
import time
import asyncio
import re

from twitchio.ext import commands

from twitch_trivia.string_util import (
    cleanse_answer_message,
    split_category_and_value,
    check_answer,
)
from twitch_trivia.bot_util import user_cooldown

logger = logging.getLogger("twitch_trivia.bot")
history_logger = logging.getLogger("twitch_trivia.history")
submission_logger = logging.getLogger("twitch_trivia.submissions")

class Bot(commands.Bot):
    def __init__(
        self, jeopardy_data, stream_id, duration, points_name, cooldown, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._jeopardy_data = jeopardy_data
        self._stream_id = stream_id
        self._duration = duration
        self._points_name = points_name
        self._cooldown = cooldown

        self._start_time = 0
        self._points = {}
        self._question_history = set()

        self._question = None
        self._correct_user = None
        self._question_lock = asyncio.Lock()
        self._submit_lock = asyncio.Lock()

    async def event_ready(self):
        logger.info(f"{self.nick} is ready!")

    @commands.command(name="daily")
    @user_cooldown(seconds=24 * 60 * 60)
    async def daily(self, ctx):
        await ctx.send(f"!addpoints {ctx.author.name} 1000")

    @commands.command(name="hourly")
    @user_cooldown(seconds=60 * 60)
    async def hourly(self, ctx):
        await ctx.send(f"!addpoints {ctx.author.name} 100")

    @commands.command(name="jeopardy")
    async def jeopardy(self, ctx):
        if ctx.message.content == "!jeopardy help":
            await ctx.send(
                "Try (!jeopardy), (!jeopardy VALUE), or (!jeopardy CATEGORY VALUE). Use (!jeopardy categories) for random categories. Answer with (!whatis ANSWER)"
            )
        elif ctx.message.content == "!jeopardy categories":
            categories = self._jeopardy_data.random_categories(5)
            await ctx.send(" | ".join(categories))
        elif self._question_lock.locked():
            time_left = (self._start_time + self._duration) - time.time()
            await ctx.send(
                f"There's still {int(time_left)} seconds left on the current question!"
            )
        else:
            async with self._question_lock:
                time_left = self._start_time + self._cooldown - time.time()
                if time_left > 0:
                    logger.info(f"Need to wait {time_left} seconds for next question.")
                    await asyncio.sleep(0)
                    return

                category, value = split_category_and_value(ctx.message.content)

                if value not in set(range(100, 2001, 100)) | set([None]):
                    await ctx.send(
                        f"Please use a point value between 100 and 2000, in increments of 100"
                    )
                    return

                question = self._jeopardy_data.random_question(
                    category=category, value=value
                )

                if question is None:
                    await ctx.send(f"Hmmm... couldn't find a question for that.")
                    return
                elif question.id in self._question_history:
                    await ctx.send(f"Hmmm... seems all those questions were asked.")
                    return
                else:
                    self._question_history.add(question.id)

                self._correct_user = None
                self._start_time = int(time.time())
                self._question = question

                await ctx.send(f"/me {question.category} for {question.value}")
                await ctx.send(question.clean_question)

                while time.time() < self._start_time + self._duration:
                    if self._correct_user:
                        break
                    await asyncio.sleep(1)

                await ctx.send(f"Answer: {question.answer}")

                if self._correct_user:
                    user_id = self._correct_user.id
                    username = self._correct_user.name
                    history_logger.info(
                        f"{self._start_time}\t{self._stream_id}\t{question.id}\t{user_id}\t{username}\t{question.value}"
                    )
                    await ctx.send(f"!addpoints {username} {question.value}")
                    self._points[username] = (
                        self._points.get(username, 0) + question.value
                    )
                else:
                    history_logger.info(
                        f"{self._start_time}\t{self._stream_id}\t{question.id}\t0\tnull\t{question.value}"
                    )
                    await ctx.send(f"No one got it right D:")

    @commands.command(name="scoreboard")
    async def scoreboard(self, ctx):
        if self._points:
            points = sorted(self._points.items(), key=lambda x: x[1], reverse=True)[:5]
            parts = [f"{username}: ${value}" for username, value in points]
            output = " | ".join(parts)
            await ctx.send(output)

    @commands.command(name="balance")
    async def balance(self, ctx):
        await ctx.send(
            f"{ctx.author.name}, you won {self._points.get(ctx.author.name, 0)} {self._points_name} this stream!"
        )

    @commands.command(name="whatis")
    async def whatis(self, ctx):
        await self.submit(ctx)

    @commands.command(name="whois")
    async def whois(self, ctx):
        await self.submit(ctx)

    @commands.command(name="whereis")
    async def whereis(self, ctx):
        await self.submit(ctx)

    async def submit(self, ctx):
        if self._question_lock.locked():
            async with self._submit_lock:
                if not self._correct_user:
                    submission_logger.info(
                        f"{self._question.id}\t{ctx.author.id}\t{ctx.author.name}\t{ctx.message.content}"
                    )
                    answer = cleanse_answer_message(ctx.message.content)
                    correct = check_answer(answer, self._question.clean_answer)
                    if correct:
                        self._correct_user = ctx.author
        else:
            await ctx.send(
                f"{ctx.author.name}, there's no active question, see (!jeopardy help)"
            )
