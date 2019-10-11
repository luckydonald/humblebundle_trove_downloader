#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import path
from typing import Union, List, Dict, Tuple
from urllib.parse import quote

from constants import TYPE_WEB, TYPE_BITTORRENT
from utils.save import sanitize_name
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

    def to_json(self):
        return {
            "url": self.url,
            "auth_request": self.auth_request,
            "file": self.file,
            "type": self.type,
            "size": self.size,
            "md5": self.md5,
            "sha1": self.sha1,
        }
    # end def
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

    def to_json(self):
        return {
            "youtube_link": self.youtube_link,
            "thumbnail": self.thumbnail,
            "screenshot": self.screenshot,
        }
    # end def
# end class


class Developer(object):
    name: str
    url: Union[None, str]

    def __init__(self, name, url):
        self.name = name
        self.url = url
    # end if

    def to_json(self):
        return {
            "name": self.name,
            "url": self.url,
        }
    # end def
# end class


class Publisher(object):
    name: str
    url: Union[None, str]

    def __init__(self, name, url):
        self.name = name
        self.url = url
    # end if

    def to_json(self):
        return {
            "name": self.name,
            "url": self.url,
        }
    # end def
# end class


class Download(object):
    name: str
    machine_name: str
    url: 'URLs'
    small: Union[None, int]
    md5: str
    sha1: Union[None, str]
    file_size: int
    human_size: str
    uploaded_at: Union[None, int]

    def __init__(
        self, name, machine_name, url, small, md5, sha1, file_size, human_size, uploaded_at
    ):
        self.name = name
        self.machine_name = machine_name
        self.url = url
        self.small = small
        self.md5 = md5
        self.sha1 = sha1
        self.file_size = file_size
        self.human_size = human_size
        self.uploaded_at = uploaded_at
    # end def

    def to_json(self):
        return {
            "name": self.name,
            "machine_name": self.machine_name,
            "url": self.url,
            "small": self.small,
            "md5": self.md5,
            "sha1": self.sha1,
            "file_size": self.file_size,
            "human_size": self.human_size,
            "uploaded_at": self.uploaded_at,
        }
    # end def
# end class


class URLs(object):
    web: str
    bittorrent: Union[None, str]

    def __init__(self, web, bittorrent):
        self.web = web
        self.bittorrent = bittorrent
    # end def

    def __iter__(self):
        """ Make it somewhat compatible to the previous dict implementation. """
        if self.web:
            yield TYPE_WEB
        # end if
        if self.bittorrent:
            yield TYPE_BITTORRENT
        # end if
    # end def

    def items(self) -> List[Tuple[str, str]]:
        """ Make it somewhat compatible to the previous dict implementation. """
        return [(k, getattr(self, k)) for k in self.__iter__()]
    # end def

    def to_json(self):
        return {
            "web": self.web,
            "bittorrent": self.bittorrent,
        }
    # end def
# end class


assert TYPE_WEB == 'web'  # makes sure you don't forget about the class above when renaming those.
assert TYPE_BITTORRENT == 'bittorrent'  # makes sure you don't forget about the class above when renaming those.


class Game(object):
    background_image: Union[None, str]
    publishers: Union[None, dict]
    date_added: Union[None, int]
    machine_name: Union[None, str]
    humble_original: Union[None, bool]
    downloads: Dict[str, Download]
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

    def to_json(self):
        return {
            'background_image': self.background_image,
            'publishers': self.publishers,
            'date_added': self.date_added,
            'machine_name': self.machine_name,
            'humble_original': self.humble_original,
            'downloads': self.downloads,
            'popularity': self.popularity,
            'trove_showcase_css': self.trove_showcase_css,
            'youtube_link': self.youtube_link,
            'all_access': self.all_access,
            'carousel_content': self.carousel_content,
            'human_name': self.human_name,
            'logo': self.logo,
            'description_text': self.description_text,
            'developers': self.developers,
            'image': self.image,
            'background_color': self.background_color,
            'marketing_blurb': self.marketing_blurb,
        }
    # end def

    @property
    def title(self):
        return self.human_name if self.human_name else self.machine_name
    # end def

    @property
    def title_sanitized(self):
        return sanitize_name(self.title)
    # end def

    @property
    def folder(self):
        return self.title_sanitized + path.sep
    # end def

    @property
    def folder_url(self):
        return quote(self.title_sanitized) + path.sep
    # end def

    @property
    def folder_data(self):
        return path.join(self.folder, 'data') + path.sep
    # end def

    @property
    def folder_data_url(self):
        return path.join(self.folder_url, 'data') + path.sep
    # end def
# end class
