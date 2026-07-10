#!/usr/bin/env bats

#  Script: ai.bats
# Purpose: HomeSetup Streamlit UI AI tests.
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

@test "when remote terminal prints wrapper chatter then command output should be filtered" {
  run python3 - "${ui_file}" <<'PY'
import re
import sys
from functools import lru_cache
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def terminal_output_line_is_noise(")
end = source.index("def strip_ansi(")
motd_start = source.index("def homesetup_motd_template(")
motd_end = source.index("def strip_remote_command_motd_block(")
namespace = {
    "re": re,
    "strip_ansi": lambda value: value,
    "strip_ssh_shared_connection_notice": lambda value: value,
    "homesetup_home": lambda: Path(".").resolve(),
    "lru_cache": lru_cache,
}
exec(
    "from __future__ import annotations\n"
    + source[motd_start:motd_end]
    + "\n"
    + source[start:end],
    namespace,
)
motd_fragments = namespace["homesetup_motd_fragment_groups"]()[0]
rendered_motd = f"[Linux-ubuntu/bash] {' root '.join(motd_fragments)} v1.9.18 "

stdout = (
    "[bash] HomeSetup is starting...\n"
    f"{rendered_motd}\n"
    "Shell option expand_aliases set to on \n"
    "Shell option checkwinsize set to on \n"
    "bash: cd: /etc/gabiroba: No such file or directory\n"
    "exit\n"
    "__HHS_TERMINAL_CWD__/etc/ssl\n"
)
output = namespace["filter_terminal_output_noise"](stdout)
assert "HomeSetup is starting" not in output
assert "Welcome root" not in output
assert "Shell option expand_aliases" not in output
assert "\nexit\n" not in f"\n{output}\n"
assert "bash: cd: /etc/gabiroba: No such file or directory" in output
assert "__HHS_TERMINAL_CWD__" in output

stderr = "Shared connection to 167.99.120.81 closed.\nConnection to host closed.\nreal error\n"
filtered = namespace["filter_terminal_output_noise"](stderr)
assert "Shared connection" not in filtered
assert "Connection to host closed" not in filtered
assert filtered == "real error\n"
PY
  assert_success
}

# TC - 13

@test "when using Ask AI then chat and model settings should support context, reset, select, and delete" {
  assert_file_contains_many "${constants_file}" \
'APP_AI_USER_AVATAR_FILE = APP_DIR / "assets/images/user.png"' \
    'APP_AI_OLLAMA_AVATAR_FILE = APP_DIR / "assets/images/ollama.png"' \
    'APP_AI_HOMESETUP_AVATAR_FILE = APP_DIR / "assets/images/homesetup.png"' \
    'APP_FAVICON_FILE = APP_DIR / "assets/images/favicon.png"'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" 'APP_FAVICON_FILE'

  run test -s "${ask_prompt_file}"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/user.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/ollama.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/homesetup.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/favicon.png"
  assert_success

  assert_file_contains_many "${ui_file}" \
'page_icon=str(hhs_ui.APP_FAVICON_FILE)' 'build_hhs_ask_execute_command(\["-k", message\])' \
    'def build_terminal_ai_context_prompt' 'def submit_ai_chat_prompt' \
    'TERMINAL_AI_DEFAULT_PROMPT = "Explain me this"' 'build_hhs_ask_command(clean_prompt)' '"Asking AI..."' \
    'submit_ai_chat_prompt(prompt, ollama_model, context_size)' 'build_hhs_ask_execute_command(\["-c"\])' \
    'build_hhs_ask_execute_command(\["-p"\])' 'build_hhs_ask_execute_command(\["-r"\])' \
    'build_hhs_ask_execute_command(\["-i", file_path\])' 'build_hhs_ask_execute_command(\["-m"\])' \
    'def render_ai_context_panel' 'def render_ai_prompt_file_panel' 'def render_ai_context_output_panel' \
    'def refresh_ai_context' 'def clear_ai_context_history' 'def refresh_ai_prompt' \
    'def refresh_ai_prompt_file' 'def save_ai_prompt_file' 'def revert_ai_prompt_file' \
    'def build_hhs_ask_prompt_file_command' 'def build_hhs_save_ask_prompt_file_command' \
    'def build_hhs_revert_ask_prompt_file_command' 'def run_hhs_ask_prompt_file' \
    'def run_hhs_save_ask_prompt_file' 'def run_hhs_revert_ask_prompt_file' 'cat "${HHS_OLLAMA_PROMPT_FILE}"' \
    'prompt_file="${HHS_OLLAMA_PROMPT_FILE}"' \
    'cp -f "${HHS_OLLAMA_PROMPT_SOURCE}" "${HHS_OLLAMA_PROMPT_FILE}"' 'def ingest_ai_context_upload' \
    'def run_hhs_ask_ingest'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/constants.py" 'AI_CONTEXT_UPLOAD_TYPES = ('

  assert_file_contains "${ui_file}" 'st.file_uploader('

  assert_file_contains_many "${css_file}" \
'\[data-testid="stFileUploader"\] button' '\[data-testid="stFileUploader"\] button \*' '.stButton button' \
    '.stButton button \*'
  assert_file_contains_many "${ui_file}" \
'type=hhs_ui_constants.AI_CONTEXT_UPLOAD_TYPES' 'key="ai_context_upload"' 'key="ai_ingest_context_button"' \
    '" Ingest"'
  run python3 - <<'PY'
import ast
import re
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
namespace = {
    "re": re,
    "hhs_ui": SimpleNamespace(
        ANSI_ESCAPE_PATTERN=re.compile(
            r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
        ),
        ESCAPED_ANSI_ESCAPE_PATTERN=re.compile(
            r"(?:\\033|\\x1b|\\e)(?:\[[0-?]*[ -/]*[@-~]|\][^\\]*(?:\\a|\\033\\|\\x1b\\)|[()][A-Za-z0-9])"
        ),
    ),
}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(
        functions[name]
        for name in (
            "strip_ansi",
            "interpret_terminal_edit_sequences",
            "clean_hhs_ask_output",
        )
    ),
    namespace,
)
raw_output = (
    "\x1b[H\x1b[2J\x1b[3J"
    "✨ llama3.1:latest[128K]:\n"
    "allows for fr\x1b[2D\x1b[Kfree use\n"
    "Using HomeSe\x1b[6D\x1b[KHomeSetup\n"
)
clean_output = namespace["clean_hhs_ask_output"](raw_output)
assert "allows for free use" in clean_output
assert "Using HomeSetup" in clean_output
assert "[2D" not in clean_output
assert "[K" not in clean_output
assert "frfree" not in clean_output
PY
  assert_success

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
refresh_body = ui_source.split("def refresh_ai_context", 1)[1].split("\ndef ", 1)[0]
context_body = ui_source.split("def render_ai_context_panel", 1)[1].split("\ndef ", 1)[0]
clear_context_body = ui_source.split("def clear_ai_context_history", 1)[1].split("\ndef ", 1)[0]
complete_context_body = ui_source.split("def complete_ai_context_action_job", 1)[1].split("\ndef ", 1)[0]
assert "queue_ai_context_action(" in refresh_body
assert "build_hhs_ask_context_command()" in refresh_body
assert "run_hhs_ask_context()" not in refresh_body
assert "run_hhs_ask_context()" not in context_body
assert "run_hhs_ask_prompt()" not in context_body
assert "render_ai_prompt_file_panel()" in context_body
assert "render_ai_context_output_panel()" in context_body
assert "queue_ai_context_action(" in clear_context_body
assert "build_hhs_ask_reset_command()" in clear_context_body
assert "run_hhs_ask_reset(close_dialogs=True)" not in clear_context_body
assert 'st.session_state["ai_context_output"] = ""' in complete_context_body
assert 'st.session_state["ai_context_error"] = ""' in complete_context_body
assert 'st.session_state["ai_chat_messages"] = []' in complete_context_body
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'key="ai_refresh_context_button"' 'key="ai_clear_context_button"' 'on_click=clear_ai_context_history'
  assert_file_not_contains "${ui_file}" 'key="ai_prompt_context_button"'

  assert_file_contains "${ui_file}" '" Refresh"'

  assert_file_not_contains "${ui_file}" '" Prompt"'

  assert_file_contains_many "${ui_file}" \
'with st.expander("Prompt", expanded=False):' 'with st.expander("History", expanded=True):' \
    'key="ai_prompt_editor"' 'key="ai_prompt_save_button"' 'key="ai_prompt_revert_button"' \
    'on_click=save_ai_prompt_file' 'on_click=revert_ai_prompt_file' \
    'upload_col, ingest_col, clear_col, refresh_col = st.columns(' \
    '\[1.35, 0.7, 0.7, 0.8\], vertical_alignment="center"' 'st.session_state\["ai_context_output"\]' \
    'st.session_state\["ai_context_error"\]'
  assert_file_contains_many "${constants_file}" \
'"ai_context_output"' '"ai_context_error"' '"ai_prompt_editor"' '"ai_prompt_error"' '"ai_prompt_loaded"'
  assert_file_contains_many "${ui_file}" \
'st.session_state.setdefault("ai_context_output", "")' 'st.session_state.setdefault("ai_context_error", "")' \
    'st.session_state.setdefault("ai_prompt_editor", "")' 'st.session_state.setdefault("ai_prompt_error", "")' \
    'st.session_state.setdefault("ai_prompt_loaded", False)' 'render_view_subtitle("AI context is clear")'
  assert_file_not_contains "${ui_file}" 'st.markdown("### AI context is clear")'

  assert_file_contains_many "${ui_file}" \
'elif ai_view == "CONTEXT"' 'render_ai_context_panel()' 'render_terminal_output(context_output)'
  assert_file_not_contains_many "${ui_file}" \
'key="ai_show_context_button"' 'show_ai_chat_context'
  assert_file_contains_many "${ui_file}" \
'" Clear"' 'build_hhs_ask_reset_command()'
  assert_file_not_contains "${ui_file}" 'run_hhs_ask_reset(close_dialogs=True)'

  assert_file_contains_many "${ui_file}" \
'st.session_state\["ai_context_output"\] = ""' 'st.session_state\["ai_context_error"\] = ""'
  run grep -q -- '-i|--ingest' "${ask_file}"
  assert_success

  run grep -q -- '-p | --prompt' "${ask_file}"
  assert_success

  assert_file_contains "${ask_file}" 'function show_prompt'

  assert_file_not_contains "${ask_file}" 'function seed_ollama_prompt_file'

  assert_file_contains_many "${ask_file}" \
'function load_ollama_prompt' 'function render_ollama_prompt_template' \
    'HHS_OLLAMA_PROMPT_SOURCE="${HHS_OLLAMA_PROMPT_SOURCE:-${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md}"' \
    'HHS_OLLAMA_PROMPT_FILE="${HHS_OLLAMA_PROMPT_FILE:-${HHS_DIR}/hhs-ask-ollama.md}"'
  assert_file_not_contains "${ask_file}" 'HHS_OLLAMA_PROMPT="### INSTRUCTIONS ###'

  assert_file_contains "${HHS_REPO_DIR}/install.bash" 'copy_file "${INSTALL_DIR}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md" "${HHS_DIR}/hhs-ask-ollama.md"'

  assert_file_contains_many "${hhsrc_file}" \
'export HHS_OLLAMA_PROMPT_SOURCE="${HHS_HOME}"/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md' \
    'export HHS_OLLAMA_PROMPT_FILE="${HHS_DIR}"/hhs-ask-ollama.md' \
    'if ! \[\[ -s "${HHS_OLLAMA_PROMPT_FILE}" \]\]; then' \
    '\cp -f "${HHS_OLLAMA_PROMPT_SOURCE}" "${HHS_OLLAMA_PROMPT_FILE}"'
  run bash --noprofile --norc -c '
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_OLLAMA_HISTORY_FILE="${2}/history.md"
    export HHS_SETUP_FILE="${2}/setup.toml"
    export HHS_MY_SHELL="bash"
    export HHS_MY_OS="Darwin"
    export HHS_MY_OS_RELEASE="test"
    export HHS_GITHUB_URL="https://example.invalid/hhs"
    export IS_PIPED=0
    mkdir -p "${HHS_DIR}"
    cp "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md" "${HHS_DIR}/hhs-ask-ollama.md"
    function __hhs_toml_get() { printf "hhs_ollama_model=llama3.1:latest\n"; }
    function quit() { return "${1:-0}"; }
    source "${1}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"
    [[ -s "${HHS_DIR}/hhs-ask-ollama.md" ]]
    show_prompt
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}"
  assert_success
  assert_output --partial '### ROLE'
  assert_output --partial 'Shell: bash'
  assert_output --partial 'Operating system: test'
  assert_output --partial 'OS family: Darwin'
  refute_output --partial '${HHS_MY_SHELL}'
  refute_output --partial '${HHS_HOME}'

  run bash --noprofile --norc -c '
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/override-hhs"
    export HHS_OLLAMA_HISTORY_FILE="${2}/history.md"
    export HHS_SETUP_FILE="${2}/setup.toml"
    export HHS_MY_SHELL="bash"
    export HHS_MY_OS="Darwin"
    export HHS_MY_OS_RELEASE="test"
    export HHS_GITHUB_URL="https://example.invalid/hhs"
    export HHS_OLLAMA_PROMPT="custom prompt"
    export IS_PIPED=0
    function __hhs_toml_get() { printf "hhs_ollama_model=llama3.1:latest\n"; }
    function quit() { return "${1:-0}"; }
    source "${1}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"
    show_prompt
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}"
  assert_success
  assert_output 'custom prompt'

  assert_file_contains_many "${ask_file}" \
