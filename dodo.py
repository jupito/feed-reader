"""PyDoIt tasks."""

from __future__ import absolute_import, division, print_function

from doit.tools import Interactive

DOIT_CONFIG = {
    'default_tasks': ['check'],
    }

CHECKERS = [
    # 'pep8',
    # 'pyflakes',
    'flake8',
    # 'pylint -r no',
    'pylint -r no -E',
    # 'pychecker',
    ]

SRC = [
    'dodo.py',
    'feed_db.py',
    'feed_tool.py',
    'feed_util.py',
    'html.py',
    'reader.cgi',
    'util.py',
    ]


def task_check():
    """Check source files."""
    for filename in SRC:
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
        'file_dep': SRC,
        'task_dep': ['check'],
        }


def task_push():
    """Commit."""
    return {
        'actions': [Interactive('git push')],
        'task_dep': ['commit'],
        }
