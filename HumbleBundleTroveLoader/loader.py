import requests
import hashlib
import json
from os import path
from bs4 import BeautifulSoup
from typing import List, Union
from settings import DOWNLOAD_DIR, COOKIE_JAR
from file_size import human_size
from progress_bar import copyfileobj, create_advanced_copy_progress
from luckydonaldUtils.logger import logging
from luckydonaldUtils.files.basics import mkdir_p

logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)

URL_TROVE = "https://www.humblebundle.com/monthly/trove"
URL_DL_SIGN = "https://www.humblebundle.com/api/v1/user/download/sign"
URL_DOWNLOADS = "https://dl.humble.com/{file}"
URL_INFO_CHUNKS = "https://www.humblebundle.com/api/v1/trove/chunk?index={chunk}"

DOWNLOAD_URL_TYPE_TO_SIGNATURE_TYPE_MAP = {
    'web': 'signed_url',
    'bittorrent': 'signed_torrent_url',
}

HASH_CHUNK_SIZE = 16 * 1024
DOWNLOAD_CHUNK_SIZE = 16 * 1024


class URLData(object):
    url: str
    auth_request: dict
    file: str
    type: str
    size: Union[int, None]
    md5: Union[str, None]
    sha1: Union[str, None]

    # noinspection PyShadowingNames
    def __init__(self, url: str, auth_request: dict, file: str, type: str, size: int, md5: str, sha1: str) -> None:
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


# now we can start.


# find out how many chunks we need to load.
response = requests.request(
    method='GET',
    url=URL_TROVE,
    cookies=COOKIE_JAR
)

with open("/tmp/trove.html", "wb") as f:
    f.write(response.content)
# end if

# parse page
soup = BeautifulSoup(response.content, features="html.parser")
json_script_tag_trove_data_element = soup.find('script', id='webpack-monthly-trove-data')
json_script_tag_trove_data_string = "\n".join(json_script_tag_trove_data_element.contents)
trove_data = json.loads(json_script_tag_trove_data_string)

CHUNKS_COUNT = trove_data['chunks']
GAME_DATA = []

logger.info(f"We have {CHUNKS_COUNT} pages of {trove_data['gamesPerChunk']} games each to load.")
for chunk in range(CHUNKS_COUNT):
    logger.debug(f"Requesting data of page {chunk + 1} of {CHUNKS_COUNT}.")
    response = requests.request(
        method='GET',
        url=URL_TROVE,
        cookies=COOKIE_JAR
    )
    chunk_data = json.loads(json_script_tag_trove_data_string)
    GAME_DATA.extend(chunk_data.get('standardProducts', []))
# end for


DOWNLOADS: List[URLData] = []  # file: url
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
                url=URL_DOWNLOADS.format(file=download),
                auth_request=auth_request_data,
                file=path.join(download_path, download.replace('/', ':')),
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

DOWNLOADS_COUNT = len(DOWNLOADS)
DOWNLOADS_COUNT_LEN = len(str(DOWNLOADS_COUNT))
url_data: URLData
for i, url_data in enumerate(DOWNLOADS):
    part = f"[{i + 1:0>{DOWNLOADS_COUNT_LEN}}/{DOWNLOADS_COUNT}]"
    logger.info(f'{part}: Checking {url_data.file!r} from {url_data.url!r}...')
    # check if file already exists.
    if path.exists(url_data.file):
        logger.debug(f'{part}: File {url_data.file!r} already exists.')
        needs_download = False
        if url_data.type != 'web':
            logger.info(
                f"{part}: Could not check size, md5 or sha1 for file {url_data.file!r} as it is not the main 'web' file, "
                f'but is of type {url_data.type!r}.'
            )
            needs_download = None
        else:
            # check file size
            logger.debug(f'{part}: File {url_data.file!r} already exists. Checking size.')
            disk_size = path.getsize(url_data.file)
            if disk_size != url_data.size:
                logger.warning(f'Existing file {url_data.file!r} has wrong filesize. Disk is {disk_size!r}, online is {url_data.size!r}.')
                needs_download = True
            # end if

            # check md5 and sha1 hash
            logger.debug(f'{part}: File {url_data.file!r} already exists. Checking file hashes.')
            hash_md5 = hashlib.md5()
            hash_sha1 = hashlib.sha1()
            callback = create_advanced_copy_progress(prefix=f"{part}: HASH ", width=None, use_color=True)
            already_copied = 0
            with open(url_data.file, "rb") as f:
                for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
                    callback(already_copied, HASH_CHUNK_SIZE, disk_size)
                    hash_md5.update(chunk)
                    hash_sha1.update(chunk)
                    already_copied += HASH_CHUNK_SIZE
                # end for
                callback(disk_size, HASH_CHUNK_SIZE, disk_size)  # enforce 100%
                print()  # enforce linebreak
            # end with
            md5 = hash_md5.hexdigest()
            sha1 = hash_sha1.hexdigest()
            if url_data.md5 is None:
                logger.warning(f'{part}: Existing file {url_data.file!r} has no md5 hashsum. Disk is {md5!r}.')
            elif md5 != url_data.md5:
                logger.warning(f'{part}: Existing file {url_data.file!r} has wrong md5 hashsum. Disk is {md5!r}, online is {url_data.md5!r}.')
                needs_download = True
            # end if
            if url_data.sha1 is None:
                logger.info(
                    f'{part}: Existing file {url_data.file!r} has no sha1 hashsum. Disk is {sha1!r}.\n'
                    f'SHA1 hash of Humble Bundle Trove items is often unreliable. Therefore this message can be ignored.'
                )
            elif sha1 != url_data.sha1:
                logger.info(
                    f'{part}: Existing file {url_data.file!r} has wrong sha1 hashsum. Disk is {sha1!r}, online is {url_data.sha1!r}.\n'
                    f'SHA1 hash of Humble Bundle Trove items is often unreliable. Therefore this message can be ignored.'
                )
                # needs_download = True  # this seems to be unreliable.
            # end if
        # end if
        if needs_download is None:
            logger.success(f'{part}: File {url_data.file!r} was found. Skipping download.')
            continue
        elif not needs_download:
            logger.success(f'{part}: Existing file {url_data.file!r} has correct metadata. Skipping download.')
            continue
        else:
            logger.warning(f'{part}: Will download again.')
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
    file_size = int(url_data.size) if isinstance(url_data.size, str) else url_data.size
    logger.info(f'{part}: Downloading {url_data.file!r} from signed url {url!r}, size reported by trove: {human_size(file_size)}')
    with requests.get(url, stream=True) as resp:
        logger.debug(f'{part}: Response: {resp}')
        file_size = int(resp.headers.get('content-length', file_size))
        logger.info(f"{part}: Download size reported by server: {human_size(file_size)}")
        prefix = f"{part}: DOWNLOAD "
        callback = create_advanced_copy_progress(prefix=prefix, width=None, use_color=True)
        with open(url_data.file, 'wb') as f:
            copyfileobj(resp.raw, f, callback=callback, total=file_size, length=DOWNLOAD_CHUNK_SIZE)
        # end with
        callback(url_data.size, DOWNLOAD_CHUNK_SIZE, url_data.size)  # enforce 100%
        print()  # enforce linebreak
    # end with
    logger.success(f'{part}: Downloaded {url_data.file!r}.')
# end for