'function ingest_context' 'is_text_context_file'
  run grep -Fq -- 'printf "%s" "(${ctx} * 0.7)/1" | bc' "${ask_file}"
  assert_success
  run grep -q -- '-r|--reset) clear_context' "${ask_file}"
  assert_success

  assert_file_not_contains "${ui_file}" 'disabled=not st.session_state\["ai_chat_messages"\]'

  assert_file_contains "${ui_file}" 'render_view_subtitle("There is no chat history")'

  assert_file_not_contains "${ui_file}" 'st.markdown("### There is no chat history")'

  assert_file_contains "${ui_file}" 'meta_col, clear_col = st.columns(\[3.6, 0.4\], vertical_alignment="center")'

  assert_file_not_contains_many "${css_file}" \
'.st-key-ai_show_context_button button' '.st-key-ai_clear_chat_button button'
  assert_file_contains_many "${ui_file}" \
'build_hhs_ask_execute_command(\["-s", model_name\])' 'def hhs_ask_timeout_seconds' \
    'return 180 if connected_ssh_host() else 90' 'timeout_seconds=hhs_ask_timeout_seconds()'
  assert_file_contains_many "${constants_file}" \
'AI_PERFORMANCE_MIN_SAMPLES = 3' 'AI_PERFORMANCE_TIMING_LIMIT = 100'
  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'AI_PERFORMANCE_MIN_SAMPLES' 'AI_PERFORMANCE_RECALC_INTERVAL' 'AI_PERFORMANCE_TIMING_LIMIT'
  assert_file_contains_many "${constants_file}" \
