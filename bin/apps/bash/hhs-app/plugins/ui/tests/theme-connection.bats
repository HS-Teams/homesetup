#!/usr/bin/env bats

#  Script: theme-connection.bats
# Purpose: HomeSetup Streamlit UI theme connection and cache tests.
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

@test "when styling HomeSetup UI then selected-item and footer styling should be configured" {
  run grep -q -- '--hhs-selected-item-label: var(--hhs-theme-text-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-selected-item-value: var(--hhs-success)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-theme-primary-color: var(' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/pastel-powerline.css"
  assert_failure

  run grep -q -- '--hhs-theme-link-color: var(' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/pastel-powerline.css"
  assert_failure

  run python3 - "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/pastel-powerline.css" "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/jetpack.css" <<'PY'
import re
import sys
from pathlib import Path

for theme_file in sys.argv[1:]:
    for line in Path(theme_file).read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if clean_line.startswith("--hhs-theme-file-link-color:"):
            continue
        assert not re.match(r"--hhs-theme-[^:]+:\s*var\(", clean_line), clean_line
PY
  assert_success

  run python3 - <<'PY'
import re
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
cache_runtime_source = Path("bin/apps/py/hhs_ui/execution/cache_runtime.py").read_text()
status_source = Path("bin/apps/py/hhs_ui/widgets/status_ui.py").read_text()
base_css = Path("bin/apps/py/hhs_ui/streamlit_ui.css").read_text()
dracula_css = Path("bin/apps/py/hhs_ui/themes/dracula.css").read_text()
homesetup_css = Path("bin/apps/py/hhs_ui/themes/homesetup.css").read_text()
jetpack_css = Path("bin/apps/py/hhs_ui/themes/jetpack.css").read_text()
pastel_powerline_css = Path("bin/apps/py/hhs_ui/themes/pastel-powerline.css").read_text()
tokyo_night_css = Path("bin/apps/py/hhs_ui/themes/tokyo-night.css").read_text()

assert 'class="hhs-footer-logo"' in ui_source
assert 'class="hhs-footer-logo-link"' in ui_source
assert 'hhs-footer-link' in ui_source
assert 'class="hhs-footer-shell-status"' in ui_source
assert 'class="hhs-footer-shell-name">{shell_name}</span>' in ui_source
assert 'href="{shell_version_url}"' in ui_source
assert 'target="_self" title="Show bash version" aria-label="Show bash version"' in ui_source
assert 'os.environ.get("HHS_MY_SHELL", "").strip().upper()' in ui_source
assert 'class="hhs-footer-remote-status"' in ui_source
footer_template = ui_source.split('<footer class="hhs-app-footer">', 1)[1].split('</footer>', 1)[0]
assert 'status_group_markup = (' in ui_source
assert 'f"{remote_status_markup}{shell_controls_markup}"' in ui_source
assert "{status_group_markup}" in footer_template
assert "st.html(" in ui_source
assert 'class="hhs-script-only"' in ui_source
assert "unsafe_allow_javascript=True" in ui_source
assert 'class="hhs-footer-glyph"></span>' in ui_source
assert 'Connected to remote  {connected_host_display}' in ui_source
assert 'os.environ.get("HHS_GITHUB_URL", "#")' in ui_source
homesetup_version_body = ui_source.split("def homesetup_version", 1)[1].split("\ndef ", 1)[0]
remember_homesetup_version_body = ui_source.split("def remember_footer_homesetup_version", 1)[1].split("\ndef ", 1)[0]
local_homesetup_version_body = ui_source.split("def local_homesetup_version", 1)[1].split("\ndef ", 1)[0]
start_footer_version_body = ui_source.split("def start_footer_homesetup_version_refresh", 1)[1].split("\ndef ", 1)[0]
complete_footer_version_body = ui_source.split("def complete_footer_homesetup_version_refresh", 1)[1].split("\ndef ", 1)[0]
assert "context = footer_version_context()" in homesetup_version_body
assert "command = build_homesetup_version_command()" in homesetup_version_body
assert "cached_background_command_result(\n        command, FOOTER_VERSION_CACHE_TAG" in homesetup_version_body
assert "start_footer_homesetup_version_refresh(command, context)" in homesetup_version_body
assert 'return version or "loading"' in local_homesetup_version_body
assert "background_command_metadata(command, FOOTER_VERSION_CACHE_TAG)" in start_footer_version_body
assert "force_local=True" not in start_footer_version_body
assert "record_footer_homesetup_version_error(context, result)" in complete_footer_version_body
assert "clear_disconnected_ssh_host" not in complete_footer_version_body
assert 'st.session_state["footer_hhs_version_cache_loaded"] = True' in remember_homesetup_version_body
assert "fallback_footer_homesetup_version(context)" in homesetup_version_body
assert 'def build_homesetup_version_command' in ui_source
assert 'FOOTER_VERSION_OUTPUT_MARKER' in ui_source
assert 'def parse_homesetup_version_output' in ui_source
assert 'def record_footer_homesetup_version_error' in ui_source
assert 'hhs_ui.VERSION' not in homesetup_version_body
constants_source = Path("bin/apps/py/hhs_ui/core/constants.py").read_text()
init_source = Path("bin/apps/py/hhs_ui/__init__.py").read_text()
assert 'FOOTER_OPEN_WORKING_DIR_QUERY_PARAM = "hhs_open_working_dir"' in constants_source
assert 'FOOTER_RUN_UPDATER_QUERY_PARAM = "hhs_run_updater_update"' in constants_source
assert 'FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM = "hhs_show_shell_version"' in constants_source
assert 'FOOTER_ASK_TERMINAL_QUERY_PARAM' not in constants_source
assert 'FOOTER_ASK_TERMINAL_PROMPT_QUERY_PARAM' not in constants_source
assert 'FOOTER_ASK_TERMINAL_REQUEST_QUERY_PARAM' not in constants_source
assert 'FOOTER_CLEAR_CACHE_QUERY_PARAM = "hhs_clear_cache"' in constants_source
assert 'FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM = "hhs_clear_application_cache"' in constants_source
assert 'FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM = "hhs_clear_application_states"' in constants_source
assert 'FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM = "hhs_clear_ai_history"' in constants_source
assert 'COMMAND_PRELOADER_CANCEL_QUERY_PARAM = "hhs_cancel_preloader"' in constants_source
assert 'FLOATING_STATUS_AUTO_DISPOSE_EXTENSION_SECONDS = 1.0' in constants_source
assert 'AI_TERMINAL_CONTEXT_MAX_CHARS = 12000' in constants_source
assert 'FOOTER_DISMISS_STATUS_QUERY_PARAM' not in constants_source
assert 'FLOATING_STATUS_AUTO_DISPOSE_EXTENSION_SECONDS' in init_source
assert 'FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM' in init_source
assert 'COMMAND_PRELOADER_CANCEL_QUERY_PARAM' in init_source
assert 'FOOTER_ASK_TERMINAL_QUERY_PARAM' not in init_source
assert 'FOOTER_ASK_TERMINAL_PROMPT_QUERY_PARAM' not in init_source
assert 'FOOTER_ASK_TERMINAL_REQUEST_QUERY_PARAM' not in init_source
assert 'FOOTER_CLEAR_CACHE_QUERY_PARAM' in init_source
assert 'FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM' in init_source
assert 'FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM' in init_source
assert 'FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM' in init_source
assert 'FOOTER_DISMISS_STATUS_QUERY_PARAM' not in init_source
assert '"updater_last_check_epoch"' not in constants_source
assert '"updater_last_check_output"' in constants_source
assert '"updater_update_available"' in constants_source
assert 'class="hhs-footer-link hhs-footer-repository-link"' in ui_source
assert 'class="hhs-footer-link hhs-footer-working-dir-link"' in ui_source
assert 'class="hhs-footer-working-dir-value"' in ui_source
assert 'href="{working_dir_url}"' in ui_source
assert 'target="_self"{working_dir_attrs}>Working dir: <span class="hhs-footer-working-dir-value">' in ui_source
render_footer_body = ui_source.split("def render_footer()", 1)[1].split("\ndef ", 1)[0]
cache_clear_script_body = ui_source.split("def render_footer_cache_clear_menu_script", 1)[1].split("\ndef ", 1)[0]
assert 'working_dir = html.escape(footer_working_directory())' in render_footer_body
assert 'os.getcwd()' not in render_footer_body
assert 'connected_to_ssh = bool(connected_ssh_host())' in render_footer_body
assert 'working_dir_url = f"?{hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM}=1"' in render_footer_body
assert 'data-open-working-dir-url="{working_dir_open_url}" role="button"' in render_footer_body
assert 'render_footer_working_directory_open_script()' in render_footer_body
assert 'class="hhs-footer-version-group"' in ui_source
assert 'class="hhs-footer-spacer"' not in ui_source
assert 'class="hhs-footer-update-link"' in ui_source
assert 'href="{update_url}" target="_self"' in ui_source
assert '' in ui_source
assert 'class="hhs-footer-shell-group"' in ui_source
assert 'def footer_cache_clear_menu_markup' in ui_source
assert 'def render_footer_cache_clear_menu_script' in ui_source
assert 'def footer_terminal_ai_menu_markup(enabled: bool)' in ui_source
assert 'def render_footer_terminal_ai_menu_script' in ui_source
assert '<details class="hhs-footer-cache-clear-menu">' in ui_source
assert '<summary class="hhs-footer-cache-clear-trigger"' in ui_source
assert '<details class="hhs-footer-terminal-ai-menu">' in ui_source
assert '<summary class="hhs-footer-terminal-ai-trigger"' in ui_source
assert 'hhs-footer-terminal-ai-menu--disabled' in ui_source
assert 'hhs-footer-terminal-ai-trigger--disabled' in ui_source
assert 'aria-disabled="true"' in ui_source
assert 'Open Terminal to ask AI about terminal output' in ui_source
assert '<form class="hhs-footer-cache-clear-form" method="get">' not in ui_source
assert '<div class="hhs-footer-cache-clear-panel" data-clear-param="{clear_param}">' in ui_source
assert '<div class="hhs-footer-terminal-ai-panel" data-default-prompt="{default_prompt}">' in ui_source
assert 'class="hhs-footer-terminal-ai-prompt-input"' in ui_source
assert 'class="hhs-footer-terminal-ai-prompt-input"\n              type="text"\n              value=""\n              placeholder="{default_prompt}"' in ui_source
assert 'value="{default_prompt}"' not in ui_source
assert '<label class="hhs-footer-terminal-ai-context-preview">' in ui_source
assert 'class="hhs-footer-terminal-ai-context-input"' in ui_source
assert 'placeholder="Terminal text"' in ui_source
assert 'aria-label="Captured terminal text"' in ui_source
assert 'readonly' in ui_source
assert '<button type="button">OK</button>' in ui_source
assert 'panel.querySelectorAll(\'input[type="checkbox"][data-param]:checked\')' in ui_source
assert 'params.set(panel.dataset.clearParam, "1")' in ui_source
assert 'window.parent.__hhsFooterCacheClearOutsideHandler' in ui_source
assert 'window.parent.__hhsFooterCacheClearOutsideFocusHandler' in cache_clear_script_body
assert 'doc.addEventListener("focusin", outsidePointerHandler, true)' in cache_clear_script_body
assert 'window.parent.addEventListener("blur", outsideFocusHandler, true)' in cache_clear_script_body
assert 'doc.querySelectorAll(".hhs-footer-terminal-ai-menu[open]")' in ui_source
assert 'doc.addEventListener("pointerdown", outsidePointerHandler, true)' in ui_source
assert 'terminal_ai_ask_command_prefix = build_hhs_ask_plugin_command(' not in ui_source
assert 'const terminalAskCommandPrefix' not in ui_source
assert 'let currentTerminalContextEvent = null' in ui_source
assert 'type: "hhs-ttyd-context-request"' in ui_source
assert 'const trigger = menu?.querySelector(".hhs-footer-terminal-ai-trigger")' in ui_source
assert 'const contextInput = panel.querySelector(".hhs-footer-terminal-ai-context-input")' in ui_source
assert 'const shellSingleQuote = (value)' in ui_source
assert "replace(/'/g" in ui_source
assert 'const shellDoubleQuote = (value) => JSON.stringify(String(value || ""))' in ui_source
assert 'const buildTerminalAskPrompt = (instruction) =>' in ui_source
assert 'const buildTerminalAskContext = (terminalEvent)' in ui_source
assert 'const buildTerminalAskCommand = (instruction, terminalEvent)' in ui_source
assert '`echo ${{shellSingleQuote(buildTerminalAskContext(terminalEvent))}} | __hhs ask execute ${{shellDoubleQuote(buildTerminalAskPrompt(instruction))}}`' in ui_source
assert '`echo ${{shellSingleQuote(buildTerminalAskPayload(instruction, terminalEvent))}} | __hhs ask execute`' not in ui_source
assert '`__hhs ask execute ${{shellDoubleQuote(buildTerminalAskPrompt(instruction, terminalEvent))}}`' not in ui_source
assert 'const submitTerminalCommand = (command)' in ui_source
assert 'type: "hhs-ttyd-command-submit"' in ui_source
assert 'submitTerminalCommand(command)' in ui_source
assert 'const contextPreviewMaxChars = 180' in ui_source
assert 'return `${{cleanValue.slice(0, contextPreviewMaxChars - 1)}}…`' in ui_source
assert 'const terminalEventMatchesRequest = (terminalEvent)' in ui_source
assert 'const applyTerminalContextEvent = (terminalEvent)' in ui_source
assert 'currentTerminalContextEvent = terminalEvent' in ui_source
assert 'const matchingTerminalContextEvent = ()' in ui_source
assert 'currentTerminalContextEvent || window.parent.__hhsTtydTerminalContextEvent' in ui_source
assert 'const refreshTerminalContextPreview = ()' in ui_source
assert 'applyTerminalContextEvent(window.parent.__hhsTtydTerminalContextEvent)' in ui_source
assert 'const closeMenu = ()' in ui_source
assert 'const resetTerminalInputs = ()' in ui_source
assert 'input.value = ""' in ui_source
assert 'const terminalContextHandler = (event)' in ui_source
assert 'window.addEventListener("message", terminalContextHandler)' in ui_source
assert 'if (window !== window.parent)' in ui_source
assert 'window.parent.__hhsFooterTerminalAiOutsideHandler' in ui_source
assert 'if (!menu || !menu.open || menu.contains(event.target))' in ui_source
assert 'setTerminalContextPreview(terminalEvent.content || "")' in ui_source
assert 'window.setTimeout(refreshTerminalContextPreview, 80)' in ui_source
assert 'window.setTimeout(refreshTerminalContextPreview, 220)' in ui_source
assert 'trigger?.addEventListener("pointerdown"' in ui_source
assert 'requestTerminalContext(false)' in ui_source
assert 'menu.removeAttribute("open")' in ui_source
assert 'const submitted = submitTerminalCommand(command)' in ui_source
assert 'if (submitted)' in ui_source
assert 'resetTerminalInputs()' in ui_source
assert 'closeMenu()' in ui_source
assert 'const prompt = (input?.value || defaultPrompt).trim() || defaultPrompt' in ui_source
terminal_ai_script_body = ui_source.split("def render_footer_terminal_ai_menu_script", 1)[1].split("\ndef ", 1)[0]
assert "window.parent.location.search" not in terminal_ai_script_body
assert "await fetch(terminalAiRequestUrl" not in terminal_ai_script_body
assert "__hhs ask execute -k" not in terminal_ai_script_body
assert "submitBridgeRerun" not in terminal_ai_script_body
assert "context: terminalEvent || {{}}" not in terminal_ai_script_body
assert ".st-key-footer_terminal_ai_bridge_container" not in terminal_ai_script_body
assert 'render_footer_cache_clear_menu_script()' in ui_source
assert 'render_footer_terminal_ai_menu_script()' in ui_source
assert 'terminal_ai_enabled = terminal_document_view_is_active()' in render_footer_body
assert 'footer_terminal_ai_menu_markup(terminal_ai_enabled)' in render_footer_body
assert 'if terminal_ai_enabled:\n            render_footer_terminal_ai_menu_script()' in render_footer_body
assert 'key=FOOTER_TERMINAL_AI_BRIDGE_BUTTON_KEY' not in ui_source
assert 'key=FOOTER_TERMINAL_AI_BRIDGE_CONTAINER_KEY' not in ui_source
assert 'on_click=handle_footer_terminal_ai_bridge_button' not in ui_source
assert 'key=FOOTER_TERMINAL_AI_BRIDGE_BUTTON_KEY' not in render_footer_body
assert 'key=FOOTER_TERMINAL_AI_BRIDGE_CONTAINER_KEY' not in render_footer_body
assert 'href="{cache_clear_url}"' not in ui_source
assert 'key="footer_cache_clear_button"' not in ui_source
assert 'on_click=open_footer_cache_clear_menu' not in ui_source
assert 'f\'<span class="hhs-footer-glyph"></span>\'' in ui_source
assert '<span class="hhs-footer-glyph-button">♻</span>' in ui_source
assert '<span class="hhs-footer-glyph-button"></span>' in ui_source
assert "hhs-footer-cache-refresh-glyph" not in ui_source
assert "hhs-footer-terminal-ai-glyph" not in ui_source
assert 'Explain me this' in ui_source
assert '<a class="hhs-footer-cache-clear-button" href="{cache_clear_url}"' not in ui_source
assert '<span class="hhs-footer-glyph"></span><span class="hhs-footer-cache-refresh-glyph">♻</span></a>' not in ui_source
assert 'def render_footer_cache_clear_menu(' not in ui_source
assert 'st.container(key="footer_cache_clear_menu")' not in ui_source
assert 'f"{shell_status_markup}{cache_clear_markup}{terminal_ai_markup}</span>"' in ui_source
assert '>Clear application cache</span>' in ui_source
assert '>Clear application states</span>' in ui_source
assert '>Clear AI history</span>' in ui_source
assert '>OK</button>' in ui_source
assert 'def open_file' in ui_source
assert 'def open_working_directory_endpoint_url' in ui_source
open_working_directory_endpoint_body = ui_source.split("def open_working_directory_endpoint_url", 1)[1].split("\ndef ", 1)[0]
assert 'update_browser_cleanup_registration()' in open_working_directory_endpoint_body
assert 'def render_footer_working_directory_open_script' in ui_source
working_dir_open_script_body = ui_source.split("def render_footer_working_directory_open_script", 1)[1].split("\ndef ", 1)[0]
assert 'open-working-directory?token={token}' in ui_source
assert 'window.parent.__hhsFooterWorkingDirOpenHandler' in working_dir_open_script_body
assert 'const selector = ".hhs-footer-working-dir-link[data-open-working-dir-url]"' in working_dir_open_script_body
assert 'const fallback = () =>' in working_dir_open_script_body
assert 'window.parent.location.href = href' in working_dir_open_script_body
assert 'event.preventDefault()' in working_dir_open_script_body
assert 'fetch(link.dataset.openWorkingDirUrl || openUrl' in working_dir_open_script_body
assert 'if (!response.ok)' in working_dir_open_script_body
assert '.catch(fallback)' in working_dir_open_script_body
assert 'window.parent.location.search' not in working_dir_open_script_body
assert 'def run_open_working_directory' in ui_source
assert 'def open_footer_working_directory' in ui_source
open_footer_working_directory_body = ui_source.split("def open_footer_working_directory", 1)[1].split("\ndef ", 1)[0]
assert 'working_dir = footer_working_directory()' in open_footer_working_directory_body
assert 'if connected_ssh_host():' in open_footer_working_directory_body
assert 'st.session_state["active_view"] = hhs_ui.SSH_VIEW' in open_footer_working_directory_body
assert 'st.session_state["ssh_view"] = "FILES"' in open_footer_working_directory_body
assert 'open_remote_explorer_path(working_dir)' in open_footer_working_directory_body
assert 'run_open_working_directory(working_dir)' in open_footer_working_directory_body
assert 'def build_footer_working_directory_command' in ui_source
assert 'return r' in ui_source and '__HHS_UI_PWD__' in ui_source and '\\pwd' in ui_source
assert 'def parse_footer_working_directory_output' in ui_source
assert 'def update_remote_footer_working_directory' in ui_source
assert 'def footer_working_directory' in ui_source
handle_footer_actions_body = ui_source.split("def handle_footer_actions", 1)[1].split("\ndef ", 1)[0]
assert "open_footer_working_directory()" in handle_footer_actions_body
footer_working_directory_body = ui_source.split("def footer_working_directory", 1)[1].split("\ndef ", 1)[0]
assert 'hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY' in footer_working_directory_body
assert 'return os.getcwd()' in footer_working_directory_body
assert 'def run_shell_version' in ui_source
assert 'def shell_version_command' in ui_source
assert 'return r"${BASH:-bash} --version"' in ui_source
assert 'shell_version_command()' in ui_source
assert '"Checking shell version..."' in ui_source
run_shell_version_body = ui_source.split("def run_shell_version", 1)[1].split("\ndef ", 1)[0]
assert "force_local=True" not in run_shell_version_body
assert 'def shell_version_output_html' in ui_source
assert 'html.escape(output)' in ui_source
assert 're.sub(r"\\r\\n|\\n|\\r", "<br>", escaped_output)' in ui_source
assert 'def render_footer_shell_version_dialog' in ui_source
assert 'render_footer_shell_version_dialog()' in ui_source
assert 'shell_version_output_html(output or "No output.")' in ui_source
assert 'css_classes="hhs-shell-version-output"' in ui_source
assert 'content_is_html=True' in ui_source
assert 'footer_shell_version_dialog_title' in ui_source
assert 'footer_shell_version_output' in ui_source
assert 'hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM' in ui_source
assert 'footer_shell_version_dialog_close_button' in ui_source
assert 'def build_hhs_updater_command' in ui_source
assert 'def start_updater_check' in ui_source
footer_actions_body = ui_source.split("def handle_footer_actions", 1)[1].split("\ndef ", 1)[0]
assert "clear_footer_shell_version_dialog()" in footer_actions_body
shell_result_index = footer_actions_body.index("result = run_shell_version()")
shell_output_index = footer_actions_body.index('st.session_state["footer_shell_version_output"]')
shell_title_index = footer_actions_body.index('st.session_state["footer_shell_version_dialog_title"] = "Shell version"')
assert shell_result_index < shell_output_index < shell_title_index
assert 'cache_delete_tag("env")' in footer_actions_body
assert "cache_delete_tag(FOOTER_VERSION_CACHE_TAG)" in footer_actions_body
assert 'st.session_state["footer_hhs_version_cache_loaded"] = False' in footer_actions_body
assert 'hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM' in footer_actions_body
assert 'hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM' in footer_actions_body
assert 'hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM' in footer_actions_body
assert 'hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM' in footer_actions_body
assert 'handle_command_preloader_cancel_action()' in footer_actions_body
assert 'hhs_ui.FOOTER_ASK_TERMINAL_QUERY_PARAM' not in footer_actions_body
assert 'hhs_ui.FOOTER_ASK_TERMINAL_PROMPT_QUERY_PARAM' not in footer_actions_body
assert 'hhs_ui.FOOTER_ASK_TERMINAL_REQUEST_QUERY_PARAM' not in footer_actions_body
assert 'hhs_ui.FOOTER_DISMISS_STATUS_QUERY_PARAM' not in footer_actions_body
assert 'pop_floating_status()' not in footer_actions_body
assert 'remove_footer_ask_terminal_query_params()' not in footer_actions_body
assert 'FOOTER_TERMINAL_AI_BRIDGE_BUTTON_KEY' not in footer_actions_body
assert 'remove_footer_cache_clear_query_params()' in footer_actions_body
assert 'apply_footer_cache_clear_options(' in footer_actions_body
assert 'open_footer_cache_clear_menu()' not in footer_actions_body
assert 'clear_cached_ui_data_preserving_state()' not in footer_actions_body
assert 'def cache_delete_command' in cache_runtime_source
assert 'cache_delete_command(command, "env")' in ui_source
clear_cache_body = cache_runtime_source.split("def clear_cached_ui_data_preserving_state", 1)[1].split("\ndef ", 1)[0]
assert "cache_clear()" in clear_cache_body
assert "st.session_state.clear()" not in clear_cache_body
assert "UI_STATE_FILE" not in clear_cache_body
assert "push_floating_status" in clear_cache_body
apply_cache_options_body = ui_source.split("def apply_footer_cache_clear_options", 1)[1].split("\ndef ", 1)[0]
assert "clear_cached_ui_data_preserving_state(show_status=False)" in apply_cache_options_body
assert "clear_application_state_data()" in apply_cache_options_body
assert "clear_ai_chat_history()" in apply_cache_options_body
assert "clear_ai_chat_history_data()" not in apply_cache_options_body
assert "AI history clear queued." in apply_cache_options_body
assert "selected_footer_cleanup_labels(" in apply_cache_options_body
assert "st.rerun()" not in apply_cache_options_body
remove_cache_params_body = ui_source.split("def remove_footer_cache_clear_query_params", 1)[1].split("\ndef ", 1)[0]
assert "hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM" in remove_cache_params_body
assert "hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM" in remove_cache_params_body
assert "hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM" in remove_cache_params_body
assert "hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM" in remove_cache_params_body
assert "def remove_footer_ask_terminal_query_params" not in ui_source
assert "def apply_footer_terminal_ai_request" not in ui_source
assert "def handle_footer_terminal_ai_bridge_button" not in ui_source
assert "def render_footer_terminal_ai_bridge_button" not in ui_source
assert "pop_footer_terminal_ai_request" not in ui_source
assert "terminal_ai_request_endpoint_url" not in ui_source
assert '"/terminal-ai-request"' not in ui_source
state_clear_body = ui_source.split("def clear_application_state_data", 1)[1].split("\ndef ", 1)[0]
assert "for state_file in ui_state_files()" in state_clear_body
assert "state_file.unlink" in state_clear_body
assert "is_persisted_ui_key" in state_clear_body
assert 'def updater_output_has_updates' in ui_source
assert 'def updater_check_due' not in ui_source
assert 'def updater_check_context' in ui_source
assert 'def restore_local_updater_status' in ui_source
assert 'def reset_updater_remote_check_state' in ui_source
assert 'def start_updater_check' in ui_source
assert 'def store_updater_check_result' in ui_source
assert 'def execute_due_updater_check' in ui_source
assert 'def execute_mount_updater_check' in ui_source
assert 'execute_due_updater_check()' in ui_source
constants_source = Path("bin/apps/py/hhs_ui/core/constants.py").read_text()
assert "UPDATER_CHECK_INTERVAL_SECONDS" not in constants_source
assert "UPDATER_CHECK_INTERVAL_SECONDS" not in init_source
store_updater_body = ui_source.split("def store_updater_check_result", 1)[1].split("\ndef ", 1)[0]
assert 'context: str = "local"' in store_updater_body
assert 'st.session_state["updater_check_started_context"] = ""' in store_updater_body
assert 'st.session_state["updater_check_context"] = context' in store_updater_body
assert 'st.session_state["updater_last_check_epoch"]' not in store_updater_body
assert 'st.session_state["updater_last_check_output"] = output' in store_updater_body
assert 'result.returncode == 0 and updater_output_has_updates(output)' in store_updater_body
assert 'if context == "local":' in store_updater_body
assert 'st.session_state["updater_remote_checked_context"] = context' in store_updater_body
assert 'save_ui_state()' in store_updater_body
execute_updater_body = ui_source.split("def execute_due_updater_check", 1)[1].split("\ndef ", 1)[0]
assert 'current_context = updater_check_context()' in execute_updater_body
assert 'restore_local_updater_status()' in execute_updater_body
assert 'updater_remote_checked_context' in execute_updater_body
assert 'start_updater_check(current_context, force_local=False)' in execute_updater_body
assert 'start_updater_check("local", force_local=True)' in execute_updater_body
assert 'updater_check_due()' not in execute_updater_body
mount_updater_body = ui_source.split("def execute_mount_updater_check", 1)[1].split("\ndef ", 1)[0]
assert 'updater_mount_check_attempted' in mount_updater_body
assert 'st.session_state["updater_check_attempted"] = True' in mount_updater_body
assert 'background_job_is_running(UPDATER_CHECK_JOB)' in mount_updater_body
assert 'start_updater_check("local", force_local=True, show_preloader_event=False)' in mount_updater_body
start_updater_body = ui_source.split("def start_updater_check", 1)[1].split("\ndef ", 1)[0]
assert 'metadata={"updater_context": context}' in start_updater_body
assert 'show_preloader_event=show_preloader_event' in start_updater_body
assert 'st.session_state["updater_check_started_context"] = context' in start_updater_body
reset_updater_body = ui_source.split("def reset_updater_remote_check_state", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["updater_check_started_context"] = ""' in reset_updater_body
assert 'st.session_state["updater_remote_checked_context"] = ""' in reset_updater_body
assert 'st.session_state["updater_check_context"] = ""' in reset_updater_body
assert 'st.session_state["updater_update_available"] = False' in reset_updater_body
assert '__hhs updater execute "{safe_operation}"' in ui_source
assert 'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")";' in ui_source
assert 'printf "y\\\\n" | ' in ui_source
assert 'def handle_footer_actions' in ui_source
assert 'force_local=not bool(connected_ssh_host())' in footer_actions_body
assert 'metadata={"updater_context": updater_check_context()}' in footer_actions_body
assert 'def push_floating_status' in status_source
assert 'def pop_floating_status' in status_source
assert 'def current_floating_status' in status_source
assert 'def effective_floating_status_timeout' in status_source
assert 'hhs_ui_constants.FLOATING_STATUS_AUTO_DISPOSE_EXTENSION_SECONDS' in status_source
assert 'def floating_status_dom_id' in status_source
assert 'def render_floating_status_dispose_script' in status_source
assert 'hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY' in status_source
assert 'def render_floating_status' in status_source
assert 'render_floating_status()' in ui_source
assert 'parentDocument.createElement("div")' in status_source
assert 'status.dataset.hhsFloatingStatusId = statusId' in status_source
assert 'querySelectorAll(".hhs-floating-status[data-hhs-floating-status-id]")' in status_source
assert "parentDocument.body.append(status)" in status_source
assert 'button.className = "hhs-floating-status-dismiss"' in status_source
assert 'dismiss.className = "hhs-floating-status-dismiss"' in status_source
assert '__hhsDisposedFloatingStatuses' in status_source
assert '__hhsRenderedFloatingStatuses' not in status_source
assert '__hhsFloatingStatusTimer' in status_source
assert 'hhs-floating-status--stable' in status_source
assert 'hhs-floating-status--disposing' in status_source
assert 'setAttribute("aria-label", "Dispose footer status")' in status_source
assert 'FOOTER_DISMISS_STATUS_QUERY_PARAM' not in ui_source
assert 'f"__hhs_open {safe_filepath}"' in ui_source
assert 'use_cache=False' in ui_source
assert 'hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE, "image/png"' in ui_source
assert 'class="hhs-footer-glyph"></span>' in ui_source
assert 'def render_sidebar_title_separator_alignment_script' in ui_source
assert 'render_sidebar_title_separator_alignment_script()' in ui_source
assert '--hhs-sidebar-title-separator-width' in ui_source
assert 'getBoundingClientRect()' in ui_source
base_block = re.search(r"\.hhs-footer-glyph\s*\{([^}]*)\}", base_css).group(1)
link_block = re.search(r"\.hhs-footer-link,[^{]+\{([^}]*)\}", base_css).group(1)
logo_link_block = re.search(r"\.hhs-footer-logo-link,[^{]+\{([^}]*)\}", base_css).group(1)
logo_block = re.search(r"\.hhs-footer-logo\s*\{([^}]*)\}", base_css).group(1)
shell_status_block = re.search(r"\.hhs-footer-shell-status,[^{]+\{([^}]*)\}", base_css).group(1)
shell_status_hover_block = re.search(r"\.hhs-footer-shell-status:hover,[^{]+\{([^}]*)\}", base_css).group(1)
shell_name_block = re.search(r"\.hhs-footer-shell-name\s*\{([^}]*)\}", base_css).group(1)
shell_name_hover_block = re.search(r"\.hhs-footer-shell-status:hover \.hhs-footer-shell-name,[^{]+\{([^}]*)\}", base_css).group(1)
remote_status_block = re.search(r"\.hhs-footer-remote-status\s*\{([^}]*)\}", base_css).group(1)
status_group_block = re.search(r"\.hhs-footer-status-group\s*\{([^}]*)\}", base_css).group(1)
shell_group_block = re.search(r"\.hhs-footer-shell-group\s*\{([^}]*)\}", base_css).group(1)
floating_status_block = re.search(r"\.hhs-floating-status\s*\{([^}]*)\}", base_css).group(1)
floating_status_stable_block = re.search(
    r"\.hhs-floating-status--stable\s*\{([^}]*)\}",
    base_css,
).group(1)
floating_status_dismiss_block = re.search(
    r"\.hhs-floating-status-dismiss\s*\{([^}]*)\}",
    base_css,
).group(1)
floating_status_dismiss_hover_block = re.search(
    r"\.hhs-floating-status-dismiss:hover,\s*\.hhs-floating-status-dismiss:focus-visible\s*\{([^}]*)\}",
    base_css,
).group(1)
floating_status_slide_up_block = re.search(
    r"@keyframes hhs-floating-status-slide-up\s*\{(.*?)\n\}",
    base_css,
    re.S,
).group(1)
script_only_block = re.search(
    r"\[data-testid=\"stElementContainer\"\]:has\(\.hhs-script-only\),\s*"
    r"\[data-testid=\"stHtml\"\]:has\(\.hhs-script-only\)\s*\{([^}]*)\}",
    base_css,
).group(1)
app_footer_block = re.search(r"\.hhs-app-footer\s*\{([^}]*)\}", base_css).group(1)
sidebar_title_block = re.search(r"\.hhs-sidebar-title\s*\{([^}]*)\}", base_css).group(1)
sidebar_title_separator_block = re.search(r"\.hhs-sidebar-title::after\s*\{([^}]*)\}", base_css).group(1)
cache_menu_block = re.search(r"\.hhs-footer-cache-clear-menu\s*\{([^}]*)\}", base_css).group(1)
cache_trigger_block = re.search(r"\.hhs-footer-cache-clear-trigger\s*\{([^}]*)\}", base_css).group(1)
cache_panel_block = re.search(r"^\.hhs-footer-cache-clear-panel\s*\{([^}]*)\}", base_css, re.M).group(1)
cache_panel_label_block = re.search(r"\.hhs-footer-cache-clear-panel label\s*\{([^}]*)\}", base_css).group(1)
cache_panel_checkbox_block = re.search(r"\.hhs-footer-cache-clear-panel input\[type=\"checkbox\"\]\s*\{([^}]*)\}", base_css).group(1)
cache_panel_button_block = re.search(r"\.hhs-footer-cache-clear-panel button\s*\{([^}]*)\}", base_css).group(1)
footer_glyph_button_block = re.search(r"\.hhs-footer-glyph-button\s*\{([^}]*)\}", base_css).group(1)
terminal_ai_menu_block = re.search(r"\.hhs-footer-terminal-ai-menu\s*\{([^}]*)\}", base_css).group(1)
terminal_ai_trigger_block = re.search(r"\.hhs-footer-terminal-ai-trigger\s*\{([^}]*)\}", base_css).group(1)
terminal_ai_disabled_menu_block = re.search(
    r"\.hhs-footer-terminal-ai-menu--disabled\s*\{([^}]*)\}",
    base_css,
).group(1)
terminal_ai_disabled_trigger_block = re.search(
    r"\.hhs-footer-terminal-ai-menu--disabled \.hhs-footer-terminal-ai-trigger\s*\{([^}]*)\}",
    base_css,
).group(1)
terminal_ai_glyph_button_block = re.search(
    r"\.hhs-footer-terminal-ai-trigger \.hhs-footer-glyph-button\s*\{([^}]*)\}",
    base_css,
).group(1)
terminal_ai_panel_block = re.search(r"^\.hhs-footer-terminal-ai-panel\s*\{([^}]*)\}", base_css, re.M).group(1)
terminal_ai_panel_label_block = re.search(r"\.hhs-footer-terminal-ai-panel label\s*\{([^}]*)\}", base_css).group(1)
terminal_ai_panel_input_block = re.search(r"\.hhs-footer-terminal-ai-panel input\[type=\"text\"\]\s*\{([^}]*)\}", base_css).group(1)
terminal_ai_context_input_block = re.search(r"\.hhs-footer-terminal-ai-context-input\s*\{([^}]*)\}", base_css).group(1)
terminal_ai_panel_button_block = re.search(r"\.hhs-footer-terminal-ai-panel button\s*\{([^}]*)\}", base_css).group(1)
block_container_block = re.search(r"\.block-container\s*\{([^}]*)\}", base_css).group(1)
main_block_gap_block = re.search(r"\[data-testid=\"stMainBlockContainer\"\] > \[data-testid=\"stVerticalBlock\"\],[^{]+\{([^}]*)\}", base_css).group(1)
active_view_block = re.search(
    r"\.st-key-active_view,\s*\.st-key-active_view_widget\s*\{([^}]*)\}",
    base_css,
    re.S,
).group(1)
sub_view_button_group_block = re.search(r"\.st-key-home_view \[data-baseweb=\"button-group\"\],[^{]+\{([^}]*)\}", base_css).group(1)
heading_block = re.search(r"\.hhs-view-heading\s*\{([^}]*)\}", base_css).group(1)
tabbed_heading_block = re.search(r"\.hhs-view-heading--with-tabs\s*\{([^}]*)\}", base_css).group(1)
direct_content_heading_block = re.search(r"\.hhs-view-heading--direct-content\s*\{([^}]*)\}", base_css).group(1)
heading_container_block = re.search(r"\[data-testid=\"stMain\"\] \[data-testid=\"stVerticalBlock\"\] > div:has\(\.hhs-view-heading\)\s*\{([^}]*)\}", base_css).group(1)
tabbed_heading_container_block = re.search(r"\[data-testid=\"stMain\"\] \[data-testid=\"stVerticalBlock\"\] > div:has\(\.hhs-view-heading--with-tabs\)\s*\{([^}]*)\}", base_css).group(1)
expander_block = re.search(r"\[data-testid=\"stExpander\"\]\s*\{([^}]*)\}", base_css).group(1)
docker_expander_block = re.search(r"\.st-key-home_docker_panel \[data-testid=\"stExpander\"\]\s*\{([^}]*)\}", base_css).group(1)
docker_expander_details_block = re.search(r"\.st-key-home_docker_panel \[data-testid=\"stExpanderDetails\"\] > \[data-testid=\"stVerticalBlock\"\]\s*\{([^}]*)\}", base_css).group(1)
hidden_streamlit_block = re.search(r"\[data-testid=\"stMain\"\] \[data-testid=\"stVerticalBlock\"\] > div:empty,[^{]+\{([^}]*)\}", base_css).group(1)
assert '[data-testid="stElementContainer"]:empty' in base_css
assert '[data-testid="stElementContainer"]:not(:has(> *))' in base_css
assert '[data-testid="stElementContainer"]:has(> div:empty)' in base_css
assert '[data-testid="stElementContainer"]:has(> [data-testid="stMarkdownContainer"]:empty)' in base_css
assert '[data-testid="stElementContainer"]:has(> [data-testid="stLayoutWrapper"]:empty)' in base_css
assert '[data-testid="stElementContainer"]:has(> [data-testid="stLayoutWrapper"]:not(:has(> *)))' in base_css
assert '[data-testid="stElementContainer"]:has(> [data-testid="stLayoutWrapper"] > div:empty)' in base_css
assert '[data-testid="stLayoutWrapper"]:empty' in base_css
assert '[data-testid="stLayoutWrapper"]:not(:has(> *))' in base_css
assert '[data-testid="stLayoutWrapper"]:has(> div:empty)' in base_css
for expected in (
    "block-size: 0 !important",
    "flex-basis: 0 !important",
    "line-height: 0 !important",
    "max-height: 0 !important",
    "display: none !important",
):
    assert expected in hidden_streamlit_block
view_key_block = re.search(r"\.st-key-active_view,[^{]+\{([^}]*)\}", base_css).group(1)
active_view_tabs_block = re.search(
    r"\.st-key-active_view \[role=\"radiogroup\"\],\s*"
    r"\.st-key-active_view_widget \[role=\"radiogroup\"\]\s*\{([^}]*)\}",
    base_css,
    re.S,
).group(1)
streamlit_chrome_block = re.search(r"\[data-testid=\"stDecoration\"\],[^{]+\{([^}]*)\}", base_css).group(1)
streamlit_header_block = re.search(r"\[data-testid=\"stHeader\"\]\s*\{([^}]*)\}", base_css).group(1)
streamlit_toolbar_block = re.search(r"\[data-testid=\"stToolbar\"\]\s*\{([^}]*)\}", base_css).group(1)
theme_block = re.search(r"\.hhs-footer-glyph\s*\{([^}]*)\}", dracula_css).group(1)
assert "color: inherit" in link_block
assert "text-decoration: none !important" in link_block
assert "filter: brightness(1.2)" in base_css
assert "filter: none" in logo_link_block
assert "height:" in logo_block
assert "width:" in logo_block
assert ".hhs-footer-shell-status" in base_css
assert ".hhs-footer-shell-group" in base_css
assert ".hhs-footer-cache-clear-menu" in base_css
assert ".hhs-footer-cache-clear-trigger" in base_css
assert ".hhs-footer-cache-clear-form" not in base_css
assert ".hhs-footer-cache-clear-panel" in base_css
assert ".hhs-footer-terminal-ai-menu" in base_css
assert ".hhs-footer-terminal-ai-trigger" in base_css
assert ".hhs-footer-terminal-ai-panel" in base_css
assert ".st-key-footer_cache_clear_button" not in base_css
assert ".hhs-footer-remote-status" in base_css
assert ".hhs-footer-status-group" in base_css
assert ".hhs-footer-repository-link:hover" in base_css
assert ".hhs-footer-working-dir-link:hover" in base_css
assert ".hhs-footer-shell-status:hover" in base_css
assert ".hhs-footer-shell-name" in base_css
assert "text-decoration: none !important" in shell_name_block
assert "text-decoration: underline !important" in shell_name_hover_block
assert "text-decoration: underline" not in shell_status_hover_block
assert "gap: var(--hhs-element-std-gap)" in shell_group_block
assert "font-size: 0.68rem" in cache_menu_block
assert "height: 1.18rem" in cache_menu_block
assert "position: relative" in cache_menu_block
assert "cursor: pointer" in cache_trigger_block
assert "height: 1.18rem" in cache_trigger_block
assert "list-style: none" in cache_trigger_block
assert "padding: 0 0.12rem" in cache_trigger_block
assert "font-size: 0.68rem" in terminal_ai_menu_block
assert "height: 1.18rem" in terminal_ai_menu_block
assert "position: relative" in terminal_ai_menu_block
assert "color: var(--hhs-warning)" in terminal_ai_menu_block
assert "cursor: pointer" in terminal_ai_trigger_block
assert "height: 1.18rem" in terminal_ai_trigger_block
assert "list-style: none" in terminal_ai_trigger_block
assert "padding: 0 0.12rem" in terminal_ai_trigger_block
assert "color: var(--hhs-warning)" in terminal_ai_trigger_block
assert "color: var(--hhs-theme-text-muted-color)" in terminal_ai_disabled_menu_block
assert "opacity: 0.45" in terminal_ai_disabled_menu_block
assert "color: var(--hhs-theme-text-muted-color)" in terminal_ai_disabled_trigger_block
assert "cursor: not-allowed" in terminal_ai_disabled_trigger_block
assert "pointer-events: none" in terminal_ai_disabled_trigger_block
assert ".hhs-footer-glyph-button" in base_css
assert ".hhs-footer-cache-refresh-glyph" not in base_css
assert ".hhs-footer-terminal-ai-glyph" not in base_css
assert "color: currentColor" in footer_glyph_button_block
assert "--hhs-theme-footer-glyph-button: 1.5rem" in base_css
assert "--hhs-theme-hhs-action-button-width: 140px" in base_css
assert "font-size: var(--hhs-theme-footer-glyph-button)" in footer_glyph_button_block
assert "height: var(--hhs-theme-footer-glyph-button)" in footer_glyph_button_block
assert "width: var(--hhs-theme-footer-glyph-button)" in footer_glyph_button_block
assert "width: var(--hhs-theme-hhs-action-button-width)" in base_css
assert ".st-key-hhs_firebase_save_button" not in base_css
assert ".st-key-hhs_firebase_alias_upload_button button" in base_css
assert "font-size: calc((var(--hhs-theme-footer-glyph-button) * 0.5) + 5px)" in terminal_ai_glyph_button_block
assert ".st-key-footer_terminal_ai_bridge_button" not in base_css
assert ".st-key-footer_terminal_ai_bridge_container" not in base_css
assert ".st-key-footer-terminal-ai-bridge-button" not in base_css
assert ".st-key-footer-terminal-ai-bridge-container" not in base_css
assert ".hhs-footer-cache-clear-button" not in base_css
assert ".hhs-footer-cache-clear-trigger:hover" in base_css
assert ".hhs-footer-terminal-ai-trigger:hover" in base_css
assert "bottom: calc(var(--hhs-footer-guard-height) + 0.7rem)" in base_css
assert "right: 1rem" in base_css
assert "background: var(--hhs-theme-secondary-background-color)" in cache_panel_block
assert "box-shadow: 0 1rem 2rem" in cache_panel_block
assert "gap: var(--hhs-element-std-gap)" in cache_panel_block
assert "position: fixed" in cache_panel_block
assert "width: min(22rem, calc(100vw - 2rem)) !important" in cache_panel_block
assert "width: 100%" in cache_panel_label_block
assert "min-height: 2.25rem" in cache_panel_label_block
assert "accent-color: var(--hhs-theme-primary-color)" in cache_panel_checkbox_block
assert "height: 1rem" in cache_panel_checkbox_block
assert "background: transparent" in cache_panel_button_block
assert "height: 2.25rem" in cache_panel_button_block
assert "width: 100%" in cache_panel_button_block
assert "background: var(--hhs-theme-secondary-background-color)" in terminal_ai_panel_block
assert "box-shadow: 0 1rem 2rem" in terminal_ai_panel_block
assert "gap: var(--hhs-element-std-gap)" in terminal_ai_panel_block
assert "position: fixed" in terminal_ai_panel_block
assert "width: min(22rem, calc(100vw - 2rem)) !important" in terminal_ai_panel_block
assert "width: 100%" in terminal_ai_panel_label_block
assert "height: 2.25rem" in terminal_ai_panel_input_block
assert "width: 100%" in terminal_ai_panel_input_block
assert "overflow: hidden" in terminal_ai_context_input_block
assert "text-overflow: ellipsis" in terminal_ai_context_input_block
assert "white-space: nowrap" in terminal_ai_context_input_block
assert "cursor: default" in terminal_ai_context_input_block
assert "background: transparent" in terminal_ai_panel_button_block
assert "height: 2.25rem" in terminal_ai_panel_button_block
assert "width: 100%" in terminal_ai_panel_button_block
assert ".hhs-footer-cache-clear-panel label:hover" in base_css
assert ".hhs-footer-cache-clear-panel button:hover" in base_css
assert ".hhs-footer-terminal-ai-panel button:hover" in base_css
assert 'div[role="dialog"]:has(.hhs-shell-version-output)' in base_css
assert ".hhs-shell-version-output" in base_css
assert "max-height: 88dvh" in base_css
assert "max-width: 92vw" in base_css
assert "width: max-content" in base_css
assert '[data-testid="stHorizontalBlock"]:has(.st-key-footer_shell_version_dialog_close_button)' in base_css
assert "justify-content: center" in base_css
assert "margin-top: 1rem" in base_css
assert '[data-testid="stColumn"]:has(.st-key-footer_shell_version_dialog_close_button)' in base_css
assert "flex: 0 0 120px !important" in base_css
assert "width: 120px !important" in base_css
assert "max-height: calc(88dvh - 8rem)" in base_css
assert "max-width: calc(92vw - 4rem)" in base_css
assert ".hhs-footer-working-dir-value" in base_css
assert "color: var(--hhs-secondary)" in base_css
assert "text-decoration: underline !important" in base_css
assert ".hhs-footer-version-group" in base_css
assert "align-items: baseline" in base_css
assert ".hhs-footer-update-link" in base_css
assert "top: -0.42em" in base_css
assert ".hhs-floating-status" in base_css
assert "hhs-floating-status-slide-up" in base_css
assert "hhs-floating-status-slide-down" in base_css
assert ".hhs-floating-status--disposing" in base_css
assert ".hhs-floating-status-kind-info" in base_css
assert ".hhs-floating-status-kind-warn" in base_css
assert ".hhs-floating-status-kind-error" in base_css
assert "var(--hhs-theme-footer-status-info-color)" in base_css
assert "var(--hhs-theme-footer-status-warn-color)" in base_css
assert "var(--hhs-theme-footer-status-error-color)" in base_css
assert "font-size: var(--hhs-theme-footer-status-text-size)" in base_css
assert "--hhs-streamlit-toolbar-guard-width: 8rem" in base_css
assert "--hhs-ttyd-max-height: 760px" in base_css
assert "--hhs-view-gap: var(--hhs-element-std-gap)" in base_css
assert "--hhs-view-section-gap: var(--hhs-element-std-gap)" in base_css
assert "padding-top: 0 !important" in block_container_block
assert ".block-container:has(#hhs-ttyd-terminal-anchor)" in base_css
assert "padding-bottom: 0 !important" in base_css
assert '[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]' in base_css
assert ".block-container > [data-testid=\"stVerticalBlock\"]" in base_css
assert "gap: var(--hhs-element-std-gap) !important" in main_block_gap_block
assert "row-gap: var(--hhs-element-std-gap) !important" in main_block_gap_block
assert "margin-bottom: 0 !important" in active_view_block
assert "margin: 0 0 var(--hhs-element-std-gap) !important" in sub_view_button_group_block
assert "def view_segmented_control_widget_key" in ui_source
assert "def save_view_segmented_control_state" in ui_source
assert "def normalized_view_segmented_control_value" in ui_source
assert "def render_view_segmented_control" in ui_source
assert "key=widget_key" in ui_source
assert "default=default_value" in ui_source
assert "required=True" in ui_source
assert "on_change=save_view_segmented_control_state" in ui_source
assert "view_segmented_control_widget_key(state_key)" in ui_source
assert "st.session_state.pop(widget_key, None)" in ui_source
assert '.stButtonGroup [data-baseweb="button-group"] button[aria-checked="true"]' in base_css
assert '.stButtonGroup [data-baseweb="button-group"] button[aria-pressed="true"]' in base_css
assert '.stButtonGroup [data-baseweb="button-group"] button[aria-selected="true"]' in base_css
assert '.stButtonGroup [data-baseweb="button-group"] button[data-selected="true"]' in base_css
assert '.stButtonGroup [data-testid="stButtonGroup"] button[aria-checked="true"]' in base_css
assert '.stButtonGroup [data-testid="stButtonGroup"] button[aria-pressed="true"]' in base_css
assert '.stButtonGroup [data-testid="stButtonGroup"] button[aria-selected="true"]' in base_css
assert '.stButtonGroup [data-testid="stButtonGroup"] button[data-selected]' in base_css
assert "fill: currentColor !important" in base_css
assert "border-bottom: 0" in heading_block
assert "margin: 0" in heading_block
assert "margin: 0 0 var(--hhs-element-std-gap) !important" in heading_block
assert "margin-bottom: calc(var(--hhs-element-std-gap) * 2) !important" in tabbed_heading_block
assert "margin-bottom: calc(var(--hhs-element-std-gap) * 2) !important" in direct_content_heading_block
assert "margin-bottom: 0 !important" in heading_container_block
assert "margin-bottom: 0 !important" in tabbed_heading_container_block
assert ui_source.count("hhs-view-heading hhs-view-heading--with-tabs") >= 6
assert ui_source.count("hhs-view-heading hhs-view-heading--direct-content") >= 2
assert "def render_view_subtitle" in table_ui_source
assert '<h3 class="hhs-view-subtitle">' in table_ui_source
assert ".hhs-view-subtitle" in base_css
assert ".hhs-view-subtitle-link" in base_css
assert ".hhs-view-subtitle-link:link" in base_css
assert ".hhs-view-subtitle-link:visited" in base_css
assert ".hhs-view-subtitle-link:hover" in base_css
assert "--hhs-theme-file-link-color: var(--hhs-theme-link-color, var(--hhs-theme-text-color))" in base_css
assert "border-bottom: 0 !important" in base_css
assert "box-shadow: none !important" in base_css
assert "color: var(--hhs-theme-file-link-color) !important" in base_css
assert "text-decoration: underline !important" in base_css
assert "margin: 0 !important" in expander_block
assert "margin: 0 !important" in docker_expander_block
assert "gap: var(--hhs-element-std-gap) !important" in docker_expander_details_block
assert "row-gap: var(--hhs-element-std-gap) !important" in docker_expander_details_block
assert "display: none !important" in hidden_streamlit_block
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has([data-testid="stDataFrame"])' in base_css
assert "margin-top: 0 !important" in base_css
assert '[data-testid="stMain"] [data-testid="stMarkdownContainer"] h5' in base_css
assert "margin: 0 !important" in base_css
assert '[data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(.hhs-inline-form-label)' in base_css
assert "margin-bottom: 0 !important" in base_css
assert '.st-key-home_docker_panel [data-testid="stVerticalBlock"] > div:has([data-testid="stDataFrame"])' in base_css
assert '.st-key-home_docker_panel [data-testid="stElementContainer"][style*="height: 0px"]' in base_css
assert '.st-key-home_docker_panel [data-testid="stElementContainer"][style*="width:0px"]' in base_css
assert ".st-key-home_view" in base_css
assert ".st-key-config_view" in base_css
assert ".st-key-history_view" in base_css
assert ".st-key-monitor_view" in base_css
assert ".st-key-ssh_view" in base_css
assert ".st-key-ai_view" in base_css
assert ".st-key-active_view_widget" in base_css
assert ".st-key-home_view_widget" in base_css
assert ".st-key-config_view_widget" in base_css
assert ".st-key-history_view_widget" in base_css
assert ".st-key-monitor_view_widget" in base_css
assert ".st-key-ssh_view_widget" in base_css
assert ".st-key-ai_view_widget" in base_css
assert "margin-top: 0 !important" in view_key_block
assert "padding-top: 0 !important" in view_key_block
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-active_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-home_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-ssh_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-ai_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-home_view_widget)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-ssh_view_widget)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-ai_view_widget)' in base_css
assert '.st-key-home_view [data-baseweb="button-group"]' in base_css
assert '.st-key-ssh_view [data-baseweb="button-group"]' in base_css
assert '.st-key-home_view_widget [data-baseweb="button-group"]' in base_css
assert '.st-key-home_view_widget [data-testid="stButtonGroup"] [role="radiogroup"]' in base_css
assert '.st-key-ssh_view_widget [data-baseweb="button-group"]' in base_css
assert '.st-key-ssh_view_widget [data-testid="stButtonGroup"] [role="radiogroup"]' in base_css
for state_key in (
    "home_view",
    "config_view",
    "history_view",
    "monitor_view",
    "ssh_view",
    "ai_view",
):
    assert f'.st-key-{state_key}_widget' in base_css
    assert f'"{state_key}"' in ui_source
