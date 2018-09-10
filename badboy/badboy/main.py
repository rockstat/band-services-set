import asyncio
import arrow
from itertools import count
from band import settings, logger, expose, pixel, redirect, error


@expose.handler()
async def test1(**params):
    return None

@expose.handler()
async def test2(**params):
    return params


@expose.handler()
async def pix(**params):
    print(params)
    return pixel()


@expose.handler()
async def red(**params):
    return redirect('https://ya.ru')
