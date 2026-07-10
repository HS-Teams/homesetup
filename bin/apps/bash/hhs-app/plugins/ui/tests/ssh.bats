#!/usr/bin/env bats

#  Script: ssh.bats
# Purpose: HomeSetup Streamlit UI SSH and terminal tests.
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

@test "when rendering SSH view then tunnel and explorer state should use exported keys" {
  assert_file_contains_many "${constants_file}" \
'SSH_VIEWS = ("TUNNELS", "FILES")' 'SSH_EXPLORER_COMPONENT_DIR = APP_DIR / "components/ssh_explorer"' \
    '"ssh_view"' '"ssh_explorer_local_path"' '"ssh_explorer_remote_path"' \
    '"ssh_tunnel_filter"' '"ssh_tunnel_other_filter"' \
    'SSH_RECONNECT_HOST_KEY = "ssh_reconnect_host"' 'SSH_RECONNECT_HOST_KEY,' \
    'SSH_TUNNEL_TABLE_KEY = "ssh_tunnel_table"'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'SSH_EXPLORER_COMPONENT_DIR'
  assert_file_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'SSH_VIEW_LABELS' 'SSH_VIEWS'
  assert_file_not_contains_many "${constants_file}" \
'SSH_EXPLORER_LOCAL_TABLE_KEY' 'SSH_EXPLORER_REMOTE_TABLE_KEY'
  assert_file_not_contains_many "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'SSH_EXPLORER_LOCAL_TABLE_KEY' 'SSH_EXPLORER_REMOTE_TABLE_KEY'

  assert_file_contains_many "${ui_file}" \
'st.session_state.setdefault("ssh_view", "TUNNELS")' \
    'st.session_state\["ssh_view"\] not in hhs_ui.SSH_VIEWS' \
    'if connected_ssh_host():' 'views = (\*views, hhs_ui.SSH_VIEW)' \
    'elif active_view == hhs_ui.SSH_VIEW:' 'render_ssh_view()'
  assert_file_not_contains "${ui_file}" 'format_func=str.upper'
}

@test "when remote SSH command closes then Streamlit UI should clear stale connection state" {
  assert_file_contains_many "${command_catalog_file}" \
'def ssh_shared_connection_closed' 'def strip_ssh_shared_connection_notice'
  assert_file_contains "${ssh_runtime_file}" 'def clear_disconnected_ssh_host'
  run python3 - "${ui_file}" "${ssh_runtime_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
ssh_runtime_source = Path(sys.argv[2]).read_text(encoding="utf-8")
clear_body = ssh_runtime_source.split("def clear_disconnected_ssh_host", 1)[1].split("\ndef ", 1)[0]
assert "queue_search_directory_home_reset()" in clear_body
assert "reset_search_directory_to_home()" not in clear_body
assert "def apply_pending_search_directory_home_reset" in source
main_body = source.split("def main(", 1)[1].split('\n\nif __name__ == "__main__":', 1)[0]
pending_reset_index = main_body.index("apply_pending_search_directory_home_reset()")
initialize_search_index = main_body.index("initialize_search_directory_home_default()")
render_main_index = main_body.index("render_main_view()")
assert pending_reset_index < initialize_search_index < render_main_index
PY
  assert_success

  assert_file_contains "${ssh_runtime_file}" \
'st.session_state\["ssh_host_selected"\] = local_hostname()'
  assert_file_contains "${command_runtime_file}" \
'handle_remote_command_result(remote_host, result)'
  assert_file_contains_many "${command_runtime_file}" \
    'if use_cache and not ssh_shared_connection_closed(result)' \
    'if remote_host and not ssh_connection_is_alive(remote_host)' \
    'completed_disconnected_ssh_process(command_to_run, remote_host)' 'st.rerun()'
  assert_file_contains_many "${command_catalog_file}" \
    'sanitize_remote_command_result(' 'ConnectTimeout=5'
}

