"""Top-level package for PyTimings."""

from importlib.metadata import PackageNotFoundError, version

__author__ = "René Fritze"
__email__ = "coding@fritze.me"

try:
    __version__ = version("pytimings")
except PackageNotFoundError:  # package is not installed (e.g. running from a source tree)
    __version__ = "0.0.0+unknown"

__all__ = ["__author__", "__email__", "__version__"]
