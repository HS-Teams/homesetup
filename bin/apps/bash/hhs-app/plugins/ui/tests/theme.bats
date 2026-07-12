#!/usr/bin/env bats

#  Script: theme.bats
# Purpose: HomeSetup Streamlit UI theme styling tests.
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

@test "when styling HomeSetup UI then Dracula theme and Nerd Font should be configured" {
  run test -s "${css_file}"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/static/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
  assert_success

  assert_file_contains_many "${constants_file}" \
'APP_STATIC_DIR = APP_DIR / "static"' \
'APP_CSS_FILE = APP_STATIC_DIR / "css/streamlit_ui.css"' \
    'APP_FONT_FAMILY = "Droid Sans Mono for Powerline Nerd Font Complete"'
  assert_file_contains_many "${theme_assets_file}" \
'def static_asset_url' 'def app_font_url' '/app/static/' \
    '<link rel="stylesheet" href="{app_css_url}">' \
    '<link rel="stylesheet" href="{theme_css_url}">'
  assert_file_not_contains "${theme_assets_file}" 'def load_app_font_data_uri'
  run grep -q -- '--hhs-ui-font-family: "Droid Sans Mono for Powerline Nerd Font Complete", monospace' "${css_file}"
  assert_success

  assert_file_contains "${css_file}" 'overflow-x: hidden'

  run grep -q -- '--hhs-theme-background-color: #282a36' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/static/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-background: var(--hhs-theme-background-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/static/themes/dracula.css"
  assert_success

  assert_file_contains_many "${theme_assets_file}" \
'def css_custom_properties' 'def theme_config_options'
  assert_file_contains_many "${ui_file}" \
'class="hhs-sidebar-title"' 'def render_sidebar_title' \
    'render_sidebar_title()' 'class="hhs-sidebar-title-logo"' \
    'hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE, "image/png"' 'class="hhs-sidebar-clock-glyph"></span>'
  assert_file_contains_many "${css_file}" \
'.hhs-sidebar-clock-glyph' 'flex: 0 0 24px' 'justify-content: center' 'width: 24px' 'margin-right: 0.45rem' \
    'color: var(--hhs-theme-text-color)'
  run grep -q -- '--hhs-theme-text-muted-color: var(--hhs-comment, var(--hhs-theme-text-color))' "${css_file}"
  assert_success

  run grep -q -- '--hhs-theme-input-placeholder-color: #686e7a' "${css_file}"
  assert_success

  assert_file_contains_many "${css_file}" \
'position: fixed' 'top: 58px'
  run grep -q -- '--hhs-sidebar-inline-inset: 20px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-sidebar-title-separator-left: 0px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-sidebar-title-separator-width: 100%' "${css_file}"
  assert_success

  assert_file_contains_many "${css_file}" \
'padding: 0 2rem 0 var(--hhs-sidebar-inline-inset)' '.hhs-sidebar-title::after'
  assert_file_contains "${ui_file}" 'def render_sidebar_title_separator_alignment_script'

  assert_file_contains_many "${css_file}" \
'.hhs-sidebar-title-logo' 'height: 24px' 'width: 24px' 'margin-right: 0.45rem'
  assert_file_contains_many "${ui_file}" \
'host_kind = "Local" if selected_host_is_local() else "SSH"' 'Host ({host_kind})' \
    'key="ssh_host_selector"' 'on_change=select_ssh_host_from_widget'
  assert_file_contains "${ssh_runtime_file}" 'def select_ssh_host_from_widget'
  assert_file_not_contains "${ui_file}" 'key="ssh_host_selected"'

  assert_file_contains_many "${ui_file}" \
'ssh_host_connected_display_' 'disabled=True'
  assert_file_not_contains "${ui_file}" 'options = ["", local_hostname()]'

  assert_file_contains_many "${ssh_runtime_file}" \
'options = [local_hostname()]' 'if not selected_host:' 'state_hosts = (' 'registered_ssh_connection_host()'
  assert_file_contains_many "${ui_file}" \
    'def selected_remote_host_requires_connection' 'def render_remote_connection_required_view' \
    'Connect to the remote host to interact' 'Remote host: {host} -&gt; {host_address}' \
    '<hr />'
  assert_file_contains_many "${ssh_core_file}" \
'def parse_ssh_config_hostnames' 'def ssh_config_hostname' 'keyword == "hostname"'
  assert_file_contains_many "${css_file}" \
'.hhs-remote-connect-required h1' '.hhs-remote-connect-required hr' '.hhs-remote-connect-required h2' \
    'color: #dc2626'
}

@test "when styling HomeSetup UI then SSH host options and cache constants should be configured" {
  assert_file_contains_many "${constants_file}" \
'HHS_DIR = Path(os.environ.get("HHS_DIR", str(APP_DIR)))' \
    'HHS_CACHE_DIR = Path(os.environ.get("HHS_CACHE_DIR", str(HHS_DIR / "cache")))' \
    'UI_STATE_FILE = HHS_CACHE_DIR / "streamlit-ui-state.json"' \
    'UI_CACHE_FILE = HHS_CACHE_DIR / "streamlit-ui-cache.json"' \
    'UI_CACHE_SSH_CONNECTION_KEY = "ui:ssh_connection"'
  assert_file_not_contains "${constants_file}" 'UI_SSH_CONNECTION_FILE'

  assert_file_contains_many "${constants_file}" \
'UI_CACHE_REALTIME_TTL_SECONDS = 30' 'UI_CACHE_NORMAL_TTL_SECONDS = 300' \
    'UI_CACHE_LOW_CHANGE_TTL_SECONDS = 900'
  assert_file_not_contains "${constants_file}" 'FLOATING_STATUS_DISMISS_DELAY_EXTENSION_SECONDS'

  assert_file_contains_many "${constants_file}" \
'FLOATING_STATUS_AUTO_DISPOSE_EXTENSION_SECONDS = 1.0' 'UI_COMMAND_LOCAL_TIMEOUT_SECONDS = 30' \
    'UI_COMMAND_REMOTE_TIMEOUT_SECONDS = 60' \
    'UI_COMMAND_DEFAULT_TIMEOUT_SECONDS = UI_COMMAND_LOCAL_TIMEOUT_SECONDS' \
    'UI_COMMAND_SEARCH_TIMEOUT_SECONDS = 300'
  assert_file_not_contains_many "${constants_file}" \
'FOOTER_DISMISS_STATUS_QUERY_PARAM' '"search_query"'
  assert_file_contains_many "${constants_file}" \
'"search_directories"' 'SEARCH_TERM_HISTORY_CACHE_KEY = "search_terms:history"' '"search_ignore_case"' \
    '"search_words"' '"search_binary"'
  assert_file_not_contains "${constants_file}" '"_hhs_search_home_context"'

  assert_file_contains_many "${constants_file}" \
'"search_replace"' '"search_replacement"'
  assert_file_not_contains_many "${constants_file}" \
'"search_result_query"' '"search_result_path"' '"search_result_type"'
  assert_file_contains_many "${ui_file}" \
'"ﮣ Connect"' '"ﮤ Disconnect"' 'key="ssh_connect_button"' 'key="ssh_disconnect_button"'
  assert_file_not_contains "${ui_file}" 'class="hhs-vspacer"'

  assert_file_contains "${ui_file}" 'class="hhs-sidebar-separator"'

  assert_file_contains_many "${css_file}" \
'.st-key-ssh_connect_button button' '.st-key-ssh_disconnect_button button' 'background: #16a34a' \
    'background: #dc2626' 'color: #ffffff' 'min-height: 2.55rem'
  run grep -q -- '--hhs-markdown-table-header: var(--hhs-theme-text-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/static/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-markdown-table-value: var(--hhs-theme-primary-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/static/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-theme-text-color-accent:' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/static/themes/dracula.css"
  assert_success

  assert_file_contains_many "${css_file}" \
'color: var(--hhs-markdown-table-header)' 'color: var(--hhs-markdown-table-value)' \
    'color: var(--hhs-theme-text-color-accent)'
  run grep -q -- '--hhs-selected-item-label: var(--hhs-theme-text-color)' "${css_file}"
  assert_success

  run grep -q -- '--hhs-selected-item-value: var(--hhs-success)' "${css_file}"
  assert_success

  assert_file_contains_many "${css_file}" \
'color: var(--hhs-selected-item-label)' 'color: var(--hhs-selected-item-value)'

}

@test "when selecting a UI theme then the selected theme should persist and restore" {
  run python3 - <<'PY'
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

app_dir = Path("bin/apps/py/hhs_ui").resolve()
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
import hhs_ui.core.theme_assets as theme_assets

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
    ui.hhs_ui.APP_THEME_CSS_FILE = themes_dir / "dracula.css"
    ui.hhs_ui.UI_STATE_FILE = tmp_path / "hhs-dir" / "streamlit-ui-state.json"
    ui.hhs_ui_constants.APP_THEME_CSS_FILE = themes_dir / "dracula.css"
    ui.hhs_ui_constants.UI_STATE_FILE = tmp_path / "hhs-dir" / "streamlit-ui-state.json"

    ui.persist_theme_selection("tokyo-night")
    assert json.loads(ui.hhs_ui.UI_STATE_FILE.read_text(encoding="utf-8"))["theme_selected"] == "tokyo-night"

    streamlit.session_state.clear()
    streamlit.session_state["active_view"] = "Home"
    streamlit.session_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = True
    streamlit.session_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] = "TERMINAL"
    streamlit.session_state[ui.hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] = "Home"
    streamlit.session_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] = "homeserver"
    streamlit.session_state["search_directories"] = ["/tmp", "/var"]
    streamlit.session_state["search_query"] = "admin"
    streamlit.session_state["search_result_query"] = "admin"
    streamlit.session_state["search_result_path"] = "/tmp"
    streamlit.session_state["search_result_type"] = "Strings"
    streamlit.session_state["path_value_overrides"] = {"/bin": "/tmp/bin"}
    ui.save_ui_state()
    saved_state = json.loads(ui.hhs_ui.UI_STATE_FILE.read_text(encoding="utf-8"))
    assert saved_state["theme_selected"] == "tokyo-night"
    assert saved_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] is True
    assert saved_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] == "TERMINAL"
    assert saved_state[ui.hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] == "Home"
    assert saved_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] == "homeserver"
    assert saved_state["search_directories"] == ["/tmp", "/var"]
    assert "search_query" not in saved_state
    assert "search_result_query" not in saved_state
    assert "search_result_path" not in saved_state
    assert "search_result_type" not in saved_state
    assert "path_value_overrides" not in saved_state

    streamlit.session_state.clear()
    ui.restore_ui_state()
    assert streamlit.session_state["theme_selected"] == "tokyo-night"
    assert streamlit.session_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] is True
    assert streamlit.session_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] == "TERMINAL"
    assert streamlit.session_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] == "homeserver"
    assert streamlit.session_state["search_directories"] == ["/tmp", "/var"]
    assert "search_query" not in streamlit.session_state
    assert "search_result_query" not in streamlit.session_state
    assert "path_value_overrides" not in streamlit.session_state
    assert "tokyo-night-css" in theme_assets.load_app_theme_css()

    config_options.clear()
    ui.configure_app_font_theme(ui.persisted_theme_name())
    assert config_options["theme.backgroundColor"] == "#1a1b26"
    assert config_options["theme.showWidgetBorder"] is True

    theme_options = theme_assets.theme_config_options("tokyo-night")
    assert theme_options["theme.backgroundColor"] == "#1a1b26"
    assert theme_options["theme.primaryColor"] == "#bb9af7"
    assert theme_options["theme.textColor"] == "#c0caf5"

    homesetup_options = theme_assets.theme_config_options("homesetup")
    assert homesetup_options["theme.backgroundColor"] == "#07111f"
    assert homesetup_options["theme.codeBackgroundColor"] == "#0b1628"

    app_state_file = tmp_path / "streamlit-ui-state.json"
    app_state_file.write_text('{"theme_selected": "dracula"}', encoding="utf-8")
    streamlit.session_state.clear()
    ui.restore_ui_state()
    assert streamlit.session_state["theme_selected"] == "tokyo-night"
PY
  assert_success
}

# TC - 9