@test "when remote commands print HomeSetup startup chatter then command output should be sanitized" {
  run python3 - "${ssh_runtime_file}" <<'PY'
import re
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def remote_command_startup_line_is_noise(")
end = source.index("def ssh_output_is_only_shared_close(")
namespace = {
    "re": re,
    "subprocess": subprocess,
    "strip_ansi": lambda value: value,
    "homesetup_home": lambda: Path(".").resolve(),
    "lru_cache": lru_cache,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

motd_fragments = namespace["homesetup_motd_fragment_groups"]()[0]
hhs_version = os.environ.get("HHS_VERSION") or Path(".VERSION").read_text(encoding="utf-8").strip()
rendered_motd = f"[Linux-ubuntu/bash] {' root '.join(motd_fragments)} v{hhs_version} "
assert namespace["remote_command_motd_line_is_boundary"](
    rendered_motd
)
ubuntu_motd = """Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-134-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Sun Jul  5 01:47:39 -03 2026

  System load:  0.02               Processes:             128
  Usage of /:   35.4% of 32.86GB   Users logged in:       0
  Memory usage: 48%                IPv4 address for eth0: 167.99.120.81
  Swap usage:   43%                IPv4 address for eth0: 10.17.0.5

Expanded Security Maintenance for Applications is not enabled.

1 update can be applied immediately.
To see these additional updates run: apt list --upgradable

4 additional security updates can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm


"""
noisy_stdout = (
    "[bash] HomeSetup is starting...\n"
    "dynamic shell setup output\n"
    "\n"
    f"{ubuntu_motd}"
    f"{rendered_motd}\n"
    "\n"
    "GNU bash, version 5.2.21(1)-release\n"
)
noisy_stderr = "Shell option expand_aliases set to on\nreal error\n"
result = subprocess.CompletedProcess(["cmd"], 0, noisy_stdout, noisy_stderr)
remote = namespace["sanitize_remote_command_result"]("remote-host", result)
assert remote.stdout == "GNU bash, version 5.2.21(1)-release\n"
assert remote.stderr == "real error\n"
assert "Welcome to Ubuntu" not in remote.stdout
assert "Expanded Security Maintenance" not in remote.stdout

local = namespace["sanitize_remote_command_result"]("", result)
assert local.stdout == noisy_stdout
assert local.stderr == noisy_stderr

closed = subprocess.CompletedProcess(
    ["cmd"], 255, "", "Shared connection to 167.99.120.81 closed.\n"
)
sanitized_closed = namespace["sanitize_remote_command_result"]("remote-host", closed)
assert sanitized_closed.stderr == closed.stderr
PY
  assert_success
}

@test "when remote terminal command fails then SSH close trailer should not clear connection" {
  run python3 - "${ui_file}" <<'PY'
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def ssh_shared_connection_closed(")
end = source.index("def ssh_output_is_only_shared_close(")
namespace = {
    "strip_ansi": lambda value: value,
    "subprocess": subprocess,
    "lru_cache": lru_cache,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

command_failure = subprocess.CompletedProcess(
    ["ssh"],
    2,
    "",
    "ls: unrecognized option '--long'\nShared connection to host closed.\n",
)
stale_connection = subprocess.CompletedProcess(
    ["ssh"],
    255,
    "",
    "Shared connection to host closed.\n",
)
assert not namespace["ssh_shared_connection_closed"](command_failure)
assert namespace["ssh_shared_connection_closed"](stale_connection)
assert (
    namespace["strip_ssh_shared_connection_notice"](command_failure.stderr)
    == "ls: unrecognized option '--long'\n"
)
PY
  assert_success
}

@test "when SSH connects from Terminal view then Terminal should be restored" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def restore_terminal_document_view(")
end = source.index("def close_document_view(")
session_state = {}
activated = []
namespace = {
    "hhs_ui": SimpleNamespace(
        DOCUMENT_VIEW_ACTIVE_KEY="document_view_active",
        DOCUMENT_PREVIOUS_VIEW_KEY="document_previous_view",
        DOCUMENT_SELECTED_KEY="document_selected",
        VIEWS=("Home", "Configs", "Services", "SSH", "History", "Monitor", "AI"),
    ),
    "st": SimpleNamespace(session_state=session_state),
    "activate_terminal_document_view": lambda: activated.append(True),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["restore_terminal_document_view"](False)
assert session_state == {}
assert activated == []

session_state["active_view"] = "Monitor"
session_state["document_previous_view"] = "SSH"
namespace["restore_terminal_document_view"](True)
assert session_state["document_view_active"] is True
assert session_state["document_previous_view"] == "SSH"
assert session_state["document_selected"] == "TERMINAL"
assert activated == [True]

session_state["document_previous_view"] = "Missing"
namespace["restore_terminal_document_view"](True)
assert session_state["document_previous_view"] == "Home"
PY
  assert_success
}

@test "when closing Terminal view then ttyd should only reset when requested" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
start = source.index("def close_document_view(")
end = source.index("def render_terminal_back_button_cleanup_script(")
session_state = {
    "active_view": "Monitor",
    "document_previous_view": "Home",
    "document_selected": "TERMINAL",
    "document_view_active": True,
}
deactivated = []
saved = []
namespace = {
    "hhs_ui": SimpleNamespace(
        DOCUMENT_PREVIOUS_VIEW_KEY="document_previous_view",
        DOCUMENT_SELECTED_KEY="document_selected",
        DOCUMENT_VIEW_ACTIVE_KEY="document_view_active",
        VIEWS=("Home", "Configs", "Services", "SSH", "History", "Monitor", "AI"),
    ),
    "st": SimpleNamespace(session_state=session_state),
    "terminal_document_view_is_active": lambda: (
        bool(session_state.get("document_view_active"))
        and session_state.get("document_selected") == "TERMINAL"
    ),
    "deactivate_terminal_document_view": lambda: deactivated.append(True),
    "save_ui_state": lambda: saved.append(dict(session_state)),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["close_document_view"]()
assert deactivated == []
assert session_state["document_view_active"] is False
assert session_state["active_view"] == "Home"
assert len(saved) == 1

session_state.update(
    {
        "active_view": "Monitor",
        "document_previous_view": "Home",
        "document_selected": "TERMINAL",
        "document_view_active": True,
    }
)
namespace["close_document_view"](reset_terminal=True)
assert deactivated == [True]
assert session_state["document_view_active"] is False
assert session_state["active_view"] == "Home"
assert len(saved) == 2
PY
  assert_success
}

@test "when SSH host switches then current main page should be preserved" {
  run python3 - "${ssh_runtime_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def reconnect_view_state_keys(")
end = source.index("def host_selector_options(")
session_state = {"active_view": "Configs"}
persisted_state = {
    "active_view": "Search",
    "config_view": "PATH",
    "home_view": "Docker",
}
namespace = {
    "HOST_SWITCH_VIEW_STATE_KEY": "_hhs_host_switch_view_state",
    "hhs_ui": SimpleNamespace(
        DOCUMENT_PREVIOUS_VIEW_KEY="document_previous_view",
        DOCUMENT_SELECTED_KEY="document_selected",
        DOCUMENT_VIEW_ACTIVE_KEY="document_view_active",
    ),
    "is_persistable_ui_value": lambda value: isinstance(
        value, (str, bool, int, float)
    ),
    "load_ui_state": lambda: persisted_state,
    "st": SimpleNamespace(session_state=session_state),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

snapshot = namespace["reconnect_view_state_snapshot"]()
assert snapshot["active_view"] == "Configs"
assert snapshot["config_view"] == "PATH"
assert snapshot["home_view"] == "Docker"
remembered = namespace["remember_host_switch_view_state"]()
assert remembered == snapshot
session_state.pop("active_view", None)
assert namespace["consume_host_switch_view_state"]() == snapshot
assert "_hhs_host_switch_view_state" not in session_state
session_state.clear()
assert namespace["consume_host_switch_view_state"]()["active_view"] == "Search"
PY
  assert_success
}

@test "when main tab is temporarily hidden then persisted tab should be preserved" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
start = source.index("def view_segmented_control_widget_key(")
end = source.index("def save_view_segmented_control_state(")
session_state = {}
persisted_state = {"active_view": "Monitor"}
saved = []
namespace = {
    "load_ui_state": lambda: persisted_state,
    "save_ui_state": lambda: saved.append(dict(session_state)),
    "st": SimpleNamespace(session_state=session_state),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

assert namespace["normalized_active_view_value"](("Home", "Monitor")) == "Monitor"
assert session_state["active_view"] == "Monitor"

session_state["active_view"] = "AI"
persisted_state["active_view"] = "AI"
assert namespace["normalized_active_view_value"](("Home", "Services")) == "Home"
assert session_state["active_view"] == "AI"

session_state["active_view_widget"] = "Search"
namespace["save_active_view_state"]("active_view_widget", ("Home", "Search"))
assert session_state["active_view"] == "Search"
assert saved[-1]["active_view"] == "Search"
PY
  assert_success
}
