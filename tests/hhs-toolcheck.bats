#!/usr/bin/env bats

#  Script: hhs-toolcheck.bats
# Purpose: hhs-toolcheck tests.
# Created: Mar 15, 2025
#  Author: OpenAI Assistant
# License: MIT

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-toolcheck.bash"
load_bats_libs

setup_file() {
  STUBS_DIR="${HHS_HOME}/tests/stubs"
  ORIGINAL_PATH="${PATH}"
  SAMPLE_VERSION_PATH="${STUBS_DIR}/sample-version"
  chmod +x "${SAMPLE_VERSION_PATH}"
  export PATH="${STUBS_DIR}:${PATH}"
}

teardown_file() {
  export PATH="${ORIGINAL_PATH}"
}

# Provide deterministic icons and OS label for output assertions.
export HHS_MY_OS="TestOS"

CHECK_ICN="[ok]"
ALIAS_ICN="[alias]"
FUNC_ICN="[func]"
CROSS_ICN="[x]"
STAR_ICN="*"
POINTER_ICN="->"

# Maintain stubbed metadata for command resolution.
STUB_TOOL_NAMES=()
STUB_TOOL_STATES=()
STUB_COMMAND_PATHS=()
STUB_ALIAS_BODIES=()
STUB_TOOL_INDEX=-1

# @purpose: Resolve a stubbed tool index by name.
# @param $1 [Req]: Tool name
stub_tool_index() {
  local tool="$1" idx=0
  STUB_TOOL_INDEX=-1
  while [[ ${idx} -lt ${#STUB_TOOL_NAMES[@]} ]]; do
    if [[ "${STUB_TOOL_NAMES[${idx}]}" == "${tool}" ]]; then
      STUB_TOOL_INDEX="${idx}"
      return 0
    fi
    idx=$((idx + 1))
  done
  return 1
}

# @purpose: Resolve or create a stubbed tool index by name.
# @param $1 [Req]: Tool name
stub_tool_slot() {
  local tool="$1"
  if stub_tool_index "${tool}"; then
    return 0
  fi
  STUB_TOOL_INDEX="${#STUB_TOOL_NAMES[@]}"
  STUB_TOOL_NAMES[${STUB_TOOL_INDEX}]="${tool}"
}

# @purpose: Return the stubbed state for a tool.
# @param $1 [Req]: Tool name
stub_tool_state() {
  local tool="$1"
  if stub_tool_index "${tool}"; then
    printf '%s' "${STUB_TOOL_STATES[${STUB_TOOL_INDEX}]}"
  fi
}

# @purpose: Return the stubbed command path for a tool.
# @param $1 [Req]: Tool name
stub_command_path() {
  local tool="$1"
  if stub_tool_index "${tool}"; then
    printf '%s' "${STUB_COMMAND_PATHS[${STUB_TOOL_INDEX}]}"
  fi
}

# @purpose: Return the stubbed alias body for a tool.
# @param $1 [Req]: Tool name
stub_alias_body() {
  local tool="$1"
  if stub_tool_index "${tool}"; then
    printf '%s' "${STUB_ALIAS_BODIES[${STUB_TOOL_INDEX}]}"
  fi
}

# Override command -v lookups to use stubbed metadata when available.
command() {
  if [[ "$1" == "-v" ]]; then
    local tool="$2"
    local kind
    kind="$(stub_tool_state "${tool}")"
    case "${kind}" in
    path)
      local path_result
      path_result="$(stub_command_path "${tool}")"
      printf '%s' "${path_result:-/usr/bin/${tool}}"
      return 0
      ;;
    alias)
      printf "alias %s='%s'" "${tool}" "$(stub_alias_body "${tool}")"
      return 0
      ;;
    function)
      printf '%s' "${tool}"
      return 0
      ;;
    missing|'')
      return 1
      ;;
    esac
  fi

  builtin command "$@"
}

# Override alias lookup to rely on stubbed metadata.
alias() {
  if [[ "$#" -eq 1 && "$1" != "-p" ]]; then
    local tool="$1"
    if [[ "$(stub_tool_state "${tool}")" == "alias" ]]; then
      printf "alias %s='%s'\n" "${tool}" "$(stub_alias_body "${tool}")"
      return 0
    fi
    return 1
  fi

  builtin alias "$@"
}

# Override __hhs_has to leverage the stubbed metadata.
__hhs_has() {
  if [[ "$#" -eq 0 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: __hhs_has <command>"
    return 1
  fi

  local tool="$1"
  case "$(stub_tool_state "${tool}")" in
  path | alias | function)
    return 0
    ;;
  missing | '')
    return 1
    ;;
  esac
}

setup() {
  STUB_TOOL_NAMES=()
  STUB_TOOL_STATES=()
  STUB_COMMAND_PATHS=()
  STUB_ALIAS_BODIES=()
  STUB_TOOL_INDEX=-1
  OLDIFS="${IFS}"
}

