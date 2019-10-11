# noinspection PyUnresolvedReferences
import utils.monkey_patch_to_json  # this needs to be first
import torrent_parser
import requests
import hashlib
import json
from os import path
from bs4 import BeautifulSoup
from typing import List
from classes import URLData, CarouselContent, Game, Developer, Download, URLs, Publisher
from settings import DOWNLOAD_DIR, COOKIE_JAR
from constants import URL_TROVE, URL_DL_SIGN, URL_DOWNLOADS, URL_INFO_CHUNKS, TYPE_WEB
from constants import TYPE_BITTORRENT, DOWNLOAD_URL_TYPE_TO_SIGNATURE_TYPE_MAP, HASH_CHUNK_SIZE, DOWNLOAD_CHUNK_SIZE
from utils.save import download_file, sanitize_name
from utils.file_size import human_size
from utils.templater import get_template
from utils.progress_bar import create_advanced_copy_progress
from luckydonaldUtils.logger import logging
from luckydonaldUtils.files.basics import mkdir_p


logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)


do_download_images = True
do_download_games = True
do_generate_html = True

# now we can start.


# find out how many chunks we need to load.
response = requests.request(
    method='GET',
    url=URL_TROVE,
    cookies=COOKIE_JAR
)

# parse page
soup = BeautifulSoup(response.content, features="html.parser")
json_script_tag_trove_data_element = soup.find('script', id='webpack-monthly-trove-data')
json_script_tag_trove_data_string = "\n".join(json_script_tag_trove_data_element.contents)
trove_data = json.loads(json_script_tag_trove_data_string)

CHUNKS_COUNT = trove_data['chunks']
GAME_DATA = []
GAME_DATA.extend(trove_data['standardProducts'])
GAME_DATA.extend(trove_data['newlyAdded'])

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


GAMES = []
GAMES_COUNT = len(GAME_DATA)
GAMES_COUNT_LEN = len(str(GAMES_COUNT))
DOWNLOAD_TOTAL_SIZE = 0
DOWNLOADS: List[URLData] = []  # file: url
for i, game_data in enumerate(GAME_DATA):
    part = f"<{i + 1:0>{GAMES_COUNT_LEN}}/{GAMES_COUNT}>"
    logger.debug(f'{part}: Parsing json: {game_data!r}')
    game = Game(
        background_image=game_data['background-image'],
        publishers=[
            Publisher(
                name=pub['publisher-name'],
                url=pub.get('publisher-url'),
            )
            for pub in (game_data['publishers'] if game_data.get('publishers', None) is not None else [])
        ],
        date_added=game_data['date-added'],
        machine_name=game_data['machine_name'],
        humble_original=game_data['humble-original'],
        downloads={
            k: Download(
                name=dl['name'],
                machine_name=dl['machine_name'],
                url=URLs(
                    web=dl['url']['web'],
                    bittorrent=dl['url'].get('bittorrent'),
                ),
                small=dl.get('small'),
                md5=dl['md5'],
                sha1=dl.get('sha1'),
                file_size=dl['file_size'],
                human_size=dl.get('size', human_size(dl['file_size'])),
                uploaded_at=dl.get('uploaded_at'),
            )
            for k, dl in game_data['downloads'].items()
        },
        popularity=game_data['popularity'],
        trove_showcase_css=game_data['trove-showcase-css'],
        youtube_link=game_data['youtube-link'],
        all_access=game_data['all-access'],
        carousel_content=CarouselContent(
            youtube_link=game_data['carousel-content'].get('youtube-link', []),
            thumbnail=game_data['carousel-content']['thumbnail'],
            screenshot=game_data['carousel-content']['screenshot'],
        ),
        human_name=game_data['human-name'],
        logo=game_data['logo'],
        description_text=game_data['description-text'],
        developers=[
            Developer(
                name=dev['developer-name'],
                url=dev.get('developer-url'),
            )
            for dev in (game_data['developers'] if game_data.get('developers', None) is not None else [])
        ],
        image=game_data['image'],
        background_color=game_data['background-color'],
        marketing_blurb=game_data['marketing-blurb'],
    )
    GAMES.append(game)
    logger.debug(f'{part}: Found Game {game.title!r} with {len(game_data["downloads"])} downloads.')
    game_path = path.join(DOWNLOAD_DIR, sanitize_name(game.title))
    mkdir_p(game_path)
    for platform, download in game.downloads.items():
        download_path = path.join(game_path, sanitize_name(platform))
        mkdir_p(download_path)
        for download_type, download_filename in download.url.items():
            download_file_path = path.join(download_path, sanitize_name(download_filename))
            auth_request_data = {
                "machine_name": download.machine_name,
                "filename": download_filename
            }
            if download_type == TYPE_WEB:
                for meta_file in ('md5', 'sha1'):
                    value = getattr(download, meta_file)
                    if value is None:
                        continue
                    # end if
                    meta_file_path = download_file_path + ".trove." + meta_file
                    with open(meta_file_path, 'w') as f:
                        f.write(value)
                    # end with
                # end for
            # end if
            DOWNLOADS.append(URLData(
                url=URL_DOWNLOADS.format(file=download),
                auth_request=auth_request_data,
                file=download_file_path,
                type=download_type,
                size=download.file_size if download_type == TYPE_WEB else None,  # only the actual file.
                md5=download.md5 if download_type == TYPE_WEB else None,  # only the actual file.
                sha1=download.sha1 if download_type == TYPE_WEB else None,  # only the actual file.
            ))
        # end for
        if download.file_size:
            DOWNLOAD_TOTAL_SIZE += download.file_size
        # end if
    # end for
    with open(path.join(game_path, 'info.json'), 'w') as f:
        json.dump(game, f, indent=2, sort_keys=True)
    # end with
