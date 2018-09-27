# Band service skeleton
# (c) Dmitry Rodin 2018
# ---------------------
import asyncio
from itertools import count
from prodict import Prodict as pdict
from band import expose, cleanup, worker, settings, logger

"""
Service state
"""
state = pdict(
    counter=settings.initial_counter_value,
    loaded=False,
    loop=0
)


@expose.handler()
async def main(data, **params):
    """
    Registering handler which can be accessible through http
    Регистрируем обработчика запросов
    """
    return state


@expose.handler()
async def tick(data, **params):
    """
    Second method, for example request counter
    Еще один метод6 в касестве проимера считающий запросы
    """
    return {}


@worker()
async def service_worker():
    """
    Это каркас воркера, который используется для начально 
    загрузки/подготовки данных и последующей оброботки новых данных
    вызывается при инициализации приложения
    """
    for num in count():
        """
        Avoid crush
        """
        try:
            """
            initial execution
            """
            if num == 0:
                state.loaded = True
            """
            periodically execution
            """
            state.loop = num
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception('my service exeption')
        await asyncio.sleep(30)


@cleanup()
async def service_cleanup():
    """
    Handle graceful shutdown
    Операции выполняемые при завершении
    """
    state.loaded = False
