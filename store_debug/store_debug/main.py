import asyncio
import ujson
from band import logger, expose
"""
Listen events and write to output
"""

@expose.listener()
async def broadcast(**params):
    logger.info('Broadcast', params=params)

