"""Library for Pennsieve utility scripts."""

import getopt
import os
import sys

from pennsieve import Pennsieve

# Extensions that Pennsieve doesn't know
EXTENSIONS = ['ome.tiff', 'fastq.gz', 'bigWig', 'bw', 'metadata']

# Global Pennsieve client instance
psv = Pennsieve()


def get_datasets():
    """
    Return a dict whose key is a dataset's short name (if available),
    and value is the dataset's long name.

    If a dataset's long name starts with 'HPAP-', then its short name
    will be the first token before whitespace character; otherwise the
    short name and long name will be identical.
    """

    ds_dict = dict()

    psv_ds = psv.datasets()
    for pd in psv_ds:
        if pd.name.startswith('HPAP-'):
            key_str = pd.name.split()[0]
        else:
            key_str = pd.name

        ds_dict[key_str] = pd.name

    return ds_dict


# All datasets on Pennsieve
psv_datasets = get_datasets()


def collection_exists(col_name, dataset):
    """
    Test whether a collection whose name is `ds_name` exists in `datasets`.
    """

    for item in dataset.items:
        if col_name == item.name:
            return True

    return False


def parse_options(args, short_opts, long_opts, syntax):
    """
    Parse input `args` based on `short_opts`, `long_opts`. If there's any
    error, or `-h` is in the options, print out `syntax_str` and exit;
    return a dict (key is option, value is the option's argument) otherwise.
    """

    if len(args) < 2:
        print(syntax)
        sys.exit(1)

    argv = args[1:]

    try:
        opts_list = getopt.getopt(argv, short_opts, long_opts)[0]
    except getopt.GetoptError:
        print("ERROR: invalid options")
        print(syntax)
        sys.exit(1)

    # Convert options from a list of tuples to a dict
    opts_dict = {x[0]: x[1] for x in opts_list}

    if '-h' in opts_dict:
        print(syntax)
        sys.exit()

    return opts_dict


def get_d_f_all_options(opts_dict):
    """Ensure that `-d`, -f` and `--all` options are exclusive."""

    d_opt = '-d' in opts_dict
    f_opt = '-f' in opts_dict
    all_opt = '--all' in opts_dict

    if d_opt + f_opt + all_opt != 1:
        print("ERROR: ONE AND ONLY ONE of `-d`, `-f` and `--all` options is allowed")
        sys.exit(1)

    return d_opt, f_opt, all_opt


def get_lines_in_file(filename):
    """Returna a list that includes all lines in `filename`."""

    if not os.path.exists(filename):
        print(f"ERROR: file '{filename}' not exist")
        sys.exit(1)

    with open(filename) as fd:
        lines = fd.read().splitlines()

    # Ensure that each line is a valid dataset name in Pennsieve.
    for k in lines:
        if k not in psv_datasets:
            print(f"ERROR: dataset '{k}' not exist on Pennsieve")
            sys.exit(1)

    return lines
