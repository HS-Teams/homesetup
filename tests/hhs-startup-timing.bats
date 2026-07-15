#!/usr/bin/env bats

#  Script: hhs-startup-timing.bats
# Purpose: HomeSetup initialization timing and log timestamp tests.
# Created: Jul 15, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

load "${HHS_HOME}/tests/test_helper"
load_bats_libs

@test "when initialization logs messages then timestamps should include live milliseconds" {
  local log_file="${BATS_TEST_TMPDIR}/hhsrc.log"

  run bash --noprofile --norc -c '
    export HHS_ACTIVE_DOTFILES=""
    export HHS_INITIALIZING=1
    export HHS_LOG_FILE="$1"
    source "$2/dotfiles/bash/bash_commons.bash"
    __hhs_log INFO "First message"
    sleep 0.03
    __hhs_log INFO "Second message"
  ' -- "${log_file}" "${HHS_HOME}"
  assert_success

  run python3 - "${log_file}" <<'PY'
import re
import sys
from datetime import datetime
from pathlib import Path

lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
pattern = re.compile(
    r"^(\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+INFO\s+(First|Second) message$"
)
timestamps = []
for line in lines:
    match = pattern.fullmatch(line)
    assert match, line
    timestamps.append(datetime.strptime(match.group(1), "%m-%d-%y %H:%M:%S.%f"))

assert len(timestamps) == 2
assert timestamps[1] > timestamps[0]
PY
  assert_success
}

@test "when Python runtime changes then initialization timing should remain comparable" {
  local system_python venv_python

  system_python="/usr/bin/python3"
  [[ -x "${system_python}" ]] || system_python="$(command -v python3)"
  venv_python="${HHS_VENV_PATH:-${HOME}/.config/hhs/venv}/bin/python3"
  [[ -x "${venv_python}" ]] || venv_python="$(command -v python3)"

  run bash --noprofile --norc -c '
    started="$($1 -c '\''import time; print(int(time.time() * 1000))'\'')"
    source "$3/dotfiles/bash/bash_commons.bash"
    PYTHON3="$2"
    finished="$(__hhs_epoch_millis)"
    elapsed=$((finished - started))
    [[ ${elapsed} -ge 0 && ${elapsed} -lt 2000 ]]
  ' -- "${system_python}" "${venv_python}" "${HHS_HOME}"
  assert_success
}

@test "when measuring initialization then epoch namespaced state should be used" {
  run python3 - "${HHS_HOME}/dotfiles/bash/hhsrc.bash" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
assert "HHS_INITIALIZATION_STARTED_MILLIS" in source
assert "HHS_INITIALIZATION_FINISHED_MILLIS" in source
assert "HHS_INITIALIZATION_ELAPSED_MILLIS" in source
assert "time.time()" in source
assert "time.monotonic()" not in source
assert "HomeSetup initialization completed in %ds %03dms" in source
assert "\nstarted=" not in source
assert "\nfinished=" not in source
assert "HHS_INITIALIZATION_LOG_TIMESTAMP=" not in source
PY
  assert_success
}