'"ai_model_performance_timings"' '"ai_model_performance_averages"' '"ai_model_performance_sample_counts"'
  assert_file_contains_many "${ui_file}" \
'def record_ai_model_request_duration' 'def ai_chat_meta_html' 'def parse_context_window_kib' \
    'def ai_context_used_percent' 'def ai_context_used_color' 'def ai_context_used_meta_html' \
    'def html_tooltip_chip' 'def model_characteristics_tooltip_html' 'def ai_context_used_tooltip_html' \
    'def ai_model_recent_duration_tooltip_html' 'def ollama_history_file' 'def ollama_prompt_file' \
    'def file_size_bytes' 'HHS_OLLAMA_HISTORY_FILE' 'HHS_OLLAMA_PROMPT_FILE' '".ollama_history"' \
    '"hhs-ask-ollama.md"' 'prompt_size = file_size_bytes(ollama_prompt_file())' \
    'history_size = file_size_bytes(ollama_history_file())' 'percent_of_context(prompt_size + history_size' \
    '"Ctx Used"' 'Current logged user' 'Prompt: ' 'Context: ' 'parse_rows_cached(' \
    'parse_ollama_model_rows(output, ollama_model)' 'timing_durations_for_model(model_name)\[-5:\]'
  assert_file_contains_many "${css_file}" \
