from band import logger, settings, response, expose
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


@expose.enricher(keys=['in.gen.track'], props=dict(ua='td.ua'))
@alru_cache(maxsize=512)
async def enrich(**params):
    """
    Detect device type using User-Agent string
    https://github.com/selwin/python-user-agents
    """
    try:
        ua = params.get('ua')
        if not ua:
            return
        parsed = parse(ua)
        res = Prodict(
            os_family=parsed.os.family,
            os_version=list(v if isinstance(v, int)
                            else 0 for v in parsed.os.version),
            browser_family=parsed.browser.family,
            browser_version=[(v if isinstance(v, int) else 0) for v in parsed.browser.version],
            device_family=parsed.device.family,
            device_brand=parsed.device.brand,
            device_model=parsed.device.model)
        res.is_bot = int(parsed.is_bot)
        res.is_tables = int(parsed.is_tablet)
        res.is_mob = int(parsed.is_mobile)
        res.is_pc = int(parsed.is_pc)
        return res
    except Exception:
        logger.exception('handle ex')
        return response.error()


@expose()
async def cache_info():
    return enrich.cache_info()
