#!/usr/bin/env bats

#  Script: hhs-starship.bats
# Purpose: HomeSetup Starship preset management tests.
# Created: Jul 21, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

export HHS_HOME="${BATS_TEST_DIRNAME}/.."

load "${HHS_HOME}/tests/test_helper"
load_bats_libs

setup() {
  export APP_NAME="hhs"
  export HHS_DIR="${BATS_TEST_TMPDIR}/hhs"
  export HHS_STARSHIP_PRESETS_DIR="${HHS_HOME}/bin/apps/bash/hhs-app/plugins/starship/hhs-presets"
  export STARSHIP_CONFIG="${BATS_TEST_TMPDIR}/starship.toml"
  export OLDIFS=$' \t\n'
  mkdir -p "${HHS_DIR}"
  set +e
  source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/starship/starship.bash"
  set -e

  function __hhs_has() {
    return 0
  }

  function quit() {
    exit "${1:-0}"
  }
}

@test "when defining HomeSetup presets then every header should contain its filename" {
  local preset_file preset_name

  for preset_file in "${HHS_STARSHIP_PRESETS_DIR}"/*.toml; do
    preset_name="$(basename "${preset_file}")"
    run grep -Fxc -- "# Preset: ${preset_name}" "${preset_file}"
    assert_success
    assert_output "1"

    run grep -Eq -- '^# Profile:' "${preset_file}"
    assert_failure
  done
}

@test "when displaying Starship help then preset query syntax should be documented" {
  run grep -Fqx -- \
    '      preset <-q | preset_name>       : Configure of query your current starship to a preset.' \
    "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/starship/starship.bash"

  assert_success
}

@test "when querying a HomeSetup preset then the configured filename should be printed" {
  printf '%s\n' '# Preset: hhs-modern.toml' > "${STARSHIP_CONFIG}"

  run execute preset -q

  assert_success
  assert_output "hhs-modern.toml"
}

@test "when querying a legacy HomeSetup profile then its filename should be normalized" {
  printf '%s\n' '# Profile: hhs-modern' > "${STARSHIP_CONFIG}"

  run execute preset -q

  assert_success
  assert_output "hhs-modern.toml"
}

@test "when querying an unmarked configuration then the query should fail" {
  printf '%s\n' 'add_newline = true' > "${STARSHIP_CONFIG}"

  run current_starship_preset

  assert_failure 2
  assert_output ""
}

@test "when applying a Starship preset then its generated configuration should be marked" {
  function starship() {
    local output_file="$4"

    printf '%s\n' 'add_newline = true' > "${output_file}"
  }

  run execute preset tokyo-night
  assert_success

  run current_starship_preset
  assert_success
  assert_output "tokyo-night"
}
