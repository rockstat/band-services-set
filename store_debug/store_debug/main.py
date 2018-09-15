import asyncio
import ujson
from band import logger, expose
"""
Listen events and write to output
"""

@expose.handler()
async def broadcast(**params):
    print(params)

