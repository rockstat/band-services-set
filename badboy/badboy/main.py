import asyncio
import arrow
from itertools import count
from band import settings, logger, expose


@expose.handler()
async def test1(**params):
    return None
