#!/usr/bin/env bats

#  Script: hhs-ui.bats
# Purpose: HomeSetup Streamlit UI tests.
# Created: Jun 25, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

export HHS_REPO_DIR="${BATS_TEST_DIRNAME%/tests}"
export HHS_HOME="${HHS_REPO_DIR}"

load test_helper
load_bats_libs

setup() {
  ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs-ui/streamlit_ui.py"
  constants_file="${HHS_REPO_DIR}/bin/apps/py/hhs-ui/constants.py"
  css_file="${HHS_REPO_DIR}/bin/apps/py/hhs-ui/streamlit_ui.css"
  ask_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"
  ui_plugin_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ui/ui.bash"
}

# TC - 1
@test "when installing HomeSetup then Streamlit should be included as a Python package" {
  run grep -q "'streamlit'" "${HHS_REPO_DIR}/install.bash"
  assert_success
}

# TC - 2
@test "when uninstalling HomeSetup then Streamlit should be included as a removable Python package" {
  run grep -q "'streamlit'" "${HHS_REPO_DIR}/uninstall.bash"
  assert_success
}

# TC - 3
@test "when registering plugins then ui plugin should expose required hhs functions" {
  run grep -q '^function help()' "${ui_plugin_file}"
  assert_success

  run grep -q '^function version()' "${ui_plugin_file}"
  assert_success

  run grep -q '^function cleanup()' "${ui_plugin_file}"
  assert_success

  run grep -q '^function execute()' "${ui_plugin_file}"
  assert_success
}

# TC - 4
@test "when loading Streamlit UI source then Python syntax should be valid" {
  run python3 -c 'import ast, pathlib; ast.parse(pathlib.Path("bin/apps/py/hhs-ui/streamlit_ui.py").read_text())'
  assert_success
}

# TC - 5
@test "when launching HomeSetup UI then plugin should use the configured Streamlit UI port" {
  run grep -q 'HHS_STREAMLIT_UI_PORT:-18501' "${HHS_REPO_DIR}/dotfiles/bash/hhsrc.bash"
  assert_success

  run grep -q 'HHS_STREAMLIT_UI_PORT:-18501' "${ui_plugin_file}"
  assert_success

  run grep -q -- '--server.port "${HHS_STREAMLIT_UI_PORT}"' "${ui_plugin_file}"
  assert_success
}

# TC - 6
@test "when listing services then HomeSetup UI should be included as a managed service" {
  services_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/services/services.bash"

  run grep -q 'homesetup-ui:running' "${services_file}"
  assert_success

  run grep -q 'homesetup-ui:stopped' "${services_file}"
  assert_success
}

# TC - 7
@test "when styling HomeSetup UI then Dracula theme and Nerd Font should be configured" {
  run test -s "${css_file}"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
  assert_success

  run grep -q 'APP_CSS_FILE = APP_DIR / "streamlit_ui.css"' "${constants_file}"
  assert_success

  run grep -q 'APP_FONT_FAMILY = "Droid Sans Mono for Powerline Nerd Font Complete"' "${constants_file}"
  assert_success

  run grep -q 'APP_THEME_OPTIONS_BY_THEME = {' "${constants_file}"
  assert_success

  run grep -q '"theme.base": "dark"' "${constants_file}"
  assert_success

  run grep -q '"theme.backgroundColor": "#282a36"' "${constants_file}"
  assert_success

  run grep -q -- '--hhs-ui-font-family: "Droid Sans Mono for Powerline Nerd Font Complete", monospace' "${css_file}"
  assert_success

  run grep -q -- '--hhs-dracula-background: #282a36' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run grep -q '<style>' "${css_file}"
  assert_failure
}

# TC - 8
@test "when selecting a UI theme then the selected theme should persist and restore" {
  run python3 - <<'PY'
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

app_dir = Path("bin/apps/py/hhs-ui").resolve()
sys.path.insert(0, str(app_dir))

streamlit = types.ModuleType("streamlit")
streamlit.session_state = {}
config_options = {}
streamlit.config = types.SimpleNamespace(
    set_option=lambda key, value: config_options.__setitem__(key, value)
)
streamlit.fragment = lambda **_kwargs: (lambda func: func)
sys.modules["streamlit"] = streamlit

components = types.ModuleType("streamlit.components")
components_v1 = types.ModuleType("streamlit.components.v1")
components.v1 = components_v1
sys.modules["streamlit.components"] = components
sys.modules["streamlit.components.v1"] = components_v1
sys.modules["altair"] = types.ModuleType("altair")
sys.modules["pandas"] = types.ModuleType("pandas")

spec = importlib.util.spec_from_file_location("streamlit_ui_under_test", app_dir / "streamlit_ui.py")
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    (themes_dir / "dracula.css").write_text("dracula-css", encoding="utf-8")
    (themes_dir / "tokyo-night.css").write_text("tokyo-night-css", encoding="utf-8")
    ui.APP_THEME_CSS_FILE = themes_dir / "dracula.css"
    ui.UI_STATE_FILE = tmp_path / "hhs-dir" / ".streamlit-ui-state"

    ui.persist_theme_selection("tokyo-night")
    assert json.loads(ui.UI_STATE_FILE.read_text(encoding="utf-8"))["theme_selected"] == "tokyo-night"

    streamlit.session_state.clear()
    streamlit.session_state["active_view"] = "Home"
    ui.save_ui_state()
    assert json.loads(ui.UI_STATE_FILE.read_text(encoding="utf-8"))["theme_selected"] == "tokyo-night"

    streamlit.session_state.clear()
    ui.restore_ui_state()
    assert streamlit.session_state["theme_selected"] == "tokyo-night"
    assert ui.load_app_theme_css() == "tokyo-night-css"

    config_options.clear()
    ui.configure_app_font_theme(ui.persisted_theme_name())
    assert config_options["theme.backgroundColor"] == "#1a1b26"

    app_state_file = tmp_path / ".streamlit-ui-state"
    app_state_file.write_text('{"theme_selected": "dracula"}', encoding="utf-8")
    streamlit.session_state.clear()
    ui.restore_ui_state()
    assert streamlit.session_state["theme_selected"] == "tokyo-night"
PY
  assert_success
}

