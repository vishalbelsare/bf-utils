#!/usr/bin/env python3

#===============================================================================
# This program is based on the legacy script `bf-legacy/bfmove.py`, which was
# written by Pete Schmitt for Blackfynn file server.
#===============================================================================

import os
import sys

from psv_lib import (
    psv,
    psv_datasets,
    parse_options,
    get_d_f_all_options,
    collection_exists,
    get_lines_in_file,
)

# Global variables

SYNTAX = """
psv-move.py -h (help)
            -d <dataset>
            -f <file_containing_datasets>
            --all (apply to all HPAP datasets)
            -S <source>
            -D <destination> (<destination> MUST be a directory)

Note: `-d`, `-f` and `--all` options are mutually exlusive.
"""


def locate_path(path, dataset):
    """Return the object that represents where to start."""

    dirs = path.split('/')

    for d in dirs:
        if d == "":
            continue
        elif collection_exists(d, dataset):
            dataset = dataset.get_items_by_name(d)[0]
        else:
            print(f"ERROR: object '{path}' NOT exist")
            sys.exit(1)

    return dataset


def move_data(ds_key, src, dest):
    """Move data from `source` to `destination`."""

    ds_name = psv_datasets.get(ds_key, None)
    if ds_name is None:
        print(f"ERROR: dataset '{ds_key}' not found on Pennsieve")
        sys.exit(1)

    dataset = psv.get_dataset(ds_name)
    src_path= locate_path(src, dataset)
    dest_path = locate_path(dest, dataset)
    psv.move(dest_path, src_path)
    print(f"'{ds_key}': '{src}' moved to '{dest}'")


def handle_f_option(f_arg, src_arg, dest_arg):
    """Handle `-f` option."""

    input_keys = get_lines_in_file(f_arg)
    for k in input_keys:
        move_data(k, src_arg, dest_arg)


def handle_all_option(src_arg, dest_arg):
    """Handle `-all` option."""

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        move_data(k, src_arg, dest_arg)


#==============================================================================
#                       Main program
#==============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(sys.argv, "hd:S:D:f:", ['all', 'help'], SYNTAX)

    # Ensure that both `-S` and `-D` options are available
    src_arg = opts_dict.get('-S', None)
    dest_arg = opts_dict.get('-D', None)

    if src_arg is None or dest_arg is None:
        print("ERROR: `-S <source>` or `-D <destination>` option not found")
        sys.exit(1)

    # Get status of `-d`, `-f` and `--all` options
    d_opt, f_opt, all_opt = get_d_f_all_options(opts_dict)

    # `-d` option
    if d_opt:
        d_arg = opts_dict['-d']
        move_data(d_arg, src_arg, dest_arg)

    # `-f` option
    if f_opt:
        f_arg = opts_dict['-f']
        handle_f_option(f_arg, src_arg, dest_arg)

    # `--all` option
    if all_opt:
        handle_all_option(src_arg, dest_arg)
