from band import settings, dome, logger

from .state import State
from .docker_manager import DockerManager
from .constants import *
from .band_config import BandConfig


dock = DockerManager(**settings)
state = State()
band_config = BandConfig(**settings)

from . import main
from . import stat_api

__VERSION__ = '0.3.0'

