#!/usr/bin/env bats

#  Script: hhs-services.bats
# Purpose: HomeSetup services plugin tests.
# Created: Jul 03, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

export HHS_REPO_DIR="${BATS_TEST_DIRNAME%/tests}"
export HHS_HOME="${HHS_REPO_DIR}"

load test_helper
load_bats_libs

setup() {
  cd "${HHS_REPO_DIR}"
  services_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/services/services.bash"
}

@test "when requesting services help with flags then usage should be displayed" {
  run bash --noprofile --norc -c '
    set -u
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    mkdir -p "${HHS_DIR}"
    function usage() { printf "%s\n" "${USAGE}"; return "${1:-0}"; }
    function quit() { return "${1:-0}"; }
    source "${2}"
    execute -h
    execute --help
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial "HomeSetup services"
  refute_output --partial "Fetching services statuses"
}

@test "when requesting services version with flags then version should be displayed" {
  run bash --noprofile --norc -c '
    set -u
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    mkdir -p "${HHS_DIR}"
    function quit() { return "${1:-0}"; }
    source "${2}"
    execute -v
    execute --version
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial "HomeSetup services plugin v"
  refute_output --partial "Fetching services statuses"
}

@test "when services argument starts with dash and is unknown then it should not filter" {
  run bash --noprofile --norc -c '
    set -u
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    mkdir -p "${HHS_DIR}"
    function usage() { printf "%s\n" "$2"; return "${1:-0}"; }
    function quit() { return "${1:-0}"; }
    source "${2}"
    execute --missing
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_failure
  assert_output --partial 'Invalid services option: "--missing"'
  refute_output --partial "Fetching services statuses"
}

@test "when managing Homebrew services then stop and start should use brew services subcommands" {
  run bash --noprofile --norc -c '
    set -u
    mkdir -p "${1}/bin"
    cat >"${1}/bin/brew" <<'"'"'BREW'"'"'
#!/usr/bin/env bash
if [[ "$1" != "services" ]]; then
  exit 64
fi
case "$2" in
  stop)
    printf '"'"'==> Successfully stopped `%s` (label: homebrew.mxcl.%s)\n'"'"' "$3" "$3"
    ;;
  start)
    printf '"'"'==> Successfully started `%s` (label: homebrew.mxcl.%s)\n'"'"' "$3" "$3"
    ;;
  *)
    exit 65
    ;;
esac
BREW
    chmod +x "${1}/bin/brew"
    export PATH="${1}/bin:${PATH}"
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    mkdir -p "${HHS_DIR}"
    function uname() { printf "Darwin\n"; }
    function quit() { return "${1:-0}"; }
    source "${2}"
    manage_service stop ollama
    manage_service start ollama
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial '==> Successfully stopped `ollama` (label: homebrew.mxcl.ollama)'
  assert_output --partial '==> Successfully started `ollama` (label: homebrew.mxcl.ollama)'
}

@test "when services argument is not an operation then it should filter status results" {
  run bash --noprofile --norc -c '
    set -u
    mkdir -p "${1}/bin"
    cat >"${1}/bin/brew" <<'"'"'BREW'"'"'
#!/usr/bin/env bash
if [[ "$1" != "services" || "$2" != "list" ]]; then
  exit 64
fi
cat <<'"'"'SERVICES'"'"'
Name Status User File
ollama started hjunior ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
postgresql@16 stopped hjunior ~/Library/LaunchAgents/homebrew.mxcl.postgresql@16.plist
redis started hjunior ~/Library/LaunchAgents/homebrew.mxcl.redis.plist
SERVICES
BREW
    chmod +x "${1}/bin/brew"
    export PATH="${1}/bin:${PATH}"
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_HIGHLIGHT_COLOR=""
    export WHITE=""
    export GREEN=""
    export RED=""
    export YELLOW=""
    export NC=""
    mkdir -p "${HHS_DIR}"
    function uname() { printf "Darwin\n"; }
    function quit() { return "${1:-0}"; }
    source "${2}"
    function is_hhs_streamlit_ui_running() { return 1; }
    execute olla
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial "ollama"
  refute_output --partial "postgresql"
  refute_output --partial "redis"
  refute_output --partial "Unknown operation"
}

