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
VERSION="0.0.3"

# Namespace cleanup.
UNSETS=(
  help version cleanup execute get_ui_url get_ui_log get_ui_pid_file is_ui_running
  open_ui ui_pids ui_port_pids status_ui stop_ui start_ui restart_ui launch_ui
  validate_ui_runtime
)

# Streamlit UI application path.
STREAMLIT_UI="${HHS_HOME}/bin/apps/py/hhs_ui/streamlit_ui.py"

# Streamlit UI port.
HHS_STREAMLIT_UI_PORT="${HHS_STREAMLIT_UI_PORT:-18501}"

# HomeSetup UI pid file.
HHS_STREAMLIT_UI_PID_FILE="${HHS_STREAMLIT_UI_PID_FILE:-${HHS_DIR}/.streamlit-ui.pid}"

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
  pid="$({ ui_pids; ui_port_pids; } | awk '!seen[$0]++' | head -n 1)"
  [[ -z "${pid}" && -s "${pid_file}" ]] && pid="$(< "${pid_file}")"

  if is_ui_running; then
    if [[ -n "${pid}" ]]; then
      echo -e "${GREEN}HomeSetup UI is running at ${BLUE}${url}${GREEN} (PID: ${pid})${NC}"
    else
      echo -e "${GREEN}HomeSetup UI is running at ${BLUE}${url}${NC}"
    fi
  else
    echo -e "${YELLOW}HomeSetup UI is stopped on port ${HHS_STREAMLIT_UI_PORT}.${NC}"
  fi
}

# @purpose: Stop the running HomeSetup Streamlit UI process.
function stop_ui() {
  local pid pid_file found=0

  pid_file="$(get_ui_pid_file)"
  while IFS= read -r pid; do
    [[ -z "${pid}" ]] && continue
    found=1
    if kill -0 "${pid}" 2>/dev/null; then
      echo -e "${YELLOW}Stopping HomeSetup UI process ${pid}...${NC}"
      kill "${pid}" 2>/dev/null || quit 2 "Unable to stop HomeSetup UI process ${pid}"
    fi
  done < <({ [[ -s "${pid_file}" ]] && cat "${pid_file}"; ui_pids; ui_port_pids; } | awk '!seen[$0]++')

  if [[ "${found}" -eq 0 ]]; then
    if is_ui_running; then
      quit 2 "HomeSetup UI is running on port ${HHS_STREAMLIT_UI_PORT}, but no process ID could be resolved."
    fi
    echo -e "${YELLOW}HomeSetup UI is already stopped.${NC}"
    rm -f "${pid_file}" 2>/dev/null || true
    return 0
  fi

  for _ in {1..20}; do
    is_ui_running || {
      rm -f "${pid_file}" 2>/dev/null || true
      echo -e "${GREEN}HomeSetup UI stopped.${NC}"
      return 0
    }
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

# @purpose: Start the HomeSetup Streamlit UI server in the background.
function start_ui() {
  local pid pid_file ui_log

  if is_ui_running; then
    echo -e "${YELLOW}HomeSetup UI is already running. Use '${APP_NAME} ${PLUGIN_NAME} execute restart' or '${APP_NAME} execute ${PLUGIN_NAME} restart' to restart it.${NC}"
    open_ui
    return 0
  fi

  validate_ui_runtime
  pid_file="$(get_ui_pid_file)"
  ui_log="$(get_ui_log)"
  mkdir -p "${HHS_LOG_DIR}"
  echo -e "${YELLOW}Starting HomeSetup UI on port ${HHS_STREAMLIT_UI_PORT}...${NC}"
  PYTHONPATH="${HHS_HOME}/bin/apps/py:${PYTHONPATH:-}" \
    nohup python3 -m streamlit run "${STREAMLIT_UI}" \
    --server.port "${HHS_STREAMLIT_UI_PORT}" \
    --server.headless true \
    "$@" >"${ui_log}" 2>&1 &
  pid=$!
  printf '%s\n' "${pid}" > "${pid_file}"
  kill -0 "${pid}" 2>/dev/null || quit 2 "Unable to start HomeSetup UI. Check ${ui_log}"

  for _ in {1..20}; do
    is_ui_running && {
      echo -e "${GREEN}HomeSetup UI started with PID: ${pid}${NC}"
      open_ui
      quit 0
    }
    sleep 0.25
  done

  quit 2 "HomeSetup UI did not become ready on port ${HHS_STREAMLIT_UI_PORT}. Check ${ui_log}"
}

# @purpose: Launch the HomeSetup Streamlit UI.
function launch_ui() {

  validate_ui_runtime

  if is_ui_running; then
    open_ui
    quit 0
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
