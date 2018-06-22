from band import dome, logger, settings, RESULT_INTERNAL_ERROR
from prodict import Prodict
from async_lru import alru_cache
from user_agents import parse
from asyncio import sleep
from pprint import pprint
import json

state = Prodict()


def crop(os=None, browser=None, device=None, **kwargs):
    result = Prodict()
    result.browser = browser
    result.os = os
    result.device = device
    return result


@alru_cache(maxsize=256)
async def handle(ua):
    try:
        parsed = parse(ua)
        res = Prodict(
            os_family=parsed.os.family,
            os_version=parsed.os.version,
            browser_family=parsed.browser.family,
            browser_version=parsed.browser.version,
            device_family=parsed.device.family,
            device_brand=parsed.device.brand,
            device_model=parsed.device.model)
        res.is_bot = int(parsed.is_bot)
        res.is_mobile = int(parsed.is_mobile or parsed.is_tablet)
        res.is_pc = int(parsed.is_pc)
        return res
    except Exception:
        logger.exception('handle ex')
    return {'error': RESULT_INTERNAL_ERROR}


@dome.expose(
    role=dome.ENRICHER,
    register=dict(key=['in.gen.track'], props=dict(ip='td.ua')))
async def enrich(td={}, **params):
    """
    Detect device type using User-Agent string
    https://github.com/selwin/python-user-agents
    """
    return await handle(td['ua'])


@dome.expose(role=dome.HANDLER)
async def cache_info():
    return locate.cache_info()


@dome.expose(role=dome.HANDLER)
async def get(ua, **kwargs):
    return await handle(ua)


# @dome.tasks.add
# async def startup():
#     """
#     Startup
#     """
#     try:
#         await sleep(100500)
#         pass

#     except Exception:
#         logger.exception('startup err')


"""
Full struct
-----------
see at https://github.com/selwin/python-user-agents/blob/master/user_agents/parsers.py

"""