setup() {
  cd "${HHS_REPO_DIR}"
  ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/streamlit_ui.py"
  cache_runtime_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/cache_runtime.py"
  command_runtime_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/command_runtime.py"
  command_catalog_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/command_catalog.py"
  dialog_ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/dialog_ui.py"
  feedback_ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/feedback_ui.py"
  path_picker_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/path_picker.py"
  status_ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/status_ui.py"
  table_ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/table_ui.py"
  terminal_ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/terminal_ui.py"
  constants_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/constants.py"
  process_resources_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/process_resources.py"
  runtime_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/runtime.py"
  search_core_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/search_core.py"
  ssh_runtime_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/ssh_runtime.py"
  ssh_core_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/ssh_core.py"
  theme_assets_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/theme_assets.py"
  ui_state_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/ui_state.py"
  css_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/streamlit_ui.css"
  ask_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"
  ask_prompt_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md"
  bash_env_file="${HHS_REPO_DIR}/dotfiles/bash/bash_env.bash"
  hhsrc_file="${HHS_REPO_DIR}/dotfiles/bash/hhsrc.bash"
  hspm_plugin_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/hspm.bash"
  ui_plugin_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ui/ui.bash"

  streamlit_ui_source="$(<"${ui_file}")"
  cache_runtime_source="$(<"${cache_runtime_file}")"
  command_runtime_source="$(<"${command_runtime_file}")"
  dialog_ui_source="$(<"${dialog_ui_file}")"
  feedback_ui_source="$(<"${feedback_ui_file}")"
  path_picker_source="$(<"${path_picker_file}")"
  status_ui_source="$(<"${status_ui_file}")"
  ssh_runtime_source="$(<"${ssh_runtime_file}")"
  table_ui_source="$(<"${table_ui_file}")"
  terminal_ui_source="$(<"${terminal_ui_file}")"
  streamlit_ui_css_source="$(<"${css_file}")"
  constants_source="$(<"${constants_file}")"
  ui_plugin_source="$(<"${ui_plugin_file}")"
  hspm_plugin_source="$(<"${hspm_plugin_file}")"
  bash_env_source="$(<"${bash_env_file}")"
  hhsrc_source="$(<"${hhsrc_file}")"
  install_source="$(<"${HHS_REPO_DIR}/install.bash")"
  uninstall_source="$(<"${HHS_REPO_DIR}/uninstall.bash")"
}

assert_text_contains() {
  local haystack="$1"
  local needle="$2"
  [[ "${haystack}" == *"${needle}"* ]]
}

assert_text_not_contains() {
  local haystack="$1"
  local needle="$2"
  [[ "${haystack}" != *"${needle}"* ]]
}

assert_text_contains_many() {
  local haystack="$1"
  shift
  local needle
  for needle in "$@"; do
    assert_text_contains "${haystack}" "${needle}" || return 1
  done
}

assert_text_not_contains_many() {
  local haystack="$1"
  shift
  local needle
  for needle in "$@"; do
    assert_text_not_contains "${haystack}" "${needle}" || return 1
  done
}

hhs_ui_pattern_is_regex() {
  local needle="$1"
  [[ "${needle}" == ^* || "${needle}" == *'.*'* ]]
}

hhs_ui_fixed_grep_pattern() {
  printf "%s" "$1" | sed 's/\\\([][(){}.$*?+|^]\)/\1/g'
}

assert_file_contains() {
  local file="$1"
  local needle="$2"
  local search_needle

  if hhs_ui_pattern_is_regex "${needle}"; then
    run grep -q -- "${needle}" "${file}"
  else
    search_needle="$(hhs_ui_fixed_grep_pattern "${needle}")"
    run grep -Fq -- "${search_needle}" "${file}"
  fi
  assert_success
}

assert_file_not_contains() {
  local file="$1"
  local needle="$2"
  local search_needle

  if hhs_ui_pattern_is_regex "${needle}"; then
    run grep -q -- "${needle}" "${file}"
  else
    search_needle="$(hhs_ui_fixed_grep_pattern "${needle}")"
    run grep -Fq -- "${search_needle}" "${file}"
  fi
  assert_failure
}

assert_file_contains_many() {
  local file="$1"
  shift
  local needle
  for needle in "$@"; do
    assert_file_contains "${file}" "${needle}" || return 1
  done
}

assert_file_not_contains_many() {
  local file="$1"
  shift
  local needle
  for needle in "$@"; do
    assert_file_not_contains "${file}" "${needle}" || return 1
  done
}

assert_python_syntax_valid() {
  local python_file="$1"
  run python3 -c 'import ast, pathlib, sys; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))' \
    "${python_file}"
  assert_success
}
