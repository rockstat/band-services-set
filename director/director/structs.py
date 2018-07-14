from collections import namedtuple
from prodict import Prodict
from typing import List

IMAGE_CATEGORIES = Prodict(user='user', collection='collection', base='base')

ImageObj = namedtuple('ImageObj', 'name category path')


