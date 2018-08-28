import band
from band import settings, logger, app, worker, cleaner

from .state_manager import StateManager, dock, image_navigator
from .constants import *

state = StateManager()

from . import api_main
from . import api_stats

@worker()
async def __state_up():
    await state.initialize()

@cleaner()
async def __state_down():
    await state.unload()

__VERSION__ = '0.3.0'

