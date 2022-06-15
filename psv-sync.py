#!/usr/bin/env python3

#===============================================================================
# This program is based on the legacy script `bf-legacy/bfsync.py`, which was
# written by Pete Schmitt for Blackfynn file server.
#
# Note that some functionalities of this script are also available in:
#    `hpap/flask_app/hpapps/pennsieve_sync.py`
# but the latter also writes logs to MySQL database.
#===============================================================================

import os
import sys
import time

from pennsieve.models import BaseCollection
import pandas as pd
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from psv_lib import (
    EXTENSIONS,
    psv,
    psv_datasets,
    parse_options,
    get_lines_in_file,
)

CATEGORIES = [
    "ATACseq",
    "B cell receptor repertoire",
    "Calcium imaging",
    "Clinical data",
    "CyTOF",
    "Flow panels for B cells",
    "Flow cytometry - Immune lineage",
    "Histology",
    "Imaging mass cytometry",
    "Morphology and viability",
    "mRNAseq",
    "Oxygen consumption",
    "Patch-Clamp",
    "Perifusions",
    "Sequencing data for sorted cells/Sort data",
    "Single-cell RNAseq",
    "Tetramer Ag specific studies by FACS",
    "WGBS",
]

SYNTAX = """
psv-sync.py -h (help)
	    -q (quick sync, check existence of file before downloading)
            -c <category>
            -d <dataset>
            -o <output_path_for_local_storage> (default is $PWD)
            -x <file_containing_excluded_paths>
            --all (apply to all HPAP datasets)
            --nodata (do not include data)
            --mirror (remove local data/directories to mirror dataset)
            --refresh (refresh HPAP website)

Note:
  * `-d` and `--all` options are mutually exclusive.
  * Categories supported by `-c` option are:
      - "ATACseq"
      - "B cell receptor repertoire"
      - "Calcium imaging"
      - "Clinical data"
      - "CyTOF"
      - "Flow panels for B cells"
      - "Flow cytometry - Immune lineage"
      - "Histology"
      - "Imaging mass cytometry"
      - "Morphology and viability"
      - "mRNAseq"
      - "Oxygen consumption"
      - "Patch-Clamp",
      - "Perifusions",
      - "Sequencing data for sorted cells/Sort data"
      - "Single-cell RNAseq"
      - "Tetramer Ag specific studies by FACS"
      - "WGBS"
"""




def get_collections(element, collections, indent=0):
    """
    Get contents of a dataset that will be processed later.  Note that
    this is a recursive function.
    """

    try:
        element._check_exists()
    except Exception:
        print(f"ERROR: {element} not exist on Pennsieve")
        sys.exit(1)

    if indent > 0:
        collections.append(f"{indent - 1}:{element.name}")

    for item in element.items:
        if isinstance(item, BaseCollection):
            get_collections(item, collections, indent=indent+1)
            continue

        pkg = psv.get(item)
        pkg_name = pkg.name
        try:
            real_name = str(pkg.sources[0].s3_key.split('/')[-1])
        except Exception:
            print(
                f"ERROR: unable to get real name of package: "
                f"'{element.name}/{pkg_name}', ignored"
            )
            continue

        real_ext = False
        for ext in EXTENSIONS:
            if real_name.lower().endswith(ext.lower()):
                real_ext = ext
                if real_ext == "bigWig":
                    real_ext = "bw"
                break

        if real_ext == False:
            real_ext = real_name.rsplit(".", 1)[-1]

        if pkg_name[-len(real_ext):] == real_ext:
            file_name = pkg_name
        else:
            file_name = pkg_name.replace(real_ext, "") + "." + real_ext

        collections.append(f"{indent}:{file_name}:{item.id}")

    return collections


def get_local_paths(root_path):
    """Get local paths of `root_path`."""

    paths = list()

    for r, d, f in os.walk(root_path):
        d = [r + "/" + x for x in d]
        f = [r + "/" + x for x in f]

        if WITH_DATA:
            dir_list = d + f
        else:
            dir_list = d

        for path in dir_list:
            paths.append(path.replace("\\\\", "/").replace("\\", "/"))

    return sorted(paths)


def create_paths(ds_key, the_list):
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

    paths = [f"{OUT_DIR}/{ds_key}/{p}" for p in paths]
    return paths


def check_package(df, pkg_name, real_name):
    """
    Check the package in question against the recorded `df` dataframe.

    Return False if the new package is found in `df`, AND `real_name` is
    a regular file; return True otherwise, which means the file will be
    downloaded.
    """

    if pkg_name in df.file_name_clean.values.tolist() and os.path.isfile(real_name):
        return False

    return True


