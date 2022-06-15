#!/usr/bin/env python3

#===============================================================================
# This program is based on the legacy script `bf-legacy/bfmeta.py`, which was
# written by Pete Schmitt for Blackfynn file server.
#===============================================================================

import datetime
import os
import sys
import time

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
psv-meta.py -h (help)
            -p <dataset path> (path to collection required)
            -d <dataset>
            -f <file containing datasets>
            --all (apply to ALL HPAP datasets)
            -k <metadata key>
            -v <metadata value>
            -m <metadata file of key:value pairs> (`-k` and `-v` will be ignored)
            -c <category> (default: 'Pennsieve')
            -t <data type> (integer, string, date, double)
            --show (show metadata)
            --remove (remove metadata)

Notes:
  * Add, remove, or show metadata to rightmost part of path;
  * Date format: "MM/DD/YYYY HH:MM:SS";
  * Options `-d`, `-f` and `--all` options are mutually exclusive.
"""


def handle_p_option(p_arg):
    """Handle `-p` option."""

    if not p_arg:
        print("ERROR: '-p <path>' option not found")
        sys.exit(1)

    if p_arg[0] == '/':
        p_arg = p_arg[1:]

    if not p_arg:
        print(f"ERROR: invalid <path> in '-p <path>' option")
        sys.exit(1)

    return p_arg


def get_meta_lines(opts_dict):
    """Get `meta_lines` based on `-m`, `-k` and `-v` options."""

    meta_lines = None
    if '-m' in opts_dict:
        m_arg = opts_dict['-c']
        if not os.path.exists(m_arg):
            print("ERROR: meta file '{m_arg}' not exist")
            sys.exit(1)

        with open(m_arg) as mf:
            meta_lines = mf.read().splitlines()

    k_arg = opts_dict.get('-k', None)
    v_arg = opts_dict.get('-v', None)

    # If `-m` option is valid, ignore `-k`, `-v` and `--remove` option
    if meta_lines is None:
        if k_arg and v_arg:
            meta_lines = [f"{k_arg}:{v_arg}"]
        elif k_arg and remove_opt:
            meta_lines = [f"{k_arg}:NOOP"]

    return meta_lines


def get_one_dataset(ds_name, path):
    """Return the dataset based on `ds_name` and `path`."""

    dataset = psv.get_dataset(ds_name)

    dirs = path.split('/')
    for d in dirs:
        if d == "":
            break

        if not collection_exists(d, dataset):
            print(f"ERROR: object '{d}' NOT exist")
            return

        dataset = dataset.get_items_by_name(d)[0]

    return dataset


def print_properties(obj):
    """Print properties (metadata) of an Pennsieve object."""

    for p in obj.properties:
        p_dict = p.as_dict()
        val = p_dict['value']
        if p_dict['dataType'] == 'date':
            val = datetime.datetime.fromtimestamp(val).strftime(
                '%Y-%m-%d %H:%M:%S'
            )

        print(
            f"Key: {p_dict['key']}, Value: {val}, "
            f"Type: {p_dict['dataType']}, Category: {p_dict['category']}",
        )


def remove_meta(dataset, key, category):
    """Remove metadata."""

    try:
        dataset.remove_property(key, category)
    except:
        print(f"ERROR: metadata whose key is '{key}' not exist in '{path}'")
        return

    print("Metadata whose key is '{key}' removed from '{path}'")


def add_meta(dataset, key, value, category, type_name):
    """Add metadata."""

    if type_name != 'date':
        if type_name is None:
            dataset.insert_property(key, value, category=category)
        else:
            dataset.insert_property(
                key, value, category=category, data_type=type_name
            )
    else:
        pattern = "%m/%d/%Y %H:%M:%S"
        date_str = str(type_name)
        try:
            epoch = int(time.mktime(time.strptime(date_str, pattern)))
        except:
            print(f"'{date_str}' does not match format 'MM/DD/YYYY HH:MM:SS'")

        epoch *= 1000
        dataset.set_property(key, epoch, category=category, data_type=type_name)

    print(f"Metadata whose key is '{key}' is added to '{path}'")


def process_meta(ds_name, path, show_opt, remove_opt, meta_lines, category, type_name):
    """
    Wrapper function that shows, adds or removes metadata, depending on
    input options.
    """

    dataset = get_one_dataset(ds_name, path)
    if dataset is None:
        return

    # Show metadata
    if show_opt:
        print(f"\nMetadata for '{ds_name}/{path}':")
        print_properties(dataset)
        return

    # If `meta_lines` is blank, exit immediately
    if not meta_lines:
        print(f"ERROR: `meta_lines` is either None or empty")
        sys.exit(1)

    # Add or remove metadata
    path = ds_name + '/' + path
    for ml in meta_lines:
        key, value = ml.split(':', 1) # split only once
        if remove_opt: # remove
            remove_meta(dataset, key, category)
        else:       # add
            add_meta(dataset, key, value, category, type_name)


def handle_d_option(d_arg, p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg):
    """Handle `-d` option."""

    ds_name = psv_datasets.get(d_arg, None)
    if ds_name is None:
        print(f"ERROR: dataset '{d_arg}' not found on Pennsieve server")
        sys.exit(1)

    process_meta(
        ds_name, p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg
    )


def handle_f_option(f_arg, p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg):
    """Handle `-f` option."""

    input_keys = get_lines_in_file(f_arg)

    for k in input_keys:
        ds_name = psv_datasets[k]
        process_meta(
            ds_name, p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg
        )


def handle_all_option(p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg):
    """Handle `--all` option."""

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        ds_name = psv_datasets[k]
        process_meta(
            ds_name, p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg
        )


#===============================================================================
#                Main program
#===============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(
        sys.argv, "ht:c:p:d:f:k:v:m:", ['remove','show','all'], SYNTAX
    )

    # `-p` option: required by `-d`, `-f` and `--all` options
    p_arg = opts_dict.get('-p', None)
    p_arg = handle_p_option(p_arg)

    # Get status of `-d`, -f` and `--all` options
    d_opt, f_opt, all_opt = get_d_f_all_options(opts_dict)

    # Optional options: `--show`, `--remove`, `-c`, `-t'
    show_opt = "--show" in opts_dict
    remove_opt = "--remove" in opts_dict
    c_arg = opts_dict.get('-c', "Pennsieve")
    t_arg = opts_dict.get('-t', None)

    # Set meta_lines
    meta_lines = get_meta_lines(opts_dict)

    # Handle `-d` option and exit
    if d_opt:
        d_arg = opts_dict['-d']
        handle_d_option(
            d_arg, p_arg, show_opt, remove_opt,
            meta_lines, c_arg, t_arg
        )

    # Handle `-f` option
    if f_opt:
        f_arg = opts_dict['-f']
        handle_f_option(
            f_arg, p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg
        )

    # Handle `--all` option
    if all_opt:
        handle_all_option(p_arg, show_opt, remove_opt, meta_lines, c_arg, t_arg)
