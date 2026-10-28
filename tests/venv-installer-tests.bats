#!/usr/bin/env bats

# Test the installer without creating a venv or installing packages.
setup() {
  local installer="${HHS_INSTALLER_UNDER_TEST:-${BATS_TEST_DIRNAME}/../install.bash}"
  sed -n '/^  install_hspylib() {/,/^  }/p' "${installer}" >"${BATS_TEST_TMPDIR}/installer.bash"
  source "${BATS_TEST_TMPDIR}/installer.bash"
  INSTALL_DIR="${BATS_TEST_DIRNAME}/.."
  INSTALL_LOG="${BATS_TEST_TMPDIR}/install.log"
  PIP_CALLS="${BATS_TEST_TMPDIR}/pip-calls"
  VENV_PYTHON3="${BATS_TEST_TMPDIR}/python3"
  VENV_PIP3=fake_pip
  VIRTUAL_ENV="${BATS_TEST_TMPDIR}/venv"
  PYTHON_MODULES=('hspylib-vault' 'hspylib-askai')
  printf '#!/bin/sh\necho Python 3.11\n' >"${VENV_PYTHON3}"
  chmod +x "${VENV_PYTHON3}"
  INSTALL_STATUS=0
  CHECK_STATUS=0
}

fake_pip() {
  printf '%s\n' "$*" >>"${PIP_CALLS}"
  case "$1" in
    -V) echo 'pip 26.1.2' ;;
    install) return "${INSTALL_STATUS}" ;;
    check) return "${CHECK_STATUS}" ;;
    freeze) echo 'hspylib-vault==0.9.137' ;;
  esac
}

quit() {
  echo "$2"
  exit "$1"
}

@test "venv installer applies constraints and checks dependencies" {
  run install_hspylib
  [ "$status" -eq 0 ]
  grep -F -- "install --upgrade -c ${INSTALL_DIR}/assets/python-constraints.txt hspylib-vault hspylib-askai" "${PIP_CALLS}"
  grep -qx check "${PIP_CALLS}"
  ! grep -q -- '--ignore-installed\|--break-system-packages' "${PIP_CALLS}"
}

@test "venv installer rejects incompatible dependencies" {
  CHECK_STATUS=1
  run install_hspylib
  [ "$status" -eq 2 ]
  [[ "$output" == *'Incompatible Python dependencies!'* ]]
  ! grep -qx freeze "${PIP_CALLS}"
}

@test "venv installer stops when package installation fails" {
  INSTALL_STATUS=1
  run install_hspylib
  [ "$status" -eq 2 ]
  [[ "$output" == *'Unable to install PyPi packages!'* ]]
  ! grep -qx check "${PIP_CALLS}"
}
