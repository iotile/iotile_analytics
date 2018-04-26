#!/usr/bin/env python

"""Usage: copy_docs <src> <dst>

A cross platform copy routine for use for tox.
"""

from __future__ import unicode_literals, print_function
import sys
import os
import time
import shutil

def delete_with_retry(folder):
    """Try multiple times to delete a folder.

    This is required on windows because of things like:
    https://bugs.python.org/issue15496
    https://blogs.msdn.microsoft.com/oldnewthing/20120907-00/?p=6663/
    https://mail.python.org/pipermail/python-dev/2013-September/128350.html
    """

    for _i in range(0, 5):
        try:
            if os.path.exists(folder):
                shutil.rmtree(folder)

            return
        except:
            time.sleep(0.1)

    print("Could not delete directory after 5 attempts: %s" % folder)
    sys.exit(1)

def copy_with_retry(src, dst):
    """Try multiple times to delete a folder.

    This is required on windows because of things like:
    https://bugs.python.org/issue15496
    https://blogs.msdn.microsoft.com/oldnewthing/20120907-00/?p=6663/
    https://mail.python.org/pipermail/python-dev/2013-September/128350.html
    """

    for _i in range(0, 5):
        try:
            if os.path.exists(dst):
                delete_with_retry(dst)

            shutil.copytree(src, dst)
            return
        except:
            time.sleep(0.1)

    print("Could not copy directory after 5 attempts")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: copy_docs <src> <dst>")
        sys.exit(1)

    srcdir = sys.argv[1]
    dstdir = sys.argv[2]

    if not os.path.exists(srcdir):
        print("Source directory does not exist: %s" % srcdir)
        sys.exit(1)

    if not os.path.isdir(srcdir):
        print("Source directory is not a directory: %s" % srcdir)
        sys.exit(1)

    if os.path.isfile(dstdir):
        print("Destination directory is actually a file: %s" % dstdir)
        sys.exit(1)

    copy_with_retry(srcdir, dstdir)
    sys.exit(0)