assert "padding-right: var(--hhs-streamlit-toolbar-guard-width)" in active_view_tabs_block
assert '.st-key-active_view [role="radiogroup"] label input[type="radio"]' in base_css
assert '.st-key-active_view_widget [role="radiogroup"] label input[type="radio"]' in base_css
assert 'appearance: none !important' in base_css
assert '.st-key-active_view [role="radiogroup"] label [data-testid="stRadioIcon"]' in base_css
assert '.st-key-active_view_widget [role="radiogroup"] label [data-testid="stRadioIcon"]' in base_css
assert '.st-key-active_view [role="radiogroup"] li::marker' in base_css
assert '.st-key-active_view_widget [role="radiogroup"] li::marker' in base_css
assert '.st-key-active_view [data-testid="stRadioOption"] > div > div:first-child' in base_css
assert '.st-key-active_view_widget [data-testid="stRadioOption"] > div > div:first-child' in base_css
assert '.st-key-active_view [data-testid="stRadioOption"] > div > div:first-child > div:first-child' in base_css
assert '.st-key-active_view_widget [data-testid="stRadioOption"] > div > div:first-child > div:first-child' in base_css
assert '[data-testid="stToolbar"]' in base_css
assert '[data-testid="stDecoration"]' in base_css
assert '[data-testid="stStatusWidget"]' in base_css
assert '[data-testid="stAppDeployButton"]' in base_css
assert '[data-testid="stMainMenu"]' in base_css
assert "#MainMenu" in base_css
assert "display: none !important" in streamlit_chrome_block
assert "height: 0 !important" in streamlit_chrome_block
assert "min-height: 0 !important" in streamlit_chrome_block
assert "display: block !important" in streamlit_header_block
assert "height: 0 !important" in streamlit_header_block
assert "pointer-events: none" in streamlit_header_block
assert "visibility: visible !important" in streamlit_header_block
assert "display: flex !important" in streamlit_toolbar_block
assert "height: 0 !important" in streamlit_toolbar_block
assert "pointer-events: none" in streamlit_toolbar_block
assert "visibility: visible !important" in streamlit_toolbar_block
assert '[data-testid="stSidebarCollapseButton"]' in base_css
assert '[data-testid="stExpandSidebarButton"]' in base_css
assert '[data-testid="stSidebarCollapsedControl"]' in base_css
assert "position: fixed !important" in base_css
assert "pointer-events: auto" in base_css
assert "border-top: 1px solid var(--hhs-floating-status-color)" in base_css
assert "border-bottom: 1px solid" in base_css
assert "border-top: 2px solid var(--hhs-comment)" in dracula_css
assert "justify-content: center" in base_css
assert "text-align: center" in base_css
assert "--hhs-footer-guard-height: 3.5rem" in base_css
assert "--hhs-floating-status-height: calc(1.85em + 20px)" in base_css
assert "--hhs-floating-status-z-index: 999999" in base_css
assert "--hhs-footer-z-index: 1000000" in base_css
assert "--hhs-footer-panel-z-index: 1000001" in base_css
assert "z-index: var(--hhs-floating-status-z-index)" in floating_status_block
assert "z-index: var(--hhs-footer-z-index)" in app_footer_block
assert "z-index: var(--hhs-footer-panel-z-index)" in cache_panel_block
assert "z-index: var(--hhs-footer-panel-z-index)" in terminal_ai_panel_block
assert "bottom: 3.25rem" in base_css
assert "font-size: 0.84rem" in base_css
assert "min-height: 3.25rem" in base_css
assert "height: 32px" in base_css
assert "background: rgba(15, 23, 42, 0.66)" in homesetup_css
assert "background: rgba(25, 24, 31, 0.82)" in jetpack_css
assert "background: rgba(20, 17, 31, 0.82)" in pastel_powerline_css
assert "left: 0" in base_css
assert "right: 0" in base_css
assert "min-height: var(--hhs-floating-status-height)" in base_css
assert "padding: 0.32em 2.5rem 0.32em var(--hhs-sidebar-inline-inset)" in base_css
assert "--hhs-sidebar-title-separator-left: 0px" in base_css
assert "--hhs-sidebar-title-separator-width: 100%" in base_css
assert "border-bottom: 0" in sidebar_title_block
assert "border-bottom: 2px solid var(--hhs-theme-text-color)" in sidebar_title_separator_block
assert 'content: ""' in sidebar_title_separator_block
assert "left: var(--hhs-sidebar-title-separator-left)" in sidebar_title_separator_block
assert "width: var(--hhs-sidebar-title-separator-width)" in sidebar_title_separator_block
assert "border-radius: 50%" in base_css
assert "height: 1.35rem" in base_css
assert "text-decoration: none !important" in base_css
assert "color: var(--hhs-floating-status-color)" in floating_status_dismiss_block
assert "var(--hhs-floating-status-color) 58%" in floating_status_dismiss_block
assert "color: var(--hhs-floating-status-color)" in floating_status_dismiss_hover_block
assert "var(--hhs-floating-status-color) 18%" in floating_status_dismiss_hover_block
assert "border-color: var(--hhs-floating-status-color)" in floating_status_dismiss_hover_block
assert "opacity:" not in floating_status_slide_up_block
assert "hhs-floating-status-slide-up" not in floating_status_stable_block
assert "animation-delay: var(--hhs-floating-status-timeout, 5s)" in floating_status_stable_block
assert "display: none !important" in script_only_block
assert "height: 0 !important" in script_only_block
assert "max-height: 0 !important" in script_only_block
assert "min-height: 0 !important" in script_only_block
assert "overflow: hidden !important" in script_only_block
assert '[data-testid="stApp"]' in base_css
assert '[data-testid="stMainBlockContainer"]' in base_css
assert "--hhs-floating-status-timeout: 5s" in base_css
assert "animation-delay: 0s, var(--hhs-floating-status-timeout, 5s)" in base_css
assert "font-family: var(--hhs-ui-font-family)" in base_css
assert "var(--hhs-font-family)" not in base_css
assert "--hhs-theme-input-placeholder-color: #686e7a" in base_css
assert "input::placeholder" in base_css
assert "textarea::placeholder" in base_css
assert 'color: var(--hhs-theme-input-placeholder-color) !important' in base_css
assert "opacity: 1 !important" in base_css
assert "--hhs-modal-scrim-z-index: 1000001" in base_css
assert "--hhs-modal-z-index: 1000002" in base_css
assert "--hhs-command-overlay-z-index: 1000010" in base_css
assert '[data-testid="stDialog"][data-baseweb="modal"]' in base_css
assert '[data-testid="stDialog"][data-baseweb="modal"] > div' in base_css
assert '[data-testid="stDialog"][data-baseweb="modal"] [role="dialog"]' in base_css
assert "min-height: 100dvh !important" in base_css
assert 'body:has(div[role="dialog"]) .hhs-app-footer' in base_css
assert 'body:has([data-testid="stDialog"][data-baseweb="modal"]) .hhs-app-footer' in base_css
assert 'body:has(div[role="dialog"]) .hhs-footer-terminal-ai-panel' in base_css
assert 'body:has([data-testid="stDialog"][data-baseweb="modal"]) .hhs-footer-terminal-ai-panel' in base_css
assert 'body:has(div[role="dialog"]) .hhs-sidebar-clock' in base_css
assert "z-index: calc(var(--hhs-modal-scrim-z-index) - 1) !important" in base_css
assert "z-index: var(--hhs-modal-z-index) !important" in base_css
assert "z-index: var(--hhs-command-overlay-z-index)" in base_css
main_body = ui_source.split("def main()", 1)[1].split('if __name__ == "__main__"', 1)[0]
assert "render_footer_terminal_ai_bridge_button()" not in main_body
assert main_body.index("render_footer_status_fragment()") < main_body.index(
    "render_folder_picker_dialog()"
)
assert main_body.index("render_folder_picker_dialog()") < main_body.index("render_browser_cleanup_script()")
assert "color: var(--hhs-warning)" in base_css
assert ".hhs-footer-spacer" not in base_css
assert "gap: 0.8rem" in base_css
assert "margin-left: auto" in status_group_block
assert "gap: 1.25rem" in status_group_block
assert "gap: 0.8rem" in shell_status_block
assert "gap: 0.8rem" in remote_status_block
assert "margin-left" not in shell_status_block
assert "margin-left" not in remote_status_block
assert "border-bottom" not in base_block
assert "border-bottom" not in theme_block
assert "color: var(--hhs-primary)" in theme_block
assert ".hhs-footer-remote-status" in dracula_css
assert "--hhs-theme-footer-status-info-color" in dracula_css
assert "--hhs-theme-footer-status-warn-color" in dracula_css
assert "--hhs-theme-footer-status-error-color" in dracula_css
assert "--hhs-theme-footer-status-text-size" in dracula_css
assert "--hhs-theme-footer-status-text-size: 1.176rem" in dracula_css
assert "--hhs-theme-footer-glyph-button: 1.5rem" in dracula_css
assert "--hhs-theme-hhs-action-button-width: 140px" in dracula_css
assert "--hhs-theme-input-placeholder-color: #686e7a" in dracula_css
assert "--hhs-theme-file-link-color: var(--hhs-theme-link-color)" in dracula_css
assert "--hhs-theme-footer-status-info-color" in homesetup_css
assert "--hhs-theme-footer-status-warn-color" in homesetup_css
assert "--hhs-theme-footer-status-error-color" in homesetup_css
assert "--hhs-theme-footer-status-text-size" in homesetup_css
assert "--hhs-theme-footer-status-text-size: 1.176rem" in homesetup_css
assert "--hhs-theme-footer-glyph-button: 1.5rem" in homesetup_css
assert "--hhs-theme-hhs-action-button-width: 140px" in homesetup_css
assert "--hhs-theme-input-placeholder-color: #686e7a" in homesetup_css
assert "--hhs-theme-file-link-color: var(--hhs-theme-link-color)" in homesetup_css
assert "--hhs-theme-footer-status-info-color" in tokyo_night_css
assert "--hhs-theme-footer-status-warn-color" in tokyo_night_css
assert "--hhs-theme-footer-status-error-color" in tokyo_night_css
assert "--hhs-theme-footer-status-text-size" in tokyo_night_css
assert "--hhs-theme-footer-status-text-size: 1.176rem" in tokyo_night_css
assert "--hhs-theme-footer-glyph-button: 1.5rem" in tokyo_night_css
assert "--hhs-theme-footer-glyph-button: 1.5rem" in jetpack_css
assert "--hhs-theme-footer-glyph-button: 1.5rem" in pastel_powerline_css
assert "--hhs-theme-hhs-action-button-width: 140px" in tokyo_night_css
assert "--hhs-theme-hhs-action-button-width: 140px" in jetpack_css
assert "--hhs-theme-hhs-action-button-width: 140px" in pastel_powerline_css
assert "--hhs-theme-input-placeholder-color: #686e7a" in tokyo_night_css
assert "--hhs-theme-input-placeholder-color: #686e7a" in jetpack_css
assert "--hhs-theme-input-placeholder-color: #686e7a" in pastel_powerline_css
assert "--hhs-theme-file-link-color: var(--hhs-theme-link-color)" in tokyo_night_css
assert "--hhs-theme-file-link-color: var(--hhs-theme-link-color)" in jetpack_css
assert "--hhs-theme-file-link-color: var(--hhs-theme-link-color)" in pastel_powerline_css
assert '.stButtonGroup [data-baseweb="button-group"] button[aria-checked="true"]' in dracula_css
assert '.stButtonGroup [data-testid="stButtonGroup"] button[aria-checked="true"]' in dracula_css
assert '.stButtonGroup [data-testid="stButtonGroup"] button[data-selected]' in dracula_css
assert "border-color: var(--hhs-primary)" in dracula_css
assert "--hhs-theme-heading-border-color: var(--hhs-theme-border-color)" in dracula_css
assert "--hhs-theme-heading-border-color: var(--hhs-theme-border-color)" in tokyo_night_css
assert ".hhs-view-heading {\n" not in dracula_css
assert ".hhs-view-heading {\n" not in homesetup_css
assert ".hhs-view-heading {\n" not in jetpack_css
assert ".hhs-view-heading {\n" not in pastel_powerline_css
assert ".hhs-view-heading {\n" not in tokyo_night_css
PY
  assert_success

  assert_file_not_contains "${css_file}" '<style>'
}
