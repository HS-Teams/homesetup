#!/usr/bin/env bats

#  Script: help-text.bats
# Purpose: HomeSetup Streamlit field help quality tests.
# Created: Jul 12, 2026
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

@test "when a field displays help then it should explain purpose and behavior" {
  run python3 - "${HHS_REPO_DIR}/bin/apps/py/hhs_ui" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
field_names = {
    "checkbox",
    "color_picker",
    "date_input",
    "file_uploader",
    "multiselect",
    "number_input",
    "radio",
    "segmented_control",
    "select_slider",
    "selectbox",
    "slider",
    "text_area",
    "text_input",
    "time_input",
    "toggle",
}
generic_descriptions = {
    "Filter the table rows.",
    "Filter the table rows by text.",
}
constant_descriptions = []

for path in root.rglob("*.py"):
    source = path.read_text(encoding="utf-8")
    assert 'f"Enter the {name_label.lower()}."' not in source
    assert 'f"Enter the {value_label.lower()}."' not in source
    assert 'f"Set {label.rstrip(\':\').lower()}."' not in source
    assert 'f"Enter {label.rstrip(\':\').lower()}."' not in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in field_names:
            continue
        help_keyword = next(
            (keyword for keyword in node.keywords if keyword.arg == "help"),
            None,
        )
        if help_keyword is None:
            continue
        value = help_keyword.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            constant_descriptions.append((path, node.lineno, value.value))

assert constant_descriptions
for path, line_number, description in constant_descriptions:
    location = f"{path}:{line_number}"
    assert description not in generic_descriptions, location
    assert len(description) >= 90, (
        f"{location}: field help should explain purpose and behavior, got "
        f"{description!r}"
    )

streamlit_tree = ast.parse((root / "streamlit_ui.py").read_text(encoding="utf-8"))
field_help = next(
    ast.literal_eval(node.value)
    for node in streamlit_tree.body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name) and target.id == "CONFIG_ADD_FIELD_HELP"
        for target in node.targets
    )
)
assert set(field_help) == {"alias", "cmd", "dir", "env", "path"}
for section, fields in field_help.items():
    for field, description in fields.items():
        assert len(description) >= 90, f"{section}.{field}: {description!r}"

for path in root.rglob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        if name != "render_chart_controls":
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        has_input = keywords.get("has_input")
        if isinstance(has_input, ast.Constant) and has_input.value is True:
            assert "input_help" in keywords, f"{path}:{node.lineno}"
PY
  assert_success
}

@test "when an icon control displays a tooltip then it should name the action" {
  run python3 - "${HHS_REPO_DIR}/bin/apps/py/hhs_ui" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
vague_tooltips = {
    "Add",
    "Cancel",
    "Close",
    "Delete",
    "Edit",
    "Open",
    "Parent",
    "Refresh",
    "Remove",
    "Search",
    "Select",
    "Start",
    "Stop",
}

for path in root.rglob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == "button":
            label = node.args[0] if node.args else None
            help_keyword = next(
                (keyword for keyword in node.keywords if keyword.arg == "help"),
                None,
            )
            if help_keyword and isinstance(help_keyword.value, ast.Constant):
                assert help_keyword.value.value not in vague_tooltips, (
                    f"{path}:{node.lineno}: {help_keyword.value.value!r}"
                )
            if isinstance(label, ast.Constant) and isinstance(label.value, str):
                icon_only = not any(character.isalnum() for character in label.value)
                has_kwargs = any(keyword.arg is None for keyword in node.keywords)
                assert not icon_only or help_keyword or has_kwargs, (
                    f"{path}:{node.lineno}: icon-only button has no tooltip"
                )
        for keyword in node.keywords:
            if keyword.arg != "selected_action_buttons":
                continue
            assert isinstance(keyword.value, (ast.List, ast.Tuple))
            for action in keyword.value.elts:
                assert isinstance(action, ast.Dict)
                action_fields = {
                    key.value: value
                    for key, value in zip(action.keys, action.values)
                    if isinstance(key, ast.Constant)
                }
                assert "help" in action_fields, f"{path}:{action.lineno}"

dialog_source = (root / "widgets" / "dialog_ui.py").read_text(encoding="utf-8")
assert "def dialog_button_help(" in dialog_source
assert 'return "Close this dialog"' in dialog_source
assert 'return "Cancel the pending action"' in dialog_source

firebase_source = (
    root / "components" / "firebase_config_form" / "index.html"
).read_text(encoding="utf-8")
assert 'revealButton.title = "Reveal"' not in firebase_source
assert 'const protectedFieldNames = new Set(["PROJECT_ID", "UID"]);' in firebase_source
assert "const isProtectedField = protectedFieldNames.has(name);" in firebase_source
assert "input.type = isProtectedField ? \"password\" : \"text\";" in firebase_source
assert 'revealButton.title = `${action} Firebase ${labelText}`;' in firebase_source
assert '`${action} ${labelText}`' in firebase_source

explorer_source = (
    root / "components" / "ssh_explorer" / "index.html"
).read_text(encoding="utf-8")
assert 'createTransferButton("", "Refresh",' not in explorer_source
assert '"Refresh both file lists"' in explorer_source

footer_source = (root / "widgets" / "footer_ui.py").read_text(encoding="utf-8")
status_source = (root / "widgets" / "status_ui.py").read_text(encoding="utf-8")
assert "Dismiss status message" in footer_source
assert "Copy error details" in footer_source
assert "Dismiss status message" in status_source
assert "Copy error details" in status_source
PY
  assert_success
}
