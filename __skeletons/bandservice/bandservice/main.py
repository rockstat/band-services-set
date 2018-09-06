import asyncio
import arrow
from itertools import count
from band import dome, settings, logger
from prodict import Prodict
"""
Docs:
- http://arrow.readthedocs.io/en/latest/ Arrow date lib
- https://realpython.com/python-itertools/ - Itertools with examples
- https://docs.python.org/3/library/itertools.html  Offical itettools doc 

"""

# Состояние, через которое взаисодействуют воркеры и функции
state = Prodict(request_counter=0)


@dome.expose(role=dome.HANDLER)
async def main(data, **params):
    """
    Registering handler which can be accessible through http
    Регистрируем обработчика запросов
    """
    return {'data': state.some_data, 'count': state.req_counter}


@dome.expose(role=dome.HANDLER)
async def tick(data, **params):
    """
    Second method, for example request counter
    Еще один метод6 в касестве проимера считающий запросы
    """
    state.req_counter += 1
    return {}


@dome.tasks.add
async def worker():
    """
    Это каркас воркера, который используется для начально 
    загрузки/подготовки данных и последующей оброботки новых данных
    """
    # Loop stop only when app stoping or chashes
    for num in count():
        # exception handling to prevent exit coused exeption
        try:
            if num == 0:
                # Load initial data, calculate initial params or fill statez
                # Этот блок выполняется при старте, может использоваться
                # для заполнения начальных значений или загрузки данных, например
                state.loaded = True
                state.req_counter = 0
                state.some_data = [1, 7, 88]

            # here every iteration operations
            # тут операци, кеторые должны выполнятсья каждый пооход
            state.loop = num

        except:
            logger.exception('my service ex')
        # Wait 30 seconds before next iteration
        await asyncio.sleep(30)
        # Or wait explicit time
        # next day, 03:10
        next_at = arrow.utcnow().shift(hours=+1)
        wait_secs = next_at.timestamp - arrow.utcnow().timestamp
        logger.debug("waiting", seconds=wait_secs)
        await asyncio.sleep(wait_secs)


@dome.shutdown
async def shutdown():
    """
    Handle graceful shutdown
    Если нужно произвести какие-нибулдь операции при остановке сервиса
    """
    pass