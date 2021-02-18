"""Top-level package for PyTimings."""

__author__ = """René Fritze"""
__email__ = 'coding@fritze.me'

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions
