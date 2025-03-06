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
load_bats_libs

PYTHON3="$(command -v python3)"

PIP3="${PYTHON3} -m pip"

# TC - 1
@test "after-installation-homesetup-venv-should-be-properly-activate" {
  run test -n "${VIRTUAL_ENV}"
  [ "$status" -eq 0 ]
  [[ "${VIRTUAL_ENV}" =~ ${HHS_VENV_PATH} ]]
}

# TC - 2
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
    [ "$status" -eq 0 ]
  done
}
