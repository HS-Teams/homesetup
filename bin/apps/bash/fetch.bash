#!/usr/bin/env bash
# shellcheck disable=2034

#  Script: fetch.bash
# Purpose: Fetch URL resource using the most commons ways.
# Created: Oct 24, 2018
#  Author: Taius
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# https://semver.org/; major.minor.patch
VERSION="1.1.2"

# Application name.
APP_NAME="$(basename "$0")"

# Help message to be displayed by the application.
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} <method> <url> [options]
    Fetch a URL using curl with optional headers, body, and formatting.

    options:
      -b | --body <json_body>       : HTTP request body (payload).
      -f | --format                 : Pretty-print JSON responses when possible.
      -H | --headers <headers>      : Comma-separated HTTP request headers.
      -s | --silent                 : Omit informational messages.
      -t | --timeout <seconds>      : Request timeout (default: 3).
      -h | --help                   : Display this help message.
      -v | --version                : Print version information.

    arguments:
      method                        : HTTP method [GET, HEAD, POST, PUT, PATCH, DELETE].
      url                           : Target URL for the request.

    examples:
      Fetch a page silently and format JSON:
        => ${APP_NAME} -s -f GET https://example.com
      Send JSON payload with custom header:
        => ${APP_NAME} --headers "Accept: application/json" --body '{"x":1}' POST https://api.site.com

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - The request is executed with curl and honors the provided timeout.

EOF

# Functions to be unset after quit.
UNSETS=(
  parse_args trim_whitespace fetch_with_curl do_fetch main
)

# Common application functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -s "${HHS_DIR:-}/bin/app-commons.bash" ]]; then
  source "${HHS_DIR}/bin/app-commons.bash"
elif [[ -s "${SCRIPT_DIR}/app-commons.bash" ]]; then
  source "${SCRIPT_DIR}/app-commons.bash"
fi

# Request timeout in seconds (default is 10).
REQ_TIMEOUT=10

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

# HTTP Method.
METHOD=

# Site URL.
URL=

# @purpose: Trim leading and trailing whitespace.
# @param $1 [Req]: String to trim
trim_whitespace() {
  local trimmed
  trimmed="$(printf '%s' "${1}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  printf '%s' "${trimmed}"
}

# @purpose: Convert text to uppercase using Bash 3-compatible syntax.
# @param $1 [Req]: Text to convert
uppercase_text() {
  printf '%s' "${1}" | tr '[:lower:]' '[:upper:]'
}

# @purpose: Ensure that a required argument is provided
# @param $1 [Req]: Argument value
require_arg() {
  if [[ -z "${1}" || "${1}" == -* ]]; then
    __hhs_errcho "${APP_NAME}" "Missing required argument." >&2
    quit 1
  fi
  printf '%s' "${1}"
}

# @purpose: Validate the HTTP method
# @param $1 [Req]: The HTTP method
validate_method() {
  local method
  method="$(uppercase_text "${1}")"
  [[ -z "${METHOD}" ]] && \
    __hhs_errcho "${APP_NAME}" "Missing required argument <method>" && quit 1
  case "${method}" in
    GET|HEAD|POST|PUT|PATCH|DELETE) return 0 ;;
    *)
      __hhs_errcho "${APP_NAME}" "Invalid HTTP method: ${method}"
      quit 1
      ;;
  esac
}

