#!/usr/bin/env bats

#  Script: navigation.bats
# Purpose: HomeSetup Streamlit UI navigation wiring tests.
# Created: Jul 09, 2026
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

@test "when registering top-level navigation then exported view constants should stay coherent" {
  assert_file_contains_many "${constants_file}" \
'VIEWS = ("Home", "Configs", "HHS", "Services", "Monitor", "Search", "History")' \
    'AI_VIEW = "AI"' 'SSH_VIEW = "SSH"' \
    'SSH_TUNNEL_FILTERS = ("All", "Reachable", "Containing")' \
    'SEARCH_FILTERS = ("All", "Containing")' 'HISTORY_FILTERS = ("All", "Containing")' \
    'ENV_FILTERS = ("All", "HHS", "Containing")' 'LIST_FILTERS = ("All", "Containing")'

  assert_file_contains "${ui_file}" 'import hhs_ui.constants as hhs_ui_constants'
  assert_file_contains_many "${ssh_core_file}" \
'def parse_ssh_config_ports' \
    'def ssh_config_port' 'def ssh_connection_display' \
    'return f"{ssh_config_hostname(clean_host)}:{ssh_config_port(clean_host)}"'
  assert_file_not_contains_many "${ui_file}" \
'import importlib' 'importlib.reload'
}

@test "when formatting navigation labels then formatter functions should use centralized maps" {
  run python3 - <<'PY'
import ast
from pathlib import Path
from types import SimpleNamespace

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
constants_path = Path("bin/apps/py/hhs_ui/constants.py")
constants_namespace = {"__file__": str(constants_path)}
exec(
    compile(constants_path.read_text(encoding="utf-8"), str(constants_path), "exec"),
    constants_namespace,
)
constant_values = {
    name: value for name, value in constants_namespace.items() if name.isupper()
}
hhs_ui = SimpleNamespace(**constant_values)
hhs_ui_constants = SimpleNamespace(**constant_values)

tree = ast.parse(ui_source)
source_lines = ui_source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
label_functions = (
    "main_view_label",
    "home_view_label",
    "config_view_label",
    "hhs_view_label",
    "history_view_label",
    "monitor_view_label",
    "ssh_view_label",
    "ai_view_label",
    "search_type_label",
)
namespace = {"hhs_ui": hhs_ui, "hhs_ui_constants": hhs_ui_constants}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(functions[name] for name in label_functions),
    namespace,
)


def assert_label_map(function_name, options, labels):
    option_values = tuple(options)
    missing = set(option_values) - set(labels)
    extra = set(labels) - set(option_values)
    assert not missing, f"{function_name} missing labels for {sorted(missing)}"
    assert not extra, f"{function_name} has stale labels for {sorted(extra)}"
    assert all(str(label).strip() for label in labels.values())
    for option in option_values:
        assert namespace[function_name](option) == labels[option]
    unknown_value = "__unknown_view_key__"
    assert namespace[function_name](unknown_value) == unknown_value


assert_label_map(
    "main_view_label",
    (*hhs_ui.VIEWS, hhs_ui.SSH_VIEW, hhs_ui.AI_VIEW),
    hhs_ui.VIEW_LABELS,
)
assert_label_map("home_view_label", hhs_ui.HOME_VIEWS, hhs_ui.HOME_VIEW_LABELS)
assert_label_map("config_view_label", hhs_ui.CONFIG_VIEWS, hhs_ui.CONFIG_VIEW_LABELS)
assert_label_map("hhs_view_label", hhs_ui.HHS_VIEWS, hhs_ui.HHS_VIEW_LABELS)
assert_label_map(
    "history_view_label", hhs_ui.HISTORY_VIEWS, hhs_ui.HISTORY_VIEW_LABELS
)
assert_label_map("monitor_view_label", hhs_ui.MONITOR_VIEWS, hhs_ui.MONITOR_VIEW_LABELS)
assert_label_map("ssh_view_label", hhs_ui.SSH_VIEWS, hhs_ui.SSH_VIEW_LABELS)
assert_label_map("ai_view_label", hhs_ui.AI_VIEWS, hhs_ui.AI_VIEW_LABELS)
assert_label_map(
    "search_type_label",
    hhs_ui_constants.SEARCH_TYPES,
    hhs_ui_constants.SEARCH_TYPE_LABELS,
)
PY
  assert_success
}

