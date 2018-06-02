from asyncio import sleep
from collections import defaultdict
from itertools import count
from prodict import Prodict
from time import time
import asyncio

from band import settings, dome, rpc, logger, app, run_task
from band.constants import NOTIFY_ALIVE, REQUEST_STATUS, OK, FRONTIER_SERVICE

from . import STATUS_RUNNING, dock, state


@dome.expose(name='list')
async def lst(**params):
    """
    Containers list with status information
    """
    status = params.pop('status', None)
    return [
        Prodict(**state.get_appstatus(c.name), **c.short_info)
        for c in await dock.containers(struct=list, status=status)
    ]


@dome.expose()
async def registrations(**params):
    """
    Provide global RPC registrations information
    """
    params = Prodict()
    conts = await lst(status=STATUS_RUNNING)
    methods = []
    for c in (c for c in conts if c.methods):
        for cm in c.methods:
            methods.append((c.name, cm[0], cm[1]))
    return dict(methods=methods)


@dome.expose(name=NOTIFY_ALIVE)
async def iamalive(name, **params):
    """
    Listen for services promotions then ask their statuses.
    It some cases takes payload to reduce calls amount
    """
    payload = Prodict()
    if name == FRONTIER_SERVICE:
        payload.update(await registrations())
    status = await rpc.request(name, REQUEST_STATUS, **payload)
    if status:
        state.set_status(name, status)


@dome.expose(path='/show/{name}')
async def show(name, **params):
    """
    Returns container details
    """
    return await dock.get(name)


@dome.expose()
async def images(**params):
    """
    Available images list
    """
    return await dock.imgnav.lst()


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
    """
    Startup and heart-beat task
    """
    for num in count():
        if num == 0:
            for c in await dock.init():
                await iamalive(c.name)
        await sleep(30)


@dome.shutdown
async def unloader(app):
    """
    Graceful shutdown task
    """
    await dock.close()
