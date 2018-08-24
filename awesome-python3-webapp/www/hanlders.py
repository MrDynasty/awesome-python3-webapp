#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/24 下午12:13
# @Author  : Mr.Dynasty
# @File    : hanlders.py
# @Software: PyCharm
# @license : Copyright(C), Mr.Dynasty

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get,post
from models import User, Comment, Blog, next_id

@get('/')
async def index(request):
    users = User.findAll()
    return {
        '__templates__' : 'test.html',
        'users' : users
    }