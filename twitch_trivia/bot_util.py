import asyncio
import logging
import time
from functools import wraps
from typing import Callable


logger = logging.getLogger("twitch_trivia")


def user_cooldown(seconds: int) -> Callable:
    """Returns a decorator that sets a user cooldown for a give bot command

    Args:
        seconds: Cooldown per user
    """
    cache = {}
    lock = asyncio.Lock()

    def wrapper(fn):
        @wraps(fn)
        async def wrapped(self, ctx):
            async with lock:
                now = time.time()
                last_run = cache.get(ctx.author.name, 0)
                if now > (last_run + seconds):
                    cache[ctx.author.name] = now
                    await fn(self, ctx)
                else:
                    logger.info(
                        f"{ctx.author.name} cannot run command for another {last_run + seconds - now} seconds"
                    )
                    await asyncio.sleep(0)

        return wrapped

    return wrapper
