#!/usr/bin/env python3

#===============================================================================
# Duplicate a Pennsieve dataset.
#
# This program is based on the legacy script `bf-legacy/bfduplicate.py`, which
# was written by Pete Schmitt for Blackfynn file server.
#===============================================================================

import sys

from pennsieve import Pennsieve
from pennsieve.models import BaseCollection, Collection

from psv_lib import (
    psv,
    psv_datasets,
    parse_options,
)


SYNTAX = """
psv-duplicate.py -h (help)
                 -d <original_dataset>
                 -n <new_dataset>
"""


def create_duplicate(src_data, new_ds, indent=0):
    """
    Clone all files in `original_ds` into `new_ds`.  Note that this is a
    recursive function.
    """
    try:
        src_data._check_exists()
    except Exception:
        print(f"ERROR: {src_data} not exist on Pennsieve")
        return

    if indent != 0:
        indentation = " " * indent
        print(f"{indentation}Creating new Collection: {src_data}")

    for item in src_data.items:
        if isinstance(item, BaseCollection):
            col = Collection(item.name)
            new_ds.add(col)
            create_duplicate(item, col, indent=indent+4)


def handle_d_option(d_arg):
    if not d_arg:
        print("ERROR: `-d <original_dataset>` option not found")
        sys.exit(1)

    # Exit if source dataset does not exist on Pennsieve
    if d_arg not in psv_datasets:
        print(f"ERROR: dataset '{d_arg}' not found on Pennsieve")
        sys.exit(1)

    ds_name = psv_datasets[d_arg]
    original_ds = psv.get_dataset(ds_name)

    return original_ds


def handle_n_option(n_arg):
    if not n_arg:
        print("ERROR: `-n <new_dataset` option not found")
        sys.exit(1)

    # Exit if destination dataset already exists on Pennsieve
    if n_arg in psv_datasets:
        print(f"ERROR: dataset '{n_arg}' already exists on Pennsieve")
        sys.exit(1)

    print(f"Creating new dataset '{n_arg}'")
    psv.create_dataset(n_arg)
    new_ds = psv.get_dataset(n_arg)

    return new_ds


#==============================================================================
#                       Main program
#==============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(sys.argv, "hd:n:", [], SYNTAX)

    # `-d` option
    d_arg = opts_dict.get('-d', None)
    original_ds = handle_d_option(d_arg)

    # `-n` option
    n_arg = opts_dict.get('-n', None)
    new_ds = handle_n_option(n_arg)

    # Duplicate
    create_duplicate(original_ds, new_ds)
