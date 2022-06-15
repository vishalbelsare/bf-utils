#!/usr/bin/env python3

#===============================================================================
# This program is based on the legacy script `bf-legacy/bfdelete.py`, which was
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
psv-delete.py -h (help)
              -p <path> (removes rightmost collection in path)
              -d <dataset>
              -f <file_containing_datasets>
              --all (apply to ALL HPAP datasets)
              --force (remove collection even if it's non-empty)"

Note: `-d`, `-f` and `--all` options are mutually exclusive.
"""


def delete_collection(ds_name, collection, deletion_location, force_opt):
    """Delete `collection` from `dset`."""

    path = deletion_location if deletion_location else "root directory"

    # get to bottom collection in path
    dataset = psv.get_dataset(ds_name)
    dirs = deletion_location.split('/')

    for d in dirs:
        if d == "":
            break  # add to root directory

        if collection_exists(d, dataset):
            dataset = dataset.get_items_by_name(d)[0]
        else:
            print(f"ERROR: collection '{d}' not exist")
            sys.exit(1)

    # Ensure collection exists, and delete it if it is empty or `--force`
    # option is specified.
    is_found = False
    for item in dataset.items:
        if item.name == collection:
            is_found = True
            break

    if is_found:
        if item.type != "Collection":
            item.delete()
            print(
                f"'{collection}' removed in '{path}' within dataset '{ds_name}'"
            )
        elif len(item.items) == 0:
            item.delete()
            print(
                f"'{collection}' removed in '{path}' within dataset '{ds_name}'"
            )
        elif force_opt:
            item.delete()
            print(
                f"'{collection}' not empty, but removed due to `--force` option"
            )
        else:
            print(f"'{collection}' NOT removed because it's not empty")
    else:
        print(
            f"ERROR: Path '{path}/{collection}' not found within dataset "
            f"'{ds_name}'"
        )


def handle_p_option(p_arg):
    """
    Parse `-p` option, and return `collection` and `deletion_location`,
    which will be used by `-d`, -f` and `--all` options.
    """

    # `-p` option is required by `-d`, `-f` and `--all` options
    if not p_arg:
        print("ERROR: '-p <dataset path>' option not found")
        sys.exit(1)

    # Remove leading '/'
    if p_arg[0] == '/':
        p_arg = p_arg[1:]

    paths = p_arg.split('/')
    collection = paths[-1]
    deletion_location = '/'.join(paths[:-1])

    return collection, deletion_location


def handle_d_option(d_arg, collection, deletion_location, force_opt):
    """Handle `-d` option."""

    ds_name = psv_datasets.get(d_arg, None)
    if ds_name is None:
        print(f"ERROR: dataset '{d_arg}' not found on Pennsieve")
        sys.exit(1)

    delete_collection(ds_name, collection, deletion_location, force_opt)


def handle_f_option(f_arg, collection, deletion_location, force_opt):
    """Handle `-f` option."""

    keys = get_lines_in_file(f_arg)

    for k in keys:
        ds_name = psv_datasets[k]
        delete_collection(ds_name, collection, deletion_location, force_opt)


def handle_all_option(collection, deletion_location, force_opt):
    """Handle `--all` option."""

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        ds_name = psv_datasets[k]
        delete_collection(ds_name, collection, deletion_location, force_opt)


#==============================================================================
#                       Main program
#==============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(sys.argv, "hp:d:f:", ['force', 'all'], SYNTAX)

    # `-p <path>` option
    p_arg = opts_dict.get('-p', None)
    collection, deletion_location = handle_p_option(p_arg)

    # Get status of `-d`, -f` and `--all` options
    d_opt, f_opt, all_opt = get_d_f_all_options(opts_dict)

    # `--force` option (optional)
    force_opt = '--force' in opts_dict

    # `-d` option
    if d_opt:
        d_arg = opts_dict['-d']
        handle_d_option(d_arg, collection, deletion_location, force_opt)

    # `-f` option
    if f_opt:
        f_arg = opts_dict['-f']
        handle_f_option(f_arg, collection, deletion_location, force_opt)

    # `--all` option
    if all_opt:
        handle_all_option(collection, deletion_location, force_opt)
