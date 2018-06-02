from inflection import underscore
from prodict import Prodict


def underdict(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            key = underscore(key)
            new_dict[key] = underdict(value)
        return new_dict
    # if hasattr(obj, '__iter__'):
    #     return [underdict(value) for value in obj]
    else:
        return obj
