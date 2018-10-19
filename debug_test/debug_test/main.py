import asyncio
import arrow
from itertools import count
from band import settings, logger, expose, response


@expose.handler()
async def test1(**params):
    return None

@expose.handler()
async def test2(**params):
    return response(params)


@expose.handler()
async def long_method(**params):
    await asyncio.sleep(15)
    return response(params)


@expose.handler()
async def error(**params):
    return response.error('Some F*cking error')

@expose.handler()
async def pix(**params):
    print(params)
    return response.pixel()


@expose.handler()
async def red(**params):
    return response.redirect('https://ya.ru')
