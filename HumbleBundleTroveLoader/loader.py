import torrent_parser
import requests
import hashlib
import json
from os import path
from bs4 import BeautifulSoup
from save import download_file
from typing import List, Union
from settings import DOWNLOAD_DIR, COOKIE_JAR
from file_size import human_size
from templater import get_template
from constants import URL_TROVE, URL_DL_SIGN, URL_DOWNLOADS, URL_INFO_CHUNKS, TYPE_WEB
from constants import TYPE_BITTORRENT, DOWNLOAD_URL_TYPE_TO_SIGNATURE_TYPE_MAP, HASH_CHUNK_SIZE, DOWNLOAD_CHUNK_SIZE
from progress_bar import copyfileobj, create_advanced_copy_progress
from luckydonaldUtils.logger import logging
from luckydonaldUtils.files.basics import mkdir_p


logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)


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
for chunk in range(CHUNKS_COUNT + 1):
    logger.debug(f"Requesting data of page {chunk + 1} of {CHUNKS_COUNT}.")
    response = requests.request(
        method='GET',
        url=URL_INFO_CHUNKS.format(chunk=chunk),
        cookies=COOKIE_JAR
    )
    chunk_data = response.json()
    GAME_DATA.extend(chunk_data)
# end for

GAMES_COUNT = len(GAME_DATA)
GAMES_COUNT_LEN = len(str(GAMES_COUNT))
DOWNLOAD_TOTAL_SIZE = 0
DOWNLOADS: List[URLData] = []  # file: url
for i, game in enumerate(GAME_DATA):
    part = f"<{i + 1:0>{GAMES_COUNT_LEN}}/{GAMES_COUNT}>"
    title = game['machine_name']
    title = game.get('human_name', title)
    title = game.get('human-name', title)
    logger.debug(f'{part}: Found Game {title!r} with {len(game["downloads"])} downloads.')
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
                size=download_meta.get('file_size', None) if download_type == TYPE_WEB else None,  # only the actual file.
                md5=download_meta.get('md5', None) if download_type == TYPE_WEB else None,  # only the actual file.
                sha1=download_meta.get('sha1', None) if download_type == TYPE_WEB else None,  # only the actual file.
            ))
        # end for
        DOWNLOAD_TOTAL_SIZE += download_meta.get('file_size', 0)
    # end for
    with open(path.join(game_path, 'info.json'), 'w') as f:
        json.dump(game, f, indent=2, sort_keys=True)
    # end with
# end for

logger.info(f'---> Total storage needed: {human_size(DOWNLOAD_TOTAL_SIZE)}')

DOWNLOADS_COUNT = len(DOWNLOADS)
DOWNLOADS_COUNT_LEN = len(str(DOWNLOADS_COUNT))
url_data: URLData
downloaded_size = 0
for i, url_data in enumerate(DOWNLOADS):
    part = f"[{i + 1:0>{DOWNLOADS_COUNT_LEN}}/{DOWNLOADS_COUNT}]"
    logger.info(f'{part}: Checking {url_data.file!r} from {url_data.url!r}...')
    # check if file already exists.
    if path.exists(url_data.file):
        logger.debug(f'{part}: File {url_data.file!r} already exists.')
        needs_download = False
        if url_data.type == TYPE_WEB:
            # check file size
            logger.debug(f'{part}: File {url_data.file!r} already exists. Checking size.')
            disk_size = path.getsize(url_data.file)
            if disk_size == url_data.size:
                logger.debug(f'{part}: File {url_data.file!r} already exists. Checking size.')
                downloaded_size += url_data.size
            else:
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
        elif url_data.type == TYPE_BITTORRENT:
            logger.debug(f'{part}: File {url_data.file!r} already exists. Checking being valid torrent file.')
            try:
                torrent_parser.parse_torrent_file(url_data.file)
            except torrent_parser.InvalidTorrentDataException as e:
                logger.warning(f'{part}: Could not parse existing torrent file.\n{e!s}', exc_info=True)
                needs_download = True
            # end try
        else:  # neither torrent nor direct web download
            logger.fatal(
                f'{part}: Could not check size, md5 or sha1 for file {url_data.file!r} as it is not of type'
                f' {TYPE_WEB!r} or {TYPE_BITTORRENT!r},  but is of type {url_data.type!r}.'
            )
            needs_download = None
        # end if
        if needs_download is None:
            logger.success(f'{part}: File {url_data.file!r} was found. Could be correct. Skipping download.')
            logger.success(f'{part}: Overall discovery progress: {human_size(downloaded_size)} of {human_size(DOWNLOAD_TOTAL_SIZE)}')
            continue
        elif not needs_download:
            logger.success(f'{part}: Existing file {url_data.file!r} has correct metadata. Skipping download.')
            logger.success(f'{part}: Overall discovery progress: {human_size(downloaded_size)} of {human_size(DOWNLOAD_TOTAL_SIZE)}')
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
    logger.info(f'{part}: Downloading {url_data.file!r} from signed url {url!r}, size reported by trove: {human_size(file_size)!r}')
    download_file(url, url_data.file, log_prefix=f"{part}: ", progress_bar_prefix=f"{part} DOWNLOAD:", file_size=)
    logger.success(f'{part}: Overall download progress: {human_size(downloaded_size)} ({downloaded_size}) of {human_size(DOWNLOAD_TOTAL_SIZE)} ({DOWNLOAD_TOTAL_SIZE}).')
