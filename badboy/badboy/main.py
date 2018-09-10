import asyncio
import arrow
from itertools import count
from band import settings, logger, expose, pixel_response, redirect_response, error_response


@expose.handler()
async def test1(**params):
    return None

@expose.handler()
async def test2(**params):
    return params


@expose.handler()
async def pix(**params):
    print(params)
    return pixel_response()


@expose.handler()
async def red(**params):
    return redirect_response('https://ya.ru')
