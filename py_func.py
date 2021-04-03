#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

import os


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_file_contents(file):
    f = open(file, "r", encoding='utf-8')
    c = ''
    if f.mode == 'r':
        c = f.read()
    f.close()
    return c


def put_file_contents(file, contents, mode="w"):
    ensure_dir(file)
    f = open(file, mode, encoding='utf-8')
    f.write(contents)
    f.close()
