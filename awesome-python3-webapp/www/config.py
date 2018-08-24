#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/24 上午11:35
# @Author  : Mr.Dynasty
# @File    : config.py
# @Software: PyCharm
# @license : Copyright(C), Mr.Dynasty

import config_default

class Dict(dict):
    '''
    Simple dict but support access as x.y style
    '''
    def __init__(self, names=(), values=(), **kw):
        super.__init__(**kw)
        for k, v in zip(names,values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute %s" % key)

    def __setattr__(self, key, value):
        self[key] = value

def merage(defaults, override):
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merage(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r
def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(v) if isinstance(v, dict) else v

configs = config_default.configs

try:
    import config_override
    configs = merage(configs, config_override.configs)
except ImportError:
    pass

configs = toDict(configs)