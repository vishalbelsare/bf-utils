#!/usr/bin/env bash

# This script runs `du -s` on input directory and substracts the sizes
# of all sub-directories.
#
# Based on the legacy script `bf-legacy/bfdu.sh`, which was written by
# Pete Schmitt for Blackfynn file server.

# Directory size in KB on Linux
DIR_SIZE_IN_KB=4

# One and only one argument is required
if [[ $# -ne 1 || $1 == '-h' ]] ; then
    echo "Usage: psv-du.sh <directory>"
    exit 1
fi

# Exit if the argument is not a valid directory
if [[ ! -d $1 ]]; then
    echo "ERROR: '$1' is not an existing directory"
    exit 1
fi

# Get size of all sub-directories
num_dirs=$(find "$1" -type d | wc -l)
dirs_size=$((num_dirs * DIR_SIZE_IN_KB))

# Get size of input path w/o directory size
raw_total=$(du -sk "$1" | awk '{print $1}')
total=$((raw_total - dirs_size))

echo -e "$total KB\t$1"