'hhs-tooltip-content' '.hhs-ai-chat-meta .hhs-tooltip:hover .hhs-tooltip-content'
  assert_file_contains_many "${ui_file}" \
'hhs-ai-chat-model hhs-ai-chat-user' 'hhs-ai-chat-model hhs-ai-context-used' 'var(--hhs-danger)' \
    'var(--hhs-warning)' 'var(--hhs-success)' 'hhs-ai-chat-model hhs-ai-chat-duration' \
    'meta_placeholder = st.empty()' 'meta_placeholder.markdown(' \
    'model_sample_count == hhs_ui.AI_PERFORMANCE_MIN_SAMPLES' 'def ai_model_performance_timings'
  run grep -q -- '-hhs_ui.AI_PERFORMANCE_TIMING_LIMIT' "${ui_file}"
  assert_success

  assert_file_contains_many "${ui_file}" \
'use_cache=False' 'ask_started_at = time.perf_counter()' \
    'record_ai_model_request_duration(ollama_model, request_duration)' '"Latency"' \
    'def parse_ollama_model_rows' 'def first_downloaded_ollama_model' 'Delete Model' 'Select Model'
}

# TC - 14

@test "when selecting missing Ask model then ask plugin should download it instead of the UI" {
  assert_file_contains_many "${ask_file}" \
'ollama pull "${model_name}"' '__hhs_toml_set "${HHS_SETUP_FILE}" "hhs_ollama_model=${model_name}" "ollama"'
  assert_file_not_contains_many "${ui_file}" \
'ollama pull' 'build_ollama_download_and_select_model_command'
}

