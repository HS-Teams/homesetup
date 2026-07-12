#!/usr/bin/env bats

#  Script: hhs.bats
# Purpose: HomeSetup Streamlit UI footer and settings tests.
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

@test "when footer statuses are queued then display timing should start on render" {
  run python3 - "${status_ui_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

class Clock:
    def __init__(self):
        self.now = 100.0

    def time(self):
        return self.now

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def push_floating_status(")
end = source.index("def floating_status_glyph(")
clock = Clock()
session_state = {}
namespace = {
    "hhs_ui_constants": SimpleNamespace(
        FLOATING_STATUS_QUEUE_KEY="_hhs_floating_status_queue",
        FLOATING_STATUS_LEGACY_KEY="_hhs_floating_status",
        FLOATING_STATUS_QUEUE_LIMIT=20,
        FLOATING_STATUS_AUTO_DISPOSE_EXTENSION_SECONDS=1.0,
    ),
    "clean_command_status_message": lambda value: str(value).strip(),
    "st": SimpleNamespace(session_state=session_state),
    "time": clock,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)
namespace["log_footer_status_message"] = lambda _message, _kind: None

namespace["push_floating_status"]("First", "success", 5.0)
clock.now = 150.0
namespace["push_floating_status"]("Second", "warning", 5.0)
queue = session_state["_hhs_floating_status_queue"]
assert [item["message"] for item in queue] == ["First", "Second"]
assert "displayed_at" not in queue[0]

status = namespace["current_floating_status"]()
assert status["message"] == "First"
assert status["kind"] == "info"
assert status["displayed_at"] == 150.0
assert namespace["effective_floating_status_timeout"](status) == 6.0

clock.now = 155.5
assert namespace["current_floating_status"]()["message"] == "First"
clock.now = 157.5
assert namespace["current_floating_status"]()["message"] == "Second"
assert session_state["_hhs_floating_status_queue"][0]["displayed_at"] == 157.5
assert namespace["pop_floating_status"]()["message"] == "Second"
assert namespace["pop_floating_status"]() is None
PY
  assert_success
}

@test "when footer statuses are logged then their kind selects the log level" {
  run python3 - "${status_ui_file}" <<'PY'
import logging
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
assert "%(asctime)s.%(msecs)03d %(levelname)s %(message)s" in source
start = source.index("def log_footer_status_message(")
end = source.index("def footer_status_file_logger(", start)
namespace = {"logging": logging}
exec("from __future__ import annotations\n" + source[start:end], namespace)

class Logger:
    def __init__(self):
        self.records = []

    def log(self, level, message):
        self.records.append((level, message))

logger = Logger()
namespace["footer_status_file_logger"] = lambda: logger
namespace["log_footer_status_message"]("Synced packages.", "info")
namespace["log_footer_status_message"]("Remote connection failed.", "error")
namespace["log_footer_status_message"]("Retrying connection.", "warn")

assert logger.records == [
    (logging.INFO, "Synced packages."),
    (logging.ERROR, "Remote connection failed."),
    (logging.WARNING, "Retrying connection."),
]
PY
  assert_success
}

@test "when choosing footer cleanup options then button controls must avoid checkbox inputs" {
  run python3 - "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/widgets/footer_ui.py" \
    "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/static/css/streamlit_ui.css" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
css = Path(sys.argv[2]).read_text(encoding="utf-8")
menu_markup = source.split(
    "def footer_cache_clear_menu_markup", 1
)[1].split("\ndef ", 1)[0]
menu_script = source.split(
    "def render_footer_cache_clear_menu_script", 1
)[1].split("\ndef ", 1)[0]

assert '<input type="checkbox"' not in source
assert "st.checkbox(" not in source
assert 'role="checkbox" aria-checked="false"' in menu_markup
assert 'class="hhs-footer-cache-clear-option"' in menu_markup
assert 'class="hhs-footer-cache-clear-submit"' in menu_markup
assert 'option.setAttribute("aria-checked"' in menu_script
assert '[role="checkbox"][aria-checked="true"]' in menu_script
assert "window.parent.location.search = params.toString()" in menu_script
assert "components.declare_component" not in source
assert '.hhs-footer-cache-clear-option[aria-checked="true"]' in css
assert ".hhs-footer-cache-clear-panel" in css
assert ".st-key-footer_cache_clear_menu" not in css
assert '.hhs-footer-cache-clear-panel input[type="checkbox"]' not in css
PY
  assert_success
}

@test "when rendering HHS Settings then table height should fit real rows" {
  run python3 - "${table_ui_file}" "${css_file}" <<'PY'
import csv
import re
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
css = Path(sys.argv[2]).read_text(encoding="utf-8")
render_body = source.split("def render_markdown_table", 1)[1].split("\ndef ", 1)[0]
assert "min_row_count: int = 0" in render_body
assert "multi_selection: bool = True" in render_body
assert "column_text_colors: dict[str, str] | None = None" in render_body
assert "show_value_column: bool = True" in render_body
assert "if multi_selection and not show_value_column:" in render_body
assert "height=markdown_table_editor_height(max(len(items), min_row_count))" in render_body
assert "return hhs_ui_constants.MARKDOWN_TABLE_HEIGHT" in source
assert "if multi_selection:" in render_body
assert "st.data_editor(" in render_body
assert "st.dataframe(" in render_body
assert '"show_value_column": show_value_column' in render_body
assert "selection_column_order = [" in render_body
assert "selection_column_order.insert(0, value_column_label)" in render_body
assert 'selection_args["on_select"] = "rerun"' in render_body
assert 'selection_args["selection_mode"] = "single-row"' in render_body
assert "markdown_table_single_selected_index(" in render_body
assert "markdown_table_single_selection_marks(" in render_body
assert "normalize_markdown_table_selection" not in render_body
assert "def themed_markdown_table_data(" in source
assert "def markdown_table_single_selection_marks(" in source
assert '"◉"' in source
assert '"○"' in source
assert "resolve_css_value(" in source
assert "styler.map(" in source
assert "40 + (len(items) + 1) * 44" not in render_body
assert "--hhs-markdown-table-height: 360px" in css
assert "--hhs-markdown-table-max-height: var(--hhs-markdown-table-height)" in css
assert "height: var(--hhs-markdown-table-height) !important" in css
assert "max-height: var(--hhs-markdown-table-max-height) !important" in css
assert "min-height: var(--hhs-markdown-table-height) !important" in css
assert ".hhs-markdown-table-single-selection" in css
assert "border-radius: 50% !important" in css
assert "radial-gradient(" in css
assert "overflow-y: auto" in css

height_start = source.index("def markdown_table_editor_height(")
height_end = source.index("def render_hhs_setup_settings_table", height_start)
height_namespace = {"hhs_ui_constants": SimpleNamespace(MARKDOWN_TABLE_HEIGHT=360)}
exec("from __future__ import annotations\n" + source[height_start:height_end], height_namespace)
assert height_namespace["markdown_table_editor_height"](0) == 360
assert height_namespace["markdown_table_editor_height"](4) == 360
assert height_namespace["markdown_table_editor_height"](12) == 360

single_selection_start = source.index("def markdown_table_single_selected_index(")
single_selection_end = source.index("def render_markdown_table", single_selection_start)
single_selection_namespace = {"table_selection_rows": lambda selection: tuple(selection or ())}
exec(
    "from __future__ import annotations\n"
    + source[single_selection_start:single_selection_end],
    single_selection_namespace,
)
assert single_selection_namespace["markdown_table_single_selected_index"]([2], 3) == 2
assert single_selection_namespace["markdown_table_single_selected_index"]([3], 3) is None
assert single_selection_namespace["markdown_table_single_selection_marks"](3, 1) == [
    "○",
    "◉",
    "○",
]

command_source = Path("bin/apps/py/hhs_ui/execution/command_catalog.py").read_text(encoding="utf-8")
parse_start = command_source.index("def hhs_setting_variable_name(")
parse_end = command_source.index("def parse_hhs_starship_info", parse_start)
parse_namespace = {
    "csv": csv,
    "re": re,
    "strip_ansi": lambda value: value,
}
exec(
    "from __future__ import annotations\n" + command_source[parse_start:parse_end],
    parse_namespace,
)

output = """
| NAME                     | PREFIX | VALUE                                 | SETTINGS TYPE | MODIFIED            |
| hhs.clitt.max.rows       |        | 15                                    | environment   | 2026-07-09 02:07:07 |
| hhs.firebase.config.file |        | $HHS_DIR/firebase.properties          | environment   | 2026-07-09 03:01:16 |
| hhs.punch.file           |        | $HOME/Dropbox/Documents/Punches/my.punch | environment | 2026-07-09 03:01:57 |
| hhs.vault.file           |        | $HOME/Dropbox/Documents/.vault        | environment   | 2026-07-09 03:02:55 |
"""
rows = parse_namespace["parse_hhs_settings_list"](output)
assert [row["Setting"] for row in rows] == [
    "hhs.clitt.max.rows",
    "hhs.firebase.config.file",
    "hhs.punch.file",
    "hhs.vault.file",
]
assert all(row["Setting"] and row["Variable"] for row in rows)
PY
  assert_success
}

@test "when Setman is unavailable then Settings list uses the SQLite database directly" {
  run python3 - "${command_catalog_file}" <<'PY'
import csv
import io
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def hhs_settings_sqlite_export_script(")
end = source.index("def build_hhs_settings_list_command(", start)
namespace = {"textwrap": textwrap}
exec("from __future__ import annotations\n" + source[start:end], namespace)
export_script = namespace["hhs_settings_sqlite_export_script"]()

with tempfile.TemporaryDirectory() as temp_dir:
    database = Path(temp_dir) / "setman.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE SETTINGS ("
            "uuid TEXT, name TEXT, prefix TEXT, value TEXT, stype TEXT, modified TEXT)"
        )
        connection.execute(
            "INSERT INTO SETTINGS VALUES (?, ?, ?, ?, ?, ?)",
            ("2", "z.setting", "", "z", "environment", "2026-07-11"),
        )
        connection.execute(
            "INSERT INTO SETTINGS VALUES (?, ?, ?, ?, ?, ?)",
            ("1", "A.setting", "", "a", "environment", "2026-07-10"),
        )

    result = subprocess.run(
        [sys.executable, "-c", export_script, str(database)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    assert [row["name"] for row in rows] == ["A.setting", "z.setting"]

    missing = subprocess.run(
        [sys.executable, "-c", export_script, str(Path(temp_dir) / "missing.db")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert missing.returncode == 0
    assert missing.stdout.strip() == "uuid,name,prefix,value,settings type,modified"

builder_body = source.split("def build_hhs_settings_list_command", 1)[1].split(
    "\ndef ", 1
)[0]
assert "python3 -m setman export" not in builder_body
assert "hhs_settings_sqlite_export_script()" in builder_body
PY
  assert_success
}

@test "when rendering HHS Firebase then configurations form should load file values" {
  run python3 - "${ui_file}" "${css_file}" "${table_ui_file}" "${cache_runtime_file}" <<'PY'
import json
import os
import posixpath
import re
import shlex
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
css = Path(sys.argv[2]).read_text(encoding="utf-8")
table_source = Path(sys.argv[3]).read_text(encoding="utf-8")
cache_runtime_source = Path(sys.argv[4]).read_text(encoding="utf-8")
component_html = (
    Path(sys.argv[1])
    .parent.joinpath("components", "firebase_config_form", "index.html")
    .read_text(encoding="utf-8")
)
assert 'elif hhs_view == "Firebase":' in source
assert "render_hhs_firebase_panel()" in source
assert 'HHS_FIREBASE_CONFIG_FILE:-${HHS_DIR}/firebase.properties' in source
assert 'with st.expander("Configurations", expanded=True):' in source
assert "FIREBASE_CONFIG_COMPONENT_DIR" in Path(sys.argv[1]).with_name("constants.py").read_text(encoding="utf-8")
assert ".st-key-hhs_firebase_configurations" in css
assert "gap: var(--hhs-element-std-gap) !important" in css
assert "HHS_FIREBASE_CONFIG_FILE\\\\t%s" in source
assert "STARSHIP_CONFIG\\\\t%s" in source
assert "def render_openable_config_path(" in source
assert "search_open_href(file_uri)" in source
assert "hhs-view-subtitle-link" in source
assert "data-hhs-open-path" in source
assert "--hhs-theme-file-link-color: var(--hhs-theme-link-color, var(--hhs-theme-text-color))" in css
assert ".hhs-view-subtitle-link:link" in css
assert ".hhs-view-subtitle-link:visited" in css
assert "color: var(--hhs-theme-file-link-color) !important" in css
assert "def hhs_setup_config_file_info()" not in source
assert "def display_hhs_config_path(" not in source
assert "def hhs_config_path_root_values(" not in source
assert "def firebase_config_component()" in source
assert '"hhs_firebase_config_form"' in source
assert "components.declare_component(" in source
assert "path=str(hhs_ui.FIREBASE_CONFIG_COMPONENT_DIR)" in source
assert "def handle_hhs_firebase_config_component_event" in source
assert "apply_hhs_firebase_component_values(event.get(\"values\", {}))" in source
assert "restore_hhs_firebase_original_values()" in source

firebase_panel_body = source.split("def render_hhs_firebase_panel", 1)[1].split("\ndef ", 1)[0]
assert "render_hhs_firebase_title()" in firebase_panel_body
assert firebase_panel_body.index("execute_pending_hhs_firebase_action()") < firebase_panel_body.index(
    "render_hhs_firebase_title()"
)
assert firebase_panel_body.index("render_hhs_firebase_title()") < firebase_panel_body.index(
    "render_cached_command_result("
)

render_body = source.split("def render_hhs_firebase_configurations", 1)[1].split("\ndef ", 1)[0]
assert 'st.text_input(' not in render_body
assert "render_hhs_firebase_config_component(action_running)" in render_body
assert "handle_hhs_firebase_config_component_event(event)" in render_body
assert "fields=hhs_firebase_component_fields()" in source
assert '"placeholder": placeholder' in source
assert "max_chars" not in render_body
assert "selected_alias = render_hhs_firebase_aliases_table(action_running)" in render_body
assert "render_hhs_firebase_aliases_actions(selected_alias, action_running)" in render_body
assert "Press enter to apply" not in component_html
assert "Press Enter to apply" not in component_html
assert 'event.key === "Enter"' in component_html
assert "event.preventDefault()" in component_html
assert "Streamlit.setComponentValue" in component_html
assert "background: var(--hhs-bg)" in component_html
assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in component_html
assert "padding-left: 1rem" not in component_html
assert "grid-template-columns: var(--hhs-label-width, max-content) minmax(0, 1fr)" in component_html
assert ".field:nth-child(odd)" in component_html
assert "--hhs-label-width: 6ch" in component_html
assert ".field:nth-child(even)" in component_html
assert "--hhs-label-width: 5.7rem" in component_html
assert "text-align: right" in component_html
assert "function displayLabel(value)" in component_html
assert 'PROJECT_ID: "Project ID"' in component_html
assert 'label.textContent = `${labelText}:`' in component_html
assert "hhs-theme-input-placeholder-color" in source
assert 'properties, "hhs-theme-input-placeholder-color", "#686e7a"' in source
assert "input::placeholder" in component_html
assert "function hasRestorableChanges()" in component_html
assert "function updateRestoreButtonState()" in component_html
assert "restoreButton.disabled = Boolean(args.disabled) || !hasRestorableChanges()" in component_html
assert "updateRestoreButtonState()" in component_html
assert 'button.type = "button"' in component_html
assert "button.dataset.action = action" in component_html
assert 'createButton(" Save", "save", "Save")' in component_html
assert 'createButton("ﭯ Restore", "restore", "Restore original file values")' in component_html
assert 'if (action === "restore")' in component_html
assert "values = fieldValues(args.fields)" in component_html
assert "render()" in component_html
assert "--hhs-button-width: 140px" in component_html
assert '"buttonWidth": resolve_css_custom_property(' in source
assert "window.sessionStorage" in component_html

setup_body = source.split("def render_hhs_setup_panel", 1)[1].split("\ndef ", 1)[0]
assert "setup_display_path = display_path_value" not in setup_body
assert "render_openable_config_path(" not in setup_body
assert "render_hhs_setup_settings_table(action_running)" in setup_body

starship_controls_body = source.split("def render_hhs_starship_controls", 1)[1].split("\ndef ", 1)[0]
assert "display_path_value(" not in starship_controls_body
assert 'with st.container(key="hhs_starship_controls"):' in starship_controls_body
assert 'with st.expander("Configurations", expanded=True):' in starship_controls_body
expander_index = starship_controls_body.index(
    'with st.expander("Configurations", expanded=True):'
)
columns_index = starship_controls_body.index(
    "cache_col, config_col, preset_col, apply_col, edit_col = st.columns("
)
assert expander_index < columns_index
assert "value=config_path" in starship_controls_body
assert ".st-key-hhs_starship_controls [data-testid=\"stExpanderDetails\"] > [data-testid=\"stVerticalBlock\"]" in css

starship_editor_body = source.split("def render_hhs_starship_config_editor", 1)[1].split("\ndef ", 1)[0]
assert "config_display_path = display_path_value(" not in starship_editor_body
assert "render_openable_config_path(" not in starship_editor_body
assert 'label_visibility="collapsed"' in starship_editor_body
assert 'render_view_subtitle(f"<code>{html.escape(config_display_path)}</code>", True)' not in starship_editor_body

firebase_panel_body = source.split("def render_hhs_firebase_panel", 1)[1].split("\ndef ", 1)[0]
assert "config_display_path = display_path_value(" not in firebase_panel_body
assert "render_openable_config_path(" not in firebase_panel_body
assert 'render_view_subtitle(f"<code>{html.escape(config_display_path)}</code>", True)' not in firebase_panel_body

aliases_table_body = source.split("def render_hhs_firebase_aliases_table", 1)[1].split("\ndef ", 1)[0]
assert "fetch_firebase_aliases()" in source
assert "def fetch_firebase_aliases_with_preloader(" in source
assert "@lru_cache(maxsize=1)" in source
assert "def fetch_firebase_aliases_cached(" in source
assert "def clear_firebase_aliases_cache(" in source
assert "def firebase_aliases_cache_is_warm(" in source
assert "fetch_firebase_aliases_cached.cache_clear()" in source
firebase_action_body = source.split("def complete_hhs_firebase_action_job", 1)[1].split("\ndef ", 1)[0]
clear_render_caches_body = cache_runtime_source.split("def clear_render_caches", 1)[1].split("\ndef ", 1)[0]
assert "clear_firebase_aliases_cache()" in firebase_action_body
assert "clear_firebase_aliases_cache()" in clear_render_caches_body
assert "render_command_loader(\"Fetching Firebase aliases\")" in source
assert "loader_placeholder.empty()" in source
assert "if firebase_aliases_cache_is_warm():" in source
assert "fetch_firebase_aliases_with_preloader()" in aliases_table_body
assert "def hhs_firebase_config_file(" in source
assert "def hhs_firebase_creds_file(" in source
assert "def hhs_firebase_configuration(" in source
assert "FirebaseConfiguration.of_file" in source
assert "FirebaseAuth.authenticate" in source
assert "HHS_FIREBASE_CREDS_FILE" in source
assert "firebase_root_json_response(firebase_config)" in source
assert "warnings.catch_warnings()" in source
assert "InsecureRequestWarning" in source
assert "def firebase_aliases_export_file(" not in source
assert '"homesetup-37970-export.json"' not in source
assert "def firebase_alias_table_rows(" in source
assert "render_markdown_table(" in aliases_table_body
assert '"Firebase Aliases"' in aliases_table_body
assert 'item_column_label="Database"' in aliases_table_body
assert 'variable_column_label="Group"' in aliases_table_body
assert '[row["Database"] for row in alias_rows]' in aliases_table_body
assert '[row["Group"] for row in alias_rows]' in aliases_table_body
assert '"Alias": [row["Alias"] for row in alias_rows]' in aliases_table_body
assert '"# Dotfiles": [row["Count"] for row in alias_rows]' in aliases_table_body
assert "min_row_count=4" not in aliases_table_body
assert "multi_selection=False" in aliases_table_body
assert "show_value_column=False" in aliases_table_body
assert '"Database": "var(--hhs-secondary)"' not in aliases_table_body
assert '"Group": "var(--hhs-secondary)"' in aliases_table_body
assert '"Alias": "var(--hhs-theme-primary-color)"' in aliases_table_body
assert "return selected_aliases[0] if selected_aliases else" in aliases_table_body

aliases_start = source.index("def hhs_firebase_config_file(")
aliases_end = source.index("def render_hhs_firebase_aliases_table", aliases_start)
aliases_namespace = {
    "json": json,
    "logging": __import__("logging"),
    "lru_cache": __import__("functools").lru_cache,
    "os": os,
    "Path": Path,
    "warnings": __import__("warnings"),
    "homesetup_config_dir": lambda: Path("/home/user/.config/hhs"),
}
exec("from __future__ import annotations\n" + source[aliases_start:aliases_end], aliases_namespace)
old_config_file = os.environ.get("HHS_FIREBASE_CONFIG_FILE")
old_creds_file = os.environ.get("HHS_FIREBASE_CREDS_FILE")
try:
    os.environ.pop("HHS_FIREBASE_CONFIG_FILE", None)
    os.environ["HHS_FIREBASE_CREDS_FILE"] = "/secure/{project_id}/firebase-creds.json"
    assert aliases_namespace["hhs_firebase_config_file"]() == Path(
        "/home/user/.config/hhs/firebase.properties"
    )
    assert aliases_namespace["hhs_firebase_creds_file"]("homesetup-37970") == Path(
        "/secure/homesetup-37970/firebase-creds.json"
    )
finally:
    if old_config_file is None:
        os.environ.pop("HHS_FIREBASE_CONFIG_FILE", None)
    else:
        os.environ["HHS_FIREBASE_CONFIG_FILE"] = old_config_file
    if old_creds_file is None:
        os.environ.pop("HHS_FIREBASE_CREDS_FILE", None)
    else:
        os.environ["HHS_FIREBASE_CREDS_FILE"] = old_creds_file

class FirebaseStatus:
    def is_2xx(self):
        return True

class FirebaseResponse:
    status_code = FirebaseStatus()
    body = json.dumps(
        {
            "homesetup": {
                "dotfiles": {
                    "demo": [{"path": ".a"}, {"path": ".b"}],
                    "home": [],
                },
                "hspylib-test": {
                    "0": [{}],
                },
            }
        }
    )

class FirebaseConfig:
    project_id = "homesetup-37970"
    uid = "firebase-user"
    database = "homesetup"
    base_url = "https://homesetup-37970.firebaseio.com:443/homesetup"
    scheme = "https"
    hostname = "homesetup-37970.firebaseio.com"
    port = 443

auth_calls = []
response_calls = []
aliases_namespace["hhs_firebase_configuration"] = lambda: FirebaseConfig()
aliases_namespace["firebase_authenticate"] = lambda project_id, uid: auth_calls.append(
    (project_id, uid)
)
aliases_namespace["firebase_rest_auth_headers"] = lambda project_id: [
    {"Authorization": f"Bearer {project_id}"}
]
def firebase_root_json_response(firebase_config):
    response_calls.append(firebase_config)
    return FirebaseResponse()

aliases_namespace["firebase_root_json_response"] = firebase_root_json_response
assert aliases_namespace["firebase_root_json_url"](FirebaseConfig()) == (
    "https://homesetup-37970.firebaseio.com:443/.json"
)
firebase_aliases = aliases_namespace["fetch_firebase_aliases"]()
firebase_aliases_again = aliases_namespace["fetch_firebase_aliases"]()
assert auth_calls == [("homesetup-37970", "firebase-user")]
assert len(response_calls) == 1
assert firebase_aliases == json.loads(FirebaseResponse.body)
assert firebase_aliases_again == firebase_aliases
assert aliases_namespace["firebase_aliases_cache_is_warm"]() is True
aliases_namespace["clear_firebase_aliases_cache"]()
assert aliases_namespace["firebase_aliases_cache_is_warm"]() is False
aliases_namespace["fetch_firebase_aliases"]()
assert len(response_calls) == 2
alias_rows = aliases_namespace["firebase_alias_table_rows"](firebase_aliases)
assert alias_rows == [
    {"Database": "homesetup", "Group": "dotfiles", "Alias": "demo", "Count": "2"},
    {"Database": "homesetup", "Group": "dotfiles", "Alias": "home", "Count": "0"},
    {"Database": "homesetup", "Group": "hspylib-test", "Alias": "0", "Count": "1"},
]
assert aliases_namespace["firebase_response_json"](
    type("BadResponse", (), {"status_code": 500, "body": "{}"})()
) == {}

command_source = Path("bin/apps/py/hhs_ui/execution/command_catalog.py").read_text(encoding="utf-8")
command_start = command_source.index("def build_hhs_firebase_plugin_command(")
command_end = command_source.index("def build_hhs_starship_plugin_command", command_start)
command_namespace = {
    "shlex": shlex,
    "build_hhs_env_environment_command": lambda: "ENV; ",
}
exec(
    "from __future__ import annotations\n"
    + command_source[command_start:command_end],
    command_namespace,
)
upload_command = command_namespace["build_hhs_firebase_alias_action_command"](
    "upload",
    "demo",
)
download_command = command_namespace["build_hhs_firebase_alias_action_command"](
    "download",
    "work alias",
)
assert "__hhs firebase execute upload demo" in upload_command
assert "__hhs firebase execute download 'work alias'" in download_command
assert 'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/firebase/firebase.bash"' in upload_command

aliases_actions_body = source.split("def render_hhs_firebase_aliases_actions", 1)[1].split("\ndef ", 1)[0]
assert "[1, 0.28, 0.28, 1]" in aliases_actions_body
assert '" Upload"' in aliases_actions_body
assert 'key="hhs_firebase_alias_upload_button"' in aliases_actions_body
assert "on_click=request_hhs_firebase_alias_action" in aliases_actions_body
assert 'args=("upload", clean_alias)' in aliases_actions_body
assert "disabled=action_disabled" in aliases_actions_body
assert '" Download"' in aliases_actions_body
assert 'key="hhs_firebase_alias_download_button"' in aliases_actions_body
assert 'args=("download", clean_alias)' in aliases_actions_body

for label, property_name, fallback_property_name, state_key, placeholder in (
    ("UID", "UID", "hhs.firebase.user.uid", "hhs_firebase_uid", "Firebase auth UID"),
    (
        "PROJECT_ID",
        "PROJECT_ID",
        "hhs.firebase.project.id",
        "hhs_firebase_project_id",
        "Firebase project ID",
    ),
    (
        "EMAIL",
        "EMAIL",
        "hhs.firebase.username",
        "hhs_firebase_email",
        "Firebase account email",
    ),
    (
        "DATABASE",
        "DATABASE",
        "hhs.firebase.database",
        "hhs_firebase_database",
        "Realtime database name",
    ),
):
    assert label in source
    assert property_name in source
    assert fallback_property_name in source
    assert state_key in source
    assert placeholder in source

namespace = {
    "HHS_CONFIG_ENV_OUTPUT_MARKER": "__HHS_CONFIG_ENV__",
    "STARSHIP_CACHE_OUTPUT_MARKER": "__HHS_STARSHIP_CACHE__",
    "STARSHIP_CONFIG_OUTPUT_MARKER": "__HHS_STARSHIP_CONFIG__",
    "STARSHIP_HHS_DIR_OUTPUT_MARKER": "__HHS_STARSHIP_HHS_DIR__",
    "STARSHIP_PRESETS_OUTPUT_MARKER": "__HHS_STARSHIP_PRESETS__",
    "STARSHIP_CONFIG_CONTENT_OUTPUT_MARKER": "__HHS_STARSHIP_CONFIG_CONTENT__",
    "STARSHIP_END_OUTPUT_MARKER": "__HHS_STARSHIP_END__",
    "FIREBASE_CONFIG_FILE_OUTPUT_MARKER": "__HHS_FIREBASE_CONFIG_FILE__",
    "FIREBASE_CONFIG_CONTENT_OUTPUT_MARKER": "__HHS_FIREBASE_CONFIG_CONTENT__",
    "FIREBASE_CONFIG_END_OUTPUT_MARKER": "__HHS_FIREBASE_END__",
    "HHS_FIREBASE_FIELDS": (
        ("UID", "UID", "hhs.firebase.user.uid", "hhs_firebase_uid", "Firebase auth UID"),
        (
            "PROJECT_ID",
            "PROJECT_ID",
            "hhs.firebase.project.id",
            "hhs_firebase_project_id",
            "Firebase project ID",
        ),
        (
            "EMAIL",
            "EMAIL",
            "hhs.firebase.username",
            "hhs_firebase_email",
            "Firebase account email",
        ),
        (
            "DATABASE",
            "DATABASE",
            "hhs.firebase.database",
            "hhs_firebase_database",
            "Realtime database name",
        ),
    ),
    "re": re,
    "strip_ansi": lambda value: value,
}
command_source = Path("bin/apps/py/hhs_ui/execution/command_catalog.py").read_text(encoding="utf-8")
parse_start = command_source.index("def parse_hhs_config_environment(")
parse_end = command_source.index("def parse_hhs_services", parse_start)
exec(
    "from __future__ import annotations\n" + command_source[parse_start:parse_end],
    namespace,
)

display_namespace = {
    "os": os,
    "Path": Path,
    "posixpath": posixpath,
    "re": re,
    "connected_ssh_host": lambda: "",
    "remote_environment_values": lambda _names: {},
    "homesetup_config_dir": lambda: Path("/home/user/.config/hhs"),
    "homesetup_home": lambda: Path("/home/user/HomeSetup"),
    "hhs_log_dir": lambda: Path("/home/user/.config/hhs/log"),
}
display_start = table_source.index("def env_path_aliases(")
display_end = table_source.index("def history_command_display_index", display_start)
exec(
    "from __future__ import annotations\n"
    + table_source[display_start:display_end],
    display_namespace,
)
expand_start = source.index("def path_variable_names(")
expand_end = source.index("def build_remote_environment_values_command", expand_start)
exec("from __future__ import annotations\n" + source[expand_start:expand_end], display_namespace)

environment = {
    "HOME": "/home/user",
    "HHS_HOME": "/home/user/HomeSetup",
    "HHS_DIR": "/home/user/.config/hhs",
    "HHS_LOG_DIR": "/home/user/.config/hhs/log",
}
display_value = display_namespace["display_path_value"](
    "/home/user/.config/hhs/firebase.properties",
    environment,
)
assert display_value == "${HHS_DIR}/firebase.properties"
starship_value = display_namespace["display_path_value"](
    "/home/user/.config/starship.toml",
    environment,
)
assert starship_value == "${HOME}/.config/starship.toml"
hhs_home_value = display_namespace["display_path_value"](
    "/home/user/HomeSetup/bin/starship.toml",
    environment,
)
assert hhs_home_value == "${HHS_HOME}/bin/starship.toml"
log_value = display_namespace["display_path_value"](
    "/home/user/.config/hhs/log/hhsrc.log",
    environment,
)
assert log_value == "${HHS_LOG_DIR}/hhsrc.log"
file_environment = {
    **environment,
    "HHS_FIREBASE_CONFIG_FILE": "/home/user/.config/hhs/firebase.properties",
}
file_value = display_namespace["display_path_value"](
    "/home/user/.config/hhs/firebase.properties",
    file_environment,
)
assert file_value == "${HHS_FIREBASE_CONFIG_FILE}"

starship_output = """__HHS_STARSHIP_CACHE__
/home/user/.cache/starship
__HHS_STARSHIP_CONFIG__
/home/user/.config/starship.toml
__HHS_STARSHIP_HHS_DIR__
/home/user/.config/hhs
__HHS_CONFIG_ENV__
HHS_DIR	/home/user/.config/hhs
HOME	/home/user
HHS_HOME	/home/user/HomeSetup
STARSHIP_CONFIG	/home/user/.config/starship.toml
__HHS_STARSHIP_PRESETS__
hhs-starship.toml
__HHS_STARSHIP_CONFIG_CONTENT__
format = "$all"
__HHS_STARSHIP_END__
"""
starship_info = namespace["parse_hhs_starship_info"](starship_output)
assert starship_info["environment"]["STARSHIP_CONFIG"] == "/home/user/.config/starship.toml"

output = """__HHS_FIREBASE_CONFIG_FILE__
/home/user/.config/hhs/firebase.properties
__HHS_CONFIG_ENV__
HHS_DIR	/home/user/.config/hhs
HOME	/home/user
HHS_HOME	/home/user/HomeSetup
HHS_FIREBASE_CONFIG_FILE	/home/user/.config/hhs/firebase.properties
__HHS_FIREBASE_CONFIG_CONTENT__
UID=abc123
PROJECT_ID=homesetup-37970
EMAIL=yorevs@gmail.com
DATABASE=homesetup
__HHS_FIREBASE_END__
"""
info = namespace["parse_hhs_firebase_info"](output)
assert info["config_file"] == "/home/user/.config/hhs/firebase.properties"
assert info["environment"]["HHS_FIREBASE_CONFIG_FILE"] == "/home/user/.config/hhs/firebase.properties"
assert info["values"]["UID"] == "abc123"
assert info["values"]["PROJECT_ID"] == "homesetup-37970"
assert info["values"]["EMAIL"] == "yorevs@gmail.com"
assert info["values"]["DATABASE"] == "homesetup"

legacy_output = """__HHS_FIREBASE_CONFIG_FILE__
/tmp/firebase.properties
__HHS_FIREBASE_CONFIG_CONTENT__
hhs.firebase.user.uid = legacy-uid
hhs.firebase.project.id = legacy-project
hhs.firebase.username = legacy@example.com
hhs.firebase.database = legacy-database
__HHS_FIREBASE_END__
"""
legacy_info = namespace["parse_hhs_firebase_info"](legacy_output)
assert legacy_info["values"]["UID"] == "legacy-uid"
assert legacy_info["values"]["PROJECT_ID"] == "legacy-project"
assert legacy_info["values"]["EMAIL"] == "legacy@example.com"
assert legacy_info["values"]["DATABASE"] == "legacy-database"

content = namespace["render_hhs_firebase_config_content"](
    "UID=old\nother.setting = keep\n",
    {
        "UID": "new",
        "PROJECT_ID": "project",
        "EMAIL": "user@example.com",
        "DATABASE": "database",
    },
)
assert "UID=new" in content
assert "other.setting = keep" in content
assert "PROJECT_ID=project" in content
assert "EMAIL=user@example.com" in content
assert "DATABASE=database" in content

legacy_content = namespace["render_hhs_firebase_config_content"](
    "hhs.firebase.user.uid = old\n",
    {
        "UID": "new",
        "PROJECT_ID": "project",
        "EMAIL": "user@example.com",
        "DATABASE": "database",
    },
)
assert "hhs.firebase.user.uid = new" in legacy_content
assert "UID=new" in legacy_content

class FakeStreamlit:
    session_state = {}

sync_namespace = {
    "HHS_FIREBASE_FIELDS": namespace["HHS_FIREBASE_FIELDS"],
    "json": __import__("json"),
    "normalize_hhs_firebase_value": namespace["normalize_hhs_firebase_value"],
    "st": FakeStreamlit(),
}
sync_start = source.index("def hhs_firebase_info_token(")
sync_end = source.index("def request_hhs_firebase_save", sync_start)
exec("from __future__ import annotations\n" + source[sync_start:sync_end], sync_namespace)

sync_info = {
    "config_file": "/home/user/.config/hhs/firebase.properties",
    "content": "UID=abc123\nPROJECT_ID=homesetup-37970\nEMAIL=yorevs@gmail.com\nDATABASE=homesetup\n",
    "values": {
        "UID": "abc123",
        "PROJECT_ID": "homesetup-37970",
        "EMAIL": "yorevs@gmail.com",
        "DATABASE": "homesetup",
    },
}
session_state = sync_namespace["st"].session_state
sync_namespace["sync_hhs_firebase_form_state"](sync_info)
assert session_state["hhs_firebase_uid"] == "abc123"
assert session_state["hhs_firebase_project_id"] == "homesetup-37970"
assert session_state["hhs_firebase_email"] == "yorevs@gmail.com"
assert session_state["hhs_firebase_database"] == "homesetup"
assert session_state["_hhs_firebase_form_dirty"] is False

for _label, _property_name, _fallback, state_key, _placeholder in namespace[
    "HHS_FIREBASE_FIELDS"
]:
    session_state.pop(state_key)
sync_namespace["sync_hhs_firebase_form_state"](sync_info)
assert session_state["hhs_firebase_uid"] == "abc123"
assert session_state["hhs_firebase_project_id"] == "homesetup-37970"
assert session_state["hhs_firebase_email"] == "yorevs@gmail.com"
assert session_state["hhs_firebase_database"] == "homesetup"

for _label, _property_name, _fallback, state_key, _placeholder in namespace[
    "HHS_FIREBASE_FIELDS"
]:
    session_state[state_key] = ""
session_state["_hhs_firebase_form_dirty"] = False
sync_namespace["sync_hhs_firebase_form_state"](sync_info)
assert session_state["hhs_firebase_uid"] == "abc123"
assert session_state["hhs_firebase_project_id"] == "homesetup-37970"
assert session_state["hhs_firebase_email"] == "yorevs@gmail.com"
assert session_state["hhs_firebase_database"] == "homesetup"

for _label, _property_name, _fallback, state_key, _placeholder in namespace[
    "HHS_FIREBASE_FIELDS"
]:
    session_state[state_key] = ""
session_state["_hhs_firebase_form_dirty"] = True
sync_namespace["sync_hhs_firebase_form_state"](sync_info)
assert session_state["hhs_firebase_uid"] == ""
assert session_state["hhs_firebase_project_id"] == ""
assert session_state["hhs_firebase_email"] == ""
assert session_state["hhs_firebase_database"] == ""
PY
  assert_success
}

@test "when rendering Firebase aliases then caption and columns should fit the table panel" {
  run python3 - "${table_ui_file}" "${css_file}" <<'PY'
import sys
from pathlib import Path

table_source = Path(sys.argv[1]).read_text(encoding="utf-8")
css = Path(sys.argv[2]).read_text(encoding="utf-8")
render_body = table_source.split("def render_markdown_table", 1)[1].split("\ndef ", 1)[0]
dataframe_css = css.split(
    'div[class*="st-key-"][class*="_markdown_table"] [data-testid="stDataFrame"] {',
    1,
)[1].split("}", 1)[0]

assert render_body.count('hhs-markdown-table-single-selection') == 1
assert "selection_marker = (" in render_body
assert 'f"{html.escape(caption)}{selection_marker}</div>"' in render_body
assert "        else:\n            selected_index = markdown_table_single_selected_index(" in render_body
assert "overflow: visible" in dataframe_css
assert "overflow-y: auto" not in dataframe_css
assert ".st-key-hhs_firebase_aliases_table_panel" not in css
assert ".hhs-table-caption" not in css
PY
  assert_success
}

# TC - 6

@test "when listing services then HomeSetup UI should be included as a managed service" {
  services_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/services/services.bash"

  assert_file_contains_many "${services_file}" \
'homesetup-ui:running' 'homesetup-ui:stopped'
}

# TC - 7
