#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union, List, Dict

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


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


class Developer(object):
    name: str
    url: str

    def __init__(self, name, url):
        self.name = name
        self.url = url
    # end if
# end class


class Game(object):
    background_image: Union[None, str]
    publishers: Union[None, dict]
    date_added: Union[None, int]
    machine_name: Union[None, str]
    humble_original: Union[None, bool]
    downloads: Dict[str, dict]
    popularity: Union[None, int]
    trove_showcase_css: Union[None, str]
    youtube_link: Union[None, str]
    all_access: Union[None, int]
    carousel_content: CarouselContent
    human_name: str
    logo: Union[None, str]
    description_text: Union[None, str]
    developers: List[Developer]
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