# end for

GAMES_BY_ID = {  # cheap way to remove duplicates
    game.machine_name: game for game in GAMES
}
GAMES = GAMES_BY_ID.items()

logger.info(f'---> Total storage needed: {human_size(DOWNLOAD_TOTAL_SIZE)}')


if do_download_games:
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
                logger.success(f'{part}: Overall discovery progress: {human_size(downloaded_size)} ({downloaded_size}) of {human_size(DOWNLOAD_TOTAL_SIZE)} ({DOWNLOAD_TOTAL_SIZE}).')
                continue
            elif not needs_download:
                logger.success(f'{part}: Existing file {url_data.file!r} has correct metadata. Skipping download.')
                logger.success(f'{part}: Overall discovery progress: {human_size(downloaded_size)} ({downloaded_size}) of {human_size(DOWNLOAD_TOTAL_SIZE)} ({DOWNLOAD_TOTAL_SIZE}).')
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
        download_file(url, url_data.file, log_prefix=f"{part}: ", progress_bar_prefix=f"{part} DOWNLOAD:", file_size=DOWNLOAD_CHUNK_SIZE)
        logger.success(f'{part}: Overall download progress: {human_size(downloaded_size)} ({downloaded_size}) of {human_size(DOWNLOAD_TOTAL_SIZE)} ({DOWNLOAD_TOTAL_SIZE}).')
    # end for
    part = f"[{'':->{GAMES_COUNT_LEN}}/{'':->{GAMES_COUNT_LEN}}]"
    logger.success(f'{part}: Done with downloading.')
# end for


if do_download_images:
    for i, game in enumerate(GAMES):
        part = f"{{{i + 1:0>{GAMES_COUNT_LEN}}/{GAMES_COUNT}}}"
        mkdir_p(path.join(DOWNLOAD_DIR, game.folder_data))

        if game.logo:
            download_file(
                game.logo, path.join(DOWNLOAD_DIR, game.folder_data, 'logo.png'),
                log_prefix=f'{part} logo: ', progress_bar_prefix="LOGO: ",
            )
        # end if
        if game.image:
            download_file(
                game.image, path.join(DOWNLOAD_DIR, game.folder_data, 'image.png'),
                log_prefix=f'{part} image: ', progress_bar_prefix="IMG: ",
            )
        # end if
        screenshot_len = len(game.carousel_content.screenshot)
        screenshot_len_len = len(str(screenshot_len))
        logger.debug(f'{part}: Found {screenshot_len} screenshots.')
        for i2, screenshot in enumerate(game.carousel_content.screenshot):
            download_file(
                screenshot, path.join(DOWNLOAD_DIR, game.folder_data, f'screenshot_{i2}.png'),
                log_prefix=f'{part} screenshot ({i2 + 1:0>{screenshot_len}}/{screenshot_len}): ',
                progress_bar_prefix=f"SCR{i2 + 1:0>{screenshot_len}}: ",
            )
        # end if
    # end for
# end if


if do_generate_html:
    part = f"<{'':->{GAMES_COUNT_LEN}}/{'':->{GAMES_COUNT_LEN}}>"
    template = get_template('./overview.html.template')
    template_txt = template.render(games=GAMES)
    html_path = path.join(DOWNLOAD_DIR, 'overview.html')
    with open(html_path, "w") as f:
        f.write(template_txt)
    # end with
    logger.success(f'{part}: Written overview to {html_path!r}')

    for i, game in enumerate(GAMES):
        part = f"<{i + 1:0>{GAMES_COUNT_LEN}}/{GAMES_COUNT}>"

        html_path = path.join(DOWNLOAD_DIR, game.folder, 'info.html')

        template = get_template('./info.html.template')
        template_txt = template.render(game=game)
        with open(html_path, "w") as f:
            f.write(template_txt)
        # end with
        logger.success(f'{part}: Written info to {html_path!r}')
    # end for
# end if
