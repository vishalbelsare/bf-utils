#!/usr/bin/env python3

"""
Print out the long names of all datasets on Pennsieve server.
"""

from psv_lib import psv_datasets

for v in sorted(psv_datasets.values()):
    print(v)
