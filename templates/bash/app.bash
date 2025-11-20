#!/usr/bin/env bash
# shellcheck disable=SC2317

#  Script: ${app.name}.bash
# Purpose: ${app.purpose}
# Created: Mon DD, YYYY
#  Author: ${author}
#  Mailto: ${author.mail}
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>

# Current application version.
VERSION=${VERSION:-1.0.0}

# This application name.
APP_NAME="${APP_NAME:-${0##*/}}"

# Help message to be displayed by the application.
USAGE=${USAGE:-"
usage: ${APP_NAME} <arguments> [options]
"}

# Default identifiers to be unset
UNSETS=('quit' 'usage' 'version' 'parse_args' 'cleanup')

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

  local exit_code=${1:-0}

  shift && echo -en "${USAGE}"
  [[ ${#} -gt 0 ]] && echo ''
  quit "${exit_code}" "$@"
}

# @purpose: Display the current application version and exit.
function version() {
  quit 0 "$APP_NAME v$VERSION"
}

# ------------------------------------------
# Basics

# @purpose: Parse command line arguments
function parse_args() {

  # If not enough arguments is passed, display usage message
  if [[ ${#} -lt 1 ]]; then
    usage 0
  fi

  # Loop through the command line options.
  # Short opts: -<C>, Long opts: --<Word>
  while [[ ${#} -gt 0 ]]; do
    case "$1" in
    -h | --help)
      usage
      ;;
    -v | --version)
      version
      ;;

    *)
      break
      ;;
    esac
    shift
  done
}

# @purpose: Cleanup procedures.
function cleanup() {
  unset -f "${UNSETS[@]}"
}

# @purpose: Program entry point
main() {

  # Execute a cleanup after the application has exited.
  trap cleanup EXIT

  echo "Executing ${APP_NAME} ..."
  parse_args "${@}"
  echo "
  ARG_NUM: ${#}
  ARGUMENTS: ${*}
  "
}

main "${@}"
quit 1
