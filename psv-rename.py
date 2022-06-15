#!/usr/bin/env python3

#===============================================================================
# This program is based on the legacy script `bf-legacy/bfrename.py`, which was
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
psv-rename.py -h (help)
              -p <path> (renames rightmost object in path)
              -d <dataset>
              -f <file_containing_datasets>
              --all (apply to ALL HPAP datasets)
              -n <new_name>
              --data (rightmost object is data)

Note: `-d`, `-f` and `--all` options are mutually exlusive.
"""


def rename_object(ds_name, p_arg, n_arg, data_opt):
    # Get to bottom collection in path
    dataset = psv.get_dataset(ds_name)
    dirs = p_arg.split('/')
    obj = dirs[-1]

    for d in dirs:
        if collection_exists(d, dataset):
            dataset = dataset.get_items_by_name(d)[0]
        else:
            printf("ERROR: dataset '{d}' NOT exist")
            sys.exit(1)

    # Ensure that the object exists and is not a package before renaming it.
    if ":package:" in str(dataset.id):
        if data_opt:
            dataset.name = n_arg
            dataset.update()
            print(f"Package '{obj}' renamed to '{n_arg}' within dataset '{ds_name}'")
        else:
            print("ERROR: please use `--data` to rename a package")
    else:
        ds.name = newname
        ds.update()
        print(f"Collection '{obj}' renamed to '{n_arg}' within dataset '{ds_name}'")


def handle_d_option(d_arg, p_arg, n_arg, data_opt):
    """Handle `-d` option."""

    ds_name = psv_datasets.get(d_arg, None)
    if ds_name is None:
        print(f"Dataset '{d_arg}' not found on Pennsieve")
        sys.exit(1)

    rename_object(ds_name, p_arg, n_arg, data_opt)


def handle_f_option(f_arg, p_arg, n_arg, data_opt):
    """Handle `-f` option."""

    input_keys = get_lines_in_file(f_arg)

    for k in input_keys:
        ds_name = psv_datasets[k]
        rename_object(ds_name, p_arg, n_arg, data_opt)


def handle_all_option(p_arg, n_arg, data_opt):
    """Handle `-all` option."""

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        ds_name = psv_datasets[k]
        rename_object(ds_name, p_arg, n_arg, data_opt)


#==============================================================================
#                       Main program
#==============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(sys.argv, "hn:p:d:f:", ['all', 'data'], SYNTAX)

    # `-n <new_name>` option is required
    n_arg = opts_dict.get('-n', None)
    if n_arg is None:
        print("ERROR: `-n <new_name>` option not found")
        sys.exit(1)

    # `-p <path>` is required
    p_arg = opts_dict.get('-p', None)
    if not p_arg:
        print("ERROR: '-p <path>' option not found")
        sys.exit(1)

    # `--data` option (optional)
    data_opt = '--data' in opts_dict

    # Get status of `-d`, -f` and `--all` options
    d_opt, f_opt, all_opt = get_d_f_all_options(opts_dict)

    # `-d` option
    if d_opt:
        d_arg = opts_dict['-d']
        handle_d_option(d_arg, p_arg, n_arg, data_opt)

    # `-f` option
    if f_opt:
        f_arg = opts_dict['-f']
        handle_f_option(f_arg, p_arg, n_arg, data_opt)

    # `--all` option
    if all_opt:
        handle_all_option(p_arg, n_arg, data_opt)