# TC - 9
@test "when rendering the main UI then current navigation tabs should be registered" {
  run grep -q 'VIEWS = ("Home", "Configs", "Services", "Monitor", "History")' "${constants_file}"
  assert_success

  run grep -q 'AI_VIEW = "AI"' "${constants_file}"
  assert_success

  run grep -q 'AI_VIEWS = ("CHAT", "SETTINGS")' "${constants_file}"
  assert_success

  run grep -q 'CONFIG_VIEWS = ("ENV", "PATH", "DIR", "CMD", "ALIAS")' "${constants_file}"
  assert_success

  run grep -q 'HISTORY_VIEWS = ("COMMANDS", "DIRECTORIES", "STATS")' "${constants_file}"
  assert_success

  run grep -q 'MONITOR_VIEWS = ("DISK", "MEM", "CPU", "PROCESSES", "LOGS")' "${constants_file}"
  assert_success

  run grep -q 'SERVICE_FILTERS = ("All", "Started", "Stopped", "Other")' "${constants_file}"
  assert_success

  run grep -q 'PATH_FILTERS = ("All", "Shell", "Private", "Custom", "Other")' "${constants_file}"
  assert_success
}

# TC - 10
@test "when executing shell commands then every UI command path should use run_bash_command" {
  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs-ui/streamlit_ui.py").read_text())
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
    if is_subprocess_run and enclosing_function(node) != "run_bash_command":
        violations.append(f"line {node.lineno}")

if violations:
    raise SystemExit("subprocess.run outside run_bash_command: " + ", ".join(violations))
PY
  assert_success

  run grep -q 'def run_bash_command(' "${ui_file}"
  assert_success

  run grep -q 'return run_bash_command(' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_services_quietly' "${ui_file}"
  assert_success
}

# TC - 11
@test "when showing command progress then command runner should paint overlay before subprocess" {
  run grep -q 'def setOverlay(' "${ui_file}"
  assert_success

  run grep -q 'def close_all_dialogs()' "${ui_file}"
  assert_success

  run grep -q 'close_all_dialogs()' "${ui_file}"
  assert_success

  run grep -q 'setOverlay(True, loader_message, close_dialogs=close_dialogs)' "${ui_file}"
  assert_success

  run grep -q 'with placeholder.container()' "${ui_file}"
  assert_success

  run grep -q 'time.sleep(0.1)' "${ui_file}"
  assert_success

  run grep -q 'setOverlay(False)' "${ui_file}"
  assert_success

  run grep -q 'hhs-tab-loader' "${css_file}"
  assert_success

  run grep -q 'background: var(--hhs-dracula-background)' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success
}

# TC - 12
@test "when confirming actions then reusable popDialog component should be used" {
  run grep -q 'def popDialog(' "${ui_file}"
  assert_success

  run grep -q '@st.dialog(title)' "${ui_file}"
  assert_success

  run grep -q 'popDialog(' "${ui_file}"
  assert_success

  run grep -q 'st.rerun(scope="app")' "${ui_file}"
  assert_success

  run grep -q 'st.warning("Clear the chat and reset AI context entirely?")' "${ui_file}"
  assert_failure

  run grep -q '@st.dialog("Confirm model change")' "${ui_file}"
  assert_failure

  run grep -q '@st.dialog("Confirm model deletion")' "${ui_file}"
  assert_failure
}

