#!/usr/bin/env bash
# shellcheck disable=2015,1090,2155,2164

#  Script: hhsrc.bash
# Purpose: This file is user specific file that gets loaded each time user creates a new
#          local session i.e. in simple words, opens a new terminal. All environment variables
#          created in this file would take effect every time a new local session is started.
# Created: Apr 29, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your shell create/change the following files:
#   ~/.hhs/.colors     : To customize your colors
#   ~/.hhs/.env        : To customize your environment variables
#   ~/.hhs/.aliases    : To customize your aliases
#   ~/.hhs/.aliasdef   : To customize your aliases definitions
#   ~/.hhs/.prompt     : To customize your prompt
#   ~/.hhs/.functions  : To customize your functions
#   ~/.hhs/.profile    : To customize your profile
#   ~/.hhs/.path       : To customize your paths

export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} hhsrc"

# Unset other used variables
unset "${!PS@}" "${!LC_@}" OLDIFS

# Unset all aliases before setting them again.
unalias -a

# Do not change this formatting, it is required to proper reset IFS to it's defaults
# The Internal Field Separator (IFS). The default value is <space><tab><newline>
export OLDIFS="${IFS}"

export PYTHON3="${PYTHON3:-python3}"

# The following variables are not inside the bash_env because we need them in the early load process.
export HHS_MY_OS="${HHS_MY_OS:-$(uname -s)}"
export HHS_MY_SHELL="${SHELL##*/}"

# Detect if HomeSetup was installed using an installation prefix.
export HHS_PREFIX_FILE="${HOME}/.hhs-prefix"

if [[ -s "${HHS_PREFIX_FILE}" ]]; then
  prefix="$(grep -m 1 . "${HHS_PREFIX_FILE}")"
  [[ -n "${prefix}" && -d "${prefix}" ]] && export HHS_PREFIX="${prefix}"
else
  unset HHS_PREFIX
fi

# Defined by the installation.
export HHS_HOME="${HHS_PREFIX:-${HOME}/HomeSetup}"
export HHS_DIR="${HOME}"/.config/hhs
export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}"/.VERSION)"
export HHS_SHOPTS_FILE="${HHS_DIR}"/shell-opts.toml
export HHS_BACKUP_DIR="${HHS_DIR}"/backup
export HHS_CACHE_DIR="${HHS_DIR}"/cache
export HHS_LOG_DIR="${HHS_DIR}"/log
export HHS_LOG_FILE="${HHS_LOG_DIR}"/hhsrc.log
export HHS_MOTD_DIR="${HHS_DIR}"/motd
export HHS_PROMPTS_DIR="${HHS_DIR}"/askai/prompts
export HHS_SETUP_FILE="${HHS_DIR}"/.homesetup.toml
export HHS_OLLAMA_PROMPT_SOURCE="${HHS_HOME}"/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md
export HHS_OLLAMA_PROMPT_FILE="${HHS_DIR}"/hhs-ask-ollama.md
export HHS_BLESH_DIR="${HHS_DIR}"/ble-sh
export HHS_VENV_PATH="${HHS_DIR}"/venv
export HHS_KEY_BINDINGS="${HHS_DIR}"/.hhs-bindings
export HHS_INPUTRC="${HOME}"/.inputrc
export HHS_ALIASDEF="${HHS_DIR}"/.aliasdef
export HHS_STREAMLIT_UI_PORT="${HHS_STREAMLIT_UI_PORT:-18501}"

# if the log directory is not found, we have to create it.
[[ -d "${HHS_LOG_DIR}" ]] || mkdir -p "${HHS_LOG_DIR}"

# if the cache directory is not found, we have to create it.
[[ -d "${HHS_CACHE_DIR}" ]] || mkdir -p "${HHS_CACHE_DIR}"

# if the motd directory is not found, we have to create it.
[[ -d "${HHS_MOTD_DIR}" ]] || mkdir -p "${HHS_MOTD_DIR}"

