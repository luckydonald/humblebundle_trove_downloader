#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def human_size(nbytes: Union[int, None]) -> Union[str, None]:
    """
    Calculates a human readable size string.
    See https://stackoverflow.com/a/14996816/3423324#python-libraries-to-calculate-human-readable-filesize-from-bytes.

    :param nbytes: The amount of bytes.
    :return: a formatted string, or `None` if the input was `None`, too.
    """
    if nbytes is None:
        return None
    # end if
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])
