"""PyDoIt tasks."""

from __future__ import absolute_import, division, print_function
import glob

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
