#!/bin/bash
#
# A wrapper of "pennsieve upload" command to upload local data to Pennsieve
# server.
#
# IMPORTANT:
# ----------
# DO NOT USE "bash -e" or "set -e", because some functions in this script may
# return non-zero values, which would terminate the script too early when `-e`
# is set.

# Function that prints the usage:
function print_help() {
    echo "==============================================================================="
    echo "USAGE: $0 <local_data> <HPAP-###> [optional_destination]"
    echo "==============================================================================="

    echo "* Example #1: upload a single data file to the root of HPAP-001:"
    echo "    $0 '<path>/my_data_file' HPAP-001"
    echo

    echo "* Example #2: upload everything inside a data directory to the root of HPAP-001:"
    echo "    $0 '<path>/my_data_dir' HPAP-001"
    echo "  Note that '<path>/my_data_dir' will NOT be created on Pennsieve server."
    echo

    echo "* Example #3: upload a single data file to 'Histology/Bone Marrow' folder of HPAP-001:"
    echo "    $0 '<path>/my_data_file' HPAP-001 'Histology/Bone Marrow'"
    echo

    echo "* Example #4: upload everything inside a data directory to 'Histology/Bone Marrow'"
    echo "              folder of HPAP-001 on Pennsieve server"
    echo "    $0 '<path>/my_data_dir' HPAP-001 'Histology/Bone Marrow'"
    echo "  Note that '<path>/my_data_dir' will NOT be created on Pennsieve server."
}


# Function to trim both leading and trailing space characters from input argument.
# See: https://stackoverflow.com/a/3352015
function trim_str() {
    local var="$*"
    var="${var#"${var%%[![:space:]]*}"}"  # remove leading whitespace char
    var="${var%"${var##*[![:space:]]}"}"  # remove trailing whitespace char
    echo "$var"
}


# Check whether "$1" is equal to one of the trimmed lines of "$2"
function line_exists() {
    local line=""
    local trimmed_line=""

    # Read "$2" line by line.
    # See: https://unix.stackexchange.com/questions/9784/
    while read -r line; do
	trimmed_line=$(trim_str $line)
	if [[ "$1" == "$trimmed_line" ]]; then
	    return 1
	fi
    done <<<"$2"
}


# Get the collection ID of "$1" from lines in "$2"
function get_psv_id() {
    local raw_name=""
    local name=""
    local raw_id=""
    local id=""

    local line=""
    while read -r line; do
	raw_name=$(echo $line | cut -d'|' -f2)
	name=$(trim_str "${raw_name}")
	if [[ "$1" == "$name" ]]; then
	    if [[ -z "$id" ]]; then
		raw_id=$(echo $line | cut -d'|' -f3)
		id=$(trim_str "${raw_id}")
	    else
		return 2
	    fi
	fi
    done <<< "$2"

    if [[ -z "$id" ]]; then
	return 1
    fi

    echo "$id"
}


# This function creates the manifest. It accepts either one or two arguments:
#   - arg #1: local path of files that will be uploaded
#   - arg #2: (optional) path on Pennsieve server
function create_manifest() {
    if [[ -z "$2" ]]; then
	pennsieve manifest create "$1"
    else
	pennsieve manifest create "$1" -t "$2"
    fi
}


#************************************************************************
#                   main program
#************************************************************************

# Ensure that "pennsieve" command is available
which pennsieve &> /dev/null
if [[ $? -ne 0 ]]; then
    echo "'pennsieve' command not found"
    exit 1
fi

# Ensure that `pennsieve-aggent` version 1.x is being used
pennsieve -h 2>&1 | grep manifest &> /dev/null
if [[ $? -ne 0 ]]; then
    echo "Error: 'pennsieve-agent' version is too old"
    echo "Please upgrade it to the latest version at:"
    echo "https://github.com/Pennsieve/pennsieve-agent/releases/"
    exit 1
fi

# Ensure that the numebr of arguments is correct
if [[ "$#" -lt 2 || "$#" -gt 3 ]]; then
    print_help
    exit 1
fi

# Ensure that `realpath` command is available
which realpath &> /dev/null
if [[ $? -ne 0 ]]; then
    echo "'realpath' command not available, please install it"
    exit 1
fi

# Ensure that "input_local_path" exists in local filesystem:
input_local_path=$(realpath "$1")
if [[ ! -e "${input_local_path}" ]]; then
    echo "Error: '$1' not found on local computer"
    exit 1
fi

# Ensure that pennsieve-agent is run by current user as a daemon
ps -ef | grep "^$USER .* pennsieve agent start$" &> /dev/null
if [[ $? -ne 0 ]]; then
    echo "Start 'pennsieve agent' as a daemon"
    pennsieve agent  &> /dev/null # start the agent as a daemon
    if [[ $? -ne 0 ]]; then
	echo "Error: 'pennsieve agent' command failed."
	echo "Please check '~/.pennsieve/config.ini' to make sure it's correct."
	exit 2
    fi
fi

# Get input dataset's internal name
input_psv_dataset="$2"
dataset_line=$(pennsieve dataset find "${input_psv_dataset}" 2>/dev/null | \
		   grep -w "${input_psv_dataset}")

# Exit if input dataset name is not found in Pennsieve server
if [[ "$?" -ne 0 ]]; then
    echo "Error: dataset '${input_psv_dataset}' not found on Pennsieve server"
    exit 1
fi

raw_dataset_name=$(echo ${dataset_line} | cut -d'|' -f3)
dataset_name=$(trim_str ${raw_dataset_name})

# Set current working dataset on Pennsieve server
pennsieve dataset use "${dataset_name}" > /dev/null

# Create manifest.
# If the output includes "failed", manifest is not created successfully.
mf_status=$(create_manifest "${input_local_path}" "$3")
mf_id=$(echo ${mf_status} | awk '{print $3}')
if (echo ${mf_status} | grep "failed" &> /dev/null); then
    echo "Error: failed to create manifest"
    pennsieve manifest delete ${mf_id} &> /dev/null
    exit 4
fi

# Upload the manifest
pennsieve upload manifest ${mf_id} &> /dev/null
if [[ "$?" -ne 0 ]]; then
    echo "Error: failed to submit upload job (manifest ID: ${mf_id})"
    exit 5
fi

echo
echo "Data uploading job #${mf_id} has been submitted successfully."
echo "  * use \"pennsieve agent subscribe\" command to see the realtime progress"
echo "  * use \"pennsieve manifest list ${mf_id}\" command to check the job"
echo "  * use \"pennsieve manifest delete ${mf_id}\" command to delete the job"
