#!/usr/bin/env bash
# shellcheck disable=SC2034

#  Script: ui.bash
# Purpose: HomeSetup Streamlit UI launcher.
# Created: Jun 25, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

# Current plugin name.
PLUGIN_NAME="ui"

# Current HomeSetup UI plugin version.
VERSION="0.0.4"

# Namespace cleanup.
UNSETS=(
  help version cleanup execute get_ui_url get_ui_log get_ui_pid_file is_ui_running
  get_ui_process_registry_file open_ui ui_pids ui_port_pids ui_recorded_processes ui_recorded_pids
  ui_process_token ui_pid_command_name ui_pid_args ui_pid_env is_python_or_streamlit_pid
  is_owned_ui_pid ui_known_pids ui_tracked_processes_alive is_managed_ui_running new_ui_owner_token
  record_ui_process cleanup_ui_process_files status_ui stop_ui validate_safe_streamlit_args start_ui
  restart_ui launch_ui validate_ui_runtime
)

# Streamlit UI application path.
STREAMLIT_UI="${HHS_HOME}/bin/apps/py/hhs_ui/streamlit_ui.py"

# Streamlit UI port.
HHS_STREAMLIT_UI_PORT="${HHS_STREAMLIT_UI_PORT:-18501}"

# HomeSetup UI pid file.
HHS_STREAMLIT_UI_PID_FILE="${HHS_STREAMLIT_UI_PID_FILE:-${HHS_DIR}/.streamlit-ui.pid}"

# HomeSetup UI process registry file.
HHS_STREAMLIT_UI_PROCESS_FILE="${HHS_STREAMLIT_UI_PROCESS_FILE:-${HHS_DIR}/.streamlit-ui.processes}"

# Usage message.
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} execute ${PLUGIN_NAME} [command] [options]

  HomeSetup Streamlit UI launcher v${VERSION}.

    commands:
      start                      : Start the UI if it is not already running.
      status                     : Show whether the UI is running.
      stop                       : Stop the running UI process.
      restart                    : Stop and start the UI.

    options:
      -h | --help                : Display this help message.
      -v | --version             : Display current plugin version.

    arguments:
      args                       : Optional arguments passed to Streamlit start/restart.

    examples:
      Open HomeSetup UI, starting it first if needed:
        => ${APP_NAME} execute ${PLUGIN_NAME}
      Start HomeSetup UI without restarting an existing process:
        => ${APP_NAME} execute ${PLUGIN_NAME} start
      Restart HomeSetup UI:
        => ${APP_NAME} execute ${PLUGIN_NAME} restart
      Show HomeSetup UI status:
        => ${APP_NAME} execute ${PLUGIN_NAME} status
      Launch HomeSetup UI on another port:
        => HHS_STREAMLIT_UI_PORT=18502 ${APP_NAME} execute ${PLUGIN_NAME}

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - The HomeSetup Python virtual environment must be active.
    - The UI port is controlled by HHS_STREAMLIT_UI_PORT.

EOF

