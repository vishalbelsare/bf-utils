#!/usr/bin/env python3

#===============================================================================
# This program is based on the legacy script `bf-legacy/bfinsert.py`, which was
# written by Pete Schmitt for Blackfynn file server.
#===============================================================================

import os
import sys

from pennsieve.models import Collection

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
psv-insert.py -h (help)
              -p <path> (insert rightmost part of path)
              -d <dataset>
              -f <file_containing_datasets>
              --all (apply to ALL HPAP datasets)

Note: `-d`, `-f` and `--all` are mutually exclusive.
"""


def insert_collection(ds_name, collection, insertion_location):
    """Insert collection at the specified location."""

    if insertion_location == "":
        path = "root directory"
    else:
        path = insertion_location

    # Get to bottom collection in path
    dataset = psv.get_dataset(ds_name)
    dirs = insertion_location.split('/')

    for d in dirs:
        if d == "":
            break  # add to root directory

        if collection_exists(d, dataset):
            dataset = dataset.get_items_by_name(d)[0]
        else:
            print(f"ERROR: Collection '{d}' not exist")
            sys.exit(1)

    # Ensure that collection does not exist before inserting it
    is_found = False
    for item in dataset.items:
        if collection == item.name:
            is_found = True
            break

    if is_found:
        print(
            f"Collection '{collection}' already exists in '{path}' within "
            f"the dataset '{ds_name}'"
        )
        return

    c = Collection(collection)
    dataset.add(c)
    print(f"Collection '{collection}' added to '{path}' within dataset '{ds_name}'")


def handle_p_option(p_arg):
    """
    Parse `-p` option, and return `collection` and `insertion_location`.
    """

    # `-p` option is required by `-d`, `-f` and `--all` options
    if not p_arg:
        print("ERROR: '-p <path>' option is not found")
        sys.exit(1)

    # Remove leading '/'
    if p_arg[0] == '/':
        p_arg = p_arg[1:]

    paths = p_arg.split('/')
    collection = paths[-1]
    insertion_location = '/'.join(paths[:-1])

    return collection, insertion_location


def handle_d_option(d_arg, collection, insertion_location):
    """Handle `-d` option."""

    ds_name = psv_datasets.get(d_arg, None)
    if ds_name is None:
        print(f"ERROR: dataset '{d_arg}' not found on Pennsieve server")
        sys.exit(1)

    insert_collection(ds_name, collection, insertion_location)


def handle_f_option(f_arg, collection, insertion_location):
    """Handle `-f` option."""

    input_keys = get_lines_in_file(f_arg)

    for k in input_keys:
        ds_name = psv_datasets[k]
        insert_collection(ds_name, collection, insertion_location)


def handle_all_option(collection, insertion_location):
    """Handle `--all` option."""

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        ds_name = psv_datasets[k]
        insert_collection(ds_name, collection, insertion_location)


#==============================================================================
#                       Main program
#==============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(sys.argv, "hp:d:f:", ['all'], SYNTAX)

    # `-p` option
    p_arg = opts_dict.get('-p', None)
    collection, insertion_location = handle_p_option(p_arg)

    # Get status of `-d`, -f` and `--all` options
    d_opt, f_opt, all_opt = get_d_f_all_options(opts_dict)

    # `-d` option
    if d_opt:
        d_arg = opts_dict['-d']
        handle_d_option(d_arg, collection, insertion_location)

    # `-f` option
    if f_opt:
        f_arg = opts_dict['-f']
        handle_f_option(f_arg, collection, insertion_location)

    # `--all` option
    if all_opt:
        handle_all_option(collection, insertion_location)
