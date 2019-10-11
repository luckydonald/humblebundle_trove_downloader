#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

from typing import Union
from file_size import human_size
from constants import DOWNLOAD_CHUNK_SIZE
from progress_bar import create_advanced_copy_progress, copyfileobj
from luckydonaldUtils.logger import logging


__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


def download_file(url: str, file: str, log_prefix: str = "", progress_bar_prefix: str = "", file_size: Union[None, int] = int):
    # noinspection PyShadowingNames
    with requests.get(url, stream=True) as response:
        logger.debug(f'{log_prefix}Response: {response}')
        dl_file_size = response.headers.get('content-length', None)
        dl_file_size = int(dl_file_size) if dl_file_size is not None else None
        logger.info(f"{log_prefix}Download size reported by server: {human_size(dl_file_size)!r}")
        file_size = dl_file_size if dl_file_size is not None else file_size
        callback = create_advanced_copy_progress(prefix=progress_bar_prefix, width=None, use_color=True)
        with open(file, 'wb') as f:
            copyfileobj(response.raw, f, callback=callback, total=file_size, length=DOWNLOAD_CHUNK_SIZE)
        # end with
        callback(file_size, DOWNLOAD_CHUNK_SIZE, file_size)  # enforce 100%
        print()  # enforce linebreak
    # end with
    logger.success(f'{log_prefix}Downloaded {url!r} to {file!r}.')
# end def
