"""PyDoIt tasks."""

from __future__ import absolute_import, division, print_function
import glob
import os

from doit.tools import Interactive


DOIT_CONFIG = {
    'default_tasks': ['check'],
    }

CHECKERS = [
    # 'pep8',
    # 'pyflakes',
    'flake8-python2',
    # 'pylint -r no',
    'pylint2 -r no -E',
    # 'pychecker',
    ]

SRC = ['feed_db.py', 'feed_tool.py', 'feed_util.py', 'html.py', 'util.py',
       'reader.cgi', 'reader.css']


def src():
    for pattern in ('*.py', '*.cgi'):
        for path in glob.iglob(pattern):
            yield path


def task_check():
    """Check source files."""
    for filename in src():
        actions = ['{} {}'.format(c, filename) for c in CHECKERS]
        yield {
            'name': filename,
            'actions': actions,
            'file_dep': [filename],
            }


def task_commit():
    """Commit."""
    return {
        'actions': [Interactive('git commit -v -a')],
        'file_dep': list(src()),
        'task_dep': ['check'],
        }


def task_push():
    """Commit."""
    return {
        'actions': [Interactive('git push')],
        'task_dep': ['commit'],
        }


def task_install():
    """Install."""
    dst = 'installdir'
    for filename in SRC:
        trg = os.path.join(dst, filename)
        yield {
            'name': filename,
            'actions': ['cp -f %(dependencies)s %(targets)s'],
            'file_dep': [filename],
            'task_dep': ['check'],
            'targets': [trg],
        }
