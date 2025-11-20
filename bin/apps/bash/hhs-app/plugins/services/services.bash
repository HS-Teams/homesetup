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
VERSION="1.0.0"

# Namespace cleanup
UNSETS=(
  help version cleanup execute
)

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
      operation                 : start | stop | restart | status.
      service_name              : Target service (required except when listing all statuses).

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

# @param $1 [Req]: operation (start, stop, restart, status)
# @param $2 [Req]: service name
# @purpose: Run a service command based on OS and method
function manage_service() {
  local action="${1}" service="${2}" os

  os="$(detect_os)"

  case "${os}" in
    darwin) brew services "${action}" "${service}" &>/dev/null ;;
    alpine) rc-service "${service}" "${action}" &>/dev/null ;;
    debian|fedora|centos) systemctl "${action}" "${service}" &>/dev/null ;;
    *) quit 1 "Unsupported OS: ${os}" ;;
  esac

  return $?
}

# @param $1 [Opt]: service filter (case-insensitive)
# @purpose: List all services with standardized indexed, dot-padded and colorized status
function list_services_status() {
  local filter="${1:-}" os service status longest=0 line service_entry=""
  local -a raw_services=()
  local i total width service_name padded_line

  os="$(detect_os)"

  # Populate raw_services array
  case "${os}" in
    darwin)
      while IFS= read -r line; do
        raw_services+=("${line}")
      done < <(brew services list | awk 'NR>1 { print $1 ":" $2 }')
      ;;
    alpine)
      while IFS= read -r line; do
        raw_services+=("${line}")
      done < <(rc-status -a | awk '{ print $1 ":" $2 }')
      ;;
    debian|fedora|centos)
      while IFS= read -r line; do
        raw_services+=("${line}")
      done < <(systemctl list-units --type=service --all --no-pager | awk '
        NR>1 && $1 ~ /\.service$/ {
          name=$1;
          sub(/\.service$/, "", name);
          state=$4;
          print name ":" state;
        }')
      ;;
    *)
      quit 2 "Unsupported OS: \"${os}\""
      ;;
  esac

  total="${#raw_services[@]}"
  width="${#total}"  # padding width for index (based on total)

  # First pass: find longest service name (filtered only)
  for line in "${raw_services[@]}"; do
    service="${line%%:*}"
    [[ -n "${filter}" && ! "${service,,}" =~ ${filter,,} ]] && continue
    [[ ${#service} -gt ${longest} ]] && longest=${#service}
  done

  printf -v dash_pad '%*s' $((width + 2 + longest + 10)) ''
  dash_pad=${dash_pad// /-}
  printf "%b\n%b\n" "${WHITE}Service$(printf '%*s' 13 ' ')Status${NC}" "${dash_pad}"

  i=1
  for line in "${raw_services[@]}"; do
    service="${line%%:*}"
    status="${line##*:}"
    [[ -n "${filter}" && ! "${service,,}" =~ ${filter,,} ]] && continue
    printf -v service_entry "%${width}d. %s" "${i}" "${service}"
    while [[ ${#service_entry} -lt $((width + 2 + longest + 3)) ]]; do service_entry+="."; done
    ((i++))
    [[ "${status}" =~ ^(started|running|enabled|active)$ ]] &&
      { printf "%b %b\n" "${HHS_HIGHLIGHT_COLOR}${service_entry}${NC}" "${GREEN} Up${NC}"; continue; }
    printf "%b %b\n" "${HHS_HIGHLIGHT_COLOR}${service_entry}${NC}" "${RED} Down${NC}"
  done
}

# @purpose: HHS plugin required function to route service commands
function execute() {
  local operation="${1:-status}" service="${2:-}" os

  os="$(detect_os)"

  case "${operation}" in
    help)
      help ;;
    version)
      version ;;
    start|stop|restart)
      [[ -z "${service}" ]] && quit 1 "Missing service name."
      echo -en "${YELLOW}${operation^} service \"${service}\"...${NC} "
      manage_service "${operation}" "${service}" && quit 0 "${GREEN}OK${NC}"
      echo -e "${RED}FAILED${NC}"
      quit 2
      ;;
    status)
      echo -e "${YELLOW}Fetching services statuses...${NC}\n"
      list_services_status "${service}"
      ;;
    *)
      echo -e "${RED}Unknown operation: \"${operation}\"\n"
      quit 2 "${YELLOW}${TIP_ICON} Tip: Try one of: start, stop, restart, status${NC}"
      ;;
  esac

  quit 0
}
