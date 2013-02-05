#!/usr/bin/env python
# cls = (categorical|color)ls.  Some useful utility functions, too (e.g. table)
# XXX Should files specifically listed on the command line be filter()ed out?
# XXX st_rdev, st_blocks will cause exceptions if used on Python < 2.2.  Hmm.
# TODO OS-specific code to decompose device numbers into (major, minor).
# TODO varying per-type sub-orders: File-instance-level __cmp__ methods?

import os, re, pwd, grp, string, sys
from posixpath import basename,splitext,dirname
from time      import strftime, localtime
from stat      import *                   # 'stat' names prefixed for import *
env = os.environ

use_color = 1                            ## deflt to using color
cmp_sign = [ ]
ordbrok = 0
fmtbrok = 0

def ioctl_GWINSZ(fd):                  #### TABULATION FUNCTIONS
    try:                                ### Discover terminal width
        import fcntl, termios, struct, os
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
        return None
    return cr

def terminal_size():                    ### decide on *some* terminal size
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)  # try open fds
    if not cr:                                                  # ...then ctty
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:                            # env vars or finally defaults
        try:
            cr = (env['LINES'], env['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])         # reverse rows, cols


if __name__ == '__main__':
  print terminal_size()