# if the prompts directory is not found, we have to create it.
[[ -d "${HHS_PROMPTS_DIR}" ]] || mkdir -p "${HHS_PROMPTS_DIR}"

# Set path so it includes user's private bin if it exists.
[[ -d "${HOME}/bin" ]] && export PATH="${PATH}:${HOME}/bin"

# Set path so it includes user's private bin if it exists.
[[ -d "${HOME}/.local/bin" ]] && export PATH="${PATH}:${HOME}/.local/bin"

# Set path so it includes `$HHS_DIR/bin` if it exists.
[[ -d "${HHS_DIR}/bin" ]] && export PATH="${PATH}:${HHS_DIR}/bin"

# Set path so it includes `bats-core` if it exists.
[[ -d "${HHS_HOME}/tests/bats/bats-core/bin" ]] && export PATH="${PATH}:${HHS_HOME}/tests/bats/bats-core/bin"

# Load all dotfiles following the order.
# Notice that the order here is important, do not reorder it.
DOTFILES=(
  'bash_env'
  'bash_aliases'
  'bash_colors'
  'bash_functions'
  'bash_icons'
  'bash_prompt'
  'profile'
)

# Custom dotfiles comes after the default one, so they can be overriden.
# Notice that the order here is important, do not reorder it.
CUSTOM_DOTFILES=(
   'env'
   'aliases'
   'colors'
   'functions'
   'prompt'
   'aliasdef'
)

# Re-create the HomeSetup log file.
HHS_INITIALIZATION_STARTED_MILLIS="$(
  "${PYTHON3:-python3}" -c 'import time; print(int(time.time() * 1000))'
)"
echo -e "HomeSetup is starting: $(date)\n" >"${HHS_LOG_FILE}"

# Source the bash common functions. Logs are available below here.
source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"
HHS_INITIALIZING=1

# -----------------------------------------------------------------------------------
# Initialization setup (homesetup.toml).
if [[ ! -s "${HHS_SETUP_FILE}" ]]; then
  __hhs_log "WARN" "HomeSetup initialization file '${HHS_SETUP_FILE}' was not found. Using defaults."
  \cp "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"
fi
while IFS=$'\t' read -r key val; do
  export "${key}=${val}"
done < <(
  awk '
    /^[[:space:]]*[a-zA-Z0-9_.]+[[:space:]]*=/ {
      separator = index($0, "=")
      key = substr($0, 1, separator - 1)
      value = substr($0, separator + 1)
      gsub(/[[:space:]]/, "", key)
      sub(/^[[:space:]]*/, "", value)
      gsub(/[\047\042]/, "", value)
      normalized = toupper(value)
      if (normalized == "TRUE") value = "1"
      if (normalized == "FALSE") value = ""
      printf "%s\t%s\n", toupper(key), value
    }
  ' "${HHS_SETUP_FILE}"
)

# -----------------------------------------------------------------------------------
# Settings (homesetup.toml) are available as environment variables from this point

