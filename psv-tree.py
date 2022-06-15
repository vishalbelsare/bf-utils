#!/usr/bin/env python3

#===============================================================================
# Print a Pennsieve dataset's content as a tree.
#
# Based on the legacy script `bf-legacy/bftree.py`, which was written by Pete
# Schmitt for Blackfynn file server.
#===============================================================================

import sys
from datetime import datetime

from pennsieve.models import BaseCollection
from termcolor import colored

from psv_lib import (
    collection_exists,
    EXTENSIONS,
    psv,
    psv_datasets,
    parse_options,
)

VERSION = "0.7.0"

SYNTAX = f"""
psv-tree.py version {VERSION}:
------------------------------------
psv-tree.py -h: (help)
            -d <dataset>: specify dataset
            --all: show all HPAP datasets
            -p <path_to_start_tree>: (optional) specify the path
            --data: (optional) show packages in output
            --realdata: (optional) show packages as uploaded names
            --nocolor: (optional) disable color in output

Note: `-d` and `--all` options are mutually exclusive.
"""


def print_tree(root, with_color, data_opt, real_opt, indent=0, verbose=True):
    """
    Print the contents of a dataset as a tree.  Note that this is a
    recursive function.
    """

    if root is None:
        return

    try:
        root._check_exists()
    except Exception:
        if verbose:
            print(f"ERROR: object '{root}' not exist on Pennsieve")
        return

    count = len(root.items)
    if count == 0:
        if with_color:
            pr_items = f" ({colored('empty', 'magenta')})"
        else:
            pr_items = " (empty)"
    elif count == 1:
        pr_items = f" (1 item)"
    else:
        pr_items = f" ({count} items)"

    print_me = " " * indent + root.name
    if indent != 0:
        if with_color:
            print_me += colored(' (C)', 'green')
        else:
            print_me += ' (C)'

    print_me += pr_items
    print(print_me)

    for item in root.items:
        if isinstance(item, BaseCollection):
            print_tree(item, with_color, data_opt, real_opt, indent=indent+4)
            continue

        if data_opt:
            package = psv.get(item)
            if real_opt:
                pkg_name = package.sources[0].name
            else:
                pkg_name = package.name

            try:
                real_name = str(package.sources[0].s3_key.split('/')[-1])
            except Exception:
                print("ERROR: unable to get real name of package: ")
                print(f"{root.name}/{pkg_name}, continuing...")
                continue

            real_ext = False
            for ext in EXTENSIONS:
                if real_name.lower().endswith(ext.lower()):
                    real_ext = ext
                    break

            if real_ext == False:
                real_ext = real_name.rsplit(".", 1)[-1]

            if pkg_name[-len(real_ext):] == real_ext:
                filename = pkg_name
            else:
                filename = pkg_name.replace(real_ext,"") + "." + real_ext

            if with_color:
                print_me = " " * (indent + 4) + filename + colored(" (pkg)", "red")
            else:
                print_me = " " * (indent + 4) + filename + " (pkg)"

            print(print_me)


def locate_path(path, ds, verbose=True):
    """
    Return the object that represents where to start printing the tree.
    """

    dirs = path.split('/')

    for d in dirs:
        if d == "":
            pass
        elif collection_exists(d, ds):
            ds = ds.get_items_by_name(d)[0]
        else:
            if verbose:
                print(f"ERROR: object '{d}' NOT exist when locating the path")

            return

    return ds


def get_d_all_options(opts_dict):
    """Ensure that `-d` and `--all` options are exclusive."""

    d_opt = '-d' in opts_dict
    all_opt = '--all' in opts_dict

    if d_opt + all_opt != 1:
        print("ERROR: ONE AND ONLY ONE of `-d` and `--all` options is allowed")
        sys.exit(1)

    return d_opt, all_opt


def handle_d_option(d_arg, p_arg, with_color, data_opt, real_opt):
    """Handle `-d <dataset>` option."""

    if d_arg not in psv_datasets:
        print(f"ERROR: Dataset '{arg}' not exist on Pennsieve")
        sys.exit(1)

    ds_name = psv_datasets[d_arg]
    dataset = psv.get_dataset(ds_name)

    if p_arg:  # `-p <path>` option is available
        dataset = locate_path(p_arg, dataset)

    print_tree(dataset, with_color, data_opt, real_opt)


def handle_all_option(p_arg, with_color, data_opt, real_opt):
    """Handle `--all` option."""

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        ds_name = psv_datasets[k]
        dataset = psv.get_dataset(ds_name)
        if p_arg:  # `-p <path>` option is available
            dataset = locate_path(p_arg, dataset, verbose=False)

        if dataset:
            print()
            if p_arg:
                print(f"{ds_name}: {p_arg}")
            print_tree(dataset, with_color, data_opt, real_opt, verbose=False)


###############################################################################
#                            Main program
###############################################################################
if __name__ == "__main__":
    # Parse options
    opts_dict = parse_options(
        sys.argv,
        "hd:p:", ['all', 'data', 'nocolor', 'realdata'],
        SYNTAX
    )

    # `-d <dataset>` or `--all` option is required
    d_opt, all_opt = get_d_all_options(opts_dict)

    with_color = '--nocolor' not in opts_dict  # optional
    data_opt = '--data' in opts_dict           # optional
    real_opt = '--realdata' in opts_dict       # optional

    if real_opt:
        data_opt = True

    # `-p <path>` is also optional
    p_arg = opts_dict.get('-p', None)

    # Handle `-d <dataset>` option
    if d_opt:
        d_arg = opts_dict['-d']
        handle_d_option(d_arg, p_arg, with_color, data_opt, real_opt)

    # Handle `--all` option
    if all_opt:
        handle_all_option(p_arg, with_color, data_opt, real_opt)
