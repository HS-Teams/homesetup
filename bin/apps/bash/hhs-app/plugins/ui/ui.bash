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
VERSION="0.0.2"

# Namespace cleanup.
UNSETS=(
  help version cleanup execute get_ui_url is_ui_running open_ui start_ui launch_ui
)

# Streamlit UI application path.
STREAMLIT_UI="${HHS_HOME}/bin/apps/py/hhs-ui/streamlit_ui.py"

# Streamlit UI port.
HHS_STREAMLIT_UI_PORT="${HHS_STREAMLIT_UI_PORT:-18501}"

# Usage message.
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} [options]

  HomeSetup Streamlit UI launcher v${VERSION}.

    options:
      -h | --help                : Display this help message.
      -v | --version             : Display current plugin version.

    arguments:
      args                       : Optional arguments passed to Streamlit.

    examples:
      Launch HomeSetup UI:
        => ${APP_NAME} ${PLUGIN_NAME}
      Launch HomeSetup UI with Streamlit arguments:
        => HHS_STREAMLIT_UI_PORT=18502 ${APP_NAME} ${PLUGIN_NAME}

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

# @purpose: Open the HomeSetup Streamlit UI in the default browser.
function open_ui() {
  local url

  url="$(get_ui_url)"
  echo -e "${GREEN}HomeSetup UI is running at ${BLUE}${url}${NC}"
  __hhs_open "${url}" &>/dev/null || true
}

# @purpose: Start the HomeSetup Streamlit UI server in the background.
function start_ui() {
  local pid ui_log

  ui_log="${HHS_LOG_DIR}/streamlit-ui.log"
  echo -e "${YELLOW}Starting HomeSetup UI on port ${HHS_STREAMLIT_UI_PORT}...${NC}"
  nohup python3 -m streamlit run "${STREAMLIT_UI}" \
    --server.port "${HHS_STREAMLIT_UI_PORT}" \
    --server.headless true \
    "$@" >"${ui_log}" 2>&1 &
  pid=$!
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

  __hhs_is_venv || quit 1 "Not available when HomeSetup python venv is not active!"
  __hhs_has python3 || quit 1 "python3 is required to launch HomeSetup UI."

  [[ -s "${STREAMLIT_UI}" ]] || quit 1 "HomeSetup UI file not found: ${STREAMLIT_UI}"

  if ! python3 -c 'import streamlit' &>/dev/null; then
    quit 1 "Streamlit is not installed. Please run HomeSetup install/repair first."
  fi

  if is_ui_running; then
    open_ui
    quit 0
  fi

  start_ui "$@"
}

# @purpose: HHS plugin required function.
function execute() {

  [[ "$1" == "-h" || "$1" == "--help" ]] && usage 0
  [[ "$1" == "-v" || "$1" == "--version" ]] && version

  launch_ui "$@"
}
