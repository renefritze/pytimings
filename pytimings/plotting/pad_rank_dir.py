#!/usr/bin/env python3

import os
import shutil
import sys


def pad_rank_dir(args):
    left_marker = args[1]

    for dirname in args[2:]:
        assert os.path.isdir(dirname)  # noqa: PTH112
        left = dirname.find(left_marker)
        right = dirname.find("_", left + len(left_marker))
        ranks = dirname[left + len(left_marker) : right]
        new = dirname.replace(left_marker + ranks, left_marker + ranks.zfill(8))
        print(f"mv {dirname} {new}")
        shutil.move(dirname, new)


if __name__ == "__main__":
    pad_rank_dir(sys.argv)
