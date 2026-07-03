#!/usr/bin/env bash
# shellcheck disable=2181,2034

#  Script: services.bash
# Purpose: Contains all HHS service management functions
# Created: Nov 19, 2025
#  Author: Hugo Saporetti Junior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="services"

# Current hhs services version
VERSION="1.0.1"

# Namespace cleanup
UNSETS=(
  help version cleanup execute detect_os service_manager lowercase is_hhs_streamlit_ui_running add_hhs_services
  manage_service service_status_manager service_status_is_up service_matches_filter list_services_status
)

# Streamlit UI port.
HHS_STREAMLIT_UI_PORT="${HHS_STREAMLIT_UI_PORT:-18501}"

# Usage message
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} <operation> [service_name] [options]
                     _
 ___  ___ _ ____   _(_) ___ ___  ___
/ __|/ _ \\ '__\\ \\ / / |/ __/ _ \\/ __|
\\__ \\  __/ |   \\ V /| | (_|  __/\\__ \\
|___/\\___|_|    \\_/ |_|\\___\\___||___\\/...${HHS_MY_OS_RELEASE}

  HomeSetup services v${VERSION}.

    options:
      -h | --help               : Display this help message.
      -v | --version            : Display current plugin version.

    arguments:
      operation                 : start | stop | restart | status | service filter.
      service_name              : Target service (required for start, stop, and restart).

    examples:
      Check status for all services:
        => ${APP_NAME} ${PLUGIN_NAME} status
      Restart a specific service:
        => ${APP_NAME} ${PLUGIN_NAME} restart sshd

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - Commands adapt to the current OS service manager (brew, rc-service, systemctl).

EOF

[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# @purpose: Print usage message
function help() {
  usage 0
}

# @purpose: Print plugin version
function version() {
  echo "HomeSetup ${PLUGIN_NAME} plugin v${VERSION}"
  quit 0
}

# @purpose: Clean up plugin functions
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# @purpose: Detect the underlying OS (alpine, debian, fedora, centos, darwin)
function detect_os() {
  local os=""

  if [[ "$(uname)" == "Darwin" ]]; then
    os="darwin"
  elif [[ -f /etc/alpine-release ]]; then
    os="alpine"
  elif [[ -f /etc/os-release ]]; then
    . /etc/os-release
    case "${ID}" in
      ubuntu|debian) os="debian" ;;
      fedora)        os="fedora" ;;
      centos|rhel)   os="centos" ;;
    esac
  fi

  echo "${os}"
}

# @param $1 [Req]: detected OS
# @purpose: Return the service manager executable for the current OS.
function service_manager() {
  local os="${1}" manager=""

  case "${os}" in
    darwin)
      manager="$(command -v brew 2>/dev/null || true)"
      [[ -z "${manager}" && -x /opt/homebrew/bin/brew ]] && manager="/opt/homebrew/bin/brew"
      [[ -z "${manager}" && -x /usr/local/bin/brew ]] && manager="/usr/local/bin/brew"
      ;;
    alpine)
      manager="$(command -v rc-service 2>/dev/null || true)"
      ;;
    debian|fedora|centos)
      manager="$(command -v systemctl 2>/dev/null || true)"
      ;;
  esac

  [[ -n "${manager}" ]] || quit 1 "Service manager not found for OS: ${os}"
  echo "${manager}"
}

# @param $1 [Req]: detected OS
# @purpose: Return the service status executable for the current OS.
function service_status_manager() {
  local os="${1}" manager=""

  case "${os}" in
    darwin|debian|fedora|centos)
      manager="$(service_manager "${os}")" || return $?
      ;;
    alpine)
      manager="$(command -v rc-status 2>/dev/null || true)"
      ;;
  esac

  [[ -n "${manager}" ]] || quit 1 "Service status manager not found for OS: ${os}"
  echo "${manager}"
}

# @param $1 [Req]: Value to lowercase.
# @purpose: Lowercase text in a Bash 3 compatible way.
function lowercase() {
  printf '%s' "${1}" | tr '[:upper:]' '[:lower:]'
}

# @param $1 [Req]: service status
# @purpose: Return whether a service status should be displayed as up.
function service_status_is_up() {
  [[ "$(lowercase "${1}")" =~ ^(started|running|enabled|active)$ ]]
}

# @param $1 [Req]: service name
# @param $2 [Req]: service status
# @param $3 [Opt]: service name or status filter
# @purpose: Return whether a service entry matches the selected filter.
function service_matches_filter() {
  local service_lc status_lc filter_lc

  service_lc="$(lowercase "${1}")"
  status_lc="$(lowercase "${2}")"
  filter_lc="$(lowercase "${3:-}")"

  case "${filter_lc}" in
    ""|all)
      return 0
      ;;
    up|started|running|enabled|active)
      service_status_is_up "${status_lc}"
      return $?
      ;;
    down|stopped|inactive|disabled|dead)
      service_status_is_up "${status_lc}"
      [[ $? -ne 0 ]]
      return $?
      ;;
    *)
      [[ "${service_lc}" == *"${filter_lc}"* ]]
      return $?
      ;;
  esac
}

