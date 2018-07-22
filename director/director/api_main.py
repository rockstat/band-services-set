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

from .constants import STATUS_RUNNING, STARTED
from .helpers import merge, str2bool
from . import dock, state, image_navigator

from pprint import pprint


@dome.expose(path='/state')
async def get_state(name=None, prop=None):
    """
    Get list of services in state or get state of specified service
    Method for debug purposes
    """
    if name:
        if name in state:
            srv = await state.get(name)
            if prop and hasattr(srv, prop):
                return getattr(srv, prop)
            return srv.full_state()
    return list(state.state.keys())


@dome.expose(name='list')
async def lst(**params):
    """
    Containers list with status information
    """
    return list(
        [fs for fs in [s.full_state() for s in state.values()] if fs.state])


@dome.expose()
async def registrations(**params):
    """
    Provide global RPC registrations information
    Method for debug purposes
    """
    methods = []
    # Iterating over containers and their methods
    for srv in state.values():
        if srv.is_active():
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
    srv = await state.get(name)
    payload = dict()
    # Payload for frontend servoce
    if name == FRONTIER_SERVICE:
        payload.update(await registrations())

    # Loading state, config, meta
    status = await rpc.request(name, REQUEST_STATUS, **payload)
    
    srv.set_appstate(status)
    
    

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
async def list_images(**params):
    """
    Available images list
    """
    return await image_navigator.lst()


@dome.expose()
async def list_configs(**params):
    """
    List of saved services configurations
    """
    return await state.configs()


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
    if not image_navigator.is_native(name):
        return 404

    srv = await state.get(name)
    srv.set_build_opts(**kwargs)

    logger.info('request with params: %s. Using config: %s', kwargs,
                srv.config)
    await dock.run_container(name, **srv.config.build_options)
    # save params and state only if successfully starter
    await state.add_to_startup(name)
    await state.resolve_docstatus(name)
    return srv.full_state()


@dome.expose()
async def rebuild_all(**kwargs):
    """
    Rebuild all controlled containers
    """
    for name in await state.should_start():
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
    async with state.clean_ctx(name, check_regs_changed()):
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
    async with state.clean_ctx(name, check_regs_changed()):
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

    async with state.clean_ctx(name, check_regs_changed()):
        # removing from control list
        await state.rm(name)
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
            await state.initialize()
            # looking for containers to request status
            for container in await dock.containers(struct=list):
                if container.running and container.native:
                    asyncio.ensure_future(sync_status(container.name))

        if num == 1:
            """
            Starting missing services
            """
            for item in await state.should_start():
                if not (item in state and (await state.get(item)).is_active()):
                    asyncio.ensure_future(run(item))
        # Remove expired services
        await sleep(5)
        await state.resolve_docstatus_all()
        await check_regs_changed()


@dome.shutdown
async def unloader():
    """
    Graceful shutdown task
    """
    # Closing configs holder
    await state.unload()
    # Shutdown docker client
    await dock.close()
    # pass
