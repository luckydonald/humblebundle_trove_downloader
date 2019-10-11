#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

URL_TROVE = "https://www.humblebundle.com/monthly/trove"
URL_DL_SIGN = "https://www.humblebundle.com/api/v1/user/download/sign"
URL_DOWNLOADS = "https://dl.humble.com/{file}"
URL_INFO_CHUNKS = "https://www.humblebundle.com/api/v1/trove/chunk?index={chunk}"

TYPE_WEB = 'web'
TYPE_BITTORRENT = 'bittorrent'

DOWNLOAD_URL_TYPE_TO_SIGNATURE_TYPE_MAP = {
    TYPE_WEB: 'signed_url',
    TYPE_BITTORRENT: 'signed_torrent_url',
}

HASH_CHUNK_SIZE = 16 * 1024
DOWNLOAD_CHUNK_SIZE = 16 * 1024
