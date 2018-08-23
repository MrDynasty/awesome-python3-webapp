#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/23 上午10:49
# @Author  : Mr.Dynasty
# @File    : apis.py
# @Software: PyCharm
# @license : Copyright(C), Mr.Dynasty

import json,logging,inspect,functools

class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional)
    '''
    def __init__(self, error, data='', message=''):
        super().__init__(message)
        self.error = error
        self.data = data
        self.messgae = message

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''
    def __init__(self, field, message=''):
        super().__init__('value:invalid', field, message)

class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource not found. The data specifies the resource name.
    '''
    def __init__(self, field, message=''):
        super().__init__('value:notfound', field, message)

class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''
    def __init__(self, message=''):
        super().__init__('permission:forbidden','permission',message)