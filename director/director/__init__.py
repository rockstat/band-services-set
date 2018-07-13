from band import settings, dome, logger, app

from .state import State
from .docker_manager import DockerManager
from .constants import *
from .band_config import band_config

dock = DockerManager(**settings)
state = State()

from . import main
from . import stat_api

__VERSION__ = '0.3.0'