def download_pkg_file(pkg, real_name, file_name, local_dir):
    """Download files in a package."""

    print(f"Downloading '{file_name}' to {local_dir}'")

    download_name = pkg.sources[0].download(real_name)
    download_name = str(download_name)

    if download_name != file_name:
        try:
            os.rename(download_name, file_name)
        except OSError:
            print(
                f"WARNING: failed to rename '{download_name}' to '{file_name}'"
            )


def download_packages(pkg_paths, df=None):
    """Download data from Pennsieve server to `pkg_paths`."""

    root_dir = os.getcwd()

    for path in pkg_paths:
        path_list = path.split('/')
        local_dir = '/'.join(path_list[:-1])

        if not os.path.isdir(local_dir):
            os.makedirs(local_dir)

        os.chdir(local_dir)

        pkg_id = path_list[-1]
        pkg_list = pkg_id.split(':')
        pkg_id = pkg_list[1:]
        pkg_id = ':'.join(pkg_id)

        package = psv.get(pkg_id)
        pkg_name = package.name
        real_name = str(package.sources[0].s3_key.split('/')[-1])

        real_ext = False
        for ext in EXTENSIONS:
            if real_name.lower().endswith(ext.lower()):
                real_ext = ext
                break

        if real_ext == False:
            real_ext = real_name.rsplit(".", 1)[-1]

        if pkg_name[-len(real_ext):] == real_ext:
            file_name = pkg_name
        else:
            file_name = pkg_name.replace(real_ext, "") + "." + real_ext

        # Reset bigwig extension
        if "bigWig" in file_name.rsplit(".", 1)[-1]:
            file_name = file_name.replace(".bigWig", ".bw")

        if QUICK_SYNC:
            if check_package(df, pkg_name, real_name):
                download_pkg_file(package, real_name, file_name, local_dir)
            else:
                print(f"Passing '{file_name}', no changes to file")
        else:
            download_pkg_file(package, real_name, file_name, local_dir)

        os.chdir(root_dir)


def excluded(item):
    """Return True if `item` is found in EXCLUDED_PATHS."""

    for x in EXCLUDED_PATHS:
        if item in x:
            return True

    return False


def remove_extension(file_name):
    """Return file_name without extension."""

    for ext in EXTENSIONS:
        if f".{ext}" in file_name:
            return file_name.replace(f".{ext}", "")

    if file_name.count(".") == 1:
        return file_name.rsplit(".", 1)[0]

    return file_name


def get_d_all_options(opts_dict):
    """Ensure that `-d` and `--all` options are exclusive."""

    d_opt = '-d' in opts_dict
    all_opt = '--all' in opts_dict

    if d_opt + all_opt != 1:
        print("ERROR: ONE AND ONLY ONE of `-d` and `--all` options is allowed")
        sys.exit(1)

    return d_opt, all_opt


def get_input_category(opts_dict):
    """Get input category based on `-c <category>` option."""

    arg = opts_dict.get('-c', None)
    if arg and arg not in CATEGORIES:
        printf(f"ERROR: category '{arg}' in `-c` option not valid")
        sys.exit(1)

    return arg


def get_output_dir(opts_dict):
    """
    Get output path based on `-o <_output_path>` option on command line.
    """

    arg = opts_dict.get('-o', '.')

    if arg in ['.', './']:
        arg = os.getcwd()
    elif not os.path.exists(arg):
        os.makedirs(arg)
    elif not os.path.isdir(arg):
        print(f"ERROR: '{arg}' exists but is not a directory")
        sys.exit(1)

    return arg


def get_excluded_paths(opts_dict):
    """Return excluded paths based on `-x <filename>` option."""

    arg = opts_dict.get('-x', None)
    if arg is None:
        return []

    return get_lines_in_file(arg)


def get_ds_paths(ds_key):
    """Get dataset path from the dataset whse short name is `ds_key`."""

    print(f"Gathering Collections from '{ds_key}' ...")

    ds_name = psv_datasets[ds_key]
    dataset = psv.get_dataset(ds_name)
    collections = list()
    ds_list = get_collections(dataset, collections)
    ds_paths = create_paths(ds_key, ds_list)

    return ds_paths


def remove_excluded():
    """Remove local files that are in excluded paths."""

    if not EXCLUDED_PATHS:
        return

    print("\nChecking for Excluded paths ...\n")
    for ep in EXCLUDED_PATHS:
        match = [x for x in ds_paths if ep in x]
        if len(match) > 0:
            del_file = match[0].split(":", 1)[0]
            # Only one match for each file in excluded paths
            if os.path.isfile(del_file):
                print(f"Removing '{ep}' ...")
                os.remove(del_file)