@test "when services argument is up then it should filter by service status" {
  run bash --noprofile --norc -c '
    set -u
    mkdir -p "${1}/bin"
    cat >"${1}/bin/brew" <<'"'"'BREW'"'"'
#!/usr/bin/env bash
if [[ "$1" != "services" || "$2" != "list" ]]; then
  exit 64
fi
cat <<'"'"'SERVICES'"'"'
Name Status User File
ollama started hjunior ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
postgresql@16 stopped hjunior ~/Library/LaunchAgents/homebrew.mxcl.postgresql@16.plist
redis started hjunior ~/Library/LaunchAgents/homebrew.mxcl.redis.plist
SERVICES
BREW
    chmod +x "${1}/bin/brew"
    export PATH="${1}/bin:${PATH}"
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_HIGHLIGHT_COLOR=""
    export WHITE=""
    export GREEN=""
    export RED=""
    export YELLOW=""
    export NC=""
    mkdir -p "${HHS_DIR}"
    function uname() { printf "Darwin\n"; }
    function quit() { return "${1:-0}"; }
    source "${2}"
    function is_hhs_streamlit_ui_running() { return 0; }
    execute up
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial "ollama"
  assert_output --partial "redis"
  assert_output --partial "homesetup-ui"
  refute_output --partial "postgresql"
}

@test "when services argument is down then it should filter by service status" {
  run bash --noprofile --norc -c '
    set -u
    mkdir -p "${1}/bin"
    cat >"${1}/bin/brew" <<'"'"'BREW'"'"'
#!/usr/bin/env bash
if [[ "$1" != "services" || "$2" != "list" ]]; then
  exit 64
fi
cat <<'"'"'SERVICES'"'"'
Name Status User File
ollama started hjunior ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
postgresql@16 stopped hjunior ~/Library/LaunchAgents/homebrew.mxcl.postgresql@16.plist
redis started hjunior ~/Library/LaunchAgents/homebrew.mxcl.redis.plist
SERVICES
BREW
    chmod +x "${1}/bin/brew"
    export PATH="${1}/bin:${PATH}"
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_HIGHLIGHT_COLOR=""
    export WHITE=""
    export GREEN=""
    export RED=""
    export YELLOW=""
    export NC=""
    mkdir -p "${HHS_DIR}"
    function uname() { printf "Darwin\n"; }
    function quit() { return "${1:-0}"; }
    source "${2}"
    function is_hhs_streamlit_ui_running() { return 1; }
    execute down
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial "postgresql"
  assert_output --partial "homesetup-ui"
  refute_output --partial "ollama"
  refute_output --partial "redis"
}

@test "when listing systemd services then active state should decide service status" {
  run bash --noprofile --norc -c '
    set -u
    mkdir -p "${1}/bin"
    cat >"${1}/bin/systemctl" <<'"'"'SYSTEMCTL'"'"'
#!/usr/bin/env bash
if [[ "$1" != "list-units" ]]; then
  exit 64
fi
cat <<'"'"'SERVICES'"'"'
UNIT LOAD ACTIVE SUB DESCRIPTION
db.service loaded active exited Database setup
worker.service loaded inactive dead Background worker
SERVICES
SYSTEMCTL
    chmod +x "${1}/bin/systemctl"
    export PATH="${1}/bin:${PATH}"
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_HIGHLIGHT_COLOR=""
    export WHITE=""
    export GREEN=""
    export RED=""
    export YELLOW=""
    export NC=""
    mkdir -p "${HHS_DIR}"
    function quit() { return "${1:-0}"; }
    source "${2}"
    function detect_os() { printf "debian\n"; }
    function is_hhs_streamlit_ui_running() { return 1; }
    list_services_status
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial "db"
  assert_output --partial " Up"
  assert_output --partial "worker"
  assert_output --partial " Down"
}

@test "when listing Alpine services then rc-status output should be parsed" {
  run bash --noprofile --norc -c '
    set -u
    mkdir -p "${1}/bin"
    cat >"${1}/bin/rc-status" <<'"'"'RCSTATUS'"'"'
#!/usr/bin/env bash
if [[ "$1" != "-a" ]]; then
  exit 64
fi
cat <<'"'"'SERVICES'"'"'
Runlevel: default
 sshd                                                              [ started ]
 cron                                                              [ stopped ]
SERVICES
RCSTATUS
    chmod +x "${1}/bin/rc-status"
    export PATH="${1}/bin:${PATH}"
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_HIGHLIGHT_COLOR=""
    export WHITE=""
    export GREEN=""
    export RED=""
    export YELLOW=""
    export NC=""
    mkdir -p "${HHS_DIR}"
    function quit() { return "${1:-0}"; }
    source "${2}"
    function detect_os() { printf "alpine\n"; }
    function is_hhs_streamlit_ui_running() { return 1; }
    list_services_status
  ' -- "${BATS_TEST_TMPDIR}" "${services_file}"
  assert_success
  assert_output --partial "sshd"
  assert_output --partial " Up"
  assert_output --partial "cron"
  assert_output --partial " Down"
}