@test "when UI creates disposable files then cache paths should be deterministic" {
  run python3 - "${ui_file}" "${constants_file}" "${ui_plugin_file}" <<'PY'
from pathlib import Path
import sys

source = (
    Path(sys.argv[1]).read_text(encoding="utf-8")
    + "\n"
    + Path(sys.argv[2]).read_text(encoding="utf-8")
    + "\n"
    + Path(sys.argv[3]).read_text(encoding="utf-8")
)
required_fragments = (
    "def ui_disposable_files_dir() -> Path:",
    "hhs_ui.HHS_CACHE_DIR.mkdir(parents=True, exist_ok=True)",
    "return hhs_ui.HHS_CACHE_DIR",
    'UI_STATE_FILE = HHS_CACHE_DIR / "streamlit-ui-state.json"',
    'UI_CACHE_FILE = HHS_CACHE_DIR / "streamlit-ui-cache.json"',
    'TTYD_INDEX_FILE = HHS_CACHE_DIR / "streamlit-ttyd-index.html"',
    'return (hhs_ui.HHS_CACHE_DIR / ".streamlit-ui-state",)',
    'return (hhs_ui.HHS_CACHE_DIR / ".streamlit-ui-cache",)',
    (
        'HHS_STREAMLIT_UI_RUNTIME_DIR="${HHS_STREAMLIT_UI_RUNTIME_DIR:-'
        '${HHS_CACHE_DIR:-${HHS_DIR}/cache}}"'
    ),
    (
        ': "${HHS_STREAMLIT_UI_PID_FILE:='
        '${HHS_STREAMLIT_UI_RUNTIME_DIR}/.streamlit-ui.pid}"'
    ),
    (
        ': "${HHS_STREAMLIT_UI_PROCESS_FILE:='
        '${HHS_STREAMLIT_UI_RUNTIME_DIR}/.streamlit-ui.processes}"'
    ),
    'function get_legacy_ui_pid_file()',
    'function get_legacy_ui_process_registry_file()',
    "def ai_context_upload_path(file_name: str) -> Path:",
    "hhs-ai-context-upload",
    "tmp_file_path.write_bytes(uploaded_file.getvalue())",
    "queue_ai_context_action(",
    "build_hhs_ask_ingest_command(str(tmp_file_path))",
    "def safe_background_job_name(job_name: str) -> str:",
    "def background_job_output_path(job_name: str, stream_name: str) -> Path:",
    'stdout_path = str(background_job_output_path(job_name, "stdout"))',
    'stderr_path = str(background_job_output_path(job_name, "stderr"))',
    'download_dir = ui_disposable_files_dir() / "hhs-search-open.dir"',
    "shutil.rmtree(download_dir, ignore_errors=True)",
    "download_dir.mkdir(parents=True, exist_ok=True)",
)
for fragment in required_fragments:
    assert fragment in source, fragment

random_temp_fragments = (
    "import tempfile",
    "tempfile.NamedTemporaryFile",
    "tempfile.mkdtemp",
)
for fragment in random_temp_fragments:
    assert fragment not in source, fragment
PY
  assert_success
}

# TC - 15

@test "when rendering AI model settings then status, scrolling, and footer guard should be present" {
  assert_file_contains_many "${constants_file}" \
'AI_MODEL_TABLE_KEY = "ai_model_table"' 'AI_MODEL_ACTION_SCROLL_HELPER_HEIGHT = 0'
  assert_file_contains_many "${ui_file}" \
'def scroll_to_ai_model_actions' 'hhs-ai-model-action-footer-guard'
  assert_file_contains "${css_file}" 'hhs-ai-model-action-footer-guard'

  run python3 - "${css_file}" <<'PY'
import sys
from pathlib import Path

css = Path(sys.argv[1]).read_text(encoding="utf-8")
assert ".hhs-ai-model-action-footer-guard" in css
assert "min-height: 8rem" in css[
    css.index(".hhs-ai-model-action-footer-guard"):
    css.index(".st-key-ai_confirm_clear_button")
]
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'status == "Downloaded"' 'color: #4da3ff'
  run grep -q -- '--hhs-model-accent: #4da3ff' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success
}

# TC - 16
