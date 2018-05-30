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


def def_labels(a_ports=[]):
    return Prodict(inband='inband', ports=pack_ports(a_ports))


def tar_image_cmd(path):
    return ['tar', '-C', path, '-c', '-X', '.dockerignore', '.']


def pack_ports(plist=[]):
    return ':'.join([str(p) for p in plist])


def unpack_ports(pstr):
    return pstr and [int(p) for p in pstr.split(':')] or []


def inject_attrs(cont):
    attrs = underdict(cont._container)
    attrs['name'] = (attrs['name']
                     if 'name' in attrs else attrs['names'][0]).strip('/')
    attrs['short_id'] = attrs['id'][:12]
    if 'state' in attrs and 'status' in attrs['state']:
        attrs['status'] = attrs['state']['status']
    if 'config' in attrs and 'labels' in attrs['config']:
        attrs['labels'] = attrs['config']['labels']
    cont.attrs = Prodict.from_dict(attrs)
    return cont


def short_info(container):
    if hasattr(container, 'attrs'):
        inject_attrs(container)
    ca = container.attrs
    dic = Prodict.from_dict({
        key: getattr(container.attrs, key)
        for key in ['short_id', 'name', 'status']
    })
    dic.ports = []
    if 'labels' in ca:
        if 'ports' in ca.labels:
            dic.ports = unpack_ports(ca.labels.ports)
    return dic