# TC - 13
@test "when using Ask AI then chat and model settings should support context, reset, select, and delete" {
  run grep -q 'APP_AI_USER_AVATAR_FILE = APP_DIR / "assets/images/user.png"' "${constants_file}"
  assert_success

  run grep -q 'APP_AI_OLLAMA_AVATAR_FILE = APP_DIR / "assets/images/ollama.png"' "${constants_file}"
  assert_success

  run grep -q 'APP_AI_HOMESETUP_AVATAR_FILE = APP_DIR / "assets/images/homesetup.png"' "${constants_file}"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/assets/images/user.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/assets/images/ollama.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/assets/images/homesetup.png"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-k", message\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-c"\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-r"\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-m"\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-s", model_name\])' "${ui_file}"
  assert_success

  run grep -q 'def parse_ollama_model_rows' "${ui_file}"
  assert_success

  run grep -q 'def first_downloaded_ollama_model' "${ui_file}"
  assert_success

  run grep -q 'Delete Model' "${ui_file}"
  assert_success

  run grep -q 'Select Model' "${ui_file}"
  assert_success
}

# TC - 14
@test "when selecting missing Ask model then ask plugin should download it instead of the UI" {
  run grep -q 'ollama pull "${model_name}"' "${ask_file}"
  assert_success

  run grep -q '__hhs_toml_set "${HHS_SETUP_FILE}" "hhs_ollama_model=${model_name}" "ollama"' "${ask_file}"
  assert_success

  run grep -q 'ollama pull' "${ui_file}"
  assert_failure

  run grep -q 'build_ollama_download_and_select_model_command' "${ui_file}"
  assert_failure
}

# TC - 15
@test "when rendering AI model settings then status, scrolling, and footer guard should be present" {
  run grep -q 'AI_MODEL_TABLE_KEY = "ai_model_table"' "${constants_file}"
  assert_success

  run grep -q 'AI_MODEL_ACTION_SCROLL_HELPER_HEIGHT = 0' "${constants_file}"
  assert_success

  run grep -q 'def scroll_to_ai_model_actions' "${ui_file}"
  assert_success

  run grep -q 'hhs-ai-model-action-footer-guard' "${ui_file}"
  assert_success

  run grep -q 'hhs-ai-model-action-footer-guard' "${css_file}"
  assert_success

  run grep -q 'hhs-ai-selected-model' "${ui_file}"
  assert_success

  run grep -q 'hhs-ai-selected-model strong' "${css_file}"
  assert_success

  run grep -q 'min-height: 8rem' "${css_file}"
  assert_success

  run grep -q 'status == "Downloaded"' "${ui_file}"
  assert_success

  run grep -q 'color: #4da3ff' "${ui_file}"
  assert_success

  run grep -q -- '--hhs-ui-blue: #4da3ff' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success
}

# TC - 16
@test "when rendering monitor panes then process listing and process kill should be wired" {
  run grep -q 'PROCESS_TABLE_KEY = "monitor_process_table"' "${constants_file}"
  assert_success

  run grep -q 'PROCESS_LIST_LINE_PATTERN' "${constants_file}"
  assert_success

  run grep -q 'def build_hhs_process_list_command' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_process_kill_command' "${ui_file}"
  assert_success

  run grep -q '__hhs_process_list' "${ui_file}"
  assert_success

  run grep -q '__hhs_process_kill -f' "${ui_file}"
  assert_success

  run grep -q 'def render_monitor_processes_panel' "${ui_file}"
  assert_success

  run grep -q 'key="monitor_process_filter"' "${ui_file}"
  assert_success
}

# TC - 17
@test "when rendering logs then VT100 colors and tail refresh should be handled in the LOGS panel" {
  run grep -q 'LOG_TAILOR_RULES' "${constants_file}"
  assert_success

  run grep -q 'def colorize_log_output' "${ui_file}"
  assert_success

  run grep -q 'def render_monitor_logs_panel' "${ui_file}"
  assert_success

  run grep -q '__hhs logs' "${ui_file}"
  assert_success

  run grep -q '@st.fragment(run_every="5s")' "${ui_file}"
  assert_success

  run grep -q 'white-space: pre' "${css_file}"
  assert_success
}

# TC - 18
@test "when rendering configs then current command-backed tables and filters should be wired" {
  run grep -q '__hhs_envs' "${ui_file}"
  assert_success

  run grep -q '__hhs_paths' "${ui_file}"
  assert_success

  run grep -q '__hhs_load_dir -l' "${ui_file}"
  assert_success

  run grep -q '__hhs_command -l' "${ui_file}"
  assert_success

  run grep -q '__hhs_aliases' "${ui_file}"
  assert_success

  run grep -q 'def render_env_rows' "${ui_file}"
  assert_success

  run grep -q 'def render_path_rows' "${ui_file}"
  assert_success

  run grep -q 'def render_dirs_table' "${ui_file}"
  assert_success

  run grep -q 'def render_cmds_table' "${ui_file}"
  assert_success

  run grep -q 'def render_aliases_table' "${ui_file}"
  assert_success
}

# TC - 19
@test "when rendering UI then deprecated table approaches should stay removed" {
  run grep -q 'st.data_editor' "${ui_file}"
  assert_failure

  run grep -q 'st.table(' "${ui_file}"
  assert_failure

  run grep -q 'render_env_table_html' "${ui_file}"
  assert_failure

  run grep -q 'hhs-env-table-scroll' "${css_file}"
  assert_failure

  run grep -q '<style>' "${css_file}"
  assert_failure
}
