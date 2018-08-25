from inflection import underscore
from prodict import Prodict


def nn(arg):
    """ not nil """
    return arg != None


def isn(arg):
    """ not nil """
    return arg == None


def tar_image_cmd(path):
    return ['tar', '-C', path, '-c', '-X', '.dockerignore', '.']


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


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


def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def merge_dicts(*args):
    if len(args) == 0:
        return
    d = args[0]
    for d2 in args[1:]:
        d.update(d2)
    return d
