#!/usr/bin/env bats

#  Script: commands-ssh.bats
# Purpose: HomeSetup Streamlit UI command and SSH source tests.
# Created: Jun 25, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

repo_dir="${BATS_TEST_DIRNAME}"
while [[ ! -f "${repo_dir}/install.bash" ]]; do
  repo_dir="${repo_dir}/.."
done
export HHS_REPO_DIR="$(cd "${repo_dir}" && pwd)"
export HHS_HOME="${HHS_REPO_DIR}"

load "${HHS_REPO_DIR}/tests/test_helper"
load_bats_libs
load "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ui/tests/hhs-ui-test-helpers.bash"

@test "when executing shell commands then every UI command path should use run_bash_command" {
  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())
violations = []
parents = {}

for node in ast.walk(tree):
    for child in ast.iter_child_nodes(node):
        parents[child] = node

def enclosing_function(node):
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, ast.FunctionDef):
            return parent.name
        parent = parents.get(parent)
    return ""

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    func = node.func
    is_subprocess_run = (
        isinstance(func, ast.Attribute)
        and func.attr == "run"
        and isinstance(func.value, ast.Name)
        and func.value.id == "subprocess"
    )
    allowed_functions = {"resolve_run_shell", "run_bash_command", "run_cleanup_bash_command"}
    if is_subprocess_run and enclosing_function(node) not in allowed_functions:
        violations.append(f"line {node.lineno}")

if violations:
    raise SystemExit("subprocess.run outside command runners: " + ", ".join(violations))
PY
  assert_success

  assert_file_contains_many "${command_runtime_file}" \
'def run_bash_command('
  assert_file_contains_many "${ui_file}" \
'return run_bash_command(' 'def run_hhs_services_quietly'
  assert_file_contains_many "${ssh_core_file}" \
'def parse_ssh_config_hosts' 'def build_ssh_connect_command' 'def build_ssh_disconnect_command'
  assert_file_contains "${constants_file}" 'UI_CACHE_SSH_CONNECTION_KEY'

  assert_file_not_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" 'UI_SSH_CONNECTION_FILE'

  assert_file_contains "${ui_file}" 'restore_registered_ssh_connection_on_session_start()'
  assert_file_contains_many "${ssh_runtime_file}" \
'def restore_registered_ssh_connection_on_session_start' \
    'ssh_connection_restore_checked' \
    'hhs_ui.SSH_RECONNECT_HOST_KEY' 'st.session_state\["ssh_connect_pending"\] = reconnect_host' \
    'f"Reconnecting to {ssh_connection_display(reconnect_host)}"' \
    'st.session_state\["ssh_reconnect_restore_view_state"\] = True' 'def reconnect_view_state_snapshot' \
    'def remember_host_switch_view_state' 'def consume_host_switch_view_state' \
    'def restore_reconnect_view_state' 'loader_message = str(' \
    'st.session_state\["ssh_connect_pending_message"\] = ""'
  assert_file_not_contains "${ui_file}" 'Disconnecting stale SSH host'

  assert_file_contains_many "${ssh_runtime_file}" \
'st.session_state\["ssh_connection_status"\] = "connected"' 'def clear_host_scoped_session_state' \
    'clear_host_scoped_session_state()' 'st.session_state\[hhs_ui.TERMINAL_CWD_KEY\] = "."' \
    'key in hhs_ui.PERSISTED_UI_KEYS'
  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/ssh_runtime.py").read_text()
