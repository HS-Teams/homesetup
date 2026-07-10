#!/usr/bin/env bats

#  Script: terminal-dialogs.bats
# Purpose: HomeSetup Streamlit UI terminal and dialog tests.
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

@test "when confirming actions then reusable pop_dialog component should be used" {
  assert_file_contains_many "${ui_file}" \
'render_folder_picker_dialog()' \
    'execute_pending_dialog_callback()' 'st.session_state\["_hhs_dialog_dismiss_requested"\] = True'
  assert_file_contains_many "${dialog_ui_file}" \
'def pop_dialog(' \
    'def queue_dialog_callback' 'def execute_pending_dialog_callback' 'def handle_dialog_button_click' \
    'def render_pending_streamlit_dialog_dismiss' 'def handle_dialog_dismiss' \
    '@st.dialog(title, dismissible=dismissible, on_dismiss=on_dismiss)' \
    'handle_dialog_button_click(' 'queue_dialog_callback(callback)' '_hhs_dialog_button_dismissal' \
    'handle_dialog_dismiss(dismiss_callback)' 'dismiss_streamlit_dialog()' \
    'render_pending_streamlit_dialog_dismiss()'
  assert_file_contains "${path_picker_file}" 'def render_folder_picker_dialog'
  run python3 - "${dialog_ui_file}" "${ui_file}" <<'PY'
from pathlib import Path
import sys

dialog_source = Path(sys.argv[1]).read_text()
ui_source = Path(sys.argv[2]).read_text()
callback_body = dialog_source.split("def handle_dialog_button_click", 1)[1].split("\ndef ", 1)[0]
dismiss_body = ui_source.split("def dismiss_streamlit_dialog", 1)[1].split("\ndef ", 1)[0]
assert "render_script_html(" not in callback_body
assert "st.html(" not in callback_body
assert "render_script_html(" not in dismiss_body
assert "st.html(" not in dismiss_body
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'close_callback=close_home_tool_action_dialog' 'close_callback=close_home_tool_tldr_dialog' \
    'close_callback=close_ssh_connection_dialog'
  assert_file_not_contains "${ui_file}" 'st.rerun(scope="app")'

  assert_file_contains_many "${ui_file}" \
'key="readme_open_button"' 'args=("README",)' 'key="handbook_open_button"' 'args=("HANDBOOK",)' \
    'key="terminal_open_button"' 'args=("TERMINAL",)' 'def terminal_document_view_is_active' \
    'if terminal_document_view_is_active():'
  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
terminal_button_body = ui_source.split("def render_sidebar_terminal_button()", 1)[1].split("\ndef ", 1)[0]
assert "if terminal_document_view_is_active():" in terminal_button_body
assert "return" in terminal_button_body.split('st.button(', 1)[0]
sidebar_body = ui_source.split("def render_sidebar()", 1)[1].split("\ndef ", 1)[0]
terminal_index = sidebar_body.index("render_sidebar_terminal_button()")
theme_index = sidebar_body.index("key=hhs_ui.THEME_SELECTED_KEY")
separator_index = sidebar_body.index('hhs-sidebar-separator')
connect_index = sidebar_body.index('key="ssh_connect_button"')
disconnect_index = sidebar_body.index('key="ssh_disconnect_button"')
readme_index = sidebar_body.index('key="readme_open_button"')
handbook_index = sidebar_body.index('key="handbook_open_button"')
assert connect_index < theme_index
assert disconnect_index < theme_index
assert theme_index < separator_index < readme_index < handbook_index < terminal_index
assert 'st.markdown("**Documents**")' not in sidebar_body
PY
  assert_success

  assert_file_contains "${ui_file}" 'document_key == "TERMINAL"'
  assert_file_contains "${terminal_ui_file}" 'def render_terminal_document_view'
  assert_file_contains_many "${constants_file}" \
'"document_view_active"' '"document_selected"' '"document_previous_view"'
  assert_file_contains_many "${ui_file}" \
'def open_document_view' 'def activate_terminal_document_view' 'def deactivate_terminal_document_view' \
    'def restore_terminal_document_view' 'activate_terminal_document_view()' \
    'st.session_state\[hhs_ui.TERMINAL_CWD_KEY\] = footer_working_directory()' 'def close_document_view'
  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
terminal_source = Path("bin/apps/py/hhs_ui/terminal_ui.py").read_text()
open_body = ui_source.split("def open_document_view", 1)[1].split("\ndef ", 1)[0]
close_body = ui_source.split("def close_document_view", 1)[1].split("\ndef ", 1)[0]
render_main_body = ui_source.split("def render_main_view", 1)[1].split("\ndef ", 1)[0]
terminal_render_body = terminal_source.split("def render_terminal_document_view", 1)[1].split("\ndef ", 1)[0]
terminal_init_body = terminal_source.split("def initialize_terminal_session_state", 1)[1].split("\ndef ", 1)[0]
deactivate_body = ui_source.split("def deactivate_terminal_document_view", 1)[1].split("\ndef ", 1)[0]
sync_events_body = terminal_source.split("def sync_ttyd_event_state", 1)[1].split("\ndef ", 1)[0]
ssh_connect_body = ui_source.split("def execute_pending_ssh_connection", 1)[1].split("\ndef ", 1)[0]
ssh_disconnect_body = ui_source.split("def execute_pending_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
assert 'terminal_document_view_is_active() and document_key != "TERMINAL"' not in open_body
assert "deactivate_terminal_document_view()" not in open_body
assert "if reset_terminal and terminal_document_view_is_active():" in close_body
assert "deactivate_terminal_document_view()" in close_body
assert "if not terminal_document_view_is_active():" in render_main_body
assert "render_ttyd_terminal_frame_hide_script()" in render_main_body
assert "stop_ttyd_session()" not in render_main_body
assert "push_floating_status" not in terminal_init_body
assert terminal_render_body.index(
    "initialize_terminal_session_state()"
) < terminal_render_body.index("ttyd_url = ensure_ttyd_session()")
assert terminal_render_body.index(
    "render_ttyd_terminal_frame(ttyd_url)"
) < terminal_render_body.index("render_command_preloader_events()")
assert terminal_render_body.index(
    "render_command_preloader_events()"
) < terminal_render_body.index("show_terminal_ready_status()")
assert "stop_ttyd_session()" in deactivate_body
assert "TERMINAL_READY_STATUS_SHOWN_KEY" in deactivate_body
assert "close_document_view(reset_terminal=True)" in sync_events_body
assert "deactivate_terminal_document_view()" in sync_events_body
assert "render_ttyd_terminal_frame_cleanup_script()" in ssh_connect_body
assert "stop_ttyd_session()" in ssh_connect_body
assert "render_ttyd_terminal_frame_cleanup_script()" in ssh_disconnect_body
assert "stop_ttyd_session()" in ssh_disconnect_body
PY
  assert_success

  assert_file_contains_many "${terminal_ui_file}" \
'def terminal_document_title' 'title = terminal_document_title()' 'html.escape(title)' \
    'def ttyd_binary' '/opt/homebrew/opt/ttyd/bin/ttyd' 'def ttyd_font_family' 'def ttyd_font_file' \
    'Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.otf' 'def ensure_ttyd_index_file' \
    'def fetch_ttyd_default_index' 'def inject_ttyd_font' 'def ttyd_font_face_style' \
    'def ttyd_background_image_file' 'def ttyd_background_image_data_url' 'APP_TERMINAL_BACKGROUND_FILE' \
    'data:image/png;base64,{encoded_image}' 'data:{mime_type};base64,{encoded_font}' \
    'background:#000000!important;' 'background-image:linear-gradient(rgba(0,0,0,0.90),rgba(0,0,0,0.90))' \
    'background-size:cover!important;' 'background-position:center center!important;' 'body::before' \
    '.xterm .xterm-screen,.xterm .xterm-rows,.xterm .xterm-screen canvas' \
    'hhs-ttyd-font-index-v23-terminal-scroll-v1' 'padding:0!important;' 'left:0!important;' 'top:0!important;' \
    'right:0!important;' 'bottom:0!important;' 'scrollbar-gutter:stable!important;' \
    'overflow-y:scroll!important;'
  assert_file_not_contains "${terminal_ui_file}" '#terminal,.terminal,.xterm,.xterm-viewport'

  run python3 - <<'PY'
import ast
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/terminal_ui.py").read_text(encoding="utf-8")
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
st = SimpleNamespace(session_state={})
namespace = {"st": st}
exec(functions["terminal_document_title"], namespace)

st.session_state = {}
local_title = namespace["terminal_document_title"]()
st.session_state = {"ssh_connection_status": "connected"}
remote_title = namespace["terminal_document_title"]()

assert local_title.strip()
assert remote_title.strip()
assert local_title != remote_title
PY
  assert_success

  assert_file_contains "${terminal_ui_file}" '::-webkit-scrollbar-thumb'

  assert_file_not_contains "${terminal_ui_file}" 'transform:translate(5px,5px)!important;'

  assert_file_contains_many "${terminal_ui_file}" \
'const inset = 10' 'frame.style.left = `${{rect.left + inset}}px`' \
    'frame.style.width = `${{Math.max(0, rect.width - (inset * 2))}}px`' 'background:transparent!important;'
  assert_file_not_contains "${terminal_ui_file}" 'width:calc(100% - 10px)!important;'

  assert_file_contains_many "${terminal_ui_file}" \
'def ttyd_bridge_script' "const transparentBackground='rgba(0,0,0,0)'" "applyTransparentTerminalBackground" \
    "scheduleTransparentTerminalBackground" "term.options.theme={...theme,background:transparentBackground}" \
    "term.refresh(0,Math.max(0,Number(term.rows||1)-1))" 'registerOscHandler(777' \
    'AI_TERMINAL_CONTEXT_MAX_CHARS' 'hhs-ttyd-context-request' 'hhs-ttyd-command-submit'
  assert_file_not_contains "${terminal_ui_file}" "def sendTerminalInput"

  assert_file_contains_many "${terminal_ui_file}" \
"const sendTerminalInput=(text)" "pasteSelectedTerminalText" "middleClickPasteHandler" \
    "if(Number(event.button)!==1){return;}" "navigator.clipboard.writeText(selected)" \
    "sendTerminalInput(selected)" "lastMiddlePasteAt" \
    "window.addEventListener('mousedown',middleClickPasteHandler,true)" \
    "window.addEventListener('auxclick',middleClickPasteHandler,true)" "sendTerminalInput('\\\\x03')" \
    'window.setTimeout(()=>{sendTerminalInput(`${cleanCommand}\\r`);},90);' "triggerDataEvent" "term.paste" \
    "terminal-context" "replyToRequester" "__hhsTtydTerminalContextEvent" \
    "__hhsTtydTerminalContextCacheHandler"
  assert_file_not_contains_many "${terminal_ui_file}" \
"def normalize_terminal_ai_request" "def store_terminal_ai_request" "def pop_footer_terminal_ai_request" \
    "def terminal_ai_request_endpoint_url" '"/terminal-ai-request"' "handle_terminal_ai_request"
  assert_file_contains_many "${ui_file}" \
"contextDelayMs = 700" "requestTerminalContext(true)" "requestTerminalContext(false)" \
    "waitForTerminalContextEvent(contextDelayMs)"
  assert_file_contains "${terminal_ui_file}" "parentWindow.__hhsTtydEventUrl"
  assert_file_not_contains "${terminal_ui_file}" 'def wait_for_ttyd_terminal_context_event'

  assert_file_contains_many "${terminal_ui_file}" \
"term.getSelection()" "lastSelectedContent" "cacheSelection" "rememberSelection" "term.onSelectionChange" \
    "__hhsTtydSelectionChangeDisposable" "selectionchange" "visibleBuffer"
  assert_file_not_contains "${terminal_ui_file}" 'def pop_ttyd_terminal_context_event'

  assert_file_contains_many "${terminal_ui_file}" \
"window.term.clear()" "hhs-ttyd-event"
  assert_file_not_contains "${constants_file}" 'TTYD_INDEX_FILE = ('

  assert_file_contains_many "${constants_file}" \
'TTYD_INDEX_FILE = HHS_CACHE_DIR / "streamlit-ttyd-index.html"' \
    'APP_TERMINAL_BACKGROUND_FILE = APP_DIR / "assets/images/term-bg.png"'
  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'"APP_TERMINAL_BACKGROUND_FILE"' '"TTYD_INDEX_FILE"'
  assert_file_contains_many "${terminal_ui_file}" \
'return hhs_ui.APP_FONT_FAMILY' 'def build_ttyd_command' 'def ttyd_shell_hook_script' \
    'def build_ttyd_hooked_bash_command' '__hhs_ttyd_after_command()' \
    'if \[\[ "${PWD}" != "${__hhs_ttyd_last_pwd}" \]\]; then' 'PROMPT_COMMAND="__hhs_ttyd_after_command' \
    'elif \[\[ -r "${HOME}/.bashrc" \]\]; then' 'fontFamily={ttyd_font_family()}, monospace' \
    'theme={"background":"#000000"}' 'cursorBlink=true' 'command.extend(("-I", index_file))' \
    'def build_ttyd_remote_command'
  run python3 - <<'PY'
from pathlib import Path

terminal_source = Path("bin/apps/py/hhs_ui/terminal_ui.py").read_text()
remote_body = terminal_source.split("def build_ttyd_remote_command", 1)[1].split("\ndef ", 1)[0]
assert '"ssh",' in remote_body
assert '"-tt",' in remote_body
PY
  assert_success

  assert_file_contains_many "${terminal_ui_file}" \
'ControlPath={ssh_control_path(host)}' 'def ensure_ttyd_session' 'def cleanup_session_resources' \
    'def schedule_cleanup_session_resources' 'def store_ttyd_event' 'def normalize_ttyd_event' \
    'def sync_ttyd_event_state' 'def ttyd_event_url' 'def ensure_ttyd_cleanup_server' \
    'def render_browser_cleanup_script' 'navigator.sendBeacon(cleanupUrl, "")' \
    'parentWindow.addEventListener("pagehide", cleanup, {{ once: true }})' \
    'parentWindow.addEventListener("beforeunload", cleanup, {{ once: true }})' \
    'parentWindow.addEventListener("message"' 'cleanup_all_registered_sessions'
  assert_file_contains "${constants_file}" 'PROCESS_RESOURCE_STATE_KEY = "_hhs_ui_process_resource_state"'

  assert_file_contains "${status_ui_file}" 'hhs_ui_constants.FOOTER_STATUS_LOG_RECORDS_REGISTRY_KEY'
  assert_file_contains_many "${process_resources_file}" \
'hhs_ui_constants.PROCESS_RESOURCE_STATE_KEY' 'hhs_ui_constants.FOOTER_STATUS_LOG_HANDLER_REGISTRY_KEY' \
    'hhs_ui_constants.FOOTER_STATUS_LOG_RECORDS_REGISTRY_KEY'
  assert_file_not_contains_many "${ui_file}" \
'hhs_ui.PROCESS_RESOURCE_STATE_KEY' 'hhs_ui.FOOTER_STATUS_LOG_HANDLER_REGISTRY_KEY' \
    'hhs_ui.FOOTER_STATUS_LOG_RECORDS_REGISTRY_KEY'
  assert_file_contains_many "${process_resources_file}" \
'def process_resource_state' 'def process_resource_registry'
  assert_file_contains_many "${terminal_ui_file}" \
'schedule_cleanup_session_resources(token)' \
    'atexit.register(cleanup_all_registered_sessions)' 'build_ssh_disconnect_command(ssh_host)' \
    'ttyd_process_is_running(process)' '"-q",' 'update_browser_cleanup_registration()' \
    'start_new_session=True' 'parentWindow.__hhsTtydCleanupHandler' 'parentWindow.removeEventListener(' \
    '"/open-working-directory"' 'def handle_open_working_directory_request'
  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
terminal_source = Path("bin/apps/py/hhs_ui/terminal_ui.py").read_text()
process_resources_source = Path("bin/apps/py/hhs_ui/process_resources.py").read_text()
assert '"working_dir": footer_working_directory()' in terminal_source
assert 'if request_path == "/open-working-directory":' in terminal_source
open_working_dir_body = terminal_source.split("def handle_open_working_directory_request", 1)[1].split("\n    def ", 1)[0]
assert 'entry = TTYD_CLEANUP_REGISTRY.get(token, {})' in open_working_dir_body
assert 'entry.get("ssh_host")' in open_working_dir_body
assert 'entry.get("cwd") or entry.get("working_dir")' in open_working_dir_body
assert 'build_open_directory_command(directory)' in open_working_dir_body
assert 'self.send_response(204 if result.returncode == 0 else 500)' in open_working_dir_body
handler_body = terminal_source.split("def handle_cleanup_request", 1)[1].split("\n    def ", 1)[0]
assert handler_body.index("self.send_response(204)") < handler_body.index(
    "schedule_cleanup_session_resources(token)"
)
schedule_body = terminal_source.split("def schedule_cleanup_session_resources", 1)[1].split("\ndef ", 1)[0]
assert "threading.Thread(" in schedule_body
assert "daemon=True" in schedule_body
state_body = process_resources_source.split("def process_resource_state", 1)[1].split("\ndef ", 1)[0]
assert "setattr(sys, hhs_ui_constants.PROCESS_RESOURCE_STATE_KEY, state)" in state_body
registry_body = process_resources_source.split("def process_resource_registry", 1)[1].split(
    "\n\nclass FooterStatusLogHandler", 1
)[0]
assert "state[key] = registry" in registry_body
assert "process_resource_registry(\n    \"ttyd_cleanup_registry\"" in terminal_source
assert "process_resource_registry(\n    \"ttyd_event_registry\"" in terminal_source
ensure_body = terminal_source.split("def ensure_ttyd_cleanup_server", 1)[1].split("\ndef ", 1)[0]
assert "process_resource_state()" in ensure_body
assert "ThreadingHTTPServer(" in ensure_body
assert 'state["ttyd_cleanup_server"] = server' in ensure_body
assert 'state["ttyd_cleanup_server_port"] = port' in ensure_body
assert 'state["ttyd_cleanup_atexit_registered"] = True' in ensure_body
browser_cleanup_body = terminal_source.split("def render_browser_cleanup_script", 1)[1].split("\ndef ", 1)[0]
assert browser_cleanup_body.index("removeEventListener(") < browser_cleanup_body.index(
    "parentWindow.addEventListener(\"pagehide\", cleanup"
)
assert "parentWindow.__hhsTtydCleanupHandler = cleanup" in browser_cleanup_body
assert 'link.dataset.hhsWorkingDir = cwd' in browser_cleanup_body
assert 'link.title = `Working dir: ${{cwd}}`' in browser_cleanup_body
PY
  assert_success

  assert_file_contains_many "${terminal_ui_file}" \
'os.killpg(process_group, signal.SIGTERM)' 'os.killpg(process_group, signal.SIGKILL)' 'subprocess.Popen('
  run python3 - "${status_ui_file}" "${command_runtime_file}" <<'PY'
from pathlib import Path
import sys

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
status_source = Path(sys.argv[1]).read_text()
command_runtime_source = Path(sys.argv[2]).read_text()
process_resources_source = Path("bin/apps/py/hhs_ui/process_resources.py").read_text()
main_body = ui_source.split("def main()", 1)[1].split('\nif __name__ == "__main__":', 1)[0]
disconnect_index = main_body.index("execute_pending_ssh_disconnection()")
connect_index = main_body.index("execute_pending_ssh_connection()")
ssh_dialog_index = main_body.index("render_ssh_connection_dialog()")
ai_initialize_index = main_body.index("initialize_ollama_service_availability()")
ai_refresh_index = main_body.index("update_ollama_service_availability_refresh()")
background_poll_index = main_body.index("render_background_job_polling_fragment()")
footer_actions_index = main_body.index("handle_footer_actions()")
updater_status_index = main_body.index("render_background_job_status(UPDATER_UPDATE_JOB)")
shell_dialog_index = main_body.index("render_footer_shell_version_dialog()")
cleanup_index = main_body.index("render_browser_cleanup_script()")
sidebar_index = main_body.index("render_sidebar()")
main_view_index = main_body.index("render_main_view()")
footer_index = main_body.index("render_footer_status_fragment()")
client_status_index = main_body.index("render_footer_client_error_bridge_script()")
assert main_body.index("install_footer_status_log_handler()") < main_body.index(
    "selected_theme = persisted_theme_name()"
)
assert 'st.session_state.setdefault("updater_check_context", "local")' in main_body
assert 'st.session_state.setdefault("updater_check_started_context", "")' in main_body
assert 'st.session_state.setdefault("updater_remote_checked_context", "")' in main_body
assert 'execute_mount_updater_check()' in main_body
assert "execute_due_updater_check()" not in main_body
assert 'if st.session_state["active_view"] not in main_views():' not in main_body
assert background_poll_index < disconnect_index < connect_index < ssh_dialog_index
assert ssh_dialog_index < ai_initialize_index < ai_refresh_index < footer_actions_index
assert footer_actions_index < updater_status_index < shell_dialog_index
assert shell_dialog_index < sidebar_index < main_view_index
assert footer_index < client_status_index < cleanup_index
footer_status_body = ui_source.split("def render_footer_status_fragment", 1)[1].split("\ndef ", 1)[0]
footer_status_decorator = ui_source[: ui_source.index("def render_footer_status_fragment")].rstrip().splitlines()[-1]
background_poll_prefix = command_runtime_source[
    : command_runtime_source.index("def render_background_job_polling_fragment")
]
background_poll_decorator = background_poll_prefix.rstrip().splitlines()[-1]
background_status_decorator = command_runtime_source[
    : command_runtime_source.index("def render_background_job_status")
].rstrip().splitlines()[-1]
assert not footer_status_decorator.startswith('@st.fragment')
assert background_poll_decorator == '@st.fragment(run_every="2s")'
assert background_status_decorator != '@st.fragment(run_every="2s")'
assert 'execute_due_updater_check()' in footer_status_body
assert 'drain_footer_status_log_records()' in footer_status_body
assert 'render_footer()' in footer_status_body
assert 'render_floating_status()' in footer_status_body
assert 'parallel=True' not in footer_status_body
assert "class FooterStatusLogHandler(logging.Handler)" in process_resources_source
assert "logging.captureWarnings(True)" in process_resources_source
assert "def drain_footer_status_log_records(" in status_source
assert "def render_footer_client_error_bridge_script(" in ui_source
assert "Missing Submit Button" in ui_source or "missing submit button" in ui_source
PY
  assert_success

  assert_file_contains_many "${terminal_ui_file}" \
'def render_ttyd_terminal_frame' 'hhs-persistent-ttyd-frame' 'dataset.src !== src' \
    'def render_ttyd_terminal_frame_cleanup_script' 'def render_ttyd_terminal_frame_hide_script' \
    'render_ttyd_terminal_frame_hide_script()' 'frame.style.display = "none"' 'stop_ttyd_session()'
  assert_file_contains "${constants_file}" 'TERMINAL_READY_STATUS_SHOWN_KEY = "terminal_ready_status_shown"'

  assert_file_contains_many "${terminal_ui_file}" \
'st.session_state.setdefault(hhs_ui.TERMINAL_CWD_KEY, footer_working_directory())' \
    '"HomeSetup terminal is ready."' 'ttyd_url = ensure_ttyd_session()'
  assert_file_not_contains_many "${ui_file}" \
'def hhs_terminal_component' 'def render_terminal_component' 'def execute_terminal_command'
  assert_file_not_contains_many "${constants_file}" \
'TERMINAL_COMPONENT_DIR' 'TERMINAL_TRANSCRIPT_KEY'
  assert_file_not_contains "${css_file}" '.st-key-hhs_terminal_component iframe'

  assert_file_contains_many "${css_file}" \
'.hhs-ttyd-terminal-frame' '.hhs-ttyd-terminal-placeholder' 'padding: 10px' \
    'height: calc(100dvh - var(--hhs-footer-guard-height) - 4.75rem)' \
    'height: calc(100dvh - var(--hhs-footer-guard-height) - 4.75rem - var(--hhs-ttyd-shell-gap))' \
    'margin: var(--hhs-ttyd-shell-gap) 0 0'
  terminal_double_gap_height='height: calc(100dvh - var(--hhs-footer-guard-height) - 4.75rem'
  terminal_double_gap_height+=' - (var(--hhs-ttyd-shell-gap) \* 2))'
  assert_file_not_contains "${css_file}" "${terminal_double_gap_height}"

  assert_file_contains_many "${css_file}" \
'max-height: var(--hhs-ttyd-max-height, 760px)' 'background: var(--hhs-terminal-background-color, #000000)' \
    'height: calc(100% - 20px)' 'width: calc(100% - 20px)'
  for theme_file in "${HHS_REPO_DIR}"/bin/apps/py/hhs_ui/themes/*.css; do
    run grep -q -- '--hhs-terminal-background-color: #000000' "${theme_file}"
    assert_success

    assert_file_contains "${theme_file}" 'background: var(--hhs-terminal-background-color)'
  done

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
feedback_source = Path("bin/apps/py/hhs_ui/feedback_ui.py").read_text()
dialog_source = Path("bin/apps/py/hhs_ui/dialog_ui.py").read_text()
assert ui_source.count("@st.dialog(") == 0
assert feedback_source.count("@st.dialog(") == 0
assert dialog_source.count("@st.dialog(") == 1
PY
  assert_success

  assert_file_not_contains_many "${ui_file}" \
'st.warning("Clear the chat and reset AI context entirely?")' '@st.dialog("Confirm model change")' \
    '@st.dialog("Confirm model deletion")'
}
