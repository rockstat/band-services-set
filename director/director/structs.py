from collections import namedtuple
from prodict import Prodict
from typing import List

IMAGE_CATEGORIES = Prodict(user='user', collection='collection', base='base')

ImageObj = namedtuple('ImageObj', 'name category path')


class ServicePostion(namedtuple('ServicePostion', 'col row')):
    __slots__ = ()
    def __str__(self):
        return f"{self.col}x{self.row}"