start_body = source.split("def execute_pending_ssh_connection", 1)[1].split("\ndef ", 1)[0]
complete_body = source.split("def complete_ssh_connection", 1)[1].split("\ndef ", 1)[0]
body = f"{start_body}\n{complete_body}"
snapshot_index = body.index("was_terminal_active = terminal_document_view_is_active()")
reset_index = body.index("clear_host_scoped_session_state()")
status_index = body.index('st.session_state["ssh_connection_status"] = "connected"')
remote_cwd_index = body.index("update_remote_footer_working_directory()")
restore_index = body.index("restore_terminal_document_view(was_terminal_active)")
availability_refresh_index = complete_body.index(
    "schedule_ollama_service_availability_refresh()"
)
assert snapshot_index < reset_index
assert reset_index < status_index
assert status_index < remote_cwd_index < restore_index
assert complete_body.index("register_ssh_connection(host)") < availability_refresh_index
assert availability_refresh_index < complete_body.index("save_ui_state()")
assert "set_overlay(True" not in body
assert "set_overlay(False" not in body
assert "show_overlay=False" not in body
assert "cache_clear()" in source.split("def clear_host_scoped_session_state", 1)[1].split("\ndef ", 1)[0]
assert "cache_clear()" in source.split("def execute_pending_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state.pop("ssh_reconnect_restore_view_state", False)' in body
assert "reset_updater_remote_check_state()" in complete_body
assert "consume_host_switch_view_state()" in body
assert "restore_reconnect_view_state(reconnect_state)" in body
assert "remember_host_switch_view_state()" in source.split("def request_ssh_host_connect", 1)[1].split("\ndef ", 1)[0]
assert "remember_host_switch_view_state()" in source.split("def request_ssh_host_disconnection", 1)[1].split("\ndef ", 1)[0]
view_state_keys_body = source.split("def reconnect_view_state_keys", 1)[1].split("\ndef ", 1)[0]
assert '"ssh_view"' in view_state_keys_body
assert '"ssh_explorer_local_path"' in view_state_keys_body
assert '"ssh_explorer_remote_path"' in view_state_keys_body
restore_reconnect_index = body.index("restore_reconnect_view_state(reconnect_state)")
assert reset_index < restore_reconnect_index < status_index
disconnect_body = source.split("def execute_pending_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
assert "st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)" in disconnect_body
assert 'st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = ""' in disconnect_body
clear_disconnect_body = source.split("def clear_completed_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
disconnect_snapshot_index = clear_disconnect_body.index("disconnect_view_state = consume_host_switch_view_state()")
disconnect_reset_index = clear_disconnect_body.index("clear_host_scoped_session_state()")
disconnect_restore_index = clear_disconnect_body.index("restore_reconnect_view_state(disconnect_view_state)")
disconnect_availability_refresh_index = clear_disconnect_body.index(
    "schedule_ollama_service_availability_refresh()"
)
assert disconnect_snapshot_index < disconnect_reset_index < disconnect_restore_index
assert clear_disconnect_body.index("cache_clear()") < disconnect_availability_refresh_index
assert disconnect_availability_refresh_index < clear_disconnect_body.index("save_ui_state()")
restore_body = source.split("def restore_registered_ssh_connection_on_session_start", 1)[1].split("\ndef ", 1)[0]
assert "registered_ssh_connection_host() or reconnect_host" in restore_body
assert "clear_disconnected_ssh_host(host)" not in restore_body
assert 'st.session_state["ssh_connect_pending"] = reconnect_host' in restore_body
assert 'st.session_state["ssh_connect_pending_message"] = (' in restore_body
assert 'st.session_state["ssh_reconnect_restore_view_state"] = True' in restore_body
assert "reset_updater_remote_check_state()" in restore_body
restore_registered_snapshot_index = restore_body.index("reconnect_state = reconnect_view_state_snapshot()")
restore_registered_reset_index = restore_body.index("clear_host_scoped_session_state()")
restore_registered_restore_index = restore_body.index("restore_reconnect_view_state(reconnect_state)")
restore_registered_status_index = restore_body.index('st.session_state["ssh_connection_status"] = "connected"')
restore_registered_availability_refresh_index = restore_body.index(
    "schedule_ollama_service_availability_refresh()"
)
assert (
    restore_registered_snapshot_index
    < restore_registered_reset_index
    < restore_registered_restore_index
    < restore_registered_status_index
)
assert restore_registered_status_index < restore_registered_availability_refresh_index
assert restore_registered_availability_refresh_index < restore_body.index("save_ui_state()")
PY
  assert_success

  assert_file_contains_many "${ssh_runtime_file}" \
'def register_ssh_connection' 'def clear_registered_ssh_connection' 'def legacy_ssh_connection_files' \
    'def unlink_legacy_ssh_connection_files' 'def request_ssh_host_connect'
  assert_file_contains "${cache_runtime_file}" 'ui_cache_metadata_key(key)'
  run grep -Fq -- 'cache[hhs_ui.UI_CACHE_SSH_CONNECTION_KEY] = {"value": {"host": clean_host}}' "${ssh_runtime_file}"
  assert_success
  assert_file_not_contains "${ui_file}" 'on_change=request_ssh_host_connection'

  assert_file_contains "${ui_file}" 'synchronize_selected_ssh_host_with_connection()'
  assert_file_contains_many "${ssh_runtime_file}" \
'def selected_ssh_host_is_connected' 'def connected_ssh_host' \
    'def synchronize_selected_ssh_host_with_connection' \
    'st.session_state\["ssh_host_selected"\] = host' 'st.session_state\["ssh_host_selector"\] = host' \
    'ssh_connection_host' 'def request_ssh_host_disconnection' 'def execute_pending_ssh_disconnection'
  run grep -q -- '-O exit' "${ssh_core_file}"
  assert_success

  assert_file_contains_many "${ssh_core_file}" \
'pgrep -f --' 'kill -TERM' 'kill -KILL' 'rm -f {safe_control_path}' 'def ssh_config_option'
  run grep -q -- '-F "${HOME}/.ssh/config"' "${ssh_core_file}"
  assert_success

  assert_file_contains_many "${ssh_core_file}" \
'ControlMaster=yes' 'ConnectionAttempts=1' 'def build_ssh_wrapped_command' 'bash -ic' \
    'safe_remote_shell = shlex.quote'
  assert_file_contains_many "${ssh_core_file}" '"ssh",' '"-tt",'
  assert_file_not_contains_many "${ui_file}" \
'JOB_NAME="${JOB_NAME:-HomeSetup-UI}"' 'source "${HOME}/.bashrc"' '[[ ! -s "${HOME}/.hhsrc" ]]' \
    '"HomeSetup" is not installed on the host.' 'def handle_missing_remote_homesetup' \
    'result.returncode != 86'
  assert_file_contains "${ssh_runtime_file}" 'def effective_bash_command'
  assert_file_contains_many "${command_runtime_file}" \
'hhs_ui_constants.RUN_SHELL_ENV_KEY: RUN_SHELL' '\[RUN_SHELL, "-lc", command_to_run\]'
  assert_file_contains_many "${runtime_file}" \
'def resolve_run_shell' '\["brew", "--prefix", "bash"\]' \
    '\["/opt/homebrew/bin/brew", "--prefix", "bash"\]' '\["/usr/local/bin/brew", "--prefix", "bash"\]' \
    'Path(run_shell) / "bin" / "bash"' 'Path("/opt/homebrew/opt/bash/bin/bash")' \
    'Path("/usr/local/opt/bash/bin/bash")' 'Path("/bin/bash")' 'RUN_SHELL = resolve_run_shell()' \
    'os.environ\[hhs_ui_constants.RUN_SHELL_ENV_KEY\] = RUN_SHELL'
  assert_file_not_contains_many "${ui_file}" \
'\["bash", "-lc"' 'source "{hhs_home}' 'export HHS_HOME="{hhs_home}' '/Users/hjunior/HomeSetup'
  assert_file_contains_many "${ssh_runtime_file}" \
'or not selected_ssh_host_is_connected(host)' 'force_local: bool = False'
  assert_file_contains_many "${ui_file}" \
    'def run_ssh_tunnels' 'def annotate_ssh_tunnel_statuses' \
    'headers = \["Local Port", "Remote Host:Port", "Kind", "Status", "Link"\]'
  assert_file_contains_many "${command_catalog_file}" \
'export HHS_DIR="${HHS_DIR:-${HOME}/.config/hhs}"' 'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"' \
    'def build_ssh_tunnels_command' 'ssh {safe_config_option} -G {safe_host}' \
    'def parse_ssh_tunnels' 'def parse_ssh_config_tunnels' 'def ssh_tunnel_status_cell_style' \
    'def display_ssh_tunnel_rows' 'def filter_ssh_tunnel_rows'
  assert_file_contains_many "${constants_file}" \
'Path(os.environ.get("HHS_HOME", APP_DIR.parents\[4\]))' '/ "assets/devel/ports-default.csv"'
  run test -s "${HHS_REPO_DIR}/assets/devel/ports-default.csv"
  assert_success

  assert_file_contains_many "${ui_file}" \
'column_config: dict\[str, object\] | None = None' 'on_select: Callable\[\[\], None\] | str = "rerun"' \
    'st.column_config.LinkColumn'
  run grep -F -q 'display_text=r"http://(127\.0\.0\.1:\d+)"' "${ui_file}"
  assert_success

  assert_file_contains_many "${ui_file}" \
'def render_ssh_view' 'def render_ssh_tunnels_panel' 'def render_ssh_files_panel' 'def ssh_explorer_row_style' \
    'def ssh_explorer_entry_is_visible' 'def ssh_explorer_sort_key'
  assert_file_not_contains "${ui_file}" 'def synchronize_ssh_explorer_table_selection'

  assert_file_contains_many "${ui_file}" \
'def ssh_explorer_component' 'components.declare_component(' 'def handle_ssh_explorer_component_event' \
    'def ssh_explorer_component_event_paths' 'def render_ssh_explorer_component' \
    'def remote_explorer_parent_path' 'def normalize_local_explorer_path' 'def normalize_remote_explorer_path' \
    'def ssh_explorer_local_default_path' 'def ssh_explorer_remote_default_path' \
    'def open_ssh_explorer_parent' 'def refresh_ssh_explorer_paths' 'def set_remote_footer_working_directory' \
    'def build_recoverable_delete_command' 'def request_ssh_explorer_delete_confirmation' \
    'def render_ssh_explorer_delete_dialog' 'def create_ssh_explorer_folder' \
    'def ssh_explorer_component_theme' 'def open_ssh_explorer_selection' \
    'def build_remote_explorer_listing_command' 'def remote_explorer_target_assignment' \
    'def build_remote_explorer_create_folder_command' 'def parse_remote_explorer_created_dir' \
    'def parse_remote_explorer_rows' 'def build_scp_to_remote_command' 'def build_scp_to_local_command' \
    'SSH_FILE_TRANSFER_JOB = "ssh_file_transfer"' '"ssh_files"' 'scp -r' \
    'Copying local file(s)/folder(s) to remote' 'Copying remote file(s)/folder(s) to local' \
    'paths = ssh_explorer_component_event_paths(event)' 'ControlPath=' 'ssh_config_option()' \
    'def ssh_view_label' 'hhs_ui.SSH_VIEWS' 'format_func=ssh_view_label' 'render_view_segmented_control(' \
    'view_segmented_control_widget_key(state_key)' 'render_ssh_tunnels_panel(host)' \
    'hhs_ui.SSH_TUNNEL_FILTERS' '"ssh_tunnel_filter"' '"ssh_tunnel_other_filter"' \
    'filter_ssh_tunnel_rows(rows, tunnel_filter, other_filter)' \
    'st.session_state.setdefault("ssh_tunnel_filter", "All")' 'render_ssh_files_panel()' \
    'event = render_ssh_explorer_component(' 'handle_ssh_explorer_component_event(event)' \
    'if action == "create_folder"' 'if action == "refresh"' 'refresh_ssh_explorer_paths(' \
    'if action == "delete"' 'request_ssh_explorer_delete_confirmation(' 'st.rerun()' \
    'key="ssh_explorer_component"' 'localRows=local_rows' 'localLoading=local_loading' \
    'remoteRows=remote_rows or \[\]' 'remoteLoading=remote_loading' 'loading=explorer_loading' \
    'explorer_loading = local_loading or remote_loading' 'tableHeight=table_height(hhs_ui.ENV_TABLE_HEIGHT)' \
    'theme=ssh_explorer_component_theme()' '"ssh_explorer_local_path", ssh_explorer_local_default_path()' \
    '"ssh_explorer_remote_path", ssh_explorer_remote_default_path()' 'selectionHint=False' \
    'component_height = table_height(hhs_ui.ENV_TABLE_HEIGHT)' 'height=component_height'
  assert_file_contains "${table_ui_file}" 'def resolve_css_custom_property'
  assert_file_not_contains_many "${ui_file}" \
'on_select=reset_ssh_explorer_remote_table_selection' 'on_select=reset_ssh_explorer_local_table_selection' \
    'key_prefix": "ssh_explorer_local_open_button"' 'key_prefix": "ssh_explorer_remote_open_button"'
  assert_file_not_contains "${css_file}" '.st-key-ssh_explorer_layout'

  assert_file_contains_many "${css_file}" \
'.st-key-ssh_explorer_component iframe' 'background: var(--hhs-background) !important'
  run grep -q -- '--hhs-ssh-explorer-height: calc(100dvh - var(--hhs-footer-guard-height) - 4.75rem - (var(--hhs-view-gap) \* 3) - 55px)' "${css_file}"
  assert_success

  assert_file_contains "${css_file}" 'height: var(--hhs-ssh-explorer-height) !important'

  run grep -q -- '--hhs-view-gap: var(--hhs-element-std-gap)' "${css_file}"
  assert_success

  assert_file_contains_many "${css_file}" \
'min-height: 0' 'overflow: hidden !important'
  run grep -F -q 'div:not([class*="st-key-ssh_explorer_component"]):has(iframe[height="0"])' "${css_file}"
  assert_success

  assert_file_not_contains_many "${css_file}" \
'.st-key-ssh_explorer_transfer_controls' '.st-key-ssh_explorer_open_selected button'
  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
  assert_success

  run cmp -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2" "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
  assert_success

  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'grid-template-columns: minmax(0, 1fr) 3.2rem minmax(0, 1fr)' 'height: 100vh' 'flex: 1 1 auto'
  run grep -q -- '--hhs-panel-bg: color-mix' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" '.path-input::placeholder'

  run grep -q -- '--hhs-placeholder: #686e7a' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'color: var(--hhs-placeholder)' '"--hhs-placeholder": themeValues.placeholder || themeValues.placeholderColor' \
    'background: var(--hhs-panel-bg)' 'overflow-y: auto'
  assert_file_not_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" 'overflow-y: scroll'

  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'scrollbar-color: var(--hhs-scrollbar)' 'scrollbar-gutter: stable' 'padding-right: var(--hhs-scrollbar-size)' \
    '.icon-button:hover:not(:disabled)' 'selectionHint: false' 'loading: false' 'localLoading: false' \
    'function explorerIsLoading' 'return Boolean(args.loading || args.localLoading || args.remoteLoading)'
  assert_file_not_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" 'function createLoadingState'

  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'app.replaceChildren()' 'Streamlit.setFrameHeight(0)'
  assert_file_not_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'.loading-state' 'Loading files'
  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'theme: {}' 'function applyTheme' 'message.theme' 'themeValues.background || themeValues.backgroundColor' \
    '"--hhs-primary": themeValues.primary || themeValues.primaryColor' 'border-color: var(--hhs-primary)' \
    '.panel.active .panel-title' 'let activePanel = "local"' 'function activatePanel' \
    'classList.toggle("active"' 'localBasePath: args.localPath' 'remoteBasePath: args.remotePath' \
    'sendCommand("parent", activeExplorerPanel(), "")' \
    'sendCommand("create_folder", activeExplorerPanel(), "")'
  assert_file_contains_many "${ui_file}" \
'Folder created on local {created_name}' 'Folder created on remote {created_name}'
  assert_file_not_contains "${ui_file}" 'Folder ready'

  run python3 - <<'PY'
from pathlib import Path

component = Path("bin/apps/py/hhs_ui/components/ssh_explorer/index.html").read_text(
    encoding="utf-8"
)
controls = component[
    component.index("function createTransferControls") : component.index("function resizeFrame")
]
assert controls.index('""') < controls.index('""') < controls.index('""')
assert controls.index('""') < controls.index('""')
assert '""' in controls
assert '""' in controls
PY
  assert_success

  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'args.selectionHint ? "Select a row to interact" : ""' 'function selectRow' 'function sendCommand' \
    'Streamlit.setComponentValue' '""' '""' 'sendCommand("refresh", "all", "")' '""' '""' \
    'sendCommand("delete", activeExplorerPanel(), "")' '""' '""' '""'
  run python3 - <<'PY'
from pathlib import Path

component = Path("bin/apps/py/hhs_ui/components/ssh_explorer/index.html").read_text(
    encoding="utf-8"
)
select_body = component[
    component.index("function selectRow") : component.index("function createElement")
]
assert "setComponentValue" not in select_body
assert "sendCommand" not in select_body
assert "activatePanel(panel, false)" in select_body
assert "selectedPanel = panel" in select_body
assert "selectedPaths[panel]" in select_body
assert "paths.add(path)" in select_body
assert "paths.delete(path)" in select_body
assert "render();" in select_body
PY
  assert_success

  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html" \
'let selectedPaths = {' 'function selectedPathList' 'function selectedRows' 'paths,'
  run grep -F -q 'Selected: [${rows.map((row) => stringValue(row.Path)).join(", ")}]' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -F -q '<p>Connected to remote' "${ui_file}"
  assert_failure

  assert_file_contains_many "${ui_file}" \
'key=hhs_ui.SSH_TUNNEL_TABLE_KEY' 'checkbox=False'
  run python3 - "${command_catalog_file}" <<'PY'
import csv
import hashlib
import os
import posixpath
import re
import shlex
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def split_ssh_command(")
end = source.index("def parse_hhs_history(")
namespace = {
    "csv": csv,
    "datetime": datetime,
    "hashlib": hashlib,
    "hhs_ui": SimpleNamespace(
        PORTS_DEFAULT_FILE=Path("assets/devel/ports-default.csv"),
        THEME_SELECTED_KEY="theme_selected",
    ),
    "lru_cache": lru_cache,
    "Path": Path,
    "posixpath": posixpath,
    "re": re,
    "shlex": shlex,
    "ssh_control_path": lambda host: f"/tmp/{host}.sock",
    "ssh_config_option": lambda: '-F "${HOME}/.ssh/config"',
    "ssh_config_file": lambda: Path.home() / ".ssh" / "config",
    "st": SimpleNamespace(session_state={"theme_selected": "test-theme"}),
    "textwrap": textwrap,
    "row_matches_text_filter": lambda row, text: (
        not text.strip()
        or text.strip().lower()
        in " ".join(str(value).lower() for value in row.values())
    ),
    "strip_ansi": lambda value: value,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

rows = namespace["parse_ssh_tunnels"](
    """
    __HHS_SSH_CONFIG__
    host homeselect
    hostname 10.0.0.5
    localforward 15432 127.0.0.1:5432
    remoteforward 0.0.0.0:9000 127.0.0.1:9000
    dynamicforward 127.0.0.1:1080
    __HHS_SSH_PROCESSES__
    100 ssh -N -L 8080:localhost:80 user@example.com
    101 /usr/bin/ssh -N -R0.0.0.0:9000:127.0.0.1:9000 remote
    102 ssh -N -D 127.0.0.1:1080 remote
    103 ssh -MNf remote
    """,
    "homeselect",
)

assert rows == [
    {
        "Type": "Local",
        "Bind": "15432",
        "Destination": "127.0.0.1:5432",
        "SSH Host": "homeselect",
        "Source": "Config",
        "Status": "",
        "PID": "",
        "Command": str(Path.home() / ".ssh" / "config"),
    },
    {
        "Type": "Remote",
        "Bind": "0.0.0.0:9000",
        "Destination": "127.0.0.1:9000",
        "SSH Host": "homeselect",
        "Source": "Config",
        "Status": "",
        "PID": "",
        "Command": str(Path.home() / ".ssh" / "config"),
    },
    {
        "Type": "Dynamic",
        "Bind": "127.0.0.1:1080",
        "Destination": "SOCKS",
        "SSH Host": "homeselect",
        "Source": "Config",
        "Status": "",
        "PID": "",
        "Command": str(Path.home() / ".ssh" / "config"),
    },
    {
        "Type": "Local",
        "Bind": "8080",
        "Destination": "localhost:80",
        "SSH Host": "user@example.com",
        "Source": "Process",
        "Status": "",
        "PID": "100",
        "Command": "ssh -N -L 8080:localhost:80 user@example.com",
    },
    {
        "Type": "Remote",
        "Bind": "0.0.0.0:9000",
        "Destination": "127.0.0.1:9000",
        "SSH Host": "remote",
        "Source": "Process",
        "Status": "",
        "PID": "101",
        "Command": "/usr/bin/ssh -N -R0.0.0.0:9000:127.0.0.1:9000 remote",
    },
    {
        "Type": "Dynamic",
        "Bind": "127.0.0.1:1080",
        "Destination": "SOCKS",
        "SSH Host": "remote",
        "Source": "Process",
        "Status": "",
        "PID": "102",
        "Command": "ssh -N -D 127.0.0.1:1080 remote",
    },
], rows

assert namespace["split_bind_address"]("127.0.0.1:1080") == ("127.0.0.1", 1080)
assert namespace["split_bind_address"]("15432") == ("127.0.0.1", 15432)
assert namespace["ssh_tunnel_status_cell_style"]("Reachable").endswith("#50fa7b;")
assert namespace["ssh_tunnel_status_cell_style"]("Not reachable").endswith("#ff5555;")
display_rows = namespace["display_ssh_tunnel_rows"](
    [{"Bind": "15432", "Destination": "127.0.0.1:5432", "Status": "Reachable"}]
)
assert display_rows == [
    {
        "Local Port": "15432",
        "Remote Host:Port": "127.0.0.1:5432",
        "Kind": "PostgreSQL",
        "Status": "Reachable",
        "Link": "http://127.0.0.1:15432",
    }
], display_rows
filter_rows = [
    {"Bind": "15432", "Destination": "127.0.0.1:5432", "Status": "Reachable"},
    {"Bind": "8080", "Destination": "localhost:80", "Status": "Not reachable"},
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "All") == filter_rows
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Reachable") == []
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "PostgreSQL") == [
    filter_rows[0]
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Other", "http") == [
    filter_rows[1]
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Containing", "http") == [
    filter_rows[1]
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Other", "localhost") == []
assert namespace["ssh_tunnel_kind"]({"Type": "Local", "Destination": "localhost:80"}) == "HTTP"
assert namespace["ssh_tunnel_kind"]({"Type": "Dynamic", "Bind": "127.0.0.1:1080"}) == "SOCKS"

explorer_start = source.index("def ssh_explorer_mtime_text(")
explorer_end = source.index("def render_ssh_view(")
exec("from __future__ import annotations\n" + source[explorer_start:explorer_end], namespace)

assert namespace["remote_explorer_parent_path"]("/home/me/project") == "/home/me"
assert namespace["remote_explorer_parent_path"]("/root") == "/"
assert namespace["remote_explorer_parent_path"]("/") == "/"
assert namespace["remote_explorer_parent_path"](".") == ".."
assert namespace["ssh_explorer_size_text"]("4096", "Dir") == "--"
assert namespace["ssh_explorer_size_text"]("2048", "File") == "2.0 KB"
assert namespace["ssh_explorer_row"](
    "Dir", "project", "4096", "0", "/tmp/project"
)["Size"] == "--"
assert namespace["normalize_remote_explorer_path"](".", "/root") == "/root"
assert namespace["normalize_remote_explorer_path"]("..", "/root") == "/"
assert namespace["normalize_remote_explorer_path"]("alerts", "/root") == "/root/alerts"
local_base = Path.cwd().resolve()
assert namespace["normalize_local_explorer_path"](".", str(local_base)) == str(local_base)
assert namespace["normalize_local_explorer_path"]("..", str(local_base)) == str(local_base.parent)
assert namespace["local_explorer_directory"]("/tmp/hhs-missing-explorer-dir") == Path.home().resolve()
assert namespace["ssh_explorer_local_default_path"]() == str(Path.home().resolve())
assert namespace["ssh_explorer_remote_default_path"]() == "~"
refresh_body = source.split("def refresh_ssh_explorer_paths", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["ssh_explorer_local_path"]' in refresh_body
assert 'st.session_state["ssh_explorer_remote_path"]' in refresh_body
assert 'set_remote_footer_working_directory(normalized_remote_path)' in refresh_body
assert 'cache_delete_tag("ssh_files")' in refresh_body
open_remote_body = source.split("def open_remote_explorer_path", 1)[1].split("\ndef ", 1)[0]
assert 'set_remote_footer_working_directory(normalized_path)' in open_remote_body
remote_rows_body = source.split("def remote_explorer_rows", 1)[1].split("\ndef ", 1)[0]
assert "set_remote_footer_working_directory(resolved_remote_path)" in remote_rows_body
delete_command = namespace["build_recoverable_delete_command"](
    ["/tmp/delete-one.txt", "/tmp/delete two"]
)
assert "gtrash put" in delete_command
assert "trash-put" in delete_command
assert "gio trash" in delete_command
assert "kioclient" in delete_command
assert "${HOME}/.Trash" in delete_command
assert "trash_with_freedesktop" in delete_command
assert "/tmp/delete-one.txt" in delete_command
assert "'/tmp/delete two'" in delete_command
assert namespace["ssh_explorer_delete_message"](
    "remote", ["/srv/app/file.txt", "/srv/app/folder"]
) == "Are you sure you want to delete file.txt, folder?"
target_assignment = namespace["remote_explorer_target_assignment"]("~/project")
assert 'raw_target=' in target_assignment
assert 'target="${HOME:-.}/${raw_target#*/}"' in target_assignment
theme_properties = {
    "hhs-background": "var(--hhs-theme-background-color)",
    "hhs-theme-background-color": "#19181f",
    "hhs-theme-primary-color": "#f1fa8c",
    "hhs-panel": "var(--missing-panel, #14131a)",
    "hhs-secondary": "var(--hhs-theme-primary-color)",
}
namespace["theme_custom_properties"] = lambda _theme_name: theme_properties
assert namespace["resolve_css_custom_property"](
    theme_properties, "hhs-background", "#000000"
) == "#19181f"
assert namespace["resolve_css_custom_property"](
    theme_properties, "hhs-panel", "#000000"
) == "#14131a"
assert namespace["resolve_css_value"](
    theme_properties, "var(--hhs-secondary)", "#ffffff"
) == "#f1fa8c"
assert namespace["resolve_css_value"](
    theme_properties, "var(--missing-color, #abcdef)", "#ffffff"
) == "#abcdef"
theme = namespace["ssh_explorer_component_theme"]()
assert theme["primary"] == "#f1fa8c"

explorer_rows = namespace["parse_remote_explorer_rows"](
    "__HHS_CWD__\t/home/me\n"
    "__HHS_FILE__\tDir\t.\t0\t1710000000\t/home/me/.\n"
    "__HHS_FILE__\tDir\t..\t0\t1710000000\t/home/me/..\n"
    "__HHS_FILE__\tDir\t.hidden\t0\t1710000000\t/home/me/.hidden\n"
    "__HHS_FILE__\tFile\t.env\t100\t1710000000\t/home/me/.env\n"
    "__HHS_FILE__\tFile\tnotes.txt\t2048\t1710000000\t/home/me/notes.txt\n"
)
assert namespace["parse_remote_explorer_cwd"](
    "__HHS_CWD__\t/home/me\n"
) == "/home/me"
assert namespace["ssh_explorer_entry_is_visible"]("src") is True
assert namespace["ssh_explorer_entry_is_visible"](".env") is False
assert namespace["ssh_explorer_entry_is_visible"](".config") is False
sort_rows = [
    {"_kind": "File", "_name": "zeta.txt"},
    {"_kind": "Dir", "_name": "beta"},
    {"_kind": "File", "_name": "alpha.txt"},
    {"_kind": "Dir", "_name": "Alpha"},
]
assert [
    row["_name"] for row in sorted(sort_rows, key=namespace["ssh_explorer_sort_key"])
] == ["Alpha", "beta", "alpha.txt", "zeta.txt"]
dir_style = namespace["ssh_explorer_row_style"]({"Name": " src", "_kind": "Dir"})
file_style = namespace["ssh_explorer_row_style"]({"Name": " notes.txt", "_kind": "File"})
assert all("#38bdf8" in style for style in dir_style)
assert all("font-weight: 800" in style for style in dir_style)
assert all("#ffffff" in style for style in file_style)
assert len(explorer_rows) == 1
assert explorer_rows[0]["Name"].endswith("notes.txt")
assert explorer_rows[0]["_name"] == "notes.txt"
assert explorer_rows[0]["_kind"] == "File"
assert explorer_rows[0]["Size"] == "2.0 KB"
assert explorer_rows[0]["Path"] == "/home/me/notes.txt"
mixed_rows = namespace["parse_remote_explorer_rows"](
    "__HHS_FILE__\tFile\tzeta.txt\t1\t1710000000\t/home/me/zeta.txt\n"
    "__HHS_FILE__\tDir\tbeta\t0\t1710000000\t/home/me/beta\n"
    "__HHS_FILE__\tFile\talpha.txt\t1\t1710000000\t/home/me/alpha.txt\n"
    "__HHS_FILE__\tDir\tAlpha\t0\t1710000000\t/home/me/Alpha\n"
)
assert [row["_name"] for row in mixed_rows] == [
    "Alpha",
    "beta",
    "alpha.txt",
    "zeta.txt",
]
listing_command = namespace["build_remote_explorer_listing_command"]("/tmp")
assert "__HHS_FILE__" in listing_command
assert "__HHS_CWD__" in listing_command
assert "\\t..\\t" not in listing_command
assert '"${abs_dir}"/.[!.]*' not in listing_command
assert 'case "${name}" in .*|"."|"..") continue ;; esac' in listing_command
assert "target=${HOME:-.}" in listing_command
assert "exit 1" not in listing_command
assert "stat -c %s" in listing_command
assert "stat -f %z" in listing_command
with tempfile.TemporaryDirectory() as tmp_dir:
    fake_home = Path(tmp_dir) / "home"
    fake_home.mkdir()
    (fake_home / "fallback.txt").write_text("ok", encoding="utf-8")
    missing_dir = Path(tmp_dir) / "deleted" / "teste"
    fallback_command = namespace["build_remote_explorer_listing_command"](
        str(missing_dir)
    )
    result = subprocess.run(
        ["bash", "-lc", fallback_command],
        capture_output=True,
        check=False,
        env={"HOME": str(fake_home), "PATH": os.environ.get("PATH", "")},
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert f"__HHS_CWD__\t{fake_home.resolve()}" in result.stdout
    assert "fallback.txt" in result.stdout
with tempfile.TemporaryDirectory() as tmp_dir:
    target_folder = Path(tmp_dir) / "parent" / "new-folder"
    create_folder_command = namespace["build_remote_explorer_create_folder_command"](
        str(target_folder)
    )
    result = subprocess.run(
        ["bash", "-lc", create_folder_command],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert target_folder.is_dir()
    created_dir = namespace["parse_remote_explorer_created_dir"](result.stdout)
    assert Path(created_dir).resolve() == target_folder.resolve()

assert "__HHS_CREATED_DIR__" in create_folder_command
assert "mkdir -p" in create_folder_command
assert 'abs_dir=$(cd "${target}" && pwd -P)' in create_folder_command
assert "New Folder" not in create_folder_command
assert namespace["parse_remote_explorer_created_dir"](
    "__HHS_CREATED_DIR__\t/root/new-folder\n"
) == "/root/new-folder"
to_remote = namespace["build_scp_to_remote_command"](
    "/local/file.txt", "/remote dir", "host.example"
)
to_local = namespace["build_scp_to_local_command"](
    "/remote/file.txt", "/local dir", "host.example"
)
multi_to_remote = namespace["build_scp_to_remote_command"](
    ["/local/file one.txt", "/local/file two.txt"], "/remote dir", "host.example"
)
multi_to_local = namespace["build_scp_to_local_command"](
    ["/remote/file-one.txt", "/remote/file-two.txt"], "/local dir", "host.example"
)
assert "scp -r" in to_remote
assert "-F \"${HOME}/.ssh/config\"" in to_remote
assert "-o ControlPath=" in to_remote
assert "/local/file.txt" in to_remote
assert "host.example:'/remote dir'" in to_remote
assert "host.example:/remote/file.txt" in to_local
assert "'/local dir'" in to_local
assert "'/local/file one.txt' '/local/file two.txt'" in multi_to_remote
assert "host.example:/remote/file-one.txt" in multi_to_local
assert "host.example:/remote/file-two.txt" in multi_to_local
PY
  assert_success

  assert_file_contains_many "${ssh_runtime_file}" \
'timeout_seconds: int | None = None' 'def command_timeout_seconds' \
    'return hhs_ui.UI_COMMAND_REMOTE_TIMEOUT_SECONDS' 'return hhs_ui.UI_COMMAND_LOCAL_TIMEOUT_SECONDS' \
    'def effective_command_timeout_seconds' 'return max(1, int(timeout_seconds))'
  assert_file_contains_many "${command_runtime_file}" \
    'effective_timeout = effective_command_timeout_seconds(' 'except subprocess.TimeoutExpired'
  assert_file_contains_many "${ssh_runtime_file}" \
    'def render_ssh_connection_dialog' 'def clear_ssh_connection_dialog' 'def dismiss_streamlit_dialog' \
    'close_callback=close_ssh_connection_dialog'
  assert_file_contains_many "${dialog_ui_file}" \
    'button[aria-label="Close"]' 'close_button.click()'
  assert_file_contains_many "${ui_file}" 'render_dialog()' 'if render_ssh_connection_dialog()'
  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/ssh_runtime.py").read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "render_ssh_connection_dialog":
        assert "st.stop()" not in ast.unparse(node)
        break
else:
    raise AssertionError("render_ssh_connection_dialog not found")
PY
  assert_success

  assert_file_contains_many "${ssh_runtime_file}" \
'return True' 'dismiss_streamlit_dialog()' 'set_overlay(False)' \
    'f"Connected to remote  {ssh_connection_display(host)}"' \
    'push_floating_status(f"Failed to connect to remote: {host}", "error")'
  assert_file_contains_many "${ui_file}" \
    'push_floating_status("Opened working directory.", "info")' \
    '"success_fallback": "AI chat history cleared."' 'status_message or f"Selected AI model: {new_model}"' \
    'status_message or f"Deleted AI model: {model_name}"' \
    'push_floating_status(f"Loaded TLDR: {tool_name}", "info")' \
    'status_message or f"Killed process: {process_name}"' \
    'status_message or f"Service {operation} completed: {service_name}"' \
    'kind_aliases = {"success": "info", "warning": "warn"}' \
    'clean_message = clean_command_status_message(str(message))' 'clean_kind not in {"info", "warn", "error"}'
  assert_file_contains "${command_catalog_file}" 'def clean_command_status_message'
  assert_file_not_contains "${ui_file}" 'Successfully connected to {host}'

  run grep -F -q 'st.session_state["ssh_connection_dialog_title"] = ""' "${ui_file}"
  assert_success

  assert_file_not_contains "${ssh_runtime_file}" \
    'ssh_connection_dialog_title"] = f"Failed to connect to {host}"'

  assert_file_not_contains "${ui_file}" 'st.error(st.session_state.get("ssh_connection_error", "SSH failed."))'
}

# TC - 11
