#!/usr/bin/env bash
# shellcheck disable=2034

#  Script: fetch.bash
# Purpose: Fetch URL resource using the most commons ways.
# Created: Oct 24, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current script version.
VERSION=1.0.0

# Application name.
APP_NAME="$(basename "$0")"

# Help message to be displayed by the application.
USAGE="usage: ${APP_NAME} <method> [options] <url>

  Fetch URL resource using the most commons ways.

    Arguments:

        method                      : The http method to be used [ GET, HEAD, POST, PUT, PATCH, DELETE ].
        url                         : The url to make the request.

    Options:
        --headers <header_list>     : Comma-separated http request headers.
        --body    <json_body>       : The http request body (payload).
        --format                    : Pretty-print the JSON response when possible.
        --silent                    : Omits all informational messages.
"

# Functions to be unset after quit.
UNSETS=(
  format_json trim_whitespace fetch_with_curl parse_args do_fetch main
)

# Common application functions.
[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

if ! declare -f format_json >/dev/null; then
  # @purpose: Pretty-print JSON payloads when formatting is requested.
  function format_json() {
    local input
    input="$(cat)"

    if command -v jq >/dev/null 2>&1; then
      printf '%s' "${input}" | jq . 2>/dev/null || printf '%s\n' "${input}"
    elif command -v python3 >/dev/null 2>&1; then
      printf '%s' "${input}" | python3 -m json.tool 2>/dev/null || printf '%s\n' "${input}"
    elif command -v python >/dev/null 2>&1; then
      printf '%s' "${input}" | python -m json.tool 2>/dev/null || printf '%s\n' "${input}"
    else
      printf '%s\n' "${input}"
    fi
  }
fi

# Request timeout in seconds.
REQ_TIMEOUT=3

# Execution return code.
RET_VAL=0

# Provided request headers (for display).
HEADERS=

# Expanded curl header arguments.
HEADER_ARGS=()

# Provided request body.
BODY=

# Provide a silent request/RESPONSE.
SILENT=

# Whether to format the response body as JSON.
FORMAT=

# Response body.
RESPONSE=

# Http status code.
STATUS=0

# @purpose: Trim leading and trailing whitespace.
function trim_whitespace() {
  local trimmed
  trimmed="$(printf '%s' "${1}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  printf '%s' "${trimmed}"
}

# @purpose: Do the request according to the method
function fetch_with_curl() {

  aux=$(mktemp)

  curl_opts=(
    '-s' '--fail' '-L' '--output' "${aux}" '-m' "${REQ_TIMEOUT}" '--write-out' "%{http_code}"
  )

  local -a curl_cmd=("curl" "${curl_opts[@]}" '-X' "${METHOD}")

  if [[ -n "${BODY}" ]]; then
    curl_cmd+=('-d' "${BODY}")
  fi

  if [[ ${#HEADER_ARGS[@]} -gt 0 ]]; then
    curl_cmd+=("${HEADER_ARGS[@]}")
  fi

  curl_cmd+=("${URL}")

  STATUS=$("${curl_cmd[@]}")

  if [[ -s "${aux}" ]]; then
    RESPONSE=$(grep . --color=none "${aux}")
    \rm -f "${aux}"
  fi

  if [[ ${STATUS} -ge 200 && ${STATUS} -lt 400 ]]; then
    RET_VAL=0
  else
    RET_VAL=1
  fi

  return $RET_VAL
}

# ------------------------------------------
# Basics

# @purpose: Parse command line arguments
parse_args() {

  [[ $# -lt 2 ]] && usage 1

  shopt -s nocasematch
  case "${1}" in
    'GET' | 'HEAD' | 'POST' | 'PUT' | 'PATCH' | 'DELETE')
      METHOD="$(tr '[:lower:]' '[:upper:]' <<< "${1}")"
      shift
      ;;
    *) quit 2 "Method \"${1}\" is not not valid!" ;;
  esac
  shopt -u nocasematch

  # Loop through the command line options.
  while test -n "$1"; do
    case "$1" in
      --headers)
        shift
        HEADER_ARGS=()
        HEADERS=""
        if [[ -n "${1}" ]]; then
          IFS=',' read -ra header_values <<< "${1}"
          for next in "${header_values[@]}"; do
            header_trimmed="$(trim_whitespace "${next}")"
            if [[ -n "${header_trimmed}" ]]; then
              HEADER_ARGS+=('-H' "${header_trimmed}")
              HEADERS+=" -H ${header_trimmed}"
            fi
          done
        fi
        ;;
      --body)
        shift
        BODY="$1"
        ;;
      --format)
        FORMAT=1
        ;;
      --silent)
        SILENT=1
        ;;
      *)
        URL="$*"
        break
        ;;
    esac
    shift
  done
}

# @purpose: Fetch the url using the most common ways.
do_fetch() {
  fetch_with_curl
  return $?
}

# @purpose: Program entry point
main() {

  parse_args "${@}"

  case "${METHOD}" in
    'GET' | 'HEAD' | 'DELETE')
      [[ -n "${BODY}" ]] && quit 1 "${METHOD} does not accept a body"
      ;;
    'PUT' | 'POST' | 'PATCH')
      [[ -z "${BODY}" ]] && quit 1 "${METHOD} requires a body"
      ;;
  esac

  [[ -z "${SILENT}" ]] && echo -e "Fetching: ${METHOD} ${HEADERS} ${URL} ..."

  if do_fetch; then
    if [[ -n "${FORMAT}" ]]; then
      printf '%s' "${RESPONSE}" | format_json
    else
      echo "${RESPONSE}"
    fi
    quit 0
  else
    if [[ -z "${SILENT}" ]]; then
      msg="Failed to process request: (Status=${STATUS})"
      __hhs_errcho "${APP_NAME}" "${msg} => [resp:${RESPONSE:-<empty>}]"
    else
      echo "${RET_VAL}" 1>&2
      quit 0
    fi
  fi
}

main "${@}"
quit 1
