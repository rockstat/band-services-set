import asyncio
import aiohttp
from band import expose, response, logger


@expose.handler()
async def test1(**params):
    return None


@expose.handler(alias='secret')
async def alias(**params):
    return {'message': 'you are catch me!'}


async def reader():
    url = 'https://bolt.rstat.org/public/dg-lessons/100stripusers.log'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status == 200:
                while True:
                    data = await res.content.read(102400)
                    if not data:
                        break
                    yield data
                        
                # async for block in res.content.read(102400):
                #     yield block
            else:
                text = res.text()
                logger.error(
                    f'request error',
                    s=res.status,
                    t=text,
                    h=res.headers)


@expose()
async def stream():
    return reader()
    


@expose.handler(alias='secret', name='again')
async def alias2(**params):
    return {'message': 'again!'}


@expose.handler(alias='test_go', name='*')
async def wildcard(name, **params):
    return {'name': name}


@expose.handler()
async def test2(**params):
    return response(params)


@expose.handler()
async def data(**params):
    return response.data(params)


@expose.handler()
async def long_method(**params):
    await asyncio.sleep(15)
    return response(params)


@expose.handler(timeout=18000)
async def long_method2(**params):
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
