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


@dome.expose(role=dome.ENRICHER, keys=['in.gen.track'], props=dict(ua='td.ua'))
@alru_cache(maxsize=256)
async def enrich(ua, **params):
    """
    Detect device type using User-Agent string
    https://github.com/selwin/python-user-agents
    """
    try:
        parsed = parse(ua)
        res = Prodict(
            os_family=parsed.os.family,
            os_version=list(v if isinstance(v, int) else 0 for v in parsed.os.version),
            browser_family=parsed.browser.family,
            browser_version=list(v if isinstance(v, int) else 0 for v in parsed.browser.version,),
            device_family=parsed.device.family,
            device_brand=parsed.device.brand,
            device_model=parsed.device.model)
        res.is_bot = int(parsed.is_bot)
        res.is_mob = int(parsed.is_mobile or parsed.is_tablet)
        res.is_pc = int(parsed.is_pc)
        return res
    except Exception:
        logger.exception('handle ex')
    return {'error': RESULT_INTERNAL_ERROR}


@dome.expose()
async def cache_info():
    return enrich.cache_info()


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