# Add custom paths to the system `$PATH`.
if [[ -f "${HHS_DIR}/.path" ]]; then
  __hhs_log "DEBUG" "Adding custom system PATH's"
  while IFS= read -r f_path || [[ -n "${f_path}" ]]; do
    [[ -z "${f_path}" || "${f_path}" == \#* ]] && continue
    PATH="${f_path}:${PATH}"
  done <"${HHS_DIR}/.path"
fi

# Input method resources
if ! [[ -s "${HHS_INPUTRC}" ]]; then
  __hhs_log "WARN" "'.inputrc' file was copied because it was not found at: ${HOME}"
  \cp -f "${HHS_HOME}/dotfiles/inputrc" "${HHS_INPUTRC}"
fi

# Alias definitions
if ! [[ -s "${HHS_ALIASDEF}" ]]; then
  __hhs_log "WARN" "'.aliasdef' file was copied because it was not found at: ${HHS_DIR}"
  \cp -f "${HHS_HOME}/dotfiles/aliasdef" "${HHS_ALIASDEF}"
fi

# Ask AI prompt
if ! [[ -s "${HHS_OLLAMA_PROMPT_FILE}" ]]; then
  __hhs_log "WARN" "'${HHS_OLLAMA_PROMPT_FILE}' file was copied because it was not found at: ${HHS_DIR}"
  \cp -f "${HHS_OLLAMA_PROMPT_SOURCE}" "${HHS_OLLAMA_PROMPT_FILE}"
fi

# -----------------------------------------------------------------------------------
# Initialize HomeSetup key bindings.
if ! [[ -s "${HHS_KEY_BINDINGS}" ]]; then
  __hhs_log "WARN" "'${HHS_KEY_BINDINGS}' file was copied because it was not found at: ${HHS_DIR}"
  \cp -f "${HHS_HOME}/dotfiles/hhs-bindings" "${HHS_KEY_BINDINGS}"
fi

if bind -f "${HHS_KEY_BINDINGS}" &>/dev/null; then
  __hhs_log "INFO" "Key bindings loaded: ${HHS_KEY_BINDINGS}"
else
  __hhs_log "WARN" "Key bindings failed to load: ${HHS_KEY_BINDINGS}"
fi

bind '"\t": menu-complete' &>/dev/null || __hhs_log "WARN" "TAB key '\t' binding failed to load."
bind '"\C-i": complete' &>/dev/null || __hhs_log "WARN" "TAB key '\C-i' binding failed to load."

# -----------------------------------------------------------------------------------
# Set system locale variables (defaults)
if [[ ${HHS_SET_LOCALES} -eq 1 ]]; then
  export LANGUAGE=${LANGUAGE:-en_US:en}
  export LANG=${LANG:-en_US.UTF-8}
  if __hhs_has "locale"; then
    export LC_ALL=${LC_ALL:-${LANG}}
    export LC_CTYPE=${LC_CTYPE:-${LANG}}
    export LC_COLLATE=${LC_COLLATE:-${LANG}}
    export LC_MESSAGES=${LC_MESSAGES:-${LANG}}
    export LC_MONETARY=${LC_MONETARY:-${LANG}}
    export LC_NUMERIC=${LC_NUMERIC:-${LANG}}
    export LC_TIME=${LC_TIME:-${LANG}}
  fi
else
  __hhs_log "WARN" "Set system locales were disabled !"
fi

# -----------------------------------------------------------------------------------
# Initialize Ble-sh plug-in if it's enabled.
if [[ ${HHS_USE_BLESH} -eq 1 ]]; then
  __hhs_log "INFO" "Loading Ble-sh plug-in"
  [[ $- == *i* ]] && __hhs_source "${HHS_BLESH_DIR}/out/ble.sh" --noattach
else
  __hhs_log "WARN" "Ble-sh initialization was disabled !"
fi

# -----------------------------------------------------------------------------------
# Activate HomeSetup Python venv.
if [[ ${HHS_PYTHON_VENV_ENABLED} -eq 1 ]]; then
  __hhs_log "DEBUG" "Activating python virtual environment"
  if __hhs_source "${HHS_VENV_PATH}"/bin/activate; then
    __hhs_log "INFO" "HomeSetup Python venv has been activated: ${HHS_VENV_PATH}"
    export HHS_PYTHON_VENV_ACTIVE=1
  else
    __hhs_log "ERROR" "Unable to activate HomeSetup Python venv!"
  fi
else
  __hhs_log "WARN" "HomeSetup Python venv auto-activation was disabled !"
fi

# -----------------------------------------------------------------------------------
# Set/Unset the shell options
if [[ ${HHS_LOAD_SHELL_OPTIONS} -eq 1 ]]; then
  if [[ ! -s "${HHS_SHOPTS_FILE}" ]]; then
    \shopt | awk '{print $1" = "$2}' >"${HHS_SHOPTS_FILE}" ||
       __hhs_log "ERROR" "Unable to create the Shell Options file !"
  fi
  re_key_pair="^([a-zA-Z0-9]*) *= *([Oo][Nn]|[Oo][Ff][Ff])$"
  while read -r line; do
    if [[ ${line} =~ ${re_key_pair} ]]; then
      option="${BASH_REMATCH[1]}"
      state="$(tr '[:upper:]' '[:lower:]' <<<"${BASH_REMATCH[2]}")"
      if [[ "${state}" == 'on' ]]; then
        \shopt -s "${option}" &>/dev/null || __hhs_log "WARN" "Unable to SET shell option: ${option}"
      elif [[ "${state}" == 'off' ]]; then
        \shopt -u "${option}" &>/dev/null || __hhs_log "WARN" "Unable to UNSET shell option: ${option}"
      fi
    fi
  done <"${HHS_SHOPTS_FILE}"
  __hhs_log "INFO" "Shell options are set !"
fi

# -----------------------------------------------------------------------------------
# Load dotfiles

# Load all HomeSetup dotfiles.
__hhs_log "INFO" "Loading HomeSetup dotfiles"
for file in "${DOTFILES[@]}"; do
  f_path="${HOME}/.${file}"
  if [[ -s "${f_path}" ]]; then
    __hhs_log "DEBUG" "Loading dotfile: ${f_path}"
    __hhs_source "${f_path}"
  else
    __hhs_log "WARN" "Skipped dotfile :: Not found -> ${f_path}"
  fi
done

# Zoxide integration
if __hhs_has 'zoxide'; then
  if ! eval "$(zoxide init bash)"; then
    __hhs_log "WARN" "Zoxide was not enabled !"
  fi
fi

# Load all Custom dotfiles:
#   source -> ~/.hhs/.env can be used to extend/override .bash_env
#   source -> ~/.hhs/.colors can be used to extend/override .bash_colors
#   source -> ~/.hhs/.prompt can be used to extend/override .bash_prompt
#   source -> ~/.hhs/.aliases can be used to extend/override .bash_aliases
#   source -> ~/.hhs/.aliasdef can be used to customize your alias definitions
#   source -> ~/.hhs/.functions can be used to extend/override .bash_functions
for file in "${CUSTOM_DOTFILES[@]}"; do
  f_path="${HHS_DIR}/.${file}"
  if [[ -s "${f_path}" ]]; then
    __hhs_log "INFO" "Loading custom dotfile: ${f_path}"
    __hhs_source "${f_path}"
  else
    __hhs_log "WARN" "Skipped custom dotfile :: Not found -> ${f_path}"
  fi
done

# Load system settings using Setman. Regenerate the export only when one of its inputs changes.
if [[ ${HHS_EXPORT_SETTINGS} -eq 1 ]] && __hhs_is_venv; then
  setman_config="hhs.setman.database = ${HHS_SETMAN_DB_FILE}"
  setman_current_config=''
  [[ -r "${HHS_SETMAN_CONFIG_FILE}" ]] && IFS= read -r setman_current_config <"${HHS_SETMAN_CONFIG_FILE}"
  if [[ "${setman_current_config}" != "${setman_config}" ]]; then
    printf '%s\n' "${setman_config}" >"${HHS_SETMAN_CONFIG_FILE}"
  fi

  setman_cache_file="${HHS_CACHE_DIR}/setman-export-v1.bash"
  setman_cache_refresh_failed=0
  setman_module_file=''
  for setman_candidate in "${HHS_VENV_PATH}"/lib/python*/site-packages/setman/__init__.py; do
    [[ -f "${setman_candidate}" ]] && setman_module_file="${setman_candidate}"
  done

  if [[ ! -s "${setman_cache_file}" || "${HHS_SETMAN_DB_FILE}" -nt "${setman_cache_file}" ||
        "${HHS_SETMAN_CONFIG_FILE}" -nt "${setman_cache_file}" ||
        "${setman_module_file}" -nt "${setman_cache_file}" ]]; then
    tmp_file="${setman_cache_file}.${BASHPID:-$$}.tmp"
    if ${PYTHON3} -m setman source -n hhs -f "${tmp_file}"; then
      \chmod 600 "${tmp_file}"
      \mv -f "${tmp_file}" "${setman_cache_file}"
    else
      setman_cache_refresh_failed=1
      \rm -f "${tmp_file}"
    fi
  fi

  if __hhs_source "${setman_cache_file}"; then
    if [[ ${setman_cache_refresh_failed} -eq 1 ]]; then
      __hhs_log "WARN" "System settings loaded from stale cache after Setman export failed !"
    else
      __hhs_log "INFO" "System settings loaded !"
    fi
  else
    __hhs_log "ERROR" "Failed to load system settings !"
  fi
else
  __hhs_log "WARN" "System settings skipped !"
fi

# Load bash completions.
if [[ ${HHS_LOAD_COMPLETIONS} -eq 1 ]]; then
  __hhs_log "INFO" "Loading bash completions!"
  if ! declare -F _get_comp_words_by_ref >/dev/null 2>&1; then
    for bash_completion_file in /usr/share/bash-completion/bash_completion /etc/bash_completion; do
      if [[ -r "${bash_completion_file}" ]]; then
        __hhs_source "${bash_completion_file}" && __hhs_log "INFO" "Bash completion helpers loaded: ${bash_completion_file}"
        break
      fi
    done
  fi
  for cpl in "${HHS_HOME}/bin/completions/${HHS_MY_SHELL}"/*-completion."${HHS_MY_SHELL}"; do
    [[ -f "${cpl}" ]] || continue
    app_name="${cpl##*/}"
    app_name="${app_name//-completion/}"
    app_name="${app_name//\.${HHS_MY_SHELL}/}"
    if __hhs_has "${app_name}"; then
      if [[ ${HHS_USE_BLESH} -eq 1 && "${app_name}" == "fzf" ]]; then
        # Note: If you want to combine fzf-completion with bash_completion, you need to load bash_completion
        # earlier than fzf-completion. This is required regardless of whether to use ble.sh or not.
        # source /etc/profile.d/bash_completion.sh
        ble-import -d integration/fzf-completion
        ble-import -d integration/fzf-key-bindings
      fi
      __hhs_source "${cpl}" && HHS_COMPLETIONS="${HHS_COMPLETIONS}${app_name} "
    else
      __hhs_log "WARN" "Skipping completion \"${app_name}\" because the application was not detected!"
    fi
  done
  export HHS_COMPLETIONS
fi

# Load bash key bindings.
if [[ ${HHS_LOAD_KEY_BINDINGS} -eq 1 ]]; then
  __hhs_log "INFO" "Loading bash HomeSetup key bindings"
  for bnd in "${HHS_HOME}/bin/key-bindings/${HHS_MY_SHELL}"/*-key-bindings."${HHS_MY_SHELL}"; do
    [[ -f "${bnd}" ]] || continue
    app_name="${bnd##*/}"
    app_name="${app_name//-key-bindings/}"
    app_name="${app_name//\.${HHS_MY_SHELL}/}"
    if __hhs_has "${app_name}"; then
      __hhs_source "${bnd}" && HHS_BINDINGS="${HHS_BINDINGS}${app_name} "
    else
      __hhs_log "WARN" "Skipping key binding \"${app_name}\" because the application was not detected!"
    fi
  done
  export HHS_BINDINGS
