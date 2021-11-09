#!/bin/bash
#
# A wrapper of "pennsieve upload" command to upload local data to Pennsieve server.
#
# IMPORTANT:
# ----------
# DO NOT USE "bash -e" or "set -e", because some functions in this script may
# return non-zero values, which would terminate the script too early.

# Function that prints the usage:
function print_help() {
    echo "==============================================================================="
    echo "COMMAND USAGE:"
    echo "$0 <local_data> <HPAP-###> [optional_destination] [--no-parent]"
    echo "==============================================================================="

    echo "* Example #1: upload './my data' to the root folder of HPAP-001:"
    echo "    $0 './my data' HPAP-001"
    echo

    echo "* Example #2: upload './my data' to 'Histology/Bone Marrow' folder of HPAP-001:"
    echo "    $0 './my data' HPAP-001 'Histology/Bone Marrow'"
    echo

    echo "* Example #3: upload each file in './my data' to the root folder of HPAP-001"
    echo "              WITHOUT creating 'my_data' folder on Pennsieve server"
    echo "    $0 './my data' HPAP-001 --no-parent"
    echo

    echo "* Example #4: upload each file in './my data/' to 'Histology/Bone Marrow' folder"
    echo "              of HPAP-001 WITHOUT creating 'my_data' folder on Pennsieve server"
    echo "    $0 './my data' HPAP-001 'Histology/Bone Marrow' --no-parent"
    echo
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


# Ensure that "pennsieve" command is available
which pennsieve > /dev/null
if [[ $? -ne 0 ]]; then
    echo "'pennsieve' command not found"
    exit 1
fi

# Ensure that the numebr of arguments is correct
if [[ "$#" -lt 2 || "$#" -gt 4 ]]; then
    print_help
    exit 1
fi

# If there are four arguments, the last one must be "--no-parent"
if [[ "$#" -eq 4 && "$4" != "--no-parent" ]]; then
    print_help
    exit 1
fi

# Ensure that "input_local_path" exists in local filesystem:
input_local_path="$1"
if [[ ! -e "${input_local_path}" ]]; then
    echo "ERROR: '$1' not exist on local computer"
    exit 1
fi

local_base=$(basename "$input_local_path")  # basename of `input_local_path`

# Get the full name of input dataset
input_psv_dataset="$2"
dataset_line=$(pennsieve datasets | grep -w "${input_psv_dataset}")

# Exit if input dataset name is not found in Pennsieve server
if [[ "$?" -ne 0 ]]; then
    echo "Error: dataset '${input_psv_dataset}' not found in Pennsieve server"
    exit 1
fi

raw_dataset_name=$(echo ${dataset_line} | cut -d'|' -f3)
dataset_name=$(trim_str ${raw_dataset_name})

# Set current working dataset on Pennsieve server
pennsieve use "${dataset_name}" > /dev/null

# Base command
upload_cmd="pennsieve upload -f"

# ---------------------------------------------------------------------
# If "optional_destination" is NOT specified, upload local data to
# the root of dataset.
# ---------------------------------------------------------------------
if [[ "$#" -eq 2 ]]; then
    # Ensure that `local_base` does NOT exist in current dataset's root yet:
    lines=$(pennsieve ls | awk 'NR > 8 {print $0}' | cut -d'|' -f2)
    line_exists "${local_base}" "$lines"
    if [[ "$?" -eq 1 ]]; then
	echo "ERROR: '${local_base}' already exists in root of '${input_psv_dataset}'"
	exit 1
    fi

    if [[ -d "${input_local_path}" ]]; then
	upload_cmd="${upload_cmd} -r"
    fi

    # Upload data now. Note: DO NOT use "${upload_cmd}", which would execute
    # the whole string as ONE command!
    ${upload_cmd} --dataset "${dataset_name}" "${input_local_path}"
    exit 0
fi

# ---------------------------------------------------------------------
# If "optional_destination" is NOT specified, and the 3rd argument is
# "--no-parent", upload every file in local data to the root of dataset.
# ---------------------------------------------------------------------
if [[ "$#" -eq 3 && "$3" == "--no-parent" ]]; then
    # Ensure that ${input_local_path} is a directory
    if ! [[ -d "${input_local_path}" ]]; then
	echo "ERROR: '${input_local_path}' is not a directory"
	exit 1
    fi

    for f in ${input_local_path}/*; do
	extra_option=''
	if [[ -d "$f" ]]; then
	    extra_option='-r'
	fi

	${upload_cmd} ${extra_option} --dataset "${dataset_name}" "$f"
    done

    exit 0
fi

# ---------------------------------------------------------------------
# If "optional_destination" is specified, check each sub-folder to get
# its collection ID, until the deepest level is reached.
# ---------------------------------------------------------------------
input_psv_dest="$3"

# Split input destination into an array
# See: https://stackoverflow.com/questions/10586153/
IFS='/' read -ra folders <<< "${input_psv_dest}"

# Remove empty entries in the array.
# See: https://stackoverflow.com/questions/16860877/
# folders=("${folders[@]/''}")  # not work on Bash 3.2.57 (macOS)

# Iterate each level of the path to get collection ID of the deepest sub-folder
current_folder_id=""
current_path=""
for i in "${folders[@]}"; do
    # Skip empty entry
    if [[ -z "$i" ]]; then
	continue
    fi

    if [[ -z "${current_folder_id}" ]]; then  # first level of the path
	toc_lines=$(pennsieve ls | awk 'NR > 8 {print $0}')
	current_path="$i"
    else                                      # paths after the first level
	toc_lines=$(pennsieve ls --collection "${current_folder_id}" | awk 'NR > 8 {print $0}')
	current_path="${current_path}/$i"
    fi

    current_folder_id=$(get_psv_id "$i" "${toc_lines}")

    # Exit if sub-folder is not found or multiple matches are found in Pennsieve server
    if [[ "$?" -eq 1 ]]; then
	echo "ERROR: '${current_path}' folder not found in Pennsieve server"
	exit 1
    elif [[ "$?" -eq 2 ]]; then
	echo "ERROR: multiple '${current_path}' folders found in Pennsieve server"
	exit 1
    fi
done

# ---------------------------------------------------------------------
# If three arguments are found and the last one is not "--no-parent",
# then upload the whole `input_local_path` to the destination.
# ---------------------------------------------------------------------
if [[ "$#" -eq 3 ]]; then
    # Ensure that `local_base` does NOT exist in `current_folder_id` yet:
    lines=$(pennsieve ls --collection "${current_folder_id}" | awk 'NR > 8 {print $0}' | cut -d'|' -f2)
    line_exists "${local_base}" "$lines"
    if [[ "$?" -eq 1 ]]; then
	echo "ERROR: '${local_base}' already exists in '${input_psv_dest}' folder"
	exit 1
    fi

    # Upload data now.
    extra_option=''
    if [[ -d "${input_local_path}" ]]; then
	extra_option='-r'
    fi

    ${upload_cmd} ${extra_option} --folder "${current_folder_id}" "${input_local_path}"
    exit 0
fi

# ---------------------------------------------------------------------
# If four arguments are found and the last one is "--no-parent", then
# upload each file in `input_local_path` to the destination.
# ---------------------------------------------------------------------
# Ensure that ${input_local_path} is a directory
if ! [[ -d "${input_local_path}" ]]; then
    echo "ERROR: '${input_local_path}' is not a directory"
    exit 1
fi

for f in ${input_local_path}/*; do
    extra_option=''
    if [[ -d "$f" ]]; then
	extra_option='-r'
    fi

    ${upload_cmd} ${extra_option} --folder "${current_folder_id}" --dataset "${dataset_name}" "$f"
done
