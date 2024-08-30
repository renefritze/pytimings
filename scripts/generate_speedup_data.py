#!/usr/bin/env python3

import os
import sys

from pytimings.tools import generate_example_data

try:
    output_dir = sys.argv[1]
except IndexError:
    output_dir = os.getcwd()  # noqa: PTH109

try:
    runs = sys.argv[2]
except IndexError:
    runs = 10

generate_example_data(output_dir=output_dir, number_of_runs=runs)
