#!/usr/bin/env bats

#  Script: venv-tests.bats
# Purpose: HomeSetup Python venv installation tests.
# Created: Mar 06, 2025
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-built-ins.bash"
load "${HHS_FUNCTIONS_DIR}/hhs-toml.bash"
load_bats_libs

setup() {
  if [[ -n "${HHS_VENV_PATH:-}" && -x "${HHS_VENV_PATH}/bin/python3" ]]; then
    export PATH="${HHS_VENV_PATH}/bin:${PATH}"
    export VIRTUAL_ENV="${HHS_VENV_PATH}"
  fi

  PYTHON3="$(command -v python3)" || fail "Python3 is not installed on this system!"
  [[ -x "${PYTHON3}" ]] || fail "Python3 binary not executable!"

  if ! "${PYTHON3}" -m pip --version &>/dev/null; then
    fail "pip for Python3 is not installed or not working!"
  fi
  PIP3="${PYTHON3} -m pip"
}

# TC - 1
@test "venv-should-be-active" {
  run __hhs_venv
  assert_success
  assert_output --partial "Virtual environment is Active"
}

# TC - 2
@test "after-installation-homesetup-venv-should-be-properly-activate" {
  run test -n "${VIRTUAL_ENV}"
  assert_success
  [[ "${VIRTUAL_ENV}" =~ ${HHS_VENV_PATH} ]]
}

# TC - 3
@test "after-installation-hspylib-modules-should-report-their-versions" {
  declare -a modules=(
    'hspylib'
    'hspylib-datasource'
    'hspylib-clitt'
    'hspylib-setman'
    'hspylib-vault'
    'hspylib-firebase'
  )

  for next in "${modules[@]}"; do
    run ${PIP3} show "${next}"
    assert_success
  done
}
