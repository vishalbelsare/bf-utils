#!/usr/bin/env python
#===============================================================================
#
#          FILE:  bftree.py
#
#         USAGE:  ./bftree.py
#
#   DESCRIPTION:
#
#       OPTIONS:  see usage below
#
#  REQUIREMENTS:  Python 3.x, blackfynn python library, blackfynn key
#       UPDATES:  170911: Added CLI opt/arg processing
#                 170922: Added -f option to show files
#                 171009: Check for existence of dataset
#                 171009: Added --nocolor option
#                 171102: Added ability to use short names for HPAP datasets
#                 171106: Added -p and -a options
#                 171110: data now shows actual file name
#                 171114: added --realdata
#                 171116: file download names now use the BF name and real
#                         extension of the uploaded filename
#                 171117: --realdata now shows uploaded filename and extension
#                         --data now shows BF filename and uploaded extension
#                 171121: created exceptions for unknown extensions
#                 180215: unified options
#                 180521: added test for package avail in print_tree()
#                 180810: added an additional check for extension
#                 181106: removed pptx and tif from extensions list
#
#                 2021-04-22: Fix the bug, pythonized the coding styles
#
#        AUTHOR:  Pete Schmitt (debtfree), pschmitt@upenn.edu & Dongbo Hu (dongbo@upenn.edu)
#       COMPANY:  University of Pennsylvania
#       VERSION:  0.6.2
#       CREATED:  09/06/2017 16:54:33 EDT
#      REVISION:  2021-04-22
#===============================================================================

import getopt
import sys
from datetime import datetime

from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
from termcolor import colored

__version__ = "0.6.2"

bf = Blackfynn()  # use 'default' profile

# extensions unknown to Blackfynn
extensions = ['ome.tiff', 'fastq.gz', 'bigWig', 'bw', 'metadata']


def flush_print(message="", with_time=False):
    if with_time:
        message = f"{datetime.now()}: {message}"

    print(message, flush=True)


def get_datasets():
    """
    Return list of tuples with short and long dataset names and
    dictionary of datasets with short name as key.
    """

    dsets = list()
    ds_dict = dict()
    ds = bf.datasets()
    for d in ds:
        if 'HPAP-' in d.name:
            tmp = d.name.split()
            ds_dict[str(tmp[0])] = str(d.name)
            dsets.append((str(tmp[0]), str(d.name)))
        else:
            ds_dict[str(d.name)] = str(d.name)
            dsets.append((str(d.name), str(d.name)))

    dsets.sort()
    return dsets, ds_dict


def print_tree(element, FILE, COLOR, REAL, indent=0, verbose=True):
    """Print the contents of a dataset as a tree."""

    try:
        element._check_exists()
    except:
        if verbose:
            flush_print(f"Object '{element}' does NOT exist when printing the tree")
        return

    count = len(element.items)
    if count == 0:
        if COLOR:
            pr_items = " (" + colored('empty', 'magenta') + ")"
        else:
            pr_items = " (empty)"
    else:
        pr_items = " (" + str(count) + " items)"

    print_me = " " * (indent) + element.name

    if indent != 0:
        if COLOR:
            print_me += colored(' (C)', 'green')
        else:
            print_me += ' (C)'

    print_me += pr_items
    flush_print(print_me)

    for item in element.items:
        if isinstance(item, BaseCollection):
            print_tree(item, FILE, COLOR, REAL, indent=indent+4)
        elif FILE:
            package = bf.get(item)
            if REAL:
                pkg_name = package.sources[0].name
            else:
                pkg_name = package.name
            try:
                real_name = str(package.sources[0].s3_key.split('/')[-1])
            except:
                flush_print("ERROR: unable to get real name of package: ")
                flush_print(f"{element.name}/{pkg_name}, continuing...")
                continue

            realext = False
            for ext in extensions:
                if real_name.lower().endswith(ext.lower()):
                    realext = ext
                    break

            if realext == False:
                realext = real_name.rsplit(".",1)[-1]

            if pkg_name[-len(realext):]==realext:
                filename = pkg_name
            else:
                filename = pkg_name.replace(realext,"")+"."+realext

            if COLOR:
                print_me = " "*(indent+4) + filename + colored(" (pkg)", "red")
            else:
                print_me = " "*(indent+4) + filename + " (pkg)"
            flush_print(f"{print_me}")


