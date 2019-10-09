import hashlib
from typing import List

import requests
import shutil
import json
from os import path
from bs4 import BeautifulSoup

from progress_bar import copyfileobj, create_advanced_copy_progress
from settings import DOWNLOAD_DIR, COOKIE_JAR
from luckydonaldUtils.files.basics import mkdir_p
from luckydonaldUtils.logger import logging

logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)

URL_TROVE = "https://www.humblebundle.com/monthly/trove"
URL_DL_SIGN = "https://www.humblebundle.com/api/v1/user/download/sign"
URL_DOWNLOAD = "https://dl.humble.com/{file}"

DOWNLOAD_URL_TYPE_TO_SIGNATURE_TYPE_MAP = {
    'web': 'signed_url',
    'bittorrent': 'signed_torrent_url',
}

response = requests.request(
    method='GET',
    url=URL_TROVE,
    cookies=COOKIE_JAR
)

with open("/tmp/trove.html", "wb") as f:
    f.write(response.content)
# end if

soup = BeautifulSoup(response.content, features="html.parser")
json_script_tag_trove_data_element = soup.find('script', id='webpack-monthly-trove-data')
json_script_tag_trove_data_string = "\n".join(json_script_tag_trove_data_element.contents)
trove_data = json.loads(json_script_tag_trove_data_string)

GAME_DATA = trove_data['standardProducts']


class URLData(object):
    url: str
    auth_request: dict
    file: str
    type: str
    size: str
    md5: str
    sha1: str

    def __init__(self, url, auth_request, file, type, size, md5, sha1) -> None:
        self.url = url
        self.auth_request = auth_request
        self.file = file
        self.type = type
        self.size = size
        self.md5 = md5
        self.sha1 = sha1
        super().__init__()
    # end if
# end class


DOWNLOADS:List[URLData] = []  # file: url
for game in GAME_DATA:
    title = game['machine_name']
    title = game.get('human_name', title)
    title = game.get('human-name', title)
    game_path = path.join(DOWNLOAD_DIR, title)
    mkdir_p(game_path)
    for platform, download_meta in game['downloads'].items():
        download_path = path.join(game_path, platform)
        mkdir_p(download_path)
        for download_type, download in download_meta['url'].items():
            auth_request_data = {
                "machine_name": download_meta['machine_name'],
                "filename": download
            }
            download_file_path = path.join(download_path, download)
            for meta_file in ('md5', 'sha1'):
                if meta_file not in download_meta:
                    continue
                # end if
                meta_file_path = download_path + "." + meta_file
                with open(meta_file_path, 'w') as f:
                    f.write(download_meta[meta_file])
                # end with
            # end for
            DOWNLOADS.append(URLData(
                url=URL_DOWNLOAD.format(file=download),
                auth_request=auth_request_data,
                file=download_file_path,
                type=download_type,
                size=download_meta.get('file_size', None) if download_type == 'web' else None,  # only the actual file.
                md5=download_meta.get('md5', None) if download_type == 'web' else None,  # only the actual file.
                sha1=download_meta.get('sha1', None) if download_type == 'web' else None,  # only the actual file.
            ))
        # end for
    # end for
    with open(path.join(game_path, 'info.json'), 'w') as f:
        json.dump(game, f, indent=2, sort_keys=True)
    # end with
# end for

url_data: URLData
for i, url_data in enumerate(DOWNLOADS):
    logger.info(f'Downloading {url_data.file!r} from {url_data.url!r}')
    # check if file already exists.
    if path.exists(url_data.file):
        logger.debug(f'File {url_data.file!r} already exists. Checking size.')

        needs_download = None

        if url_data.type != 'web':
            logger.info(
                f'Could not checking size, md5 or sha1 for file {url_data.file!r} as it is not the main "web" file, '
                f'but is of type {url_data.type}.'
            )
            needs_download = False
        else:
            # check file size
            disk_size = path.getsize(url_data.file)
            if disk_size != url_data.size:
                logger.warning(f'Existing file {url_data.file!r} has wrong filesize. Disk is {disk_size}, online is {url_data.size}.')
                needs_download = True
            # end if

            # check md5 and sha1 hash
            hash_md5 = hashlib.md5()
            hash_sha1 = hashlib.sha1()
            with open(url_data.file, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
                    hash_sha1.update(chunk)
                # end for
            # end with
            md5 = hash_md5.hexdigest()
            sha1 = hash_sha1.hexdigest()
            if url_data.md5 is None:
                logger.warning(f'Existing file {url_data.file!r} has no md5 hashsum. Disk is {md5}.')
            elif md5 != url_data.md5:
                logger.warning(f'Existing file {url_data.file!r} has wrong md5 hashsum. Disk is {md5}, online is {url_data.md5}.')
                needs_download = True
            # end if
            if url_data.sha1 is None:
                logger.warning(f'Existing file {url_data.file!r} has no sha1 hashsum. Disk is {sha1}.')
            elif sha1 != url_data.sha1:
                logger.warning(f'Existing file {url_data.file!r} has wrong sha1 hashsum. Disk is {sha1}, online is {url_data.sha1}.')
                # needs_download = True
            # end if
        # end if
        if needs_download is None:
            logger.success(f'Existing file {url_data.file!r} was found.')
            continue
        elif not needs_download:
            logger.success(f'Existing file {url_data.file!r} has correct metadata.')
            continue
        else:
            logger.warning(f'Will download again.')
        # end if
    # end if

    # get a download url with signature
    signature = requests.request(
        method='POST',
        url=URL_DL_SIGN,
        headers={
            'Accept': 'application/json',
        },
        cookies=COOKIE_JAR,
        data=url_data.auth_request,
    )
    json_signature = signature.json()
    url = json_signature[DOWNLOAD_URL_TYPE_TO_SIGNATURE_TYPE_MAP[url_data.type]]
    logger.info(f'Downloading {url_data.file!r} from signed url {url!r}')
    with requests.get(url, stream=True) as r:
        logger.debug(f'Downloading {url_data.file!r} from signed url {url!r}: {r}')
        with open(url_data.file, 'wb') as f:
            copyfileobj(r.raw, f, callback=create_advanced_copy_progress(prefix="DL ", width=30), total=url_data.size)
        # end with
    # end with
    logger.success(f'Downloaded {url_data.file!r}.')
# end for

