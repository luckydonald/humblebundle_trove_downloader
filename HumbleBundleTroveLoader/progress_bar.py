import os
import shutil
from typing import Union

"""
A progress bar.
Improved upon https://stackoverflow.com/a/48450305/3423324#get-progress-back-from-shutil-file-copy-thread.
"""


FULL_BLOCK = '█'
# this is a gradient of incompleteness
INCOMPLETE_BLOCK_GRAD = ['░', '▒', '▓']


ACTIVITY_MODE = ['▹', '▸']


def build_progress_bar(percent: float, width: Union[None, int] = None) -> str:
    # This will only work for python 3.3+ due to use of
    # os.get_terminal_size the print function etc.
    assert (isinstance(percent, float))
    assert (0. <= percent <= 100.)
    width = prepare_width(width)
    # progress bar is block_widget separator perc_widget : ####### 30%
    assert (width >= 3)  # not very meaningful if not

    perc_per_block = 100.0/width
    # epsilon is the sensitivity of rendering a gradient block
    epsilon = 1e-6
    # number of blocks that should be represented as complete
    full_blocks = int((percent + epsilon) / perc_per_block)
    # the rest are "incomplete"
    empty_blocks = width - full_blocks

    # build blocks widget
    blocks_widget = ([FULL_BLOCK] * full_blocks)
    blocks_widget.extend([INCOMPLETE_BLOCK_GRAD[0]] * empty_blocks)
    # marginal case - remainder due to how granular our blocks are
    remainder = percent - full_blocks * perc_per_block
    # epsilon needed for rounding errors (check would be != 0.)
    # based on reminder modify first empty block shading
    # depending on remainder
    if remainder > epsilon:
        grad_index = int((len(INCOMPLETE_BLOCK_GRAD) * remainder)/perc_per_block)
        blocks_widget[full_blocks] = INCOMPLETE_BLOCK_GRAD[grad_index]
    # end if
    return ''.join(blocks_widget)
# end def


def build_activity_bar(integer: int, width: int) -> str:
    """
    Without having real progress.
    :param integer:
    :param width:
    :return:
    """
    assert (isinstance(integer, int))
    width = prepare_width(width)
    # progress bar is block_widget separator perc_widget : ####### 30%
    assert (width >= 3)  # not very meaningful if not

    position = integer % width
    return (ACTIVITY_MODE[0] * (position - 1)) + (ACTIVITY_MODE[1]) + (ACTIVITY_MODE[0] * (width - position))
# end def


def prepare_width(width):
    # if width unset use full terminal
    if width is None:
        width = os.get_terminal_size().columns
    # end with
    return width
# end def


def build_process_label(percent: float, decimals: int = 2) -> str:
    """
    Create a label showing the percentage. '[xxx.xx%]'
    note that having decimals (decimals > 0) causes a separator to
    be added as another character:       4 + 1 + decimals

    - minimum width is '[100%]' = 6.     4 + 0 + 0
    - default width is '[100.00%]' = 9.  4 + 1 + 2
    """
    assert (isinstance(percent, float))
    assert (0. <= percent <= 100.)
    assert (isinstance(decimals, int))
    assert (decimals >= 0)
    digits = 3 + (1 + decimals if decimals > 0 else 0)
    return "[{percent: >{digits}.{decimals}f}%]".format(percent=percent, digits=digits, decimals=decimals)
# end def


def build_progress_line(percent: float, width: Union[None, int] = None, decimals: int = 2) -> str:
    label = build_process_label(percent, decimals)
    remaining_width = width - len(label)
    if remaining_width > 5:
        # if we have enough space is available, a space between progress bar and label can be added.
        label = " " + label
        remaining_width -= 1  # subtract the space
    # end if

    return build_progress_bar(percent, remaining_width) + label
# end def


def build_activity_line(integer: int, width: Union[None, int] = None) -> str:
    assert(width > 2)
    return build_activity_bar(integer, width)
# end def


def copy_progress(copied, total):
    print('\r' + progress_percentage(100*copied/total, width=30), end='')


def copyfile(src, dst, *, follow_symlinks=True):
    """Copy data from src to dst.

    If follow_symlinks is not set and src is a symbolic link, a new
    symlink will be created instead of copying the file it points to.

    """
    if shutil._samefile(src, dst):
        raise shutil.SameFileError("{!r} and {!r} are the same file".format(src, dst))

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if shutil.stat.S_ISFIFO(st.st_mode):
                raise shutil.SpecialFileError("`%s` is a named pipe" % fn)

    if not follow_symlinks and os.path.islink(src):
        os.symlink(os.readlink(src), dst)
    else:
        size = os.stat(src).st_size
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                copyfileobj(fsrc, fdst, callback=create_advanced_copy_progress(), total=size)
    return dst


def copyfileobj(fsrc, fdst, callback, total, length=16*1024):
    copied = 0
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        copied += len(buf)
        callback(copied, length=length, total=total)


def copy_with_progress(src, dst, *, follow_symlinks=True):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst, follow_symlinks=follow_symlinks)
    shutil.copymode(src, dst)
    return dst


def create_advanced_copy_progress(prefix="", suffix="", width=None):
    width = prepare_width(width)
    width -= len(prefix) + len(suffix)

    def advanced_copy_progress(copied, length, total):
        if total is None:
            print('\r' + prefix + build_activity_line(copied//length, width=width), end='')
        else:
            print('\r' + build_progress_line(100*copied/total, width=width), end='')
        # end if
    # end def
    return advanced_copy_progress
# end def