[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# @purpose: HHS plugin required function.
function help() {
  usage 0
}

# @purpose: HHS plugin required function.
function version() {
  echo "HomeSetup ${PLUGIN_NAME} plugin v${VERSION}"
  quit 0
}

# @purpose: HHS plugin required function.
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# @purpose: Get the HomeSetup Streamlit UI URL.
function get_ui_url() {
  echo "http://localhost:${HHS_STREAMLIT_UI_PORT}"
}

# @purpose: Get the HomeSetup Streamlit UI log file.
function get_ui_log() {
  echo "${HHS_LOG_DIR}/streamlit-ui.log"
}

# @purpose: Get the HomeSetup Streamlit UI pid file.
function get_ui_pid_file() {
  echo "${HHS_STREAMLIT_UI_PID_FILE}"
}

# @purpose: Get the HomeSetup Streamlit UI process registry file.
function get_ui_process_registry_file() {
  echo "${HHS_STREAMLIT_UI_PROCESS_FILE}"
}

# @purpose: Check whether the HomeSetup Streamlit UI port is accepting connections.
function is_ui_running() {
  python3 - "${HHS_STREAMLIT_UI_PORT}" <<'PY' &>/dev/null
import socket
import sys

port = int(sys.argv[1])
with socket.create_connection(("127.0.0.1", port), timeout=0.2):
    pass
PY
}

# @purpose: Print HomeSetup Streamlit UI process IDs for the configured script and port.
function ui_pids() {
  ps -eo pid=,args= 2>/dev/null | awk -v script="${STREAMLIT_UI}" -v port="${HHS_STREAMLIT_UI_PORT}" '
    index($0, "streamlit run") && index($0, script) && index($0, "--server.port " port) {
      print $1
    }
  '
}

# @purpose: Print process IDs listening on the configured HomeSetup Streamlit UI port.
function ui_port_pids() {
  if __hhs_has lsof; then
    lsof -nP -tiTCP:"${HHS_STREAMLIT_UI_PORT}" -sTCP:LISTEN 2>/dev/null
    return 0
  fi

  ps -eo pid=,args= 2>/dev/null | awk -v port="${HHS_STREAMLIT_UI_PORT}" '
    index($0, "streamlit run") && index($0, "--server.port " port) {
      print $1
    }
  '
}

# @purpose: Print HomeSetup Streamlit UI process records created by the launcher.
function ui_recorded_processes() {
  local pid_file process_file

  pid_file="$(get_ui_pid_file)"
  process_file="$(get_ui_process_registry_file)"
  {
    [[ -s "${pid_file}" ]] && awk '{ print $1, $2 }' "${pid_file}"
    [[ -s "${process_file}" ]] && cat "${process_file}"
  } | awk '$1 ~ /^[0-9]+$/ && $2 ~ /^[A-Za-z0-9_.-]+$/ && !seen[$1]++ { print $1, $2 }'
}

# @purpose: Print HomeSetup Streamlit UI process IDs recorded by the launcher.
function ui_recorded_pids() {
  ui_recorded_processes | awk '{ print $1 }'
}

# @purpose: Print the launcher token recorded for a HomeSetup Streamlit UI process ID.
function ui_process_token() {
  local pid="$1"

  ui_recorded_processes | awk -v pid="${pid}" '$1 == pid { print $2; exit }'
}

# @purpose: Print the executable command name for a process ID.
function ui_pid_command_name() {
  ps -p "$1" -o comm= 2>/dev/null | awk 'NR == 1 { sub(/^.*\//, "", $0); print $0 }'
}

# @purpose: Print the command line for a process ID.
function ui_pid_args() {
  ps -p "$1" -o args= 2>/dev/null || true
}

# @purpose: Print the command line and environment for a process ID.
function ui_pid_env() {
  ps eww -p "$1" 2>/dev/null || true
}

# @purpose: Check whether a PID belongs to a Python or Streamlit process.
function is_python_or_streamlit_pid() {
  local command_name first_arg pid_args

  command_name="$(ui_pid_command_name "$1")"
  if [[ -n "${command_name}" ]]; then
    [[ "${command_name}" =~ ^(python([0-9]+(\.[0-9]+)*)?|streamlit)$ ]]
    return
  fi

  pid_args="$(ui_pid_args "$1")"
  first_arg="${pid_args%%[[:space:]]*}"
  first_arg="${first_arg##*/}"
  [[ "${first_arg}" =~ ^(python([0-9]+(\.[0-9]+)*)?|streamlit)$ ]]
}

# @purpose: Check whether a PID is owned by this UI plugin launch.
function is_owned_ui_pid() {
  local args env pid token

  pid="$1"
  [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
  token="$(ui_process_token "${pid}")"
  [[ -n "${token}" ]] || return 1
  kill -0 "${pid}" 2>/dev/null || return 1
  is_python_or_streamlit_pid "${pid}" || return 1

  args="$(ui_pid_args "${pid}")"
  [[ "${args}" == *"-m streamlit run ${STREAMLIT_UI}"* ]] || return 1
  [[ "${args}" == *"--server.port ${HHS_STREAMLIT_UI_PORT}"* ]] || return 1
  [[ "${args}" == *"--server.address 127.0.0.1"* ]] || return 1

  env="$(ui_pid_env "${pid}")"
  [[ "${env}" == *"HHS_STREAMLIT_UI_OWNER=${token}"* ]] || return 1
}

# @purpose: Print every HomeSetup Streamlit UI process ID recorded by the launcher.
function ui_known_pids() {
  ui_recorded_pids | awk '/^[0-9]+$/ && !seen[$1]++'
}

# @purpose: Check whether any tracked HomeSetup Streamlit UI process is still alive.
function ui_tracked_processes_alive() {
  local pid

  while IFS= read -r pid; do
    [[ -z "${pid}" ]] && continue
    is_owned_ui_pid "${pid}" && return 0
  done < <(ui_recorded_pids)

  return 1
}

# @purpose: Check whether the configured UI port is served by a plugin-recorded process.
function is_managed_ui_running() {
  local pid port_pid

  is_ui_running || return 1
  while IFS= read -r port_pid; do
    [[ -z "${port_pid}" ]] && continue
    while IFS= read -r pid; do
      [[ -z "${pid}" ]] && continue
      [[ "${pid}" == "${port_pid}" ]] && is_owned_ui_pid "${pid}" && return 0
    done < <(ui_known_pids)
  done < <(ui_port_pids)

  return 1
}

# @purpose: Generate a launcher ownership token for a HomeSetup Streamlit UI process.
function new_ui_owner_token() {
  printf 'hhs-ui.%s.%s.%s\n' "$$" "${RANDOM}" "$(date +%s 2>/dev/null || echo 0)"
}

# @purpose: Record a HomeSetup Streamlit UI process ID and ownership token.
function record_ui_process() {
  local pid process_file tmp_file token

  pid="$1"
  token="$2"
  [[ "${pid}" =~ ^[0-9]+$ && -n "${token}" ]] || return 1

  process_file="$(get_ui_process_registry_file)"
  mkdir -p "$(dirname "${process_file}")"
  printf '%s %s\n' "${pid}" "${token}" > "$(get_ui_pid_file)"
  printf '%s %s\n' "${pid}" "${token}" >> "${process_file}"

  tmp_file="${process_file}.$$"
  awk '$1 ~ /^[0-9]+$/ && $2 ~ /^[A-Za-z0-9_.-]+$/ && !seen[$1]++ { print $1, $2 }' "${process_file}" > "${tmp_file}" \
    && mv "${tmp_file}" "${process_file}"
}

# @purpose: Remove HomeSetup Streamlit UI process tracking files.
function cleanup_ui_process_files() {
  rm -f "$(get_ui_pid_file)" "$(get_ui_process_registry_file)" 2>/dev/null || true
}

# @purpose: Open the HomeSetup Streamlit UI in the default browser.
function open_ui() {
  local url

  url="$(get_ui_url)"
  echo -e "${GREEN}HomeSetup UI is running at ${BLUE}${url}${NC}"
  __hhs_open "${url}" &>/dev/null || true
}

# @purpose: Print the HomeSetup Streamlit UI runtime status.
function status_ui() {
  local pid pid_file url

  pid_file="$(get_ui_pid_file)"
  url="$(get_ui_url)"
  pid="$(ui_known_pids | head -n 1)"
  [[ -z "${pid}" && -s "${pid_file}" ]] && pid="$(< "${pid_file}")"

  if is_managed_ui_running; then
    if [[ -n "${pid}" ]]; then
      echo -e "${GREEN}HomeSetup UI is running at ${BLUE}${url}${GREEN} (PID: ${pid})${NC}"
    else
      echo -e "${GREEN}HomeSetup UI is running at ${BLUE}${url}${NC}"
    fi
  elif is_ui_running; then
    echo -e "${YELLOW}Port ${HHS_STREAMLIT_UI_PORT} is in use by a process not started by the UI plugin.${NC}"
  else
    echo -e "${YELLOW}HomeSetup UI is stopped on port ${HHS_STREAMLIT_UI_PORT}.${NC}"
  fi
}

# @purpose: Stop the running HomeSetup Streamlit UI process.
function stop_ui() {
  local known_pids pid found=0

  known_pids="$(ui_known_pids)"
  while IFS= read -r pid; do
    [[ -z "${pid}" ]] && continue
    if is_owned_ui_pid "${pid}"; then
      found=1
      echo -e "${YELLOW}Stopping HomeSetup UI process ${pid}...${NC}"
      kill "${pid}" 2>/dev/null || quit 2 "Unable to stop HomeSetup UI process ${pid}"
    fi
  done <<< "${known_pids}"

  if [[ "${found}" -eq 0 ]]; then
    if is_ui_running; then
      echo -e "${YELLOW}Port ${HHS_STREAMLIT_UI_PORT} is in use by a process not started by the UI plugin. Leaving it running.${NC}"
      cleanup_ui_process_files
      return 0
    fi
    echo -e "${YELLOW}HomeSetup UI is already stopped.${NC}"
    cleanup_ui_process_files
    return 0
  fi

  for _ in {1..20}; do
    if ! ui_tracked_processes_alive; then
      cleanup_ui_process_files
      echo -e "${GREEN}HomeSetup UI stopped.${NC}"
      return 0
    fi
    sleep 0.25
  done

  quit 2 "HomeSetup UI did not stop cleanly on port ${HHS_STREAMLIT_UI_PORT}"
}

# @purpose: Validate the HomeSetup Streamlit UI runtime dependencies.
function validate_ui_runtime() {
  __hhs_is_venv || quit 1 "Not available when HomeSetup python venv is not active!"
  __hhs_has python3 || quit 1 "python3 is required to launch HomeSetup UI."

  [[ -s "${STREAMLIT_UI}" ]] || quit 1 "HomeSetup UI file not found: ${STREAMLIT_UI}"

  if ! python3 -c 'import streamlit' &>/dev/null; then
    quit 1 "Streamlit is not installed. Please run HomeSetup install/repair first."
  fi
}

# @purpose: Reject caller-provided Streamlit args that would weaken UI network/security settings.
function validate_safe_streamlit_args() {
  local arg protected_option

  for arg in "$@"; do
    protected_option="${arg%%=*}"
    case "${protected_option}" in
      --browser.serverAddress | --browser.serverPort | --server.address | --server.enableCORS | --server.enableXsrfProtection | --server.port)
        quit 1 "Protected Streamlit option is managed by HomeSetup UI and cannot be overridden: ${protected_option}"
        ;;
    esac
  done
}

# @purpose: Start the HomeSetup Streamlit UI server in the background.
function start_ui() {
  local owner_token pid ui_log

  if is_ui_running; then
    if is_managed_ui_running; then
      echo -e "${YELLOW}HomeSetup UI is already running. Use '${APP_NAME} ${PLUGIN_NAME} execute restart' or '${APP_NAME} execute ${PLUGIN_NAME} restart' to restart it.${NC}"
      open_ui
      return 0
    fi
    quit 2 "Port ${HHS_STREAMLIT_UI_PORT} is already in use by a process not started by the UI plugin."
  fi

  validate_ui_runtime
  validate_safe_streamlit_args "$@"
  ui_log="$(get_ui_log)"
  mkdir -p "${HHS_LOG_DIR}" "$(dirname "$(get_ui_process_registry_file)")"
  owner_token="$(new_ui_owner_token)"
  echo -e "${YELLOW}Starting HomeSetup UI on port ${HHS_STREAMLIT_UI_PORT}...${NC}"
  STREAMLIT_BROWSER_GATHER_USAGE_STATS="false" \
    STREAMLIT_BROWSER_SERVER_ADDRESS="localhost" \
    STREAMLIT_BROWSER_SERVER_PORT="${HHS_STREAMLIT_UI_PORT}" \
    STREAMLIT_SERVER_ADDRESS="127.0.0.1" \
    HHS_STREAMLIT_UI_OWNER="${owner_token}" \
    PYTHONPATH="${HHS_HOME}/bin/apps/py:${PYTHONPATH:-}" \
    nohup python3 -m streamlit run "${STREAMLIT_UI}" \
    --server.address 127.0.0.1 \
    --server.port "${HHS_STREAMLIT_UI_PORT}" \
    --server.headless true \
    --browser.serverAddress localhost \
    --browser.serverPort "${HHS_STREAMLIT_UI_PORT}" \
    --browser.gatherUsageStats false \
    "$@" >"${ui_log}" 2>&1 &
  pid=$!
  record_ui_process "${pid}" "${owner_token}"
  kill -0 "${pid}" 2>/dev/null || {
    cleanup_ui_process_files
    quit 2 "Unable to start HomeSetup UI. Check ${ui_log}"
  }

  for _ in {1..20}; do
    is_ui_running && {
      echo -e "${GREEN}HomeSetup UI started with PID: ${pid}${NC}"
      open_ui
      quit 0
    }
    sleep 0.25
  done

  stop_ui &>/dev/null || true
  quit 2 "HomeSetup UI did not become ready on port ${HHS_STREAMLIT_UI_PORT}. Check ${ui_log}"
}

# @purpose: Launch the HomeSetup Streamlit UI.
function launch_ui() {

  validate_ui_runtime

  if is_ui_running; then
    if is_managed_ui_running; then
      open_ui
      quit 0
    fi
    quit 2 "Port ${HHS_STREAMLIT_UI_PORT} is already in use by a process not started by the UI plugin."
  fi

  start_ui "$@"
}

# @purpose: Restart the HomeSetup Streamlit UI server.
function restart_ui() {
  stop_ui
  launch_ui "$@"
}

# @purpose: HHS plugin required function.
function execute() {

  [[ "$1" == "-h" || "$1" == "--help" ]] && usage 0
  [[ "$1" == "-v" || "$1" == "--version" ]] && version
  [[ "$1" == "execute" ]] && shift

  case "${1:-open}" in
    open)
      shift || true
      launch_ui "$@"
      ;;
    start)
      shift
      start_ui "$@"
      ;;
    status)
      status_ui
      ;;
    stop)
      stop_ui
      ;;
    restart)
      shift
      restart_ui "$@"
      ;;
    *)
      launch_ui "$@"
      ;;
  esac
}