# end for


class CarouselContent(object):
    youtube_link: List[str]
    thumbnail: List[str]
    screenshot: List[str]

    def __init__(
        self,
        youtube_link: List[str],
        thumbnail: List[str],
        screenshot: List[str],
    ):
        self.youtube_link = youtube_link
        self.thumbnail = thumbnail
        self.screenshot = screenshot
    # end def
# end class


class Game(object):
    background_image: Union[None, str]
    publishers: Union[None, dict]
    date_added: Union[None, int]
    machine_name: Union[None, str]
    humble_original: Union[None, bool]
    downloads: Union[None, dict]
    popularity: Union[None, int]
    trove_showcase_css: Union[None, str]
    youtube_link: Union[None, str]
    all_access: Union[None, int]
    carousel_content: CarouselContent
    human_name: str
    logo: Union[None, str]
    description_text: Union[None, str]
    developers: Union[None, str]
    image: Union[None, str]
    background_color: Union[None, str]
    marketing_blurb: Union[None, str]

    def __init__(
        self,
        background_image, publishers, date_added, machine_name, humble_original, downloads, popularity,
        trove_showcase_css, youtube_link, all_access, carousel_content, human_name, logo, description_text,
        developers, image, background_color, marketing_blurb
    ):
        self.background_image = background_image
        self.publishers = publishers
        self.date_added = date_added
        self.machine_name = machine_name
        self.humble_original = humble_original
        self.downloads = downloads
        self.popularity = popularity
        self.trove_showcase_css = trove_showcase_css
        self.youtube_link = youtube_link
        self.all_access = all_access
        self.carousel_content = carousel_content
        self.human_name = human_name
        self.logo = logo
        self.description_text = description_text
        self.developers = developers
        self.image = image
        self.background_color = background_color
        self.marketing_blurb = marketing_blurb
    # end def
# end class


for game_data in GAME_DATA:
    part = f"<{i + 1:0>{GAMES_COUNT_LEN}}/{GAMES_COUNT}>"
    game = Game(
        background_image = game_data['background-image'],
        publishers = game_data['publishers'],
        date_added = game_data['date-added'],
        machine_name = game_data['machine_name'],
        humble_original = game_data['humble-original'],
        downloads = game_data['downloads'],
        popularity = game_data['popularity'],
        trove_showcase_css = game_data['trove-showcase-css'],
        youtube_link = game_data['youtube-link'],
        all_access = game_data['all-access'],
        carousel_content=CarouselContent(
            youtube_link=game_data['carousel-content']['youtube-link'],
            thumbnail=game_data['carousel-content']['thumbnail'],
            screenshot=game_data['carousel-content']['screenshot'],
        ),
        human_name = game_data['human-name'],
        logo = game_data['logo'],
        description_text = game_data['description-text'],
        developers = game_data['developers'],
        image = game_data['image'],
        background_color = game_data['background-color'],
        marketing_blurb = game_data['marketing-blurb'],
    )

    game_path = path.join(DOWNLOAD_DIR, game.human_name.replace(':', ' - ').replace('/', ':'))
    # noinspection PyTypeChecker
    html_path = path.join(game_path, 'index.html')
    # noinspection PyTypeChecker
    files_path = path.join(game_path, 'data/')

    if game.logo:
        download_file(game.logo, path.join(files_path, 'logo.png'))
    # end if
    if game.image:
        download_file(game.image, path.join(files_path, 'image.png'))
    # end if
    for i, screenshot in enumerate(game.carousel_content.screenshot):
        download_file(screenshot, path.join(files_path, f'screenshot_{i}.png'))
    # end if
    template = get_template('./info.html.template')
    template_txt = template.render(game=game)
    with open(html_path, "w") as f:
        f.write(template_txt)
    # end with
    logger.success(f'{part}: Written info to {html_path!r}')
# end for
