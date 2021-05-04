#!/bin/bash
#===============================================================================
#
#          FILE:  install.sh
#
#         USAGE:  ./install.sh  [install_directory]
#
#   DESCRIPTION:  Install Pennsieve utilities
#
#        AUTHOR:  Dongbo Hu
#       CREATED:  05/04/2021
#===============================================================================

# Get absolute path of the source directory
abs_curr_file=$(readlink -e "$0")
abs_curr_dir=$(dirname ${abs_curr_file})

if  [ "$#" -eq 0 ]; then
    INST_DIR=$HOME/bin
elif [ "$#" -eq 1 ] && [ "$1" != "-h" ]; then
    INST_DIR=$1
else
    echo "Usage: ${abs_curr_file} [installation_dir] (default: $HOME/bin)"
    exit 0
fi

# Create installation directory
mkdir -pv ${INST_DIR}

# Go to the current script's directory
cd ${abs_curr_dir}

# Create soft links in INST_DIR
for f in bf*.py bfdu.sh; do
    echo "Installing $f into ${INST_DIR} ..."
    if [ "$f" = "bfdu.sh" ]; then
	extension=".sh"
    else
	extension=".py"
    fi

    dest_name=$(basename $f $extension)
    ln -sf ${abs_curr_dir}/$f ${INST_DIR}/${dest_name}
done