def mirror(ds_key, ds_paths):
    """Mirror Pennsieve dataset and local directory."""

    log_str = f"dataset '{ds_key}'" if ds_key else "all datasets"
    print(f"\nMirroring dataset '{log_str}' and '{OUT_DIR}' ...")

    ds_paths.sort(reverse=True)
    # Remove Pennsieve ":package:" ending to match local paths
    ds_paths = [":".join(x.split(":", 2)[:2]) for x in ds_paths]

    root_dir = OUT_DIR
    if ds_key:
        root_dir += '/' + ds_key

    local_paths = get_local_paths(root_dir, WITH_DATA)
    local_paths.sort(reverse=True)

    for lp in local_paths:
        if lp not in ds_paths:
            print(f"Removing '{lp}' because it does not exist on Pennsieve")

            if os.path.isdir(lp):
                os.removedirs(lp)
            else:
                os.unlink(lp)


def refresh_hpap():
    """Send refresh signal to HPAP website."""

    hpap_url = 'https://hpap.pmacs.upenn.edu/services/refreshDirectories'
    resp = str(requests.put(hpap_url, verify=False))

    if '200' in resp:
        print("Refresh signal sent to HPAP web server")
    else:
        print(f"ERROR: PUT request failed: '{resp}' returned from {hpap_url}")


def sync_data(ds_key, ds_paths):
    """Sync input daset paths."""

    print(f"\nCreating local directory structure in '{OUT_DIR}'")

    ds_paths.sort()
    for p in ds_paths:
        if not os.path.isdir(p):
            if ':package:' in p:
                continue
            if not excluded(p):
                continue
            os.makedirs(p)

    # `--nodata` option is not available
    if WITH_DATA:
        start_time = time.time()
        pkg_paths = list()
        print(f"\nRetrieving dataset packages to {OUT_DIR}")
        for p in ds_paths:
            if CATEGORY_ARG and CATEGORY_ARG not in p:
                continue
            if ":package:" not in p:
                continue

            pkg_split = p.rsplit("/", 1)[-1].split(":", 1)
            file_name = pkg_split[0]
            pkg_id = pkg_split[1]
            if not excluded(file_name) and not excluded(pkg_id):
                pkg_paths.append(p)

        if QUICK_SYNC:  # `-q` option is available
            hpap_files = []
            for root, b, files in os.walk(OUT_DIR):
                hpap_files.extend([[root, x] for x in files])

            data_df = pd.DataFrame(hpap_files, columns=['root', 'file_name'])

            data_df.loc[:, 'file_name_clean'] = data_df.file_name.apply(
                remove_extension
            )

            download_packages(pkg_paths, data_df)

        else: # `-q` option is not specified
            download_packages(pkg_paths)

        download_time = time.time() - start_time
        log_str = f"'{ds_key}'" if ds_key else "all donors"
        print(f"\nDownload time of {log_str}: {download_time:.2f} seconds")

    # Operations after file downloading:
    # (1) Remove files that are in excluded paths
    remove_excluded()

    # (2) mirroring if `--mirror` option is available
    if MIRROR:
        mirror(ds_key, ds_paths)

    # (3) Send refresh signal if `--refresh` option is available
    if REFRESH:
        refresh_hpap()


def handle_d_option(opts_dict):
    """Handle `-d <arg>` option."""

    ds_key = opts_dict['-d']
    if ds_key not in psv_datasets:
        printf(f"ERROR: dataset '{arg}' not exist on Pennsieve")
        sys.exit(1)

    ds_paths = get_ds_paths(ds_key)
    sync_data(ds_key, ds_paths)


def handle_all_option(opts_dict):
    """Handle `--all` option."""

    print("\nGathering all HPAP datasets ...")
    ds_paths = []

    for k in sorted(psv_datasets):
        if not k.startswith('HPAP-'):
            continue

        tmp_paths = get_ds_paths(k)
        ds_paths.extend(tmp_paths)

    sync_data(None, ds_paths)


#==============================================================================
#                       Main program
#==============================================================================
if __name__ == '__main__':
    # Parse options
    opts_dict = parse_options(
        sys.argv,
        "hqc:d:o:x:", ['all', 'mirror', 'nodata', 'refresh'],
        SYNTAX
    )

    d_opt, all_opt = get_d_all_options(opts_dict)  # `-d` and `--all` options

    # Global variables derived from input options
    CATEGORY_ARG = get_input_category(opts_dict)   # based on `-c <arg>` option
    OUT_DIR = get_output_dir(opts_dict)            # based on `-o <arg>` option
    EXCLUDED_PATHS = get_excluded_paths(opts_dict) # based on `-x <arg>` option

    QUICK_SYNC = '-q' in opts_dict
    MIRROR = '--mirror' in opts_dict
    WITH_DATA = '--nodata' not in opts_dict
    REFRESH = 'refresh' in opts_dict

    # Handle `-d` option
    if d_opt:
        handle_d_option(opts_dict)

    # Handle `--all` option
    if all_opt:
        handle_all_option(opts_dict)
