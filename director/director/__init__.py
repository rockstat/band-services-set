from band import settings, dome, logger, app

from .state import State
from .docker_manager import DockerManager
from .constants import *
from .band_config import BandConfig

band_config = BandConfig(**settings)
dock = DockerManager(**settings)
state = State()

from . import main
from . import stat_api

__VERSION__ = '0.3.0'