@test "when rendering navigation controls then exported options and formatters should be wired" {
  run python3 - <<'PY'
import ast
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
tree = ast.parse(source)
functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def expression_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{expression_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return ast.unparse(node)


def literal_value(node):
    return node.value if isinstance(node, ast.Constant) else ast.unparse(node)


def keyword_map(call):
    return {keyword.arg: keyword.value for keyword in call.keywords}


expected_segmented_controls = {
    "render_home_view": ("hhs_ui.HOME_VIEWS", "home_view", "System", "home_view_label"),
    "render_hhs_view": ("hhs_ui.HHS_VIEWS", "hhs_view", "SETUP", "hhs_view_label"),
    "render_configs_view": (
        "hhs_ui.CONFIG_VIEWS",
        "config_view",
        "ENV",
        "config_view_label",
    ),
    "render_ssh_view": ("hhs_ui.SSH_VIEWS", "ssh_view", "TUNNELS", "ssh_view_label"),
    "render_history_view": (
        "hhs_ui.HISTORY_VIEWS",
        "history_view",
        "COMMANDS",
        "history_view_label",
    ),
    "render_monitor_view": (
        "hhs_ui.MONITOR_VIEWS",
        "monitor_view",
        "DISK",
        "monitor_view_label",
    ),
    "render_ai_view": ("hhs_ui.AI_VIEWS", "ai_view", "CHAT", "ai_view_label"),
}
for function_name, (options_name, state_key, default, formatter) in (
    expected_segmented_controls.items()
):
    calls = [
        node
        for node in ast.walk(functions[function_name])
        if isinstance(node, ast.Call)
        and expression_name(node.func) == "render_view_segmented_control"
    ]
    assert len(calls) == 1, f"{function_name} should render one segmented control"
    call = calls[0]
    assert expression_name(call.args[1]) == options_name
    assert literal_value(call.args[2]) == state_key
    assert literal_value(call.args[3]) == default
    assert expression_name(keyword_map(call)["format_func"]) == formatter

active_view_calls = [
    node
    for node in ast.walk(functions["render_active_view_control"])
    if isinstance(node, ast.Call) and expression_name(node.func) == "st.radio"
]
assert len(active_view_calls) == 1
active_view_keywords = keyword_map(active_view_calls[0])
assert expression_name(active_view_keywords["format_func"]) == "main_view_label"
assert expression_name(active_view_keywords["on_change"]) == "save_active_view_state"
assert expression_name(active_view_keywords["key"]) == "widget_key"
assert expression_name(active_view_calls[0].args[1]) == "visible_views"
PY
  assert_success
}

@test "when selecting main views then visible views should be computed and dispatched explicitly" {
  run python3 - <<'PY'
import ast
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
}
function_sources = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}

ssh_connected = False
ai_available = False
hhs_ui = SimpleNamespace(
    VIEWS=("Home", "Configs", "HHS", "Services", "Monitor", "Search", "History"),
    SSH_VIEW="SSH",
    AI_VIEW="AI",
)
namespace = {
    "hhs_ui": hhs_ui,
    "connected_ssh_host": lambda: "remote" if ssh_connected else "",
    "ollama_service_is_available": lambda: ai_available,
}
exec(function_sources["main_views"], namespace)

assert namespace["main_views"]() == hhs_ui.VIEWS
ssh_connected = True
assert namespace["main_views"]() == (*hhs_ui.VIEWS, hhs_ui.SSH_VIEW)
ai_available = True
assert namespace["main_views"]() == (*hhs_ui.VIEWS, hhs_ui.SSH_VIEW, hhs_ui.AI_VIEW)
ssh_connected = False
assert namespace["main_views"]() == (*hhs_ui.VIEWS, hhs_ui.AI_VIEW)


def expression_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{expression_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return ast.unparse(node)


dispatches = {}
for node in ast.walk(functions["render_main_view"]):
    if not isinstance(node, ast.If):
        continue
    test = node.test
    if not (
        isinstance(test, ast.Compare)
        and expression_name(test.left) == "active_view"
        and len(test.comparators) == 1
    ):
        continue
    key = expression_name(test.comparators[0])
    first_expression = next(
        statement
        for statement in node.body
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
    )
    dispatches[key] = expression_name(first_expression.value.func)

assert dispatches == {
    "'Home'": "render_home_view",
    "'Configs'": "render_configs_view",
    "'HHS'": "render_hhs_view",
    "'Services'": "render_service_view",
    "hhs_ui.SSH_VIEW": "render_ssh_view",
    "'History'": "render_history_view",
    "'Monitor'": "render_monitor_view",
    "'Search'": "render_search_view",
    "hhs_ui.AI_VIEW": "render_ai_view",
}

body = function_sources["render_main_view"]
assert body.index("terminal_document_view_is_active()") < body.index(
    "selected_remote_host_requires_connection()"
)
assert body.index("selected_remote_host_requires_connection()") < body.index(
    "DOCUMENT_VIEW_ACTIVE_KEY"
)
assert body.index("DOCUMENT_VIEW_ACTIVE_KEY") < body.index("visible_views = main_views()")
assert body.index("visible_views = main_views()") < body.index(
    "render_active_view_control(visible_views)"
)
PY
  assert_success
}

@test "when rendering sidebar document shortcuts then callbacks should select document keys" {
  run python3 - <<'PY'
import ast
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
tree = ast.parse(source)
functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def expression_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{expression_name(node.value)}.{node.attr}"
    return ast.unparse(node)


def literal_value(node):
    return node.value if isinstance(node, ast.Constant) else ast.unparse(node)


def keyword_map(call):
    return {keyword.arg: keyword.value for keyword in call.keywords}


def button_calls(function_name):
    return [
        node
        for node in ast.walk(functions[function_name])
        if isinstance(node, ast.Call) and expression_name(node.func) == "st.button"
    ]


buttons = {}
for function_name in ("render_sidebar", "render_sidebar_terminal_button"):
    for call in button_calls(function_name):
        keywords = keyword_map(call)
        key_node = keywords.get("key")
        if key_node is None:
            continue
        key = literal_value(key_node)
        buttons[key] = keywords

for key, document_key in {
    "readme_open_button": "README",
    "handbook_open_button": "HANDBOOK",
    "terminal_open_button": "TERMINAL",
}.items():
    keywords = buttons[key]
    assert expression_name(keywords["on_click"]) == "open_document_view"
    args = keywords["args"]
    assert isinstance(args, ast.Tuple)
    assert [literal_value(element) for element in args.elts] == [document_key]
    assert literal_value(keywords["width"]) == "stretch"

terminal_body = [
    statement
    for statement in functions["render_sidebar_terminal_button"].body
    if not (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )
]
assert isinstance(terminal_body[0], ast.If)
assert expression_name(terminal_body[0].test.func) == "terminal_document_view_is_active"
assert any(isinstance(statement, ast.Return) for statement in terminal_body[0].body)
PY
  assert_success
}
