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

@test "when rendering Home Docker then command-backed container and image tables should be wired" {
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
    'with st.expander("Available Images", expanded=True)' 'def render_docker_command_table' \
    'render_docker_container_table(containers_result)' \
    'render_docker_image_table(images_result)' 'docker_container_table_key(),' \
    'docker_image_table_key(),' '"label": "Start"' '"label": "Stop"' \
    '"label": "Remove"' '"label": "Delete"'
  run grep -F -q '["CONTAINER ID", "IMAGE", "NAMES", "STATUS", "CREATED AT"]' "${ui_file}"
  assert_success

  run grep -F -q '["IMAGE ID", "REPOSITORY", "TAG", "SIZE", "CREATED AT"]' "${ui_file}"
  assert_success

  assert_file_contains_many "${ui_file}" \
'"disabled": lambda row, _index: docker_container_is_up(row)' \
    '"disabled": lambda row, _index: not docker_container_is_up(row)' \
    'build_docker_container_action_command' 'build_docker_image_delete_command'
  assert_file_contains_many "${command_catalog_file}" \
'def docker_container_is_up' 'docker image rm -f' 'docker ps -a --format' 'docker images --format'
  run grep -F -q '{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}' "${command_catalog_file}"
  assert_success

  assert_file_contains "${ui_file}" 'return "docker ps -q >/dev/null 2>&1"'

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
    'DOCKER_IMAGE_TABLE_KEY = "docker_image_table"'
  assert_file_contains_many "${ui_file}" \
'hhs_ui.DOCKER_CONTAINER_TABLE_KEY' 'hhs_ui.DOCKER_IMAGE_TABLE_KEY'
}

@test "when rendering Home tools and shell options then filters and actions should be wired" {
  assert_file_contains_many "${constants_file}" \
'"home_tools_filter"' '"home_tools_other_filter"' \
    'HOME_TOOLS_FILTERS = ("All", "Installed", "Not Installed", "Aliased", "Containing")' \
    'SHOPTS_FILTERS = ("All", "ON", "OFF", "Containing")' \
    '"home_shopts_filter"' '"home_shopts_other_filter"'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" 'HOME_TOOLS_FILTERS'
  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'SHOPTS_FILTERS' 'SHOPT_LINE_PATTERN'

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
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" 'HOME_TOOLS_TABLE_KEY'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'HOME_TOOLS_TABLE_RESET_COUNTER_KEY'
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
    'label": "TLDR"' 'empty_hint: str = "Select a row to interact"' \
    'empty_caption: str = "Select a row to interact"'
}
