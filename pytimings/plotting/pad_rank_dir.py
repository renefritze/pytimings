#!/usr/bin/env python3

import sys
import os
import shutil

# left_marker = '_n'
# left_marker = '.01_'
left_marker = sys.argv[1]

for dirname in sys.argv[2:]:
    assert os.path.isdir(dirname)
    left = dirname.find(left_marker)
    right = dirname.find('_', left + len(left_marker))
    ranks = dirname[left + len(left_marker) : right]
    new = dirname.replace(left_marker + ranks, left_marker + ranks.zfill(8))
    print('mv {} {}'.format(dirname, new))
    shutil.move(dirname, new)
