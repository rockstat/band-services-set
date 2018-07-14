from asyncio import sleep
from collections import defaultdict, deque
from itertools import count
from prodict import Prodict
from time import time
import asyncio
import ujson
import copy

from band import settings, dome, rpc, logger, app, run_task
from band.constants import NOTIFY_ALIVE, REQUEST_STATUS, OK, FRONTIER_SERVICE, DIRECTOR_SERVICE

from .constants import STATUS_RUNNING, DUMMY_REC, STARTED
from .helpers import merge, str2bool
from .state_ctx import StateCtx
from . import dock, state, band_config


@dome.expose(name='list')
async def lst(**params):
    """
    Containers list with status information
    """
    # By default return all containers
    
    res = {}
    for srv in state.values():
        if srv.app:
            res[srv.name] = srv.state()
    cs = await dock.containers(status=params.pop('status', None))
    for name, cont in cs.items():
        res[name].update(cont.short_info) if name in res else res.update(
            dict(name=cont.short_info))
    return list(res.values())


@dome.expose()
async def registrations(**params):
    """
    Provide global RPC registrations information
    """
    methods = []
    # Iterating over containers and their methods
    for srv in state.state.values():
        for method in srv.methods:
            methods.append(method)
    return dict(register=methods)


@dome.expose(name=NOTIFY_ALIVE)
async def sync_status(name, **params):
    """
    Listen for services promotions then ask their statuses.
    It some cases takes payload to reduce calls amount
    """
    # Service-dependent payload send with status request
    payload = dict()
    # Payload for frontend servoce
    if name == FRONTIER_SERVICE:
        payload.update(await registrations())
    # Loading state, config, meta
    status = await rpc.request(name, REQUEST_STATUS, **payload)
    config = await band_config.load_config(name)
    meta = await dock.image_meta(name)
    # reconfiguring service state
    srv = state.update(name, status=status, meta=meta, config=config)
    # saving configuration
    await band_config.save_config(name, srv.config)


async def check_regs_changed():
    key = hash(ujson.dumps(await registrations()))
    if key != state.last_key:
        state.last_key = key
        await sync_status(name=FRONTIER_SERVICE)


@dome.expose(path='/show/{name}')
async def show(name, **params):
    """
    Returns container details
    """
    container = await dock.get(name)
    # check container exists
    if not container:
        return 404
    return container and container.short_info


@dome.expose()
async def images(**params):
    """
    Available images list
    """
    return await dock.imgnav.lst()


@dome.expose(path='/status/{name}')
async def status_call(name, **params):
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
async def run(name, **kwargs):
    """
    Create image and run new container with service
    """
    if not dock.is_band_image(name):
        return 404

    srv = state[name]
    srv.set_build_opts(**kwargs)

    logger.info('request with params: %s. Using config: %s', kwargs, srv.config)
    container = await dock.run_container(name, **srv.config)
    # save params and state only if successfully starter
    await band_config.save_config(name, srv.config)
    await band_config.set_add(STARTED, name)
    return container


@dome.expose()
async def rebuild_all(**kwargs):
    """
    Rebuild all controlled containers
    """
    for name in await band_config.set_get(STARTED):
        await run(name)
    return 200


@dome.expose(path='/restart/{name}')
async def restart(name, **params):
    """
    Restart service
    """
    container = await dock.get(name)
    # check container exists
    if not container:
        return 404
    # executing main action
    async with StateCtx(name, check_regs_changed()):
        return await dock.restart_container(name)


@dome.expose(path='/stop/{name}')
async def stop(name, **params):
    """
    Stop container. Only for persistent containers
    """
    container = await dock.get(name)
    # check container exists
    if not container:
        return 404
    # accessible only for persistent containers
    if not container.auto_removable():
        return 400
    # executing main action
    async with StateCtx(name, check_regs_changed()):
        return await dock.stop_container(name)


@dome.expose(path='/rm/{name}')
async def remove(name, **params):
    """
    Unload/remove service
    """
    container = await dock.get(name)
    # check container exists
    if not container:
        return 404

    async with StateCtx(name, check_regs_changed()):
        # removing from control list
        await band_config.set_rm(STARTED, name)
        # executing remove
        return await dock.remove_container(name)


@dome.tasks.add
async def startup():
    """
    Heart-beat task
    """
    for num in count():
        """
        Load steps:
        0. Loading data, sending requests
        2. Creating missing
        3+ Monitoring
        """
        if num == 0:
            """
            Onstart tasks: loaders, readers, etc...
            """
            # starting config
            await band_config.initialize()
            # Inspecting docker containers
            for c in await dock.containers(struct=list):
                if c.running:
                    await sync_status(c.name)
            # check state exists
            started_present = await band_config.set_exists(STARTED)
            if not started_present:
                await band_config.set_add(STARTED, *settings.default_services)
        if num == 1:
            """
            Starting missing services
            """
            for item in await band_config.set_get(STARTED):
                if item not in state:
                    asyncio.ensure_future(run(item))
        # Remove expired services
        await sleep(5)
        await check_regs_changed()


@dome.shutdown
async def unloader():
    """
    Graceful shutdown task
    """
    # Closing configs holder
    await band_config.unload()
    # Shutdown docker client
    await dock.close()
    # pass
