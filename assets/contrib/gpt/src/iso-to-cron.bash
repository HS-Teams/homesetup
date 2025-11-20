#!/usr/bin/env bash

# Script Name: iso-to-cron.bash
# Purpose: Convert ISO 8601 formatted time to cron expression
# Created Date: Aug 23, 2024
# Author: Hugo
# Required Packages: None
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
USAGE="usage: $(basename "$0") [options]

Options:
  -h, --help          Display this help message and exit
  -v, --version       Print version information and exit
  -i, --iso-to-cron   Convert ISO date to cron expression
  -c, --cron-to-iso   Convert cron expression to ISO date

Examples:
  $(basename "$0") -i \"2024-08-23T15:30:00\"
  $(basename "$0") -c \"30 15 23 8 *\"
"

# @purpose: Display usage message
usage() {
    echo "$USAGE"
    exit 2
}

# @purpose: Display the version information
version() {
    echo "$(basename "$0") version ${VERSION}"
    exit 0
}

# @purpose: Convert ISO 8601 time to cron expression
iso_to_cron() {
    local iso_time="$1"
    local cron_minute cron_hour cron_day cron_month cron_weekday
    local iso_time_no_tz

    # Remove the 'Z' if present (indicating UTC)
    iso_time_no_tz="${iso_time//Z/}"

    # Convert the ISO time to cron components
    cron_minute=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$iso_time_no_tz" "+%M")
    cron_hour=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$iso_time_no_tz" "+%H")
    cron_day=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$iso_time_no_tz" "+%d")
    cron_month=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$iso_time_no_tz" "+%m")
    cron_weekday=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$iso_time_no_tz" "+%u")

    # Convert weekday from 1-7 (Monday-Sunday) to 0-6 (Sunday-Saturday)
    cron_weekday=$(( cron_weekday % 7 ))

    echo "${cron_minute} ${cron_hour} ${cron_day} ${cron_month} *"
}

# @purpose: Convert a cron expression into an ISO 8601 date format
cron_to_iso() {
    local cron_expr="$1"
    local minute hour day month day_of_week

    IFS=' ' read -r minute hour day month day_of_week <<< "$cron_expr"

    # Replace '*' with appropriate ranges for date components
    minute="${minute//\*/00}"
    hour="${hour//\*/00}"
    day="${day//\*/01}"
    month="${month//\*/01}"
    day_of_week="${day_of_week//\*/1}"

    # Convert cron components to ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
    printf "%s-%02d-%02dT%02d:%02d:00\n" "$(date +%Y)" "${month}" "${day}" "${hour}" "${minute}"
}

# @purpose: Parse command-line arguments and execute corresponding actions
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help) usage ;;
            -v|--version) version ;;
            -i|--iso-to-cron)
                if [[ -z "$2" ]] || ! iso_to_cron "$2"; then echo "ERROR: ISO date not provided."; usage; fi
                shift
                ;;
            -c|--cron-to-iso)
                if [[ -z "$2" ]] || ! cron_to_iso "$2"; then echo "ERROR: Cron expression not provided."; usage; fi
                shift
                ;;
            *) echo "ERROR: Invalid option $1"; usage ;;
        esac
        shift
    done
}

# Main execution
[[ $# -eq 0 ]] && usage
parse_args "$@"