fi

# Restore the last used directory
if [[ ${HHS_RESTORE_LAST_DIR} -eq 1 && -s "${HHS_DIR}/.last_dirs" ]]; then
  IFS= read -r last_dir <"${HHS_DIR}/.last_dirs"
  [[ "${last_dir}" == '~/'* ]] && last_dir="${HOME}/${last_dir#\~/}"
  \cd "${last_dir}" 2> /dev/null || {
    __hhs_log "WARN" "Unable to enter last directory: '${last_dir}' because it was not found !"
    \cd "${HOME}"
  }
fi

# Attach ble-sh to bash if it's enabled.
if [[ ${HHS_USE_BLESH} -eq 1 && -d "${HHS_BLESH_DIR}" ]]; then
  __hhs_log "DEBUG" "Attaching Ble-sh plug-in"
  [[ ! ${BLE_VERSION-} ]] || ble-attach
else
  unset HHS_USE_BLESH
  __hhs_log "WARN" "Ble-sh was not enabled !"
fi

# Attach atuin to bash if it's enabled
if [[ ${HHS_USE_ATUIN} -eq 1 ]] && __hhs_has 'atuin'; then
  __hhs_log "DEBUG" "Attaching Atuin plug-in"
  if ! eval "$(atuin init bash)" || ! atuin import auto &>/dev/null; then
    __hhs_log "WARN" "Atuin was not enabled !"
  fi
