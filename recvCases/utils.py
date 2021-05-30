import os
import re
import datetime
import random
from base64 import b64encode
from io import BytesIO

from django.utils.crypto import get_random_string

def rand_str(length=32, type="lower_hex"):
    """
    生成指定长度的随机字符串或者数字, 可以用于密钥等安全场景
    :param length: 字符串或者数字的长度
    :param type: str 代表随机字符串，num 代表随机数字
    :return: 字符串
    """
    if type == "str":
        return get_random_string(length, allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    elif type == "lower_str":
        return get_random_string(length, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789")
    elif type == "lower_hex":
        return random.choice("123456789abcdef") + get_random_string(length - 1, allowed_chars="0123456789abcdef")
    else:
        return random.choice("123456789") + get_random_string(length - 1, allowed_chars="0123456789")

def natural_sort_key(s, _nsre=re.compile(r"(\d+)")):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]

def filter_name_list(name_list, dir=""):
    ret = []
    prefix = 1
    while True:
        in_name = f"{prefix}.in"
        out_name = f"{prefix}.out"
        if f"{dir}{in_name}" in name_list and f"{dir}{out_name}" in name_list:
            ret.append(in_name)
            ret.append(out_name)
            prefix += 1
            continue
        else:
            return sorted(ret, key=natural_sort_key)

class APIError(Exception):
    def __init__(self, msg, err=None):
        self.err = err
        self.msg = msg
        super().__init__(err, msg)