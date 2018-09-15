import asyncio
import ujson
from band import logger, expose
"""
Listen events and write to output
"""

@expose(role=dome.LISTENER)
async def broadcast(**params):
    print(params)