fi

# Reuse one clock read for short-lived health caching and update scheduling.
current_epoch=''
current_update_stamp=''
if [[ ${HHS_OLLAMA_AI_AUTOSTART:-0} -eq 1 || ${HHS_NO_AUTO_UPDATE:-0} -ne 1 ]]; then
  read -r current_epoch current_update_stamp < <(date '+%s %s%S')
fi

# Start the Ollama server if it's enabled. Cache successful health checks briefly across terminals.
if __hhs_has 'ollama' && [[ ${HHS_OLLAMA_AI_AUTOSTART} -eq 1 ]]; then
  ollama_health_cache="${HHS_CACHE_DIR}/ollama-health.timestamp"
  ollama_health_timestamp=0
  [[ -r "${ollama_health_cache}" ]] && IFS= read -r ollama_health_timestamp <"${ollama_health_cache}"
  [[ "${ollama_health_timestamp}" =~ ^[0-9]+$ ]] || ollama_health_timestamp=0

  if ((current_epoch >= ollama_health_timestamp && current_epoch - ollama_health_timestamp < 30)); then
    __hhs_log "DEBUG" "Ollama health check is still current"
  else
    __hhs_log "DEBUG" "Starting Ollama server"
    if ! ollama ps &>/dev/null; then
      nohup ollama serve >"${HHS_LOG_DIR}/ollama.log" 2>&1 &
      pid=$!
      if kill -0 "${pid}" 2>/dev/null; then
        printf '%s\n' "${current_epoch}" >"${ollama_health_cache}"
        __hhs_log "INFO" "Ollama server started with PID: ${pid}"
      else
        __hhs_log "ERROR" "Unable to start Ollama server!"
      fi
    else
      printf '%s\n' "${current_epoch}" >"${ollama_health_cache}"
      __hhs_log "INFO" "Ollama server is already running with PID: $(pgrep 'ollama')"
    fi
  fi
