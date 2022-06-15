#!/usr/bin/env bash
#
# This script installs `psv-*` scripts in this repository to a specified
# installation directory (default: "$HOME/bin").

# Get absolute path of the source directory
abs_curr_file=$(readlink -e "$0")
abs_curr_dir=$(dirname ${abs_curr_file})

if  [ "$#" -eq 0 ]; then
    INST_DIR=$HOME/bin
elif [ "$#" -eq 1 ] && [ "$1" != "-h" ]; then
    INST_DIR=$1
else
    echo "Usage: ${abs_curr_file} [installation_dir]"
    echo "Note: default installation_dir: $HOME/bin"
    exit 0
fi

# Create installation directory
mkdir -pv ${INST_DIR}

# Go to the current script's directory
cd ${abs_curr_dir}

# Install `psv-*.py` and `psv-du.sh`
for f in psv-*.py psv-*.bash; do
    echo "Installing $f into ${INST_DIR}"

    # Get file extension (with the leading '.'), see the discussion at:
    # https://stackoverflow.com/questions/965053
    extension=".${f##*.}"

    # Get basename (w/o extension)
    dest_name=$(basename $f $extension)

    # Force create symlink in ${INST_DIR}
    ln -sf ${abs_curr_dir}/$f ${INST_DIR}/${dest_name}
done
