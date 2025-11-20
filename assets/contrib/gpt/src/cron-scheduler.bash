#!/usr/bin/env bash

# cron-scheduler.bash
# Purpose: Schedule a script as a cron job based on an ISO date provided by the user
# Created Date: Aug 23, 2024
# Author: Hugo
# Required Packages: cron
# Powered by [HomeSetup](https://github.com/yorevs/homesetup)
# GPT: [HHS-Script-Generator](https://chatgpt.com/g/g-ra0RVB9Jo-homesetup-script-generator)

# +------------------------------------------------------------------------------+
# | AIs CAN MAKE MISTAKES.                                                       |
# | For your safety, verify important information and code before executing it.  |
# |                                                                              |
# | This program comes with NO WARRANTY, to the extent permitted by law.         |
# +------------------------------------------------------------------------------+

# https://semver.org/ ; major.minor.patch
VERSION="1.0.0" # https://semver.org/ ; major.minor.patch

# Usage message
USAGE="usage: $(basename "$0") -s <script_path> -i <iso_date> [-u <user>]
Example: $(basename "$0") -s /path/to/script.sh -i 2024-08-23T15:30:00Z -u username"

# @purpose: Display help message and exit
usage() {
    echo "$USAGE"
    exit 2
}

# @purpose: Display the version information
version() {
    echo "$(basename "$0") version ${VERSION}"
    exit 0
}

# @purpose: Parse command line arguments
parse_args() {
    while getopts ":s:i:u:hv" opt; do
        case ${opt} in
            s) SCRIPT_PATH=${OPTARG} ;;
            i) ISO_DATE=${OPTARG} ;;
            u) USER=${OPTARG} ;;
            h) usage ;;
            v) version ;;
            \?) echo -e "\033[31mERROR\033[m: Invalid option -${OPTARG}" >&2; usage ;;
            :) echo -e "\033[31mERROR\033[m: Option -${OPTARG} requires an argument." >&2; usage ;;
        esac
    done

    # Ensure mandatory arguments are provided
    if [[ -z "${SCRIPT_PATH}" ]] || [[ -z "${ISO_DATE}" ]]; then
        echo -e "\033[31mERROR\033[m: Both script path and ISO date must be provided."
        usage
    fi
}

# @purpose: Check if the iso-to-cron.bash script exists in the same directory
require_iso_to_cron() {
    if [[ ! -f "$(dirname "$0")/iso-to-cron.bash" ]]; then
        echo -e "\033[31mERROR\033[m: iso-to-cron.bash is not found in the current directory. Please ensure it's present and try again."
        exit 1
    fi
}

# @purpose: Schedule the script as a cron job
schedule_cron_job() {
    CRON_EXPR=$("$(dirname "$0")/iso-to-cron.bash" -i "${ISO_DATE}")
    if [[ $? -ne 0 ]]; then
        echo -e "\033[31mERROR\033[m: Failed to convert ISO date to cron expression."
        exit 1
    fi

    CRON_JOB="${CRON_EXPR} ${USER:+-u ${USER}} ${SCRIPT_PATH}"
    echo "${CRON_JOB}" | crontab -
    if [[ $? -eq 0 ]]; then
        echo -e "\033[32mSUCCESS\033[m: Script has been scheduled successfully."
    else
        echo -e "\033[31mERROR\033[m: Failed to schedule the script."
        exit 1
    fi
}

# Main execution flow
parse_args "$@"
require_iso_to_cron
schedule_cron_job
