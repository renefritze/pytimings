import os


def ensure_directory_exists(dirname):
    """create dirname if it doesn't exist"""
    try:
        os.makedirs(dirname)
    except FileExistsError:
        pass
