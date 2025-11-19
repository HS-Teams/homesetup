#!/usr/bin/env bash

#  Script: taius.bash
# Purpose: Manager for HomeSetup AskAI integration
# Created: Aug 19, 2024
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current script version.
VERSION="$(pip show hspylib-askai | grep Version)"

# Current plugin name
PLUGIN_NAME="taius"

UNSETS=(
  help version cleanup execute
)

# Usage message
USAGE="$(cat <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} [options] <question>
    Ask Taius (HomeSetup AskAI) anything about your environment.
    Requires the HomeSetup virtual environment and AskAI package.

    options:
      -h | --help                    : Display this help message and exit.
      -v | --version                 : Print the Taius plugin version.

    arguments:
      question                       : Prompt to forward to the AskAI engine.

  Notes:
    - AskAI must be installed and the HomeSetup python venv activated.
    - Additional flags are forwarded directly to 'python3 -m askai'.
EOF
)"

[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# @purpose: HHS plugin required function
function help() {
  usage 0
}

# @purpose: HHS plugin required function
function version() {
  echo "HomeSetup ${PLUGIN_NAME} plugin ${VERSION}"
  quit 0
}

# @purpose: HHS plugin required function
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# @purpose: HHS plugin required function
function execute() {
  local args

  __hhs_is_venv || quit 1 "Not available when HomeSetup python venv is not active!"

  [[ -z "$1" || "$1" == "-h" || "$1" == "--help" ]] && usage 0
  [[ "$1" == "-v" || "$1" == "--version" ]] && version

  [[ -n "${HHS_AI_ENABLED}" ]] || quit 1 "AskAI is not installed. Visit ${HHS_ASKAI_URL} for installation instructions"

  # Filter out options starting with - followed by letters
  args=()
  for arg in "$@"; do
    [[ ! "$arg" =~ ^-[a-zA-Z] ]] && args+=("$arg")
  done

  python3 -m askai -r rag "${args[@]}" 2>&1 || quit 0

  quit 1 "Failed to execute AskAI"
}
