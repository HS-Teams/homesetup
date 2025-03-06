#!/usr/bin/env bash
# shellcheck disable=SC1090

#  Script: bash_commons.bash
# Purpose: This file is a set of commonly used functions. Dotfiles sometimes requires the following functions
#          to be available for use. It is sources from the first loaded dotfile.
# Created: Apr 26, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} bash_commons"

# @function: Private function that issues a HomeSetup restart.
function __hhs_restart__() {

  JOB_NAME='HomeSetup restart!' source "${HOME}/.bashrc"
}

# @function: Echo an error message, using red color, into stderr.
# @param $1 [Req] : The application or function name.
# @param $2..$N [Req] : The message to be echoed.
function __hhs_errcho() {

  local app_name="${1:-$$}"

  if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <message>"
    return 1
  fi

  shift

  echo -e "${RED}✘ Fatal: ${WHITE}${app_name} ${POINTER_ICN} ${*}${NC}" 1>&2

  return 0
}

# @function: Check if a command is available on the current shell session.
# @param $1 [Req] : The command to check.
function __hhs_has() {

  local cmd="$1"

  if [[ $# -eq 0 || '-h' == "$1" ]]; then
    echo "usage: ${FUNCNAME[0]} <command>"
    return 1
  fi

  type "${cmd}" &>/dev/null

  return $?
}

# @function: Check if a python module is installed.
# @param $1 [Req] : The python module to check.
function __hhs_has_module() {
  local module="$1"

  if [[ $# -eq 0 || '-h' == "$1" ]]; then
    echo "usage: ${FUNCNAME[0]} <python module/package>"
    return 1
  fi

  pip show "${module}" &>/dev/null

  return $?
}

# @function: Check if HomeSetup venv is active.
function __hhs_is_venv() {

  [[ "${HHS_VENV_PATH}/bin/python3" == "$(command -v python3)" ]] && return 0

  return 1
}

# @function: Make sure HomeSetup venv is active.
# @param $1 [Req] : The application or function name.
function __hhs_ensure_venv() {

  __hhs_is_venv && return 0

  __hhs_errcho "${1:-${FUNCNAME[1]}}" "Not available when HomeSetup python venv is not active!"

  return 1
}

# @function: Log a message to the HomeSetup log file.
# @param $1 [Req] : The log level.
# @param $* [Req] : The log level. One of ["WARN", "DEBUG", "INFO", "ERROR", "ALL"].
function __hhs_log() {

  local level="${1}" message="${2}"

  if [[ $# -lt 2 || '-h' == "$1" ]]; then
    echo "usage: ${FUNCNAME[0]} <log_level> <log_message>"
    return 1
  fi

  case "${level}" in
  'INFO' | 'WARN' | 'ERROR' | 'ALL')
    printf "%s %5.5s  %s\n" "$(date +'%m-%d-%y %H:%M:%S ')" "${level}" "${message}" >>"${HHS_LOG_FILE}"
    ;;
  'DEBUG')
    [[ "${HHS_VERBOSE_LOGS}" -eq 1 ]] &&
      printf "%s %5.5s  %s\n" "$(date +'%m-%d-%y %H:%M:%S ')" "${level}" "${message}" >>"${HHS_LOG_FILE}"
    ;;
  *)
    echo "${FUNCNAME[0]}: invalid log level \"${level}\" !" 2>&1
    return 1
    ;;
  esac

  return 0
}

# @function: Replacement for the original source bash command.
# @param $1 [Req] : Path to the file to be source'd
function __hhs_source() {

  local filepath="$1"

  if [[ $# -eq 0 || '-h' == "$1" ]]; then
    echo "usage: ${FUNCNAME[0]} <filepath>"
  elif [[ ! -s "${filepath}" ]]; then
    __hhs_log "WARN" "${FUNCNAME[0]}: Skipping \"${filepath}\" because it was not found or empty!"
  else
    if source "${filepath}" >>"${HHS_LOG_FILE}"; then
      __hhs_log "DEBUG" "File \"${filepath}\" was loaded !"
      return 0
    else
      __hhs_log "ERROR" "Failed to load file \"${filepath}\"!"
    fi
  fi

  return 1
}

# shellcheck disable=SC2139
# @function: Check if an alias does not exists and create it, otherwise just ignore it. Do not support the use of single quotes in the expression
# @param $1 [Req] : The alias to set/check.
# @param $* [Req] : The alias expression.
function __hhs_alias() {

  local all_args alias_expr alias_name

  if [[ $# -eq 0 || '-h' == "$1" ]]; then
    echo "usage: ${FUNCNAME[0]} <alias_name>='<alias_expr>"
    return 1
  fi

  all_args="${*}"
  alias_expr="${all_args#*=}"
  alias_name="${all_args//=*/}"

  if ! type "$alias_name" >/dev/null 2>&1; then
    if alias "${alias_name}"="${alias_expr}" >/dev/null 2>&1; then
      return 0
    else
      __hhs_errcho "${FUNCNAME[0]}" "Failed to alias: \"${alias_name}\" !" 2>&1
    fi
  else
    __hhs_log "WARN" "Setting alias: \"${alias_name}\" was skipped because it already exists !"
  fi

  return 1
}

# @function: Check whether an URL is reachable.
# @param $1 [Req] : The URL to test reachability.
function __hhs_is_reachable() {
  if [[ $# -eq 0 || '-h' == "$1" || -z "$1" ]]; then
    echo "usage: ${FUNCNAME[0]} <url>"
    return 1
  fi

  \curl --output /dev/null --silent --connect-timeout 1 --max-time 1 --head --fail "${1}"

  return $?
}

if ! __hhs_has 'ised'; then

  # @function: In-place sed.
  # @param $1..$N [Req] : Sed parameters.
  function ised() {
    case "${HHS_MY_OS}" in
    Darwin)
      sed -i '' -E "${@}"
      ;;
    Linux)
      sed -i'' -r "${@}"
      ;;
    esac

    return $?
  }

fi

if ! __hhs_has 'esed'; then

  # @function: Regex sed. Same as sed -r.
  # @param $1..$N [Req] : Sed parameters.
  function esed() {
    case "${HHS_MY_OS}" in
    Darwin)
      sed -E "${@}"
      ;;
    Linux)
      sed -r "${@}"
      ;;
    esac

    return $?
  }

fi

# @purpose: `trim' all leading and trailing whitespaces.
# @param $1..$N [Req] : The text to be trimmed.
function trim() {

  file=${1:-/dev/stdin}
  if [[ "${file}" == '/dev/stdin' ]]; then
    while read -r stream; do
      echo -n "${stream}" | esed 's/^[[:blank:]]*|[[:blank:]]*$//g'
    done <"${file}"
  else
    esed 's/^[[:blank:]]*|[[:blank:]]*$//g' "${file}"
  fi

  return 0
}

# @purpose: Check whether the list contains the specified string.
# @param $1 [Req] : The list to check against.
# @param $2 [Req] : The string to be checked.
function list_contains() {
  [[ -z "${1}" || -z "${2}" ]] && return 1
  [[ ${1} =~ (^|[[:space:]])${2}($|[[:space:]]) ]] && return 0

  return 1
}

function __hhs_clean_escapes() {
  sed -E 's/\x1b(\[[0-9;]*[a-zA-Z]|\([a-zA-Z])//g'
}

# @purpose: Copy text to clipboard in a cross-platform manner (macOS & Linux).
function __hhs_clipboard() {
  local cb_copy

  if command -v pbcopy >/dev/null 2>&1; then
    cb_copy='pbcopy'
  elif command -v xclip >/dev/null 2>&1; then
    cb_copy='xclip -selection clipboard'
  elif command -v xsel >/dev/null 2>&1; then
    cb_copy='xsel --clipboard --input'
  elif command -v wl-copy >/dev/null 2>&1; then
    cb_copy='wl-copy'
  else
    __hhs_errcho "${FUNCNAME[0]}" "Clipboard copy not supported. Install xclip, xsel, or wl-copy."
    return 1
  fi
  ${cb_copy}

  return 0
}
