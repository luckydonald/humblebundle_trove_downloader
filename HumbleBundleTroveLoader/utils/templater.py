#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from luckydonaldUtils.logger import logging
from jinja2 import  Environment, FileSystemLoader
from jinja2.exceptions import TemplateSyntaxError


__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class RelEnvironment(Environment):
    """
    Override join_path() to enable relative template paths.

    http://stackoverflow.com/a/8530761/3423324
    """
    def join_path(self, template, parent):
        return os.path.join(os.path.dirname(parent), template)
    # end def join_path
# end class RelEnvironment


def get_template(file_name, searchpath="templates"):
    env = RelEnvironment(loader=FileSystemLoader(searchpath=searchpath))
    import os
    try:
        return env.get_template(file_name)
    except TemplateSyntaxError as e:
        logger.warn("{file}:{line} {msg}".format(msg=e.message, file=e.filename if e.filename else file_name, line=e.lineno))
        raise e
    # end with
# end def get_template