fi

# Schedule HomeSetup updates without blocking the first prompt.
if [[ ${HHS_NO_AUTO_UPDATE:-0} -ne 1 ]]; then
  last_update=0
  [[ -r "${HHS_DIR}/.last_update" ]] && IFS= read -r last_update <"${HHS_DIR}/.last_update"
  [[ "${last_update}" =~ ^[0-9]+$ ]] || last_update=0

  if [[ ${current_update_stamp} -ge ${last_update} ]]; then
    update_lock_file="${HHS_CACHE_DIR}/startup-update.pid"
    update_pid=''
    [[ -r "${update_lock_file}" ]] && IFS= read -r update_pid <"${update_lock_file}"
    if [[ ! "${update_pid}" =~ ^[0-9]+$ ]] || ! kill -0 "${update_pid}" 2>/dev/null; then
      \rm -f "${update_lock_file}"
      (
        trap '\rm -f "${update_lock_file}"' EXIT
        if __hhs_is_reachable 'https://github.com/'; then
          __hhs updater execute check
        else
          __hhs_errcho 'hhsrc' "HomeSetup GitHub website is unreachable !"
        fi
      ) >>"${HHS_LOG_DIR}/startup-update.log" 2>&1 &
      update_pid=$!
      printf '%s\n' "${update_pid}" >"${update_lock_file}"
      disown "${update_pid}" 2>/dev/null || true
      __hhs_log "INFO" "HomeSetup update check scheduled with PID: ${update_pid}"
    fi
  fi
  echo -en "\033[1J\033[H"
