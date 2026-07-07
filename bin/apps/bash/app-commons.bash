#!/usr/bin/env bash
# shellcheck disable=1090,1091

#  Script: app-commons.bash
# Purpose: Commonly used bash code functions and variables
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current application version.
VERSION=${VERSION:-1.0.0}

# This application name.
APP_NAME="${APP_NAME:-${0##*/}}"

# Direct app execution may happen before hhsrc has exported these paths.
HHS_DIR="${HHS_DIR:-${HOME}/.config/hhs}"
HHS_BACKUP_DIR="${HHS_BACKUP_DIR:-${HHS_DIR}/backup}"
HHS_CACHE_DIR="${HHS_CACHE_DIR:-${HHS_DIR}/cache}"
HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"
HHS_LOG_FILE="${HHS_LOG_FILE:-${HHS_LOG_DIR}/hhsrc.log}"
mkdir -p "${HHS_LOG_DIR}" "${HHS_CACHE_DIR}" 2>/dev/null || true

# Help message to be displayed by the application.
if [[ -z "${USAGE:-}" ]]; then
  read -r -d '' USAGE <<EOF
usage: ${APP_NAME} <arguments> [options]
    Common application helpers for HomeSetup scripts.

    options:
      -h | --help             : Display this help message.
      -v | --version          : Display program version.

    arguments:
      arguments               : Script-specific positional arguments.

    examples:
      Show help for an app using the shared options:
        => ${APP_NAME} --help

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

EOF
fi

# Default identifiers to be unset
UNSETS=('quit' 'usage' 'version' 'trim')

# @purpose: Source a HomeSetup dotfile from the checkout or installed home.
# @param $1 [Req] : The dotfile basename without leading dot or .bash suffix.
function source_hhs_dotfile() {
  local dotfile_name="$1"
  local checkout_file="${HHS_HOME:-}/dotfiles/bash/${dotfile_name}.bash"
  local installed_file="${HOME}/.${dotfile_name}"

  if [[ -s "${checkout_file}" ]]; then
    source "${checkout_file}"
  elif [[ -s "${installed_file}" ]]; then
    source "${installed_file}"
  fi
}

# Save currently active dotfiles.
OLD_DOTFILES=("${HHS_ACTIVE_DOTFILES:-}")
# Unset to allow sourcing them again
unset HHS_ACTIVE_DOTFILES

# We need to load the dotfiles below due to non-interactive shell.
source_hhs_dotfile bash_commons
source_hhs_dotfile bash_env
source_hhs_dotfile bash_aliases
source_hhs_dotfile bash_colors
source_hhs_dotfile bash_functions
source_hhs_dotfile bash_icons

# Re-export active dotfiles.
export HHS_ACTIVE_DOTFILES="${OLD_DOTFILES[*]}"

# Execute a cleanup after the application has exited.
trap _app_cleanups_ EXIT

# @purpose: When the application has exited, execute some cleanups.
function _app_cleanups_() {
  # Unset all declared functions
  unset -f quit usage version trim list_contains toml_get_key source_hhs_dotfile
  unset -f "${UNSETS[*]}"
}

# @purpose: Exit the application with the provided exit code and exhibits an exit message if provided.
# @param $1 [Req] : The exit return code. 0 = SUCCESS, 1 = FAILURE, * = ERROR .
# @param $2 [Opt] : The exit message to be displayed.
function quit() {

  local msg exit_code=${1:-0}

  shift
  msg="${*}"

  [[ ${exit_code} -ne 0 && -n "${msg}" ]] && __hhs_errcho "${APP_NAME}" "${msg}${NC}\n" 1>&2
  [[ ${exit_code} -eq 0 && -n "${msg}" ]] && echo -e "${msg} \n" 1>&2

  exit "${exit_code}"
}

# @purpose: Display the usage message and exit with the provided code ( or zero as default ).
# @param $1 [Req] : The exit return code. 0 = SUCCESS, 1 = FAILURE .
# @param $2 [Opt] : The exit message to be displayed.
function usage() {

  local exit_code=${1:-1}

  shift && echo -e "${USAGE}"
  [[ ${#} -gt 0 ]] && echo ''
  quit "${exit_code}" "$@"
}

# @purpose: Display the current application version and exit.
function version() {
  quit 0 "${APP_NAME} v${VERSION}"
}

# Check if the user passed the help or version parameters.
[[ "$1" = '-h' || "$1" = '--help' ]] && usage 0
[[ "$1" = '-v' || "$1" = '--version' ]] && version
