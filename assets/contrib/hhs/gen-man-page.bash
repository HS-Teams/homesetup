#!/usr/bin/env bash
# shellcheck disable=SC1090

#  Script: gen-man-page.bash
# Purpose: Generate a manual for a Shell Script.
# Created: Sep 11, 2012
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current Version
VERSION="1.0.0"

# Help message to be displayed by the script.
read -r -d '' USAGE <<EOF
usage: $(basename "$0") [options]
    Generate a manual page template for the provided shell script.
    Parses header metadata to populate NAME, DESCRIPTION and more.

    options:
      -h | --help                    : Show this help message and exit.
      -v | --version                 : Print version information and exit.
      -s | --script <path>           : Script file to parse for metadata (required).

    arguments:
      (none)                         : All inputs are supplied via options.

  Notes:
    - The generated roff content is printed to stdout for use with man(1).
    - Ensure the target script contains the expected header comments.
EOF

RED="\033[31m"
GREEN="\033[32m"
NC="\033[m"

TODAY=$(date +'%m-%d-%Y')
SCRIPT="${SCRIPT:-MyScript}"
MAN_DATA=

# @purpose: Parse command line arguments.
parse_args() {

  # If no argument is passed, just enter HomeSetup directory.
  if [[ ${#} -eq 0 ]]; then
    echo "${USAGE}"
    exit 0
  fi

  # Loop through the command line options.
  # Short opts: -<C>, Long opts: --<Word>.
  while [[ ${#} -gt 0 ]]; do
    case "${1}" in
    -h | --help)
      echo "${USAGE}" && exit 0
      ;;
    -v | --version)
      echo "$(basename "$0") v${VERSION}" && exit 0
      ;;
    -s | --script)
      [[ -z "${2}" ]] && {
        echo -e "${RED}Script path must be specified!${NC}\n\n${USAGE}"
        exit 1
      }
      SCRIPT="${2}"
      shift
      ;;

    *)
      echo -e "${RED}## Invalid option: '${1}' ${NC}"
      break
      ;;
    esac
    shift
  done
}

#!/bin/bash

# Function: generate_man_data
# Description: Parses a script file to extract metadata and populate MAN_DATA variables for manual page generation.
generate_man_data() {
  local script_file="$1"

  if [[ ! -f "$script_file" ]]; then
    echo "Error: File '$script_file' does not exist."
    return 1
  fi

  # Extract header comments (lines starting with #)
  while IFS= read -r line; do

    # Skip empty lines
    [[ ! "$line" =~ ^#\s*(.+:.+) ]] && continue

    # Remove leading '#', spaces
    clean_line="$(echo "${line}" | awk '{$1=$1};1')"
    clean_line="${clean_line//# /}"

    case "${clean_line//# /}" in
    Script:*)
      SCRIPT_NAME="$(echo "$clean_line" | awk -F': ' '{print $2}')"
      SCRIPT="${SCRIPT_NAME##*/}"
      TITLE="${SCRIPT%.*}"
      ;;
    Purpose:*)
      PURPOSE="$(echo "$clean_line" | awk -F': ' '{print $2}')"
      ;;
    Created:*)
      CREATED_DATE="$(echo "$clean_line" | awk -F': ' '{print $2}')"
      TODAY="$CREATED_DATE"
      ;;
    Author:*)
      AUTHOR_INFO="$(echo "$clean_line" | awk -F': ' '{print $2}')"
      ;;
    Mailto:*)
      MAILTO="$(echo "$clean_line" | awk -F': ' '{print $2}')"
      ;;
    Site:*)
      SITE="$(echo "$clean_line" | awk -F': ' '{print $2}')"
      ;;
    *)
      # You can handle additional fields here if needed
      ;;
    esac
  done <"$script_file"

  # Combine CONTACT_INFO from Mailto and Site
  CONTACT_INFO=()
  [[ -n "${MAILTO}" ]] && CONTACT_INFO+=("Mailto: ${MAILTO}" '.br')
  [[ -n "${SITE}" ]] && CONTACT_INFO+=("Site: ${SITE}")

  # Extract variables from the script file
  # VERSION
  VERSION_LINE="$(grep -E '^VERSION=' "$script_file" | head -n1)"
  if [[ -n "$VERSION_LINE" ]]; then
    VERSION="${VERSION_LINE#VERSION=}"
    VERSION="${VERSION//\"/}" # Remove quotes if any
  fi

  # Populate MAN_DATA
  MAN_DATA=$(echo -e "
  .\" ${TITLE:-Manual title}
  .TH ${SCRIPT} 8 \"${TODAY}\" v\"${VERSION}\" \"${TITLE}\" Manual
  .SH NAME
  ${SCRIPT} \- ${PURPOSE:-Script purpose}
  .SH SYNOPSIS
  ${SCRIPT} ${SYNOPSIS:-Synopsis here}
  .SH DESCRIPTION
  ${DESCRIPTION:-Description here}
  .SH OPTIONS
  ${OPTIONS:-Script options}
  .SH SEE ALSO
  ${SEE_ALSO:-See also section}
  .SH TODO
  ${TODOS:-Todo section}
  .SH AUTHOR
  ${AUTHOR_INFO:-Author information}
  .SH CONTACT INFO
  ${CONTACT_INFO[*]//.br/$'\n.br\n'}" | awk '{$1=$1};1')
}

parse_args "${@}"

# Extract variables from the script file
SCRIPT="${SCRIPT:-MyScript}"
MAN_DIR="${TEMP:-/tmp}/${SCRIPT//\.*/}.8"
mkdir -p "${MAN_DIR}" || {
  echo -e "${RED}Unable to create man dir: ${MAN_DIR}!${NC}"
  exit 1
}
MAN_FILE="${MAN_DIR}/$(basename "${SCRIPT//\.*/}")"

generate_man_data "${SCRIPT}"

OLDIFS="${IFS}"
while IFS=$'\n' read -r line; do
  echo -e "${line}"
done <<<"${MAN_DATA#?? }" >"${MAN_FILE}"
IFS="${OLDIFS}"

echo -e "${GREEN}Man page created at at: ${MAN_FILE}${NC}"
man "${MAN_FILE}"

echo ''
