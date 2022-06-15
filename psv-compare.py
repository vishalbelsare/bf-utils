#!/usr/bin/env python3

#===============================================================================
# This program is based on the legacy script `bf-legacy/bfcompare.py`, which was
# written by Pete Schmitt for Blackfynn file server.
#===============================================================================

import os
import sys

from pennsieve.models import BaseCollection

from psv_lib import (
    EXTENSIONS,
    psv,
    psv_datasets,
    parse_options,
)

SYNTAX = """
psv-compare.py -h (help)
               -c <compared dataset>
               -p <local path to compare>
               --all (compare with all datasets)
               -d <dataset> (required)
               -i (optional, case-insensitive comparison)
               --data (optional, also compare data)

Note: `-c`, `-p` and `--all` are mutually exclusive.
"""


def get_collections(element, collections, data_opt, indent=0):
    """Get the contents of a dataset as a tree."""

    try:
        element._check_exists()
    except Exception:
        print(f"ERROR: {element} not exist on Pennsieve")
        return

    if indent > 0:
        collections.append(f"{indent - 1}:{element.name}")
        print(".", end="")

    for item in element.items:
        if isinstance(item, BaseCollection):
            get_collections(item, collections, data_opt, indent=indent+1)
        elif data_opt:
            pkg = psv.get(item)
            pkg_name = pkg.name
            try:
                real_name = str(pkg.sources[0].s3_key.split('/')[-1])
            except:
                print(
                    f"\nERROR: unable to get real name of package: "
                    f"{elment.name}/{pkg_name}, so it will be ignored"
                )
                continue

            real_ext = None
            for ext in EXTENSIONS:
                if real_name.lower().endswith(ext.lower()):
                    real_ext = ext
                    break

            if real_ext is None:
                real_ext = real_name.rsplit(".", 1)[-1]

            if pkg_name[-len(real_ext):] == real_ext:
                filename = pkg_name
            else:
                filename = pkg_name.replace(real_ext, "") + "." + real_ext

            collections.append(f"{indent}:{filename}")

    return collections


def create_paths(the_list):
    """Create a list of UNIX-like paths from Pennsieve dataset."""

    paths = list()

    for item in the_list:
        colon = item.find(':')
        indent = int(item[:colon])
        collection = item[colon+1:]

        if indent == 0:
            path = [0] * 100
            path[0] = collection
            paths.append(collection)
        else:
            path[indent] = collection
            p0 = path[0]

            for i in range(1, indent + 1):
                if path[i] != 0:
                    p0 += "/" + path[i]

            paths.append(p0)

    return paths


def find(collection, paths, case_sensitive):
    """Search paths for collection."""

    for p in paths:
        if case_sensitive and p == collection:
            return True

        if not case_sensitive and p.upper() == collection.upper():
            return True

    return False


def find_first_only(paths_1, paths_2, case_sensitive):
    """Find paths that are in `ds1` but not in `ds2`."""

    for p1 in paths_1:
        if not find(p1, paths_2, case_sensitive):
            print(p1)


def compare_datasets(d_arg, d_paths, c_dataset, case_sensitive, data_opt):
    """Compare `d_dataset` and `c_dataset`."""

    c_paths = get_ds_paths(c_dataset)

    print(f"\n\nData in '{d_arg}' but are NOT in '{c_dataset.name}':")
    print('*' * 80)
    find_first_only(d_paths, c_paths, case_sensitive)

    print(f"\nData in '{c_dataset.name}' but are NOT in '{d_arg}':")
    print('*' * 80)
    find_first_only(c_paths, d_paths, case_sensitive)


def get_local_paths(p_arg, data_opt):
    os.chdir(p_arg)
    paths = list()

    for r, d, f in os.walk('.'):
        if data_opt:
            dir_list = d + f
        else:
            dir_list = d

        for item in dir_list:
            paths.append((r + '/' + item)[2:])

    paths.sort()
    return paths


def get_ds_paths(dataset):
    """Get paths in input dataset."""

    print(f"\nGathering collections from '{dataset.name}'")
    collections = []
    ds_list = get_collections(dataset, collections, data_opt)
    ds_paths = create_paths(ds_list)
    ds_paths.sort()

    return ds_paths


def handle_d_option(d_arg):
    """Handle `-d` option."""

    if not d_arg:
        print("ERROR: `-d <dataset>` option not found")
        sys.exit(1)

    ds_name = psv_datasets.get(d_arg, None)
    if ds_name is None:
        print(f"ERROR: dataset '{d_arg}' not found on Pennsieve")
        sys.exit(1)

    dataset = psv.get_dataset(ds_name)
    ds_paths = get_ds_paths(dataset)
    return ds_paths


def get_c_p_all_options(opts_dict):
    """Ensure that only one of `-c`, `-d` and `--all` is being used."""

    c_opt = '-c' in opts_dict
    p_opt = '-p' in opts_dict
    all_opt = '--all' in opts_dict

    if c_opt + p_opt + all_opt != 1:
        print("ERROR: ONE AND ONLY ONE of `-c`, `-p` and `--all` options is allowed")
        sys.exit(1)

    return c_opt, p_opt, all_opt


def handle_c_option(c_arg, d_arg, d_paths, case_sensitive, data_opt):
    """Handle `-c` option."""

    if not c_arg:
        print("ERROR: `-c <compared_dataset>` option not found")
        sys.exit(1)

    ds_name = psv_datasets.get(c_arg, None)
    if ds_name is None:
        print(f"ERROR: dataset '{c_arg}' not found on Pennsieve server")
        sys.exit(1)

    c_dataset = psv.get_dataset(ds_name)
    compare_datasets(d_arg, d_paths, c_dataset, case_sensitive, data_opt)


def handle_p_option(p_arg, d_arg, d_paths, case_sensitive, data_opt):
    """Handle `-p` option."""

    local_paths = get_local_paths(p_arg, data_opt)

    print(f"\n\nData in '{d_arg}' but are NOT in '{p_arg}':")
    print('*' * 80)
    find_first_only(d_paths, local_paths, case_sensitive)

    print(f"\nData in '{p_arg}' but are NOT in '{d_arg}':")
    print('*' * 80)
    find_first_only(local_paths, d_paths, case_sensitive)


def handle_all_option(d_arg, d_paths, case_sensitive, data_opt):
    """Handle `--all` option."""

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        ds_name = psv_datasets[k]
        c_dataset = psv.get_dataset(ds_name)
        compare_datasets(d_arg, d_paths, c_dataset, case_sensitive, data_opt)


#==============================================================================
#                       Main program
#==============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(sys.argv, "hip:d:c:", ['all', 'data'], SYNTAX)

    # `-i` option
    case_sensitive = '-i' not in opts_dict
    if not case_sensitive:
        print("INFO: case-insensitive comparison enabled")

    # `--data` option
    data_opt = '--data' in opts_dict

    # `-c`, `-p` and `--all` options
    c_opt, p_opt, all_opt = get_c_p_all_options(opts_dict)

    # `-d` is required. It specifies the input dataset.
    d_arg = opts_dict.get('-d', None)
    d_paths = handle_d_option(d_arg)

    # `-c <compared_dataset>` option
    if c_opt:
        c_arg = opts_dict.get('-c', None)
        handle_c_option(c_arg, d_arg, d_paths, case_sensitive, data_opt)

    # `-p <path>` option
    if p_opt:
        p_arg = opts_dict.get('-p', None)
        handle_p_option(p_arg, d_arg, d_paths, case_sensitive, data_opt)

    # `--all` option
    if all_opt:
        handle_all_option(d_arg, d_paths, case_sensitive, data_opt)
