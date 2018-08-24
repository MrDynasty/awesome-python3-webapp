#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/22 下午6:01
# @Author  : Mr.Dynasty
# @File    : coroweb.py
# @Software: PyCharm
# @license : Copyright(C), Mr.Dynasty

import asyncio, os, inspect, logging, functools

from urllib import parse
from aiohttp import web
from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(functools)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

def has_request_arg(fn):
    '''
    检查函数是否有request参数，返回bool。若有request参数，检查该参数是否为最后一个参数，否则抛出异常
    '''
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s %s' % (fn.__name__,sig))
    return found

def has_var_kw_arg(fn):
    '''
    检查函数是否有关键字参数集，返回布尔值
    '''
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

def has_named_kw_args(fn):
    '''
    检查函数是否有命名关键字参数集，返回布尔值
    '''
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind != inspect.Parameter.KEYWORD_ONLY:
            return True

def get_named_kw_args(fn):
    '''
    将函数所有的 命名关键字参数名 作为一个tuple返回
    '''
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

def get_required_kw_args(fn):
    '''
    将函数所有的 没有默认值的 命名关键字参数名 作为一个tuple返回
    '''
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

class RequestHanlder(object):
    '''
    请求处理器，用来封装请求处理函数
    '''
    def __index__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    async def __call__(self, request):
        '''
        分析请求 ，request hanlder, must be a coroutine that accepts a request instance as its only argument and returns a streamresponse derived instance
        '''
        kw = None
        if self._has_request_arg or self._has_named_kw_args or self._has_var_kw_arg:
            # 当传入的参数含有 request参数 或 命名关键字参数 或 关键词参数
            if request.method == 'POST':
                # POST请求预处理
                if not request.content_type:
                    # 无正文类型信息时返回
                    return web.HTTPBadRequest('Missing Content-Type')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    #处理json类型传入的数据，传入参数字典中
                    params = await request.json()
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest('JSON body must be object')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencode') or ct.startswith('application/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupport Content-Type: %s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw == None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg or self._named_kw_args:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
                for k, v in request.match_info.items():
                    if k in kw:
                        logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                    kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    # 当存在关键字参数未被赋值时返回 例如，一般登录注册时未输入密码，提示密码未输入
                    return web.HTTPBadRequest('Missing arguments: %s' % name)
        logging.info('call with args: %s' % kw)
        try:
            r = self._func(**kw)
            # 最后调用处理函数，并传入请求参数，进行请求处理
            return r
        except APIError as e:
            return dict(error=e.error,data=e.data,message=e.messgae)

def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)
    logging.info('add static %s => %s' % ('/static/', path))

def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
        logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
        app.router.add_route(method, path, RequestHanlder(app, fn))

def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals()), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            # 略过所有私有属性
            continue
            fn = getattr(mod, attr)
            if callable(fn):
                method = getattr(fn, '__method__', None)
                path = getattr(fn, '__route__', None)
                if method and path:
                    add_route(app, fn)


