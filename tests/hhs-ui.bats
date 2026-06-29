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
  hspm_plugin_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/hspm.bash"
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

  run grep -q 'reinstall <package...>' "${hspm_plugin_file}"
  assert_success

  run grep -q 'reinstall_recipe' "${hspm_plugin_file}"
  assert_success
}

# TC - 4
@test "when installing Ollama on Linux then hspm should use the current official installer URL" {
  ollama_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/ollama.recipe"
  ollama_darwin_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/ollama.recipe"

  run grep -q 'https://ollama.com/install.sh' "${ollama_recipe_file}"
  assert_success

  run grep -q 'OllamaInstall.sh' "${ollama_recipe_file}"
  assert_failure

  run grep -q 'systemctl stop ollama' "${ollama_recipe_file}"
  assert_success

  run grep -q "pkill -f 'ollama serve'" "${ollama_recipe_file}"
  assert_success

  run grep -q 'brew services stop ollama' "${ollama_darwin_recipe_file}"
  assert_success
}

# TC - 5
@test "when loading hspm recipes then Bash syntax should be valid" {
  run bash --noprofile --norc -c '
    for recipe in "$1"/bin/apps/bash/hhs-app/plugins/hspm/recipes/*/*.recipe; do
      bash -n "${recipe}" || exit 1
    done
  ' -- "${HHS_REPO_DIR}"
  assert_success
}

# TC - 6
@test "when reviewing hspm recipes then known stale recipe targets should be updated" {
  nvm_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/nvm.recipe"
  vue_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/vue.recipe"
  jenkins_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/jenkins.recipe"

  run grep -q 'https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.5/install.sh' "${nvm_recipe_file}"
  assert_success

  run grep -q 'creationix/nvm' "${nvm_recipe_file}"
  assert_failure

  run grep -q 'npm install -g @vue/cli' "${vue_recipe_file}"
  assert_success

  run grep -q 'openjdk-21-jre' "${jenkins_recipe_file}"
  assert_success

  run grep -q 'jenkins.io-2026.key' "${jenkins_recipe_file}"
  assert_success
}

# TC - 7
@test "when hspm install recipe fails then execute should return failure" {
  run bash --noprofile --norc -c '
    set -u
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_LOG_DIR="${1}/log"
    export HHS_MY_OS="$(uname -s)"
    export HHS_MY_OS_RELEASE="test"
    export HHS_MY_OS_PACKMAN="test-packman"
    export HHS_DEV_TOOLS=""
    export HHS_HIGHLIGHT_COLOR=""
    export BLUE=""
    export GREEN=""
    export NC=""
    export ORANGE=""
    export RED=""
    export WHITE=""
    export YELLOW=""
    export OLDIFS="${IFS}"
    export PLUGINS_DIR="${1}/plugins"
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}" "${PLUGINS_DIR}/hspm/recipes/${HHS_MY_OS}"
    printf "%s\n" \
      "function _depends_() { return 0; }" \
      "function _install_() { return 22; }" \
      "function _uninstall_() { return 0; }" \
      "function _which_() { return 1; }" \
      > "${PLUGINS_DIR}/hspm/recipes/${HHS_MY_OS}/default.recipe"
    touch "${PLUGINS_DIR}/hspm/catalog.toml"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_errcho() {
      shift
      printf "%s\n" "$*" >&2
    }
    source "${2}"
    execute install broken-package
  ' -- "${BATS_TEST_TMPDIR}" "${hspm_plugin_file}"
  assert_failure
  assert_output --partial 'Failed to install "broken-package"'
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
@test "when remote SSH command closes then Streamlit UI should clear stale connection state" {
  run grep -q 'def ssh_shared_connection_closed' "${ui_file}"
  assert_success

  run grep -q 'def clear_disconnected_ssh_host' "${ui_file}"
  assert_success

  run grep -q 'handle_remote_command_result(remote_host, result)' "${ui_file}"
  assert_success

  run grep -q 'result = completed_process_from_cache(command_to_run, cached_value)' "${ui_file}"
  assert_success

  run grep -q 'if use_cache and not ssh_shared_connection_closed(result)' "${ui_file}"
  assert_success

  run grep -q 'if remote_host and not ssh_connection_is_alive(remote_host)' "${ui_file}"
  assert_success

  run grep -q 'completed_disconnected_ssh_process(command_to_run, remote_host)' "${ui_file}"
  assert_success

  run grep -q 'st.rerun()' "${ui_file}"
  assert_success

  run grep -q 'ConnectTimeout=5' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_host_selected"\] = local_hostname()' "${ui_file}"
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

  run grep -q -- '--hhs-ui-font-family: "Droid Sans Mono for Powerline Nerd Font Complete", monospace' "${css_file}"
  assert_success

  run grep -q -- '--hhs-theme-background-color: #282a36' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-background: var(--hhs-theme-background-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run grep -q 'def css_custom_properties' "${ui_file}"
  assert_success

  run grep -q 'def theme_config_options' "${ui_file}"
  assert_success

  run grep -q 'class="hhs-sidebar-title"' "${ui_file}"
  assert_success

  run grep -q 'color: var(--hhs-theme-text-color)' "${css_file}"
  assert_success

  run grep -q 'position: fixed' "${css_file}"
  assert_success

  run grep -q 'top: 58px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-sidebar-inline-inset: 20px' "${css_file}"
  assert_success

  run grep -q 'padding: 0 2rem 0 var(--hhs-sidebar-inline-inset)' "${css_file}"
  assert_success

  run grep -q 'host_kind = "Local" if selected_host_is_local() else "SSH"' "${ui_file}"
  assert_success

  run grep -q 'Host ({host_kind})' "${ui_file}"
  assert_success

  run grep -q 'def select_ssh_host_from_widget' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_host_selector"' "${ui_file}"
  assert_success

  run grep -q 'on_change=select_ssh_host_from_widget' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_host_selected"' "${ui_file}"
  assert_failure

  run grep -q 'ssh_host_connected_display_' "${ui_file}"
  assert_success

  run grep -q 'disabled=True' "${ui_file}"
  assert_success

  run grep -Fq 'options = ["", local_hostname()]' "${ui_file}"
  assert_failure

  run grep -Fq 'options = [local_hostname()]' "${ui_file}"
  assert_success

  run grep -q 'if not selected_host:' "${ui_file}"
  assert_success

  run grep -q 'state_hosts = (' "${ui_file}"
  assert_success

  run grep -q 'registered_ssh_connection_host()' "${ui_file}"
  assert_success

  run grep -q 'def selected_remote_host_requires_connection' "${ui_file}"
  assert_success

  run grep -q 'def render_remote_connection_required_view' "${ui_file}"
  assert_success

  run grep -q 'Connect to the remote host to interact' "${ui_file}"
  assert_success

  run grep -q 'Remote host: {host} -&gt; {host_address}' "${ui_file}"
  assert_success

  run grep -q 'def parse_ssh_config_hostnames' "${ui_file}"
  assert_success

  run grep -q 'def ssh_config_hostname' "${ui_file}"
  assert_success

  run grep -q 'keyword == "hostname"' "${ui_file}"
  assert_success

  run grep -q '<hr />' "${ui_file}"
  assert_success

  run grep -q '.hhs-remote-connect-required h1' "${css_file}"
  assert_success

  run grep -q '.hhs-remote-connect-required hr' "${css_file}"
  assert_success

  run grep -q '.hhs-remote-connect-required h2' "${css_file}"
  assert_success

  run grep -q 'color: #dc2626' "${css_file}"
  assert_success

  run grep -q 'UI_CACHE_FILE = Path(os.environ.get("HHS_DIR", APP_DIR)) / ".streamlit-ui-cache"' "${constants_file}"
  assert_success

  run grep -q 'UI_CACHE_FILE = Path(os.environ.get("HHS_CACHE_DIR"' "${constants_file}"
  assert_failure

  run grep -q '"Connect"' "${ui_file}"
  assert_success

  run grep -q '"Disconnect"' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_connect_button"' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_disconnect_button"' "${ui_file}"
  assert_success

  run grep -q 'class="hhs-vspacer"' "${ui_file}"
  assert_success

  run grep -q 'class="hhs-sidebar-separator"' "${ui_file}"
  assert_success

  run grep -q '.st-key-ssh_connect_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-ssh_disconnect_button button' "${css_file}"
  assert_success

  run grep -q 'background: #16a34a' "${css_file}"
  assert_success

  run grep -q 'background: #dc2626' "${css_file}"
  assert_success

  run grep -q 'color: #ffffff' "${css_file}"
  assert_success

  run grep -q 'min-height: 2.55rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-markdown-table-header: var(--hhs-theme-text-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-markdown-table-value: var(--hhs-theme-primary-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-theme-text-color-accent:' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run grep -q 'color: var(--hhs-markdown-table-header)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-markdown-table-value)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-theme-text-color-accent)' "${css_file}"
  assert_success

  run grep -q -- '--hhs-selected-item-label: var(--hhs-theme-text-color)' "${css_file}"
  assert_success

  run grep -q -- '--hhs-selected-item-value: var(--hhs-success)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-selected-item-label)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-selected-item-value)' "${css_file}"
  assert_success

  run grep -q -- '--hhs-selected-item-label: var(--hhs-theme-text-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-selected-item-value: var(--hhs-success)' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success

  run python3 - <<'PY'
import re
from pathlib import Path

ui_source = Path("bin/apps/py/hhs-ui/streamlit_ui.py").read_text()
base_css = Path("bin/apps/py/hhs-ui/streamlit_ui.css").read_text()
dracula_css = Path("bin/apps/py/hhs-ui/themes/dracula.css").read_text()

assert 'class="hhs-footer-logo"' in ui_source
assert 'class="hhs-footer-logo-link"' in ui_source
assert 'class="hhs-footer-link"' in ui_source
assert 'os.environ.get("HHS_GITHUB_URL", "#")' in ui_source
constants_source = Path("bin/apps/py/hhs-ui/constants.py").read_text()
assert 'FOOTER_OPEN_WORKING_DIR_QUERY_PARAM = "hhs_open_working_dir"' in constants_source
assert 'href="{working_dir_url}" target="_self">Working dir:' in ui_source
assert 'def build_open_directory_command' in ui_source
assert 'def run_open_working_directory' in ui_source
assert 'def handle_footer_actions' in ui_source
assert 'open "$target"' in ui_source
assert 'xdg-open "$target"' in ui_source
assert 'gio open "$target"' in ui_source
assert 'sensible-browser "$target"' in ui_source
assert 'use_cache=False' in ui_source
assert 'load_app_image_data_uri(APP_AI_HOMESETUP_AVATAR_FILE, "image/png")' in ui_source
assert 'class="hhs-footer-glyph"></span>' in ui_source
base_block = re.search(r"\.hhs-footer-glyph\s*\{([^}]*)\}", base_css).group(1)
link_block = re.search(r"\.hhs-footer-link,[^{]+\{([^}]*)\}", base_css).group(1)
logo_link_block = re.search(r"\.hhs-footer-logo-link,[^{]+\{([^}]*)\}", base_css).group(1)
logo_block = re.search(r"\.hhs-footer-logo\s*\{([^}]*)\}", base_css).group(1)
theme_block = re.search(r"\.hhs-footer-glyph\s*\{([^}]*)\}", dracula_css).group(1)
assert "color: inherit" in link_block
assert "text-decoration: none !important" in link_block
assert "filter: brightness(1.2)" in base_css
assert "filter: none" in logo_link_block
assert "height:" in logo_block
assert "width:" in logo_block
assert "border-bottom" not in base_block
assert "border-bottom" not in theme_block
assert "color: var(--hhs-primary)" in theme_block
assert '.stButtonGroup [data-baseweb="button-group"] button[aria-checked="true"]' in dracula_css
assert "border-color: var(--hhs-primary)" in dracula_css
PY
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
    (themes_dir / "dracula.css").write_text("""
:root {
  --hhs-theme-base: dark;
  --hhs-theme-background-color: #282a36;
  --hhs-theme-primary-color: #bd93f9;
  --hhs-theme-text-color: #f8f8f2;
  --hhs-theme-code-background-color: #21222c;
  --hhs-theme-show-widget-border: true;
}
dracula-css
""", encoding="utf-8")
    (themes_dir / "homesetup.css").write_text("""
:root {
  --hhs-theme-base: dark;
  --hhs-theme-background-color: #07111f;
  --hhs-theme-primary-color: #3b82f6;
  --hhs-theme-text-color: #dbeafe;
  --hhs-theme-code-background-color: #0b1628;
  --hhs-theme-show-widget-border: true;
}
homesetup-css
""", encoding="utf-8")
    (themes_dir / "tokyo-night.css").write_text("""
:root {
  --hhs-theme-base: dark;
  --hhs-theme-background-color: #1a1b26;
  --hhs-theme-primary-color: #bb9af7;
  --hhs-theme-text-color: #c0caf5;
  --hhs-theme-code-background-color: #16161e;
  --hhs-theme-show-widget-border: true;
}
tokyo-night-css
""", encoding="utf-8")
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
    assert "tokyo-night-css" in ui.load_app_theme_css()

    config_options.clear()
    ui.configure_app_font_theme(ui.persisted_theme_name())
    assert config_options["theme.backgroundColor"] == "#1a1b26"
    assert config_options["theme.showWidgetBorder"] is True

    theme_options = ui.theme_config_options("tokyo-night")
    assert theme_options["theme.backgroundColor"] == "#1a1b26"
    assert theme_options["theme.primaryColor"] == "#bb9af7"
    assert theme_options["theme.textColor"] == "#c0caf5"

    homesetup_options = ui.theme_config_options("homesetup")
    assert homesetup_options["theme.backgroundColor"] == "#07111f"
    assert homesetup_options["theme.codeBackgroundColor"] == "#0b1628"

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

  run grep -q 'HOME_VIEWS = ("System", "Tools")' "${constants_file}"
  assert_success

  run grep -q '"home_tools_filter"' "${constants_file}"
  assert_success

  run grep -q '"home_tools_other_filter"' "${constants_file}"
  assert_success

  run grep -q 'def filter_tool_rows' "${ui_file}"
  assert_success

  run grep -q 'key="home_tools_filter"' "${ui_file}"
  assert_success

  run grep -q 'LIST_FILTERS' "${ui_file}"
  assert_success

  run grep -q 'key="home_tools_other_filter"' "${ui_file}"
  assert_success

  run grep -q 'HOME_TOOLS_TABLE_KEY = "home_tools_table"' "${constants_file}"
  assert_success

  run grep -q 'HOME_TOOLS_TABLE_RESET_COUNTER_KEY = "home_tools_table_reset_counter"' "${constants_file}"
  assert_success

  run grep -q 'def home_tools_table_key' "${ui_file}"
  assert_success

  run grep -q 'def reset_home_tools_table_selection' "${ui_file}"
  assert_success

  run grep -q 'key=home_tools_table_key()' "${ui_file}"
  assert_success

  run grep -q 'reset_home_tools_table_selection()' "${ui_file}"
  assert_success

  run grep -q 'checkbox=True' "${ui_file}"
  assert_success

  run grep -q 'selected_label=lambda row, _index: f"Selected: {row.get('"'"'Tool'"'"', '"'"''"'"')}"' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_hspm_command' "${ui_file}"
  assert_success

  run grep -q 'def home_tool_is_installed' "${ui_file}"
  assert_success

  run grep -q 'def home_tool_is_not_found' "${ui_file}"
  assert_success

  run grep -q '__hhs hspm execute' "${ui_file}"
  assert_success

  run grep -q '"install", "uninstall", "reinstall"' "${ui_file}"
  assert_success

  run grep -q 'def build_tool_tldr_command' "${ui_file}"
  assert_success

  run grep -q 'tldr {shlex.quote(tool_name.strip())}' "${ui_file}"
  assert_success

  run grep -q 'def apply_selected_tool_action' "${ui_file}"
  assert_success

  run grep -q 'home_tool_action_execute_pending' "${ui_file}"
  assert_success

  run grep -q 'def execute_pending_home_tool_action' "${ui_file}"
  assert_success

  run grep -q 'def render_home_tool_action_dialog' "${ui_file}"
  assert_success

  run grep -q 'def render_terminal_output' "${ui_file}"
  assert_success

  run grep -q 'hhs-home-tool-action-output' "${ui_file}"
  assert_success

  run grep -q '.hhs-home-tool-action-output' "${css_file}"
  assert_success

  run grep -q 'max-height: min(52dvh, 28rem)' "${css_file}"
  assert_success

  run grep -q 'max-width: min(82vw, 58rem)' "${css_file}"
  assert_success

  run grep -q 'def home_tool_action_noun' "${ui_file}"
  assert_success

  run grep -q '"Installation"' "${ui_file}"
  assert_success

  run grep -q 'title = f"{home_tool_action_noun(operation)} of {tool_name} {status}"' "${ui_file}"
  assert_success

  run grep -q 'def apply_selected_tool_tldr' "${ui_file}"
  assert_success

  run grep -q 'def render_home_tool_tldr_dialog' "${ui_file}"
  assert_success

  run grep -q 'label": "Install"' "${ui_file}"
  assert_success

  run grep -q 'label": "Uninstall"' "${ui_file}"
  assert_success

  run grep -q 'label": "Reinstall"' "${ui_file}"
  assert_success

  run grep -q 'label": "TLDR"' "${ui_file}"
  assert_success

  run grep -q 'empty_hint: str = "Select a row to interact"' "${ui_file}"
  assert_success

  run grep -q 'empty_caption: str = "Select a row to interact"' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs-ui/streamlit_ui.py").read_text()
old_labels = (
    "Tools filter",
    "Tools filter text",
    "Environment filter",
    "Environment filter text",
    "PATH filter",
    "PATH filter text",
    "DIR filter",
    "DIR filter text",
    "COMMAND filter",
    "COMMAND filter text",
    "ALIAS filter",
    "ALIAS filter text",
    "SERVICE filter",
    "SERVICE filter text",
    "COMMANDS filter",
    "COMMANDS filter text",
    "DIRECTORIES filter",
    "DIRECTORIES filter text",
    ">Filter</span>",
    'st.text_input("Filter"',
)
missing_defaults = (
    '"Filters"',
    '"Select a row to interact"',
)
violations = [label for label in old_labels if label in source]
violations.extend(default for default in missing_defaults if default not in source)
if violations:
    raise AssertionError("\n".join(violations))
PY
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

  run grep -q 'def parse_ssh_config_hosts' "${ui_file}"
  assert_success

  run grep -q 'def build_ssh_connect_command' "${ui_file}"
  assert_success

  run grep -q 'def build_ssh_disconnect_command' "${ui_file}"
  assert_success

  run grep -q 'UI_SSH_CONNECTION_FILE' "${constants_file}"
  assert_success

  run grep -q 'def restore_registered_ssh_connection_on_session_start' "${ui_file}"
  assert_success

  run grep -q 'restore_registered_ssh_connection_on_session_start()' "${ui_file}"
  assert_success

  run grep -q 'ssh_connection_restore_checked' "${ui_file}"
  assert_success

  run grep -q 'Disconnecting stale SSH host' "${ui_file}"
  assert_failure

  run grep -q 'st.session_state\["ssh_connection_status"\] = "connected"' "${ui_file}"
  assert_success

  run grep -q 'def register_ssh_connection' "${ui_file}"
  assert_success

  run grep -q 'def clear_registered_ssh_connection' "${ui_file}"
  assert_success

  run grep -q 'def request_ssh_host_connect' "${ui_file}"
  assert_success

  run grep -q 'on_change=request_ssh_host_connection' "${ui_file}"
  assert_failure

  run grep -q 'def selected_ssh_host_is_connected' "${ui_file}"
  assert_success

  run grep -q 'def connected_ssh_host' "${ui_file}"
  assert_success

  run grep -q 'def synchronize_selected_ssh_host_with_connection' "${ui_file}"
  assert_success

  run grep -q 'synchronize_selected_ssh_host_with_connection()' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_host_selected"\] = host' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_host_selector"\] = host' "${ui_file}"
  assert_success

  run grep -q 'ssh_connection_host' "${ui_file}"
  assert_success

  run grep -q 'def request_ssh_host_disconnection' "${ui_file}"
  assert_success

  run grep -q 'def execute_pending_ssh_disconnection' "${ui_file}"
  assert_success

  run grep -q -- '-O exit' "${ui_file}"
  assert_success

  run grep -q 'pgrep -f --' "${ui_file}"
  assert_success

  run grep -q 'kill -TERM' "${ui_file}"
  assert_success

  run grep -q 'kill -KILL' "${ui_file}"
  assert_success

  run grep -q 'rm -f {safe_control_path}' "${ui_file}"
  assert_success

  run grep -q 'def ssh_config_option' "${ui_file}"
  assert_success

  run grep -q -- '-F "${HOME}/.ssh/config"' "${ui_file}"
  assert_success

  run grep -q 'ControlMaster=yes' "${ui_file}"
  assert_success

  run grep -q 'ConnectionAttempts=1' "${ui_file}"
  assert_success

  run grep -q 'timeout_seconds=15' "${ui_file}"
  assert_success

  run grep -q 'def build_ssh_wrapped_command' "${ui_file}"
  assert_success

  run grep -q 'bash -ic' "${ui_file}"
  assert_success

  run grep -q 'ssh -tt' "${ui_file}"
  assert_success

  run grep -q 'safe_remote_shell = shlex.quote' "${ui_file}"
  assert_success

  run grep -Fq 'JOB_NAME="${JOB_NAME:-HomeSetup-UI}"' "${ui_file}"
  assert_failure

  run grep -Fq 'source "${HOME}/.bashrc"' "${ui_file}"
  assert_failure

  run grep -Fq '[[ ! -s "${HOME}/.hhsrc" ]]' "${ui_file}"
  assert_failure

  run grep -Fq '"HomeSetup" is not installed on the host.' "${ui_file}"
  assert_failure

  run grep -Fq 'def handle_missing_remote_homesetup' "${ui_file}"
  assert_failure

  run grep -Fq 'result.returncode != 86' "${ui_file}"
  assert_failure

  run grep -q 'def effective_bash_command' "${ui_file}"
  assert_success

  run grep -q 'source "{hhs_home}' "${ui_file}"
  assert_failure

  run grep -q 'export HHS_HOME="{hhs_home}' "${ui_file}"
  assert_failure

  run grep -q '/Users/hjunior/HomeSetup' "${ui_file}"
  assert_failure

  run grep -q 'export HHS_DIR="${HHS_DIR:-${HOME}/.config/hhs}"' "${ui_file}"
  assert_failure

  run grep -q 'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"' "${ui_file}"
  assert_success

  run grep -q 'or not selected_ssh_host_is_connected(host)' "${ui_file}"
  assert_success

  run grep -q 'force_local: bool = False' "${ui_file}"
  assert_success

  run grep -q 'timeout_seconds: int | None = None' "${ui_file}"
  assert_success

  run grep -q 'effective_timeout = 60' "${ui_file}"
  assert_success

  run grep -q 'except subprocess.TimeoutExpired' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'def clear_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'def dismiss_streamlit_dialog' "${ui_file}"
  assert_success

  run grep -Fq 'button[aria-label="Close"]' "${ui_file}"
  assert_success

  run grep -q 'close_button.click()' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'render_dialog()' "${ui_file}"
  assert_success

  run grep -q 'if render_ssh_connection_dialog()' "${ui_file}"
  assert_success

  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs-ui/streamlit_ui.py").read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "render_ssh_connection_dialog":
        assert "st.stop()" not in ast.unparse(node)
        break
else:
    raise AssertionError("render_ssh_connection_dialog not found")
PY
  assert_success

  run grep -q 'return True' "${ui_file}"
  assert_success

  run grep -q 'dismiss_streamlit_dialog()' "${ui_file}"
  assert_success

  run grep -q 'set_overlay(False)' "${ui_file}"
  assert_success

  run grep -q 'Successfully connected to {host}' "${ui_file}"
  assert_success

  run grep -q 'Failed to connect to {host}' "${ui_file}"
  assert_success

  run grep -q 'st.error(st.session_state.get("ssh_connection_error", "SSH failed."))' "${ui_file}"
  assert_failure
}

# TC - 11
@test "when showing command progress then command runner should paint overlay before subprocess" {
  run grep -q 'def set_overlay(' "${ui_file}"
  assert_success

  run grep -q 'def close_all_dialogs()' "${ui_file}"
  assert_success

  run grep -q 'close_all_dialogs()' "${ui_file}"
  assert_success

  run grep -q 'set_overlay(True, loader_message, close_dialogs=close_dialogs)' "${ui_file}"
  assert_success

  run grep -q 'with placeholder.container()' "${ui_file}"
  assert_success

  run grep -q 'time.sleep(0.1)' "${ui_file}"
  assert_success

  run grep -q 'components.html(' "${ui_file}"
  assert_success

  run grep -q 'window.setInterval(render_elapsed, 1000)' "${ui_file}"
  assert_success

  run grep -q 'set_overlay(False)' "${ui_file}"
  assert_success

  run grep -q 'hhs-tab-loader' "${css_file}"
  assert_success

  run grep -q 'background: var(--hhs-background)' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
  assert_success
}

# TC - 12
@test "when confirming actions then reusable pop_dialog component should be used" {
  run grep -q 'def pop_dialog(' "${ui_file}"
  assert_success

  run grep -q 'def queue_dialog_callback' "${ui_file}"
  assert_success

  run grep -q 'def execute_pending_dialog_callback' "${ui_file}"
  assert_success

  run grep -q 'def handle_dialog_button_click' "${ui_file}"
  assert_success

  run grep -q 'def handle_dialog_dismiss' "${ui_file}"
  assert_success

  run grep -q 'execute_pending_dialog_callback()' "${ui_file}"
  assert_success

  run grep -q '@st.dialog(title, dismissible=dismissible, on_dismiss=on_dismiss)' "${ui_file}"
  assert_success

  run grep -q 'handle_dialog_button_click(' "${ui_file}"
  assert_success

  run grep -q 'queue_dialog_callback(callback)' "${ui_file}"
  assert_success

  run grep -q '_hhs_dialog_button_dismissal' "${ui_file}"
  assert_success

  run grep -q 'handle_dialog_dismiss(dismiss_callback)' "${ui_file}"
  assert_success

  run grep -q 'dismiss_streamlit_dialog()' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_home_tool_action_dialog' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_home_tool_tldr_dialog' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'st.rerun(scope="app")' "${ui_file}"
  assert_failure

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs-ui/streamlit_ui.py").read_text()
assert ui_source.count("@st.dialog(") == 1
PY
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

  run grep -q 'def hhs_ask_timeout_seconds' "${ui_file}"
  assert_success

  run grep -q 'return 180 if connected_ssh_host() else 90' "${ui_file}"
  assert_success

  run grep -q 'timeout_seconds=hhs_ask_timeout_seconds()' "${ui_file}"
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

  run grep -q -- '--hhs-model-accent: #4da3ff' "${HHS_REPO_DIR}/bin/apps/py/hhs-ui/themes/dracula.css"
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

@test "when listing saved dirs then hhs load dir should not fall through to alias loading" {
  run bash --noprofile --norc -c '
    export HHS_DIR="${1}/hhs"
    export HHS_SAVED_DIRS_FILE="${HHS_DIR}/.saved_dirs"
    export HHS_HIGHLIGHT_COLOR=""
    export WHITE=""
    export GREEN=""
    export YELLOW=""
    export NC=""
    mkdir -p "${HHS_DIR}" "${1}/project"
    printf "PROJECT=%s/project\n" "${1}" > "${HHS_SAVED_DIRS_FILE}"
    function __hhs_errcho() {
      printf "%s\n" "$*" >&2
    }
    source "${2}/bin/hhs-functions/bash/hhs-dirs.bash"
    __hhs_load_dir -l
  ' -- "${BATS_TEST_TMPDIR}" "${HHS_REPO_DIR}"
  assert_success
  assert_output --partial 'PROJECT'
  refute_output --partial 'Alias "" not found'
}

@test "when listing directory history with no recorded dirs then hhs dirs should print an explicit message" {
  run bash --noprofile --norc -c '
    export HHS_DIR="${1}/hhs"
    export HHS_DIRS_FILE="${HHS_DIR}/.dirs"
    mkdir -p "${HHS_DIR}"
    : > "${HHS_DIRS_FILE}"
    function dirs() {
      return 0
    }
    source "${2}/bin/hhs-functions/bash/hhs-dirs.bash"
    __hhs_dirs -l
  ' -- "${BATS_TEST_TMPDIR}" "${HHS_REPO_DIR}"
  assert_success
  assert_output --partial 'No directories recorded yet'
}

@test "when rendering directory history then Streamlit should handle successful empty output" {
  run grep -q 'message = strip_ansi(result.stdout).strip() or "No directories recorded yet"' "${ui_file}"
  assert_success

  run grep -q 'st.info(message)' "${ui_file}"
  assert_success
}

@test "when parsing saved dirs then escaped ANSI sequences should be stripped" {
  run python3 - <<'PY'
import re

ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
)
ESCAPED_ANSI_ESCAPE_PATTERN = re.compile(
    r"(?:\\033|\\x1b|\\e)(?:\[[0-?]*[ -/]*[@-~]|\][^\\]*(?:\\a|\\033\\|\\x1b\\)|[()][A-Za-z0-9])"
)
DIR_LINE_PATTERN = re.compile(r"^(.+?)\.{2,}\s+(?:|=>)\s+'?(.*?)'?$")

def strip_ansi(value):
    return ESCAPED_ANSI_ESCAPE_PATTERN.sub("", ANSI_ESCAPE_PATTERN.sub("", value))

def parse_hhs_dirs(output):
    rows = []
    for line in strip_ansi(output).splitlines():
        match = DIR_LINE_PATTERN.match(line.strip())
        if match:
            rows.append({"Name": match.group(1).strip(), "Value": match.group(2).strip()})
    return rows

rows = parse_hhs_dirs(r"\033[0;36mAKS\033[0;97m......................................  '/tmp/aks'")
assert rows == [{"Name": "AKS", "Value": "/tmp/aks"}], rows
PY
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
