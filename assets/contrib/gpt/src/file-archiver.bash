#!/usr/bin/env bash

# Script Name: file-archiver.bash
# Purpose: Find and compress files older than a specified number of days in a directory
# Created Date: Aug 23, 2024
# Author: Hugo
# Required Packages: None
# Powered by HomeSetup (https://github.com/yorevs/homesetup)
# GPT: [HHS-Script-Generator](https://chatgpt.com/g/g-ra0RVB9Jo-homesetup-script-generator)

# +------------------------------------------------------------------------------+
# | AIs CAN MAKE MISTAKES.                                                       |
# | For your safety, verify important information and code before executing it.  |
# |                                                                              |
# | This program comes with NO WARRANTY, to the extent permitted by law.         |
# +------------------------------------------------------------------------------+

# https://semver.org/ ; major.minor.patch
VERSION="1.0.0"

# Usage message
USAGE="usage: $(basename "$0") -d directory [-n days] [-h] [-v]

  Options:
    -d, --directory   Specify the directory to search (mandatory).
    -n, --days        Specify the number of days old the files should be (default: 30 days).
    -h, --help        Display help message and exit.
    -v, --version     Print version information and exit.

  Example:
    $(basename "$0") -d /path/to/directory -n 60
"

# List of guarded directories
PROTECTED_DIRS="/ /bin /boot /dev /etc /lib /lib64 /proc /root /sbin /sys /usr /var"

# @purpose: Display the usage message
usage() {
    echo "${USAGE}"
    exit 2
}

# @purpose: Display the version information
version() {
    echo "$(basename "$0") version ${VERSION}"
    exit 0
}

# @purpose: Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d|--directory) DIRECTORY="$2"; shift 2 ;;
            -n|--days) DAYS="$2"; shift 2 ;;
            -h|--help) usage ;;
            -v|--version) version ;;
            *) echo -e "\033[31mERROR\033[m: Invalid option: $1"; usage ;;
        esac
    done

    # Check if the directory argument is missing
    if [[ -z "${DIRECTORY}" ]]; then
        echo -e "\033[31mERROR\033[m: The directory argument (-d) is mandatory."
        usage
    fi
}

# Set default value for DAYS
DAYS=30

# Parse command-line arguments
parse_args "$@"

# @purpose: Check if the directory is a critical system directory
is_protected_directory() {
    local dir="$1"
    for protected_dir in ${PROTECTED_DIRS}; do
        if [[ "${dir}" == "${protected_dir}" ]]; then
            echo -e "\033[31mERROR\033[m: Attempting to modify a protected system directory (${dir}) is not allowed."
            exit 1
        fi
    done
}

# @purpose: Find and compress files older than the specified number of days with safeguards
archive_files() {
    find "${DIRECTORY}" -type f -mtime +"${DAYS}" | while read -r file; do
        # Check if the file variable is empty
        if [[ -z "${file}" ]]; then
            echo -e "\033[31mERROR\033[m: File variable is empty. Skipping."
            continue
        fi

        # Get the creation date of the file (macOS specific)
        timestamp=$(stat -f "%SB" -t "%Y%m%d%H%M%S" "${file}")
        # Compress the file with the timestamp in the archive name
        tar -czf "${file}_${timestamp}.tar.gz" "${file}" && rm "${file}"
        echo -e "\033[32mSUCCESS\033[m: Compressed and archived ${file} to ${file}_${timestamp}.tar.gz"
    done
}

# Check if the specified directory is protected
is_protected_directory "${DIRECTORY}"

# Archive files
archive_files
