#!/usr/bin/env bats

#  Script: home.bats
# Purpose: HomeSetup Streamlit UI Home view tests.
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

@test "when rendering Home Docker then command-backed resource tables should be wired" {
  assert_file_contains "${constants_file}" 'HOME_VIEWS = ("System", "Docker", "Tools", "SHOPTS")'
  assert_file_contains_many "${ui_file}" \
'def home_view_label' 'format_func=home_view_label' 'elif home_view == "Docker"' \
    'render_home_docker_panel()' 'def render_home_docker_panel' \
    'with st.container(key="home_docker_panel")' 'def render_docker_agent_required_view' \
    'def docker_agent_failure_message' 'def docker_agent_is_running' \
    'Docker agent is not running' \
    'Docker command timedout' 'if not docker_agent_is_running()'
  assert_file_contains "${command_catalog_file}" 'def build_docker_agent_check_command'
  assert_file_not_contains "${ui_file}" ' Docker Containers'

  assert_file_contains_many "${ui_file}" \
'with st.expander("All Containers", expanded=True)' \
    'with st.expander("Available Images", expanded=True)' \
    'with st.expander("Available Volumes", expanded=False)' \
    'with st.expander("Available Networks", expanded=False)' \
    'render_persisted_expander_state_script(' \
    '"hhs.home.docker.volumes.expanded"' \
    '"hhs.home.docker.networks.expanded"' \
    'default_expanded=False' \
    'def render_docker_command_table' \
    'render_docker_container_table(containers_result)' \
    'render_docker_image_table(images_result)' \
    'render_docker_volume_table(volumes_result, volume_usage)' \
    'render_docker_network_table(networks_result, network_usage)' \
    'table_key = docker_container_table_key()' \
    'table_key = docker_image_table_key()' 'table_key = docker_volume_table_key()' \
    'table_key = docker_network_table_key()' '"label": "Start"' '"label": "Stop"' \
    '"label": "Remove"' '"label": "Delete"' 'multi_selection=True' \
    'def render_docker_selected_actions' 'def docker_selected_container_ids' \
    'def docker_selected_image_ids' 'def docker_selected_volume_names' \
    'def docker_selected_prunable_network_ids' 'def docker_resource_usage_label' \
    'def docker_rows_with_usage' 'def docker_network_rows_with_usage' \
    'def docker_selected_resources_are_unused' \
    'def docker_selected_networks_have_active_usage' \
    'Select one or more rows to interact' \
    'styled_docker_rows(rows, headers)' \
    'if "STATUS" in headers'
  run grep -F -q '["CONTAINER ID", "IMAGE", "NAMES", "STATUS", "CREATED AT"]' "${ui_file}"
  assert_success

  run grep -F -q '["IMAGE ID", "REPOSITORY", "TAG", "SIZE", "CREATED AT"]' "${ui_file}"
  assert_success

  run grep -F -q '["VOLUME NAME", "DRIVER", "In-Use"]' "${ui_file}"
  assert_success

  run grep -F -q '["NETWORK ID", "NAME", "DRIVER", "SCOPE", "In-Use"]' "${ui_file}"
  assert_success

  run grep -F -c '"label": "Prune"' "${ui_file}"
  assert_output "2"

  assert_file_contains_many "${ui_file}" \
'all_selected_running = bool(selected_rows) and all(' \
    'all_selected_stopped = bool(selected_rows) and all(' \
    'docker_container_is_up(row) for row in selected_rows' \
    'not docker_container_is_up(row) for row in selected_rows' \
    '"args": ("start", container_ids)' '"args": ("stop", container_ids)' \
    '"args": ("rm", container_ids)' '"args": (image_ids,)' \
    '"args": (volume_names,)' '"args": (network_ids,)' \
    'build_docker_container_action_command' 'build_docker_image_delete_command' \
    'build_docker_volume_remove_command' 'build_docker_network_remove_command'
  assert_file_contains_many "${command_catalog_file}" \
    'def docker_action_targets' 'def quoted_docker_action_targets' \
    'def docker_container_resource_usage' 'def build_docker_resource_usage_command' \
    'def docker_container_is_up' 'docker image rm -f' 'docker ps -a --format' \
    'docker images --format' 'docker volume ls --format' 'docker network ls --format' \
    'docker ps -a --no-trunc --format' 'docker volume rm' 'docker network rm'
  run grep -F -q '{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}' "${command_catalog_file}"
  assert_success

  assert_file_contains "${command_catalog_file}" 'return "docker ps -q >/dev/null 2>&1"'

  run python3 - "${command_catalog_file}" <<'PY'
import shlex
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def docker_action_targets(")
end = source.index("def _build_hhs_hspm_command_prefix", start)
namespace = {"shlex": shlex}
exec("from __future__ import annotations\n" + source[start:end], namespace)

assert namespace["docker_action_targets"]((" one ", "", "two")) == ("one", "two")
assert namespace["build_docker_container_action_command"](
    "stop",
    ("abc123", "container with spaces"),
) == "docker stop abc123 'container with spaces'"
assert namespace["build_docker_image_delete_command"](
    ("img123", "image with spaces"),
) == "docker image rm -f img123 'image with spaces'"
assert namespace["build_docker_volume_remove_command"](
    ("volume-one", "volume with spaces"),
) == "docker volume rm volume-one 'volume with spaces'"
assert namespace["build_docker_network_remove_command"](
    ("network123", "network with spaces"),
) == "docker network rm network123 'network with spaces'"
try:
    namespace["build_docker_container_action_command"]("restart", "abc123")
except ValueError as error:
    assert "Unsupported Docker container operation" in str(error)
else:
    raise AssertionError("unsupported Docker operations must fail")
try:
    namespace["build_docker_image_delete_command"](())
except ValueError as error:
    assert "require at least one target ID" in str(error)
else:
    raise AssertionError("empty Docker targets must fail")
PY
  assert_success

  run python3 - "${ui_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def docker_selected_prunable_network_ids(")
end = source.index("def render_docker_container_table(", start)
namespace = {
    "hhs_ui": SimpleNamespace(
        DOCKER_BUILT_IN_NETWORK_NAMES=frozenset({"bridge", "host", "none"})
    )
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

usage = {"app-data": ("api", "worker")}
rows = namespace["docker_rows_with_usage"](
    [
        {"VOLUME NAME": "app-data", "DRIVER": "local"},
        {"VOLUME NAME": "unused-data", "DRIVER": "local"},
    ],
    "VOLUME NAME",
    usage,
)
assert rows[0]["In-Use"] == "Yes: api, worker"
assert rows[1]["In-Use"] == "No"
assert namespace["docker_selected_resources_are_unused"]([rows[1]]) is True
assert namespace["docker_selected_resources_are_unused"](rows) is False

network_rows = namespace["docker_network_rows_with_usage"](
    [
        {"NETWORK ID": "bridge-id", "NAME": "bridge"},
        {"NETWORK ID": "host-id", "NAME": "host"},
        {"NETWORK ID": "none-id", "NAME": "none"},
        {"NETWORK ID": "app-id", "NAME": "app-net"},
        {"NETWORK ID": "unused-id", "NAME": "unused-net"},
    ],
    {"app-net": ("api",)},
)
assert [row["In-Use"] for row in network_rows] == [
    "Built-In",
    "Built-In",
    "Built-In",
    "Yes: api",
    "No",
]
assert namespace["docker_selected_prunable_network_ids"](network_rows) == (
    "unused-id",
)
assert namespace["docker_selected_networks_have_active_usage"](
    network_rows
) is True
assert namespace["docker_selected_networks_have_active_usage"](
    [*network_rows[:3], network_rows[4]]
) is False
PY
  assert_success

  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
agent_body = source.split("def docker_agent_is_running", 1)[1].split("\ndef ", 1)[0]
assert "use_cache=False" not in agent_body
assert "show_overlay=False" not in agent_body
docker_body = source.split("def render_home_docker_panel", 1)[1].split("\ndef ", 1)[0]
assert "command_timeout_seconds()" in docker_body
assert "docker_agent_failure_message(agent_result)" in docker_body
required_index = docker_body.index("render_docker_agent_required_view(")
containers_index = docker_body.index('st.expander("All Containers"')
assert required_index < containers_index
PY
  assert_success

  assert_file_contains_many "${constants_file}" \
'DOCKER_CONTAINER_TABLE_KEY = "docker_container_table"' \
    'DOCKER_IMAGE_TABLE_KEY = "docker_image_table"' \
    'DOCKER_VOLUME_TABLE_KEY = "docker_volume_table"' \
    'DOCKER_NETWORK_TABLE_KEY = "docker_network_table"' \
    'DOCKER_BUILT_IN_NETWORK_NAMES = frozenset({"bridge", "host", "none"})'
  assert_file_contains_many "${ui_file}" \
'hhs_ui.DOCKER_CONTAINER_TABLE_KEY' 'hhs_ui.DOCKER_IMAGE_TABLE_KEY' \
    'hhs_ui.DOCKER_VOLUME_TABLE_KEY' 'hhs_ui.DOCKER_NETWORK_TABLE_KEY' \
    'def docker_resource_table_key' 'def reset_docker_resource_table_selection'
}

@test "when rendering Home tools and shell options then filters and actions should be wired" {
  assert_file_contains_many "${constants_file}" \
'"home_tools_filter"' '"home_tools_other_filter"' \
    'HOME_TOOLS_FILTERS = ("All", "Installed", "Not Installed", "Aliased", "Containing")' \
    'SHOPTS_FILTERS = ("All", "ON", "OFF", "Containing")' \
    '"home_shopts_filter"' '"home_shopts_other_filter"'
  assert_hhs_ui_exports HOME_TOOLS_FILTERS SHOPTS_FILTERS SHOPT_LINE_PATTERN

  assert_file_contains_many "${ui_file}" \
'def filter_tool_rows' '"home_tools_filter"' 'hhs_ui.HOME_TOOLS_FILTERS' \
    'hhs_ui.FIVE_OPTION_FILTER_COLUMNS' 'home_tool_is_installed(row)' \
    'home_tool_is_not_found(row)' '"home_tools_other_filter"' \
    'def render_home_shopts_panel' 'elif home_view == "SHOPTS"' \
    'render_home_shopts_panel()' 'hhs_ui.SHOPTS_FILTERS' \
    '"home_shopts_filter"' '"home_shopts_other_filter"'

  assert_file_contains_many "${constants_file}" \
'HOME_TOOLS_TABLE_KEY = "home_tools_table"' \
    'HOME_TOOLS_TABLE_RESET_COUNTER_KEY = "home_tools_table_reset_counter"' \
    'HOME_SHOPTS_TABLE_KEY = "home_shopts_table"' \
    'HOME_SHOPTS_TABLE_RESET_COUNTER_KEY = "home_shopts_table_reset_counter"'
  assert_hhs_ui_exports HOME_TOOLS_TABLE_KEY HOME_TOOLS_TABLE_RESET_COUNTER_KEY
  assert_file_contains_many "${ui_file}" \
'def home_tools_table_key' 'def reset_home_tools_table_selection' \
    'key=home_tools_table_key()' 'reset_home_tools_table_selection()' \
    'def home_shopts_table_key' 'def reset_home_shopts_table_selection' \
    'key=home_shopts_table_key()' 'reset_home_shopts_table_selection()'

  assert_file_contains_many "${command_catalog_file}" \
'def build_hhs_hspm_command' '__hhs hspm execute' '"install", "uninstall", "reinstall"' \
    'def build_tool_tldr_command' 'tldr {shlex.quote(tool_name.strip())}'
  assert_file_contains_many "${table_ui_file}" \
'def home_tool_is_installed' 'def home_tool_is_not_found'
  assert_file_contains_many "${ui_file}" \
    'def apply_selected_tool_action' 'home_tool_action_execute_pending' \
    'def execute_pending_home_tool_action' 'def render_home_tool_action_dialog' \
    'hhs-home-tool-action-output'
  assert_file_contains "${feedback_ui_file}" 'def render_terminal_output'
  assert_file_contains_many "${css_file}" \
'.hhs-home-tool-action-output' 'max-height: min(52dvh, 28rem)' \
    'max-width: min(82vw, 58rem)'
  assert_file_contains_many "${ui_file}" \
'def home_tool_action_noun' '"Installation"' \
    'title = f"{home_tool_action_noun(operation)} of {tool_name} {status}"' \
    'def apply_selected_tool_tldr' 'def render_home_tool_tldr_dialog' \
    'label": "Install"' 'label": "Uninstall"' 'label": "Reinstall"' \
    'label": "TLDR"'
  assert_file_contains_many "${table_ui_file}" \
    'empty_hint: str = "Select a row to interact"' \
    'empty_caption: str = "Select a row to interact"'
}
