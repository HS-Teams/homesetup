#!/usr/bin/env bats

#  Script: command-progress.bats
# Purpose: HomeSetup Streamlit UI command progress tests.
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

@test "when showing command progress then command runner should paint overlay before subprocess" {
  assert_file_contains "${feedback_ui_file}" 'def set_overlay('

  assert_file_not_contains_many "${ui_file}" \
'def render_footer_visibility_script' 'render_footer_visibility_script(hidden=True)' \
    'render_footer_visibility_script(hidden=False)' 'hhs-footer-hidden' 'classList.add("hhs-main-hidden")' \
    'classList.remove("hhs-main-hidden")'
  assert_file_not_contains "${css_file}" '.hhs-main-hidden \[data-testid="stMain"\]'

  assert_file_not_contains_many "${ui_file}" \
'_hhs_footer_visibility_sequence' 'dataset.hhsFooterVisibilitySequence'
  assert_file_not_contains "${css_file}" '.hhs-footer-hidden .hhs-app-footer'

  assert_file_contains "${ui_file}" 'timeout_seconds=effective_timeout'
  assert_file_contains "${dialog_ui_file}" 'def close_all_dialogs()'
  assert_file_contains_many "${feedback_ui_file}" \
'close_all_dialogs()' \
    'overlay.id = "hhs-command-overlay"' 'overlay.style.inset = "0"' 'overlay.style.width = "auto"'
  assert_file_not_contains "${feedback_ui_file}" 'overlay.style.width = "100vw"'

  assert_file_contains_many "${feedback_ui_file}" \
'overlay.style.height = "100dvh"' 'overlay.style.alignItems = "center"' \
    'overlay.style.justifyContent = "center"' 'doc.body.appendChild(overlay)' \
    'doc.body.dataset.hhsCommandOverlayHidden = "false"' \
    'const clearedAt = Number(parentWindow.__hhsCommandOverlayClearedAt || 0)' 'createdAt <= clearedAt' \
    'parentWindow.__hhsCommandOverlayToken = overlayToken' 'overlay.dataset.hhsOverlayToken = overlayToken' \
    'overlay.dataset.hhsOverlayCreatedAt = String(createdAt)' 'def clear_preloader()' 'clear_preloader()' \
    'doc.body.dataset.hhsCommandOverlayHidden = "true"' \
    'parentWindow.__hhsCommandOverlayClearedAt = Date.now()' \
    'const observer = new parentWindow.MutationObserver(remove_overlay)' \
    'observer.observe(doc.body, { childList: true })' 'overlayCreatedAt > clearedAt' \
    'parentWindow.setTimeout(remove_overlay, 50)' 'parentWindow.setTimeout(remove_overlay, 250)' \
    'parentWindow.setTimeout(remove_overlay, 1000)'
  assert_file_not_contains_many "${ui_file}" \
'command_overlay_slot' 'placeholder_key = "_hhs_overlay_placeholder"' 'with placeholder.container()' \
    'st.container(key=f"command_overlay_slot_{sequence}")' 'sequence_key = "_hhs_overlay_slot_sequence"'
  assert_file_contains_many "${feedback_ui_file}" \
'hhs-tab-loader-label' 'def loader_label_html' '"%primary_color%": "hhs-loader-primary"' \
    '"%secondary_color%": "hhs-loader-secondary"' 'safe_message_html = loader_label_html(message)' \
    'label.innerHTML = {json.dumps(safe_message_html)}' 'COMMAND_PRELOADER_BUS' \
    'def create_command_preloader_event_bus' \
    'from hspylib.modules.eventbus.fluid import FluidEvent, FluidEventBus' 'FluidEventBus(' \
    'start=FluidEvent(' 'finish=FluidEvent(' 'events.start.emit(' 'events.finish.emit(' \
    'events.start.subscribe(cb_event_handler=enqueue_command_preloader_event)' \
    'events.finish.subscribe(cb_event_handler=enqueue_command_preloader_event)' '"hhs:command-preloader"'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/core/ui_definitions.py" \
    'COMMAND_PRELOADER_BUS = "hhs-ui-command-preloader"'
  assert_file_contains_many "${ui_file}" \
    'show_preloader_event: bool = False' '"preloader_token": command_preloader_token' \
    'finish_background_job_preloader(' 'show_preloader_event=True'
  run python3 - "${feedback_ui_file}" <<'PY'
from pathlib import Path
import html
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def loader_label_html(")
end = source.index("def render_command_loader_timer(")
namespace = {"html": html}
exec("from __future__ import annotations\n" + source[start:end], namespace)
rendered = namespace["loader_label_html"](
    "Searching for %primary_color%<term>%primary_color% "
    "in %secondary_color%/tmp/a&b%secondary_color%"
)
assert '<span class="hhs-loader-primary">&lt;term&gt;</span>' in rendered
assert '<span class="hhs-loader-secondary">/tmp/a&amp;b</span>' in rendered
PY
  assert_success

  run python3 - "${feedback_ui_file}" <<'PY'
from pathlib import Path
import html
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def command_loader_html(")
end = source.index("def command_preloader_event_queue(")
namespace = {"html": html}
exec("from __future__ import annotations\n" + source[start:end], namespace)
rendered = namespace["command_loader_html"](
    "Searching for %primary_color%*.mp4%primary_color% "
    "in %secondary_color%/tmp/a&b%secondary_color%",
    'loader"id',
    123,
    30,
    "search_command:token&1",
)
assert "%primary_color%" not in rendered
assert "%secondary_color%" not in rendered
assert '<span class="hhs-loader-primary">*.mp4</span>' in rendered
assert '<span class="hhs-loader-secondary">/tmp/a&amp;b</span>' in rendered
assert 'data-loader-id="loader&quot;id"' in rendered
assert 'class="hhs-command-loader-close"' in rendered
assert 'data-hhs-preloader-token="search_command:token&amp;1"' in rendered
PY
  assert_success

  run python3 - "${feedback_ui_file}" "${ui_file}" "${command_runtime_file}" <<'PY'
from pathlib import Path
import ast
import html
import sys
import types

feedback_source = Path(sys.argv[1]).read_text(encoding="utf-8")
ui_source = Path(sys.argv[2]).read_text(encoding="utf-8")
command_runtime_source = Path(sys.argv[3]).read_text(encoding="utf-8")
start = feedback_source.index("def loader_label_html(")
end = feedback_source.index("def render_command_loader_timer(")
namespace = {
    "COMMAND_PRELOADER_START_EVENT": "command:start",
    "COMMAND_PRELOADER_FINISH_EVENT": "command:finish",
    "COMMAND_PRELOADER_EVENT_QUEUE_KEY": "_hhs_command_preloader_events",
    "html": html,
    "hhs_ui_constants": types.SimpleNamespace(FLOATING_STATUS_QUEUE_LIMIT=20),
    "st": types.SimpleNamespace(session_state={}),
}
exec("from __future__ import annotations\n" + feedback_source[start:end], namespace)

class Args:
    token = "token-1"
    message = "Searching %primary_color%needle%primary_color%"
    timeout_seconds = 30
    status = ""

event = types.SimpleNamespace(name="command:start", args=Args())
payload = namespace["command_preloader_event_payload"](event)
assert payload["event"] == "command:start"
assert payload["token"] == "token-1"
assert payload["timeoutSeconds"] == 30
assert '<span class="hhs-loader-primary">needle</span>' in payload["messageHtml"]

renderer_body = feedback_source.split("def render_command_preloader_events", 1)[1].split("\ndef ", 1)[0]
background_status_body = command_runtime_source.split(
    "def render_background_job_status", 1
)[1].split("\ndef ", 1)[0]
assert 'parentWindow.__hhsCommandOverlayExpiryTimer = parentWindow.setTimeout' not in renderer_body
assert 'removeOverlay(String(detail.token || ""))' in renderer_body
assert 'overlay.className = "hhs-tab-loader";' in renderer_body
assert 'overlay.className = "hhs-tab-loader hhs-tab-loader-transient";' not in renderer_body
assert 'overlay.classList.remove("hhs-tab-loader-transient")' in renderer_body
assert "def command_elapsed_helper_js" in feedback_source
assert 'typeof parentWindow.__hhsRenderCommandElapsed !== "function"' in feedback_source
assert "def command_overlay_close_button_html" in feedback_source
assert "def command_overlay_close_helper_js" in feedback_source
assert "def stop_background_job_by_preloader_token" in command_runtime_source
assert "def handle_command_preloader_cancel_action" in ui_source
assert "hhs_ui.COMMAND_PRELOADER_CANCEL_QUERY_PARAM" in ui_source
assert 'class="hhs-tab-loader-close"' in feedback_source
assert "bindCommandOverlayClose(overlay)" in feedback_source
assert "bindCommandLoaderClose(loader)" in feedback_source
assert "parentWindow.__hhsDismissCommandOverlay" in feedback_source
assert 'cleanToken.includes(":")' in feedback_source
assert feedback_source.count("elapsedSeconds > 25 && elapsedSeconds < 60") == 1
assert feedback_source.count("elapsedSeconds >= 60") == 1
assert "elapsed_ratio >=" not in feedback_source
assert "elapsedRatio >=" not in feedback_source
assert "job[\"preloader_finished\"] = True" in command_runtime_source
assert "def dismiss_background_job_preloader" in command_runtime_source
assert 'dismiss_background_job_preloader(job_name, job, "error")' in background_status_body
assert "process.poll() is not None" in background_status_body
assert "background_job_result(job_name)" not in background_status_body
assert background_status_body.count("render_command_preloader_events()") == 1

tree = ast.parse(ui_source)
parents = {}
for parent in ast.walk(tree):
    for child in ast.iter_child_nodes(parent):
        parents[child] = parent

def enclosing_function_name(node):
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, ast.FunctionDef):
            return parent.name
        parent = parents.get(parent)
    return ""

javascript_html_functions = []
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    func = node.func
    if not (
        isinstance(func, ast.Attribute)
        and func.attr == "html"
        and isinstance(func.value, ast.Name)
        and func.value.id == "st"
    ):
        continue
    for keyword in node.keywords:
        if (
            keyword.arg == "unsafe_allow_javascript"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
        ):
            javascript_html_functions.append(enclosing_function_name(node))

assert javascript_html_functions == ["render_script_html"]
render_script_body = ui_source.split("def render_script_html", 1)[1].split("\ndef ", 1)[0]
assert 'class="hhs-script-only"' in render_script_body
assert "unsafe_allow_javascript=True" in render_script_body
PY
  assert_success

  assert_file_contains_many "${feedback_ui_file}" \
'time.sleep(0.1)' 'render_script_html('
  assert_file_not_contains "${ui_file}" 'components.html('

  assert_file_contains "${ui_file}" 'class="hhs-script-only"'
  assert_file_contains_many "${feedback_ui_file}" \
'overlay.style.zIndex = "1000010"' \
    'parentWindow.__hhsCommandOverlayTimer = parentWindow.setInterval(render_elapsed, 1000)' \
    'parentWindow.__hhsCommandOverlayExpiryTimer = parentWindow.setTimeout' 'data-timeout-seconds' \
    'hhs-tab-loader-close' 'hhs_ui.COMMAND_PRELOADER_CANCEL_QUERY_PARAM' \
    'elapsedSeconds > 25 && elapsedSeconds < 60' 'elapsedSeconds >= 60'
  assert_file_not_contains_many "${feedback_ui_file}" \
'elapsed_ratio >= 0.3 && elapsed_ratio < 0.6' 'elapsedRatio >= 0.3 && elapsedRatio < 0.6'
  assert_file_contains_many "${feedback_ui_file}" \
'hhs-loader-elapsed-warning' 'hhs-loader-elapsed-danger'
  assert_file_contains "${ui_file}" 'set_overlay(False)'
  assert_file_contains_many "${command_runtime_file}" \
'def run_bash_subprocess' \
    'result = run_bash_subprocess(command_to_run, effective_timeout)' 'subprocess.Popen(' \
    'start_new_session=True' 'stop_process(process)' 'Command timed out after {timeout_seconds} seconds.'
  assert_file_contains_many "${css_file}" \
'hhs-tab-loader' '.hhs-tab-loader-close' '.hhs-command-loader-close:hover' 'border-color: #ff5555' \
    'color: #ff5555' 'margin: var(--hhs-element-std-gap, 1rem)' 'width: max-content' 'overflow-wrap: anywhere' \
    '.hhs-command-loader {' 'margin: var(--hhs-element-std-gap, 1rem) auto' 'justify-content: center' \
    '.hhs-tab-loader-elapsed.hhs-loader-elapsed-warning' '.hhs-loader-primary' 'color: var(--hhs-primary)' \
    '.hhs-loader-secondary' 'color: var(--hhs-secondary)' 'color: #facc15 !important' \
    '.hhs-tab-loader-elapsed.hhs-loader-elapsed-danger' 'color: #ff5555 !important'
  run grep -F -q 'div[class*="st-key-command_overlay_slot_"]' "${css_file}"
  assert_failure

  run grep -F -q '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:empty' "${css_file}"
  assert_success

  run grep -F -q '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has([data-testid="stMarkdownContainer"] style)' "${css_file}"
  assert_success

  run grep -F -q 'div:not([class*="st-key-ssh_explorer_component"]):has(iframe[height="0"])' "${css_file}"
  assert_success

  assert_file_contains_many "${css_file}" \
'height: 0 !important' 'position: fixed'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css" 'background: var(--hhs-background)'
}