# @purpose: Validate the URL format
# @param $1 [Req]: The URL
validate_url() {
  local url="${1}"
    # Validate required args
  [[ ${#args[@]} -lt 2 ]] && \
    __hhs_errcho "${APP_NAME}" "Missing required argument <url>." && quit 1
  if [[ "${url}" =~ ^https?:// ]]; then
    return 0
  else
    __hhs_errcho "${APP_NAME}" "Invalid URL: %s" "${url}"
    quit 1
  fi
}

# @purpose: Parse CLI arguments (short and long options supported)
# @param $@ [Req]: All arguments passed to script
parse_args() {
  local args header oldifs

  declare -a args=()

  while [[ $# -gt 0 ]]; do
    arg="$1"; shift

    case "${arg}" in
      -b|--body)
        [[ -z "$1" || "$1" == -* || "$1" =~ ^(GET|POST|PUT|PATCH|DELETE|HEAD)$ ]] && \
          __hhs_errcho "${APP_NAME}" "--body requires a value." && quit 1
        BODY="$1"
        shift
        ;;
      -H|--headers)
        [[ -z "$1" || "$1" == -* || "$1" =~ ^(GET|POST|PUT|PATCH|DELETE|HEAD)$ ]] && \
          __hhs_errcho "${APP_NAME}" "--headers requires a value." && quit 1
        HEADERS="$1"
        shift
        ;;
      -t|--timeout)
        [[ -z "$1" || "$1" =~ ^[0-9]+$ ]] || {
          __hhs_errcho "${APP_NAME}" "--timeout requires a numeric value."
          quit 1
        }
        REQ_TIMEOUT="$1"
        shift
        ;;
      -f|--format) FORMAT=true ;;
      -s|--silent) SILENT=true ;;
      -h|--help) usage 0 ;;
      -v|--version) version ; quit 0 ;;
      -*) __hhs_errcho "${APP_NAME}" "Unknown option: '${1}'" && usage 1 ;;
      *) args+=("${arg}") ;;
    esac
  done

  [[ ${#args[@]} -eq 0 ]] && \
    __hhs_errcho "${APP_NAME}" "Missing required arguments <method> and <url>" && usage 1

  # Positional arguments
  METHOD="$(trim_whitespace "${args[0]}")"
  URL="$(trim_whitespace "${args[1]}")"

  if [[ -n "${HEADERS}" ]]; then
    oldifs="${IFS}"
    IFS=','
    for header in ${HEADERS}; do
      header="$(trim_whitespace "${header}")"
      [[ -n "${header}" ]] && HEADER_ARGS+=('-H' "${header}")
    done
    IFS="${oldifs}"
  fi

  validate_method "${METHOD}"
  validate_url "${URL}"
}

# @purpose: Run curl request using constructed args
# @purpose: Run curl request using constructed args, no tempfile
fetch_with_curl() {
  local status http_status curl_opts response response_len ret_val=1

  curl_opts=(
    '--silent' '--fail' '--location'
    '--max-time' "${REQ_TIMEOUT}"
    '--write-out' '%{http_code}'
  )

  local -a curl_cmd=("curl" "${curl_opts[@]}" '-X' "${METHOD}")

  [[ -n "${BODY}" ]] && curl_cmd+=('-d' "${BODY}")
  [[ ${#HEADER_ARGS[@]} -gt 0 ]] && curl_cmd+=("${HEADER_ARGS[@]}")
  curl_cmd+=("${URL}")

  # Run curl and capture both response and status code in one go
  response="$("${curl_cmd[@]}" 2>/dev/null)"
  status=$?
  response_len="${#response}"
  if [[ ${response_len} -ge 3 ]]; then
    http_status="${response:$((response_len - 3)):3}"
    RESPONSE="${response:0:$((response_len - 3))}"
  else
    http_status=0
    RESPONSE="${response}"
  fi
  STATUS="${http_status}"

  case "${status}" in
    28) __hhs_errcho "${APP_NAME}" "Request timed out after ${REQ_TIMEOUT}s." && quit 2 ;;
    52) __hhs_errcho "${APP_NAME}" "Server responded with no data." && quit 2 ;;
    0)  [[ ${STATUS} -ge 200 && ${STATUS} -lt 400 ]] && ret_val=0;;
    *)  ret_val=1 ;;
  esac

  return $ret_val
}

# @purpose: Program entry point
main() {
  parse_args "$@"

  case "${METHOD}" in
    GET|HEAD|DELETE)
      [[ -n "${BODY}" ]] && {
        __hhs_errcho "${APP_NAME}" "${METHOD} does not accept a request body" >&2
        quit 1
      }
      ;;
    POST|PUT|PATCH)
      [[ -z "${BODY}" ]] && {
        __hhs_errcho "${APP_NAME}"  "${METHOD} requires a body (--body)" >&2
        quit 1
      }
      ;;
  esac

  [[ -z "${SILENT}" ]] && echo -e "Fetching: ${METHOD} ${HEADERS} ${URL} ..."

  if fetch_with_curl; then
    if [[ -n "${FORMAT}" ]]; then
      command -v jq >/dev/null && printf '%s' "${RESPONSE}" | __hhs_json_print '.' || echo "${RESPONSE}"
    else
      [[ -n "${RESPONSE}" ]] && echo "${RESPONSE}"
    fi
    quit 0
  else
    if [[ -z "${SILENT}" ]]; then
      quit 1 "1 Failed to process request: (Status=${STATUS}) => [resp:${RESPONSE:-<empty>}]"
    else
      echo "${RET_VAL}" 1>&2
    fi
    quit 1 "${APP_NAME} 2 Failed to execute the \"${METHOD}\" request to \"${URL}\"."
  fi
}

main "$@"
quit 1 "${APP_NAME} 3 Failed to execute the \"${METHOD}\" request to \"${URL}\"."
