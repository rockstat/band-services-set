import asyncio
from itertools import count
from band import dome, settings, logger


@dome.expose()
async def main(data, **params):
    return {'data': [1, 2, 3]}


@dome.tasks.add
async def worker():
    for num in count():
        try:
            # first iteration / initialization
            if num == 0:
                # Load initial data
                pass
            else:
                # Control your data
                pass
        except:
            logger.exception('my service ex')
        # Wait between iteration
        await asyncio.sleep(30)


@dome.shutdown
async def shutdown():
    # Handle graceful shutdown
    pass