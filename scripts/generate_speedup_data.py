#!/usr/bin/env python3

import sys
from pathlib import Path

from pytimings.tools import generate_example_data

try:
    output_dir = sys.argv[1]
except IndexError:
    output_dir = Path.cwd()

try:
    runs = sys.argv[2]
except IndexError:
    runs = 10

generate_example_data(output_dir=output_dir, number_of_runs=runs)
