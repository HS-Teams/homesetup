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

# Current plugin name
PLUGIN_NAME="taius"

# Current script version.
VERSION="$(pip show hspylib-askai | grep Version)"

# Namespace cleanup
UNSETS=(
  help version cleanup execute
)

# Usage message
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} <question> [options]

 _____     _
|_   _|_ _(_)_   _ ___
  | |/ _\` | | | | / __|
  | | (_| | | |_| \\__ \\
  |_|\\__,_|_|\\__,_|___/...AskAI

  HomeSetup AskAI integration v${VERSION}.

    options:
      -h | --help              : Display this help message.
      -v | --version           : Display current plugin version.

    arguments:
      question                 : The question to ask Taius about HomeSetup.

    examples:
      Ask for usage guidance:
        => ${APP_NAME} ${PLUGIN_NAME} "How do I update HomeSetup?"

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - Requires the HomeSetup Python virtual environment and AskAI installation.
EOF

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

  python3 -m askai -r rag "${args[@]}" 2>&1 || quit 2

  quit 0
}