teardown() {
  rm -f "${SAMPLE_VERSION_PATH}"
  IFS="${OLDIFS}"
}

stub_path_tool() {
  local tool="$1"
  local path="$2"
  stub_tool_slot "${tool}"
  STUB_TOOL_STATES[${STUB_TOOL_INDEX}]='path'
  STUB_COMMAND_PATHS[${STUB_TOOL_INDEX}]="${path}"
  STUB_ALIAS_BODIES[${STUB_TOOL_INDEX}]=""
}

stub_alias_tool() {
  local tool="$1"
  local body="$2"
  stub_tool_slot "${tool}"
  STUB_TOOL_STATES[${STUB_TOOL_INDEX}]='alias'
  STUB_COMMAND_PATHS[${STUB_TOOL_INDEX}]=""
  STUB_ALIAS_BODIES[${STUB_TOOL_INDEX}]="${body}"
}

stub_function_tool() {
  local tool="$1"
  stub_tool_slot "${tool}"
  STUB_TOOL_STATES[${STUB_TOOL_INDEX}]='function'
  STUB_COMMAND_PATHS[${STUB_TOOL_INDEX}]=""
  STUB_ALIAS_BODIES[${STUB_TOOL_INDEX}]=""
}

stub_missing_tool() {
  local tool="$1"
  stub_tool_slot "${tool}"
  STUB_TOOL_STATES[${STUB_TOOL_INDEX}]='missing'
  STUB_COMMAND_PATHS[${STUB_TOOL_INDEX}]=""
  STUB_ALIAS_BODIES[${STUB_TOOL_INDEX}]=""
}

# TC - 1
@test "when-invoking-toolcheck-without-arguments-then-prints-usage" {
  run __hhs_toolcheck
  assert_failure
  assert_output --partial "usage: __hhs_toolcheck"
}

# TC - 2
@test "when-tool-exists-on-path-then-reports-installed" {
  stub_path_tool "path-tool" "/stub/bin/path-tool"

  run __hhs_toolcheck "path-tool"

  assert_success
  assert_output --partial "[TestOS] Checking: path-tool"
  assert_output --partial "INSTALLED => /stub/bin/path-tool"
}

# TC - 3
@test "when-tool-is-aliased-then-reports-alias" {
  stub_alias_tool "alias-tool" "echo aliased"

  run __hhs_toolcheck "alias-tool"

  assert_success
  assert_output --partial "ALIASED   => alias alias-tool='echo aliased'"
}

# TC - 4
@test "when-tool-is-a-function-then-reports-function" {
  stub_function_tool "function-tool"

  run __hhs_toolcheck "function-tool"

  assert_success
  assert_output --partial "function function-tool(){...}"
}

# TC - 5
@test "when-tool-is-missing-then-reports-not-found" {
  stub_missing_tool "missing-tool"

  run __hhs_toolcheck "missing-tool"

  assert_failure
  assert_output --partial "NOT FOUND"
}

# TC - 6
@test "when-tool-is-missing-in-quiet-mode-then-suppresses-output" {
  stub_missing_tool "missing-tool"

  run __hhs_toolcheck -q "missing-tool"

  assert_failure
  assert_output ""
}

# TC - 7
@test "when-checking-version-of-installed-tool-then-shows-version" {
  stub_path_tool "sample-version" "${STUBS_DIR}/sample-version"

  run __hhs_version "sample-version"

  assert_success
  assert_output --partial "sample-version 1.0.0"
}

# TC - 8
@test "when-checking-version-of-missing-tool-then-shows-error" {
  stub_missing_tool "ghost"

  run __hhs_version "ghost"

  assert_failure
  assert_output --partial "Can't check version"
}

# TC - 9
@test "when-running-tools-with-custom-list-then-invokes-toolcheck-for-each" {
  stub_path_tool "tool-a" "/stub/bin/tool-a"
  stub_alias_tool "tool-b" "echo B"
  stub_missing_tool "tool-c"

  run __hhs_tools tool-a tool-b tool-c

  assert_success
  assert_output --partial "Checking (3) development tools"
  assert_output --partial "Checking: tool-a"
  assert_output --partial "Checking: tool-b"
  assert_output --partial "Checking: tool-c"
  assert_output --partial "To check the current installed version"
}

# TC - 10
@test "when-running-tools-with-default-list-containing-missing-tool-then-returns-success" {
  HHS_DEV_TOOLS=(tool-a missing-tool)
  stub_path_tool "tool-a" "/stub/bin/tool-a"
  stub_missing_tool "missing-tool"

  run __hhs_tools

  assert_success
  assert_output --partial "Checking (2) development tools"
  assert_output --partial "Checking: tool-a"
  assert_output --partial "Checking: missing-tool"
}
