from asyncio import sleep
from collections import defaultdict
from itertools import count
from prodict import Prodict
from time import time
import asyncio

from band import settings, dome, rpc, logger, app, run_task
from band.constants import NOTIFY_ALIVE, REQUEST_STATUS

from . import dock, state


@dome.expose(name=NOTIFY_ALIVE)
async def iamalive(name, **params):
    """
    Accept services promotions
    """
    status = await rpc.request(name, REQUEST_STATUS)
    if status:
        state.set_status(name, status)


@dome.expose(path='/show/{name}')
async def show(name, **params):
    """
    Show container details
    """
    return await dock.get(name)


@dome.expose()
async def images(**params):
    """
    List images
    """
    return await dock.imgnav.lst()


@dome.expose()
async def ls(**params):
    """
    List container and docker status
    """
    return list((await dock.containers()).keys())


@dome.expose(name='list')
async def lst(**params):
    """
    Containers with info
    """
    return [{
        **state.get_appstatus(c.name),
        **c.short_info
    } for c in await dock.containers(list)]


@dome.expose(path='/status/{name}')
async def ask_status(name, **params):
    """
    Ask service status
    """
    return await rpc.request(name, REQUEST_STATUS)


@dome.expose(path='/call/{name}/{method}')
async def call(name, method, **params):
    """
    Call service method
    """
    return await rpc.request(name, method, **params)


@dome.expose(path='/run/{name}')
async def run(name, **params):
    """
    Create image and run new container with service
    """
    return await dock.run_container(name, params)


@dome.expose(path='/restart/{name}')
async def restart(name, **params):
    """
    Restart service
    """
    state.clear_status(name)
    return await dock.restart_container(name)


@dome.expose(path='/stop/{name}')
async def stop(name, **params):
    """
    HTTP endpoint
    stop container
    """
    state.clear_status(name)
    return await dock.stop_container(name)


@dome.expose(path='/rm/{name}')
async def remove(name, **params):
    """
    Unload/remove service
    """
    state.clear_status(name)
    return await dock.remove_container(name)


@dome.tasks.add
async def startup():
    for num in count():
        if num == 0:
            for c in await dock.init():
                await iamalive(c.name)
        await sleep(30)


@dome.shutdown
async def unloader(app):
    await dock.close()
