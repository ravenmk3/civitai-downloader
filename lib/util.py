import base64
import functools
import hashlib
import logging
import math
import os
import shutil
import sys
import time
import urllib.parse

import yaml
from requests import HTTPError


def base64_decode_str(encoded: str) -> str:
    return base64.b64decode(encoded).decode('utf-8')


def human_readable_size(size: int) -> str:
    units = [(4, 'TB'), (3, 'GB'), (2, 'MB'), (1, 'KB')]
    for unit in units:
        step = math.pow(1024, unit[0])
        if size >= step:
            value = round(float(size) / step, 2)
            return f'{value} {unit[1]}'
    return f'{size} B'


def md5_hex(val: any) -> str:
    if not isinstance(val, bytes):
        if not isinstance(val, str):
            val = str(val)
        val = val.encode('utf-8')
    h = hashlib.md5()
    h.update(val)
    return h.hexdigest().lower()


def safe_filename(name: str) -> str:
    chars = r'\/:*?"<>|'
    for c in chars:
        name = name.replace(c, '_')
    return name.strip()


def safe_rmtree(path: str):
    for i in range(99999):
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                return
            except Exception as e:
                logging.error(e)
                time.sleep(1)


def safe_move(src: str, dst: str):
    for i in range(99999):
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                return
            except Exception as e:
                logging.error(e)
                time.sleep(1)


def get_ext_from_url(url: str) -> str:
    u = urllib.parse.urlparse(url)
    _, ext = os.path.splitext(u.path)
    return ext


def http_retry(count: int = 99999):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for n in range(count):
                try:
                    result = func(*args, **kwargs)
                    return result
                except HTTPError as e:
                    code = e.response.status_code
                    logging.error('Response status: %d, %s', code, str(e))
                    if code == 404:
                        return None
                    if code == 403:
                        return None
                    if code == 429:
                        time.sleep(1)
                    if code == 514:
                        time.sleep(1)
                except Exception as e:
                    logging.error(e, exc_info=True)

        return wrapper

    return decorator


def save_yaml(filename: str, data: any):
    with open(filename, 'w+', encoding='utf-8') as fp:
        yaml.dump(data, fp)


def config_logging():
    # encoding='utf-8'
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='%(message)s')