fi

# Remove PATH duplicates
PATH=$(awk -F: '{for (i=1;i<=NF;i++) { if ( !x[$i]++ ) printf("%s:",$i); }}' <<<"${PATH}")
export PATH

# Bash hooks
function command_not_found_handle() {
  __hhs_errcho "bash" "Command not found: \"\033[9m${1}\033[m\""
  echo -e "\n${YELLOW}${TIP_ICON} Tip: Try 'type $1', 'which $1' or ask 'Command not found: \"${1}\"' for help.${NC}"
  return 127
}

echo -en "\033[H\033[J"

# Print System MOTDs
if [[ -s /run/motd.dynamic ]]; then
    cat /run/motd.dynamic        # Ubuntu/Debian with update-motd
elif [[ -s /etc/motd ]]; then
    cat /etc/motd                # RHEL, CentOS, Fedora, macOS, etc.
fi

# HomeSetup MOTDs
if [[ -d "${HHS_MOTD_DIR}" ]]; then
  while IFS= read -r motd; do
    echo -e "$(eval "echo -e \"$(<"${motd}")\"")"
  done < <(find "${HHS_MOTD_DIR}" -type f | sort -u)
fi


# -----------------------------------------------------------------------------------
# Finalization

HHS_INITIALIZATION_FINISHED_MILLIS="$(__hhs_epoch_millis)"
HHS_INITIALIZATION_ELAPSED_MILLIS=$((
  HHS_INITIALIZATION_FINISHED_MILLIS - HHS_INITIALIZATION_STARTED_MILLIS
))
HHS_INITIALIZATION_ELAPSED_SECONDS=$((HHS_INITIALIZATION_ELAPSED_MILLIS / 1000))
HHS_INITIALIZATION_REMAINDER_MILLIS=$((
  HHS_INITIALIZATION_ELAPSED_MILLIS - (HHS_INITIALIZATION_ELAPSED_SECONDS * 1000)
))

printf -v HHS_INITIALIZATION_DURATION_MESSAGE \
  'HomeSetup initialization completed in %ds %03dms' \
  "${HHS_INITIALIZATION_ELAPSED_SECONDS}" \
  "${HHS_INITIALIZATION_REMAINDER_MILLIS}"
__hhs_log "INFO" "${HHS_INITIALIZATION_DURATION_MESSAGE}"
echo '' >>"${HHS_LOG_FILE}"

unset HHS_ALIAS_COMMAND_CATALOG HHS_ALIAS_COMMAND_CATALOG_INITIALIZED HHS_INITIALIZING
unset HHS_INITIALIZATION_CURRENT_LOG_TIMESTAMP HHS_INITIALIZATION_FINISHED_MILLIS
unset HHS_INITIALIZATION_LOG_EPOCH_SECOND HHS_INITIALIZATION_LOG_PREFIX
unset HHS_INITIALIZATION_REMAINDER_MILLIS HHS_INITIALIZATION_STARTED_MILLIS
unset HHS_INITIALIZATION_ELAPSED_MILLIS HHS_INITIALIZATION_ELAPSED_SECONDS
unset HHS_INITIALIZATION_DURATION_MESSAGE
unset state option line file all
unset f_path tmp_file re_key_pair prefs cpl bnd pref re motd app_name last_dir key val
unset setman_cache_file setman_cache_refresh_failed setman_candidate setman_config setman_current_config
unset setman_module_file
unset current_epoch current_update_stamp last_update ollama_health_cache ollama_health_timestamp pid
unset update_lock_file update_pid
