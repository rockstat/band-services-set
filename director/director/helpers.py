from inflection import underscore
from prodict import Prodict

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
