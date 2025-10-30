#!/usr/bin/env bash

#
# Script Name: img-meta.bash
# Purpose: Extract and display all metadata from an image file (EXIF, IPTC, XMP, MakerNotes).
# Created Date: Oct 29, 2025
# Author: yorevs
# Required Packages: exiftool, jq (install via 'brew install exiftool jq')
# Powered by: HomeSetup (https://github.com/yorevs/homesetup)
#

# +------------------------------------------------------------------------------+
# | DISCLAIMER:                                                                  |
# | AIs CAN MAKE MISTAKES.                                                       |
# | For your safety, verify important information and code before executing it.  |
# |                                                                              |
# | This program comes with NO WARRANTY, to the extent permitted by law.         |
# +------------------------------------------------------------------------------+

# https://semver.org/; major.minor.patch
VERSION="1.0.0"

USAGE="
Usage: $(basename "$0") <image> [OPTIONS]

Options:
  -o, --output <file>    Export metadata to JSON file
  -h, --help             Display this help message
  -v, --version          Display version information

Examples:
  $(basename "$0") photo.jpg
  $(basename "$0") photo.jpg -o metadata.json
"

# @purpose: Show help message
usage() {
  echo "${USAGE}"
  exit 0
}

# @purpose: Show version
version() {
  echo "$(basename "$0") version ${VERSION}"
  exit 0
}

# @purpose: Check dependencies
require_exiftool() {
  for pkg in exiftool jq; do
    if ! command -v "${pkg}" >/dev/null 2>&1; then
      echo -e "\033[31mERROR:\033[m '${pkg}' is required. Install it with: brew install ${pkg}"
      exit 2
    fi
  done
}

# @purpose: Parse arguments
parse_args() {
  if [[ $# -lt 1 ]]; then usage; fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output)
        OUTPUT_FILE="${2:-}"
        if [[ -z "${OUTPUT_FILE}" ]]; then
          echo -e "\033[31mERROR:\033[m Missing filename after '$1'"
          exit 1
        fi
        shift 2
        ;;
      -h|--help) usage ;;
      -v|--version) version ;;
      *)
        if [[ -z "${IMAGE_FILE}" ]]; then
          IMAGE_FILE="$1"
        else
          echo -e "\033[31mERROR:\033[m Unexpected argument: $1"
          usage
        fi
        shift
        ;;
    esac
  done

  if [[ -z "${IMAGE_FILE}" ]]; then
    echo -e "\033[31mERROR:\033[m No image specified."
    usage
  fi
}

# @purpose: Extract and display all metadata
extract_metadata() {
  local img="${1}"
  echo -e "\033[34mINFORMATIVE:\033[m Extracting all metadata from '${img}'..."
  echo

  # Display in full key=value format for readability
  exiftool -a -u -g1 "${img}"

  if [[ -n "${OUTPUT_FILE}" ]]; then
    echo
    echo -e "\033[34mINFORMATIVE:\033[m Exporting metadata to JSON file: '${OUTPUT_FILE}'..."
    exiftool -json -a -u -g1 "${img}" | jq '.' > "${OUTPUT_FILE}"
    echo -e "\033[32mSUCCESS:\033[m Metadata exported successfully."
  fi
}

# --- MAIN EXECUTION ---
require_exiftool
parse_args "$@"

if [[ ! -f "${IMAGE_FILE}" ]]; then
  echo -e "\033[31mERROR:\033[m File not found: '${IMAGE_FILE}'"
  exit 1
fi

extract_metadata "${IMAGE_FILE}"
echo
echo -e "\033[32mDONE:\033[m Metadata extraction complete."
exit 0
