from band import settings, dome, logger, app

from .state_manager import StateManager, dock, image_navigator
from .constants import *

state = StateManager()

from . import api_main
from . import api_stats

@dome.tasks.add
async def _state_up():
    await state.initialize()

@dome.shutdown
async def _state_down():
    await state.unload()

__VERSION__ = '0.3.0'