def collection_exists(ds,name):
    """ test if expected collection in path exists """
    for i in ds.items:
        if name == i.name: return True

    return False


def locate_path(ds, path, verbose=True):
    """ Return the object that represents where to
        start to print the tree """
    dirs = path.split('/')

    for i in range(len(dirs)):
        if dirs[i] == "":
            pass
        elif collection_exists(ds, dirs[i]):
            ds = ds.get_items_by_name(dirs[i])[0]
        else:
            if verbose:
                flush_print(f"Object '{dirs[i]}' does NOT exist when locating the path")
            return

    return ds


###############################################################################
#                            Main program
###############################################################################
if __name__ == "__main__":
    usage_str = (
        f"Usage of bftree version {__version__}:\n"
        "------------------------------\n"
        "bftree -d <dataset>\n"
        "       --all (or -a): show all HPAP datasets\n"
        "       --path (or -p) <path to start tree>: specify the path\n"
        "       --data: show packages in output\n"
        "       --realdata: show packages as uploaded names\n"
        "       --nocolor: no colorful output\n"
        "       --list (or -l): list datasets\n"
        "       --version (or -v): print version number\n"
        "       --help (or -h): usage text (this screen)\n"
        "Note: '-d' and '--all' are mutually exclusive\n"
    )

    FILE = False
    COLOR = True
    ALL = False
    PATH = False
    DATASET = False
    REAL = False

    if len(sys.argv) < 2:
        flush_print(usage_str)
        sys.exit(1)

    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(
            argv,
            "ad:hlp:v",
            ['all', 'data', 'help', 'list', 'nocolor', 'path', 'realdata', 'version']
        )
    except getopt.GetoptError:
        flush_print(usage_str)
        sys.exit(1)

    dsets, ds_dict = get_datasets()
    dset = None

    for opt, arg in opts:
        if opt == '--version' or opt == '-v':
            flush_print(__version__)
            sys.exit()
        elif opt == '--help' or opt == '-h':
            flush_print(usage_str)
            sys.exit()
        elif opt == '--data':
            FILE=True
        elif opt == '--all' or opt == '-a':
            ALL = True
        elif opt == '--path' or opt == '-p':
            path = arg
            PATH = True
        elif opt == '--realdata':
            REAL = True
            FILE = True
        elif opt == '--nocolor':
            COLOR = False
        elif opt == '--list' or opt == '-l':
            for ds in dsets:
                flush_print(ds[0])
            sys.exit()
        elif opt == '-d':
            DATASET = True
            try:
                dset = bf.get_dataset(ds_dict[arg])
            except:
                flush_print(f"Dataset {arg} does NOT exist")
                sys.exit(1)
        elif opt == '--version' or opt == '-v':
            flush_print(__version__)
            sys.exit()

    if PATH and DATASET:
        dset = locate_path(dset, path)
        if dset:
            print_tree(dset, FILE, COLOR, REAL)
    elif ALL:
        for ds in dsets:
            if 'HPAP-' not in ds[0]:
                continue
            dset = bf.get_dataset(ds[1])
            dataset = dset
            if PATH:
                dset = locate_path(dset, path, verbose=False)
                if dset:
                    flush_print()
                    flush_print(f"{dataset.name}: {path}")
                    print_tree(dset, FILE, COLOR, REAL, verbose=False)
    elif dset:
        print_tree(dset, FILE, COLOR, REAL)
    else:
        flush_print("ERROR: Incompatible command options\n")
        flush_print(usage_str)
