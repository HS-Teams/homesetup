#!/usr/bin/env bash

# Script Name: media-converter.bash
# Purpose: Convert media files from one format to another using ffmpeg.
# Created Date: Aug 23, 2024
# Author: Hugo
# Required Packages: ffmpeg
# Powered by [HomeSetup](https://github.com/yorevs/homesetup)
# GPT: [HHS-Script-Generator](https://chatgpt.com/g/g-ra0RVB9Jo-homesetup-script-generator)

# +-----------------------------------------------------------------------------+
# | AIs CAN MAKE MISTAKES.                                                      |
# | For your safety, verify important information and code before executing it. |
# |                                                                             |
# | This program comes with NO WARRANTY, to the extent permitted by law.        |
# +-----------------------------------------------------------------------------+

# https://semver.org/ ; major.minor.patch
VERSION="0.0.1"  # https://semver.org/ ; major.minor.patch

# Usage message
USAGE="$(cat <<EOF
usage: $(basename "$0") -i <input> -f <format> [options]
    Convert media files to another format via ffmpeg.
    Automatically infers the output name when not provided.

    options:
      -i | --input <file>            : Source media file to convert (required).
      -f | --format <ext>            : Desired output format (e.g. mp4, mp3, avi).
      -o | --output <file>           : Optional output path; defaults to input name plus new extension.
      -h | --help                    : Display this help message and exit.
      -v | --version                 : Print version information and exit.

    arguments:
      (none)                         : All configuration is supplied via options.

  Notes:
    - Requires ffmpeg to be installed and available on the PATH.
    - Existing output files are overwritten by ffmpeg unless protected externally.
EOF
)"

# @purpose: Display the usage/help message
usage() {
    echo "$USAGE"
}

# @purpose: Display the version information
version() {
    echo "$(basename "$0") version ${VERSION}"
    exit 0
}

# @purpose: Check if ffmpeg is installed
require_ffmpeg() {
    if ! command -v ffmpeg &> /dev/null; then
        echo -e "\033[31mERROR\033[m: ffmpeg is required but not installed. Install it using 'brew install ffmpeg'."
        exit 2
    fi
}

# @purpose: Parse command-line arguments
parse_args() {
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            -i|--input) INPUT="$2"; shift ;;
            -o|--output) OUTPUT="$2"; shift ;;
            -f|--format) FORMAT="$2"; shift ;;
            -h|--help) usage; exit 0 ;;
            -v|--version) version ;;
            *) echo -e "\033[31mERROR\033[m: Unknown option: $1"; usage; exit 1 ;;
        esac
        shift
    done
}

# @purpose: Main conversion logic
main() {
    require_ffmpeg

    if [[ -z "${INPUT}" ]] || [[ -z "${FORMAT}" ]]; then
        echo -e "\033[31mERROR\033[m: Input file and format are required."
        usage
        exit 1  # Exit with a non-zero status to indicate failure
    fi

    # Determine output file name if not provided
    if [[ -z "${OUTPUT}" ]]; then
        OUTPUT="${INPUT%.*}.${FORMAT}"
    fi

    # Perform the conversion using ffmpeg
    if ffmpeg -i "${INPUT}" "${OUTPUT}"; then
        echo -e "\033[32mSUCCESS\033[m: Conversion complete. Output file: ${OUTPUT}"
    else
        echo -e "\033[31mERROR\033[m: Conversion failed."
        exit 1
    fi
}

# Entry point
parse_args "$@"
main