# @purpose: Check whether the HomeSetup Streamlit UI port is accepting connections.
function is_hhs_streamlit_ui_running() {
  python3 - "${HHS_STREAMLIT_UI_PORT}" <<'PY' &>/dev/null
import socket
import sys

port = int(sys.argv[1])
with socket.create_connection(("127.0.0.1", port), timeout=0.2):
    pass
PY
}

# @purpose: Add HomeSetup-managed services to the service status list.
function add_hhs_services() {
  if is_hhs_streamlit_ui_running; then
    raw_services+=("homesetup-ui:running")
  else
    raw_services+=("homesetup-ui:stopped")
  fi
}

# @param $1 [Req]: operation (start, stop, restart, status)
# @param $2 [Req]: service name
# @purpose: Run a service command based on OS and method
function manage_service() {
  local action="${1}" service="${2}" os manager

  os="$(detect_os)"
  manager="$(service_manager "${os}")" || return $?

  case "${os}" in
    darwin)
      case "${action}" in
        start) "${manager}" services start "${service}" ;;
        stop) "${manager}" services stop "${service}" ;;
        restart)
          "${manager}" services stop "${service}" &&
            "${manager}" services start "${service}"
          ;;
        *) "${manager}" services "${action}" "${service}" ;;
      esac
      ;;
    alpine) "${manager}" "${service}" "${action}" ;;
    debian|fedora|centos) "${manager}" "${action}" "${service}" ;;
    *) quit 1 "Unsupported OS: ${os}" ;;
  esac

  return $?
}

# @param $1 [Opt]: service filter (case-insensitive)
# @purpose: List all services with standardized indexed, dot-padded and colorized status
function list_services_status() {
  local filter="${1:-}" os service status longest=0 line service_entry="" manager
  local -a raw_services=()
  local i total width service_name padded_line

  os="$(detect_os)"
  manager="$(service_status_manager "${os}")" || return $?

  # Populate raw_services array
  case "${os}" in
    darwin)
      while IFS= read -r line; do
        raw_services+=("${line}")
      done < <("${manager}" services list | awk 'NR>1 { print $1 ":" $2 }')
      ;;
    alpine)
      while IFS= read -r line; do
        raw_services+=("${line}")
      done < <("${manager}" -a | awk '
        /\[/ {
          status=$0;
          sub(/^.*\[ */, "", status);
          sub(/ *\].*$/, "", status);
          print $1 ":" status;
        }')
      ;;
    debian|fedora|centos)
      while IFS= read -r line; do
        raw_services+=("${line}")
      done < <("${manager}" list-units --type=service --all --no-pager | awk '
        NR>1 && $1 ~ /\.service$/ {
          name=$1;
          sub(/\.service$/, "", name);
          state=$3;
          print name ":" state;
        }')
      ;;
    *)
      quit 2 "Unsupported OS: \"${os}\""
      ;;
  esac

  add_hhs_services

  total="${#raw_services[@]}"
  width="${#total}"  # padding width for index (based on total)

  # First pass: find longest service name (filtered only)
  for line in "${raw_services[@]}"; do
    service="${line%%:*}"
    status="${line##*:}"
    service_matches_filter "${service}" "${status}" "${filter}" || continue
    [[ ${#service} -gt ${longest} ]] && longest=${#service}
  done

  printf -v dash_pad '  %*s  ' $((width + 2 + longest + 10)) ''
  dash_pad=${dash_pad// /-}
  printf "  %b\n%b\n" "${WHITE}Service$(printf '%*s' 13 ' ')Status${NC}" "${dash_pad}"

  i=1
  for line in "${raw_services[@]}"; do
    service="${line%%:*}"
    status="${line##*:}"
    service_matches_filter "${service}" "${status}" "${filter}" || continue
    printf -v service_entry "%${width}d: %s" "${i}" "${service}"
    while [[ ${#service_entry} -lt $((width + 2 + longest + 3)) ]]; do service_entry+="."; done
    ((i++))
    service_status_is_up "${status}" &&
      { printf "  %b %b\n" "${HHS_HIGHLIGHT_COLOR}${service_entry}${NC}" "${GREEN} Up${NC}"; continue; }
    printf "  %b %b\n" "${HHS_HIGHLIGHT_COLOR}${service_entry}${NC}" "${RED} Down${NC}"
  done
}

# @purpose: HHS plugin required function to route service commands
function execute() {
  local operation="${1:-status}" service="${2:-}"

  case "${operation}" in
    -h|--help|help)
      help ;;
    -v|--version|version)
      version ;;
    start|stop|restart)
      [[ -z "${service}" ]] && quit 1 "Missing service name."
      echo -en "${YELLOW}${operation^} service \"${service}\"...${NC} "
      manage_service "${operation}" "${service}" && quit 0 "${GREEN}OK${NC}"
      echo -e "${RED}FAILED${NC}"
      quit 1
      ;;
    status)
      echo -e "${YELLOW}Fetching services statuses...${NC}\n"
      list_services_status "${service}"
      ;;
    -*)
      usage 1 "Invalid ${PLUGIN_NAME} option: \"${operation}\" !"
      return $?
      ;;
    *)
      echo -e "${YELLOW}Fetching services statuses...${NC}\n"
      list_services_status "${operation}"
      ;;
  esac

  quit 0
}
