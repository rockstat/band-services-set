
class CopyClear:
    def __init__(self, item):
        self.item = item

    def __enter__(self):
        return self.item[:]

    def __exit__(self, exc_type, exc, tb):
        self.item.clear()


def flatten_dict(dd, separator='.', prefix=''):
    return {
        prefix + separator + k if prefix else k: v
        for kk, vv in dd.items()
        for k, v in flatten_dict(vv, separator, kk).items()
    } if isinstance(dd, dict) else {
        prefix: dd
    }


def prefixer(dd, prefix='_'):
    return {prefix + k: v
            for k, v in dd.items()} if isinstance(dd, dict) else {
                prefix: dd
    }

