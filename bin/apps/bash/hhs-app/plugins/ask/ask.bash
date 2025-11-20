#!/usr/bin/env bash

#  Script: ask.bash
# Purpose: Offline ollama-AI agent integration for HomeSetup.
# Created: Nov 12, 2025
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="ask"

# Current script version.
VERSION="1.0.0"

# Namespace cleanup
UNSETS=(
  help version cleanup execute show_context clear_context show_models start_ollama select_ollama_model ensure_ollama
)

# Usage message
read -r -d '' USAGE <<USAGE
usage: ${APP_NAME} ${PLUGIN_NAME} <question> [options]

    _        _
   / \\   ___| | __
  / _ \\ / __| |/ /
 / ___ \\__ \\   <
/_/   \\_\\___/_|\\_\\...Ollama-AI

  Offline ollama-AI agent integration for HomeSetup v${VERSION}.

    options:
      -h | --help                      : Show this help message and exit.
      -v | --version                   : Show version and exit.
      -c | --context                   : Show current Ollama context (history) and exit.
      -r | --reset                     : Reset history before executing (fresh new session) and exit.
      -m | --models                    : List available Ollama models and exit.
      -s | --select-model [model_name] : Select the Ollama model to use.
      -k | --keep                      : Keep the response file after execution.

    arguments:
      question                         : The prompt to ask Ollama.

    examples:
      Ask a question using the current model:
        => ${APP_NAME} ${PLUGIN_NAME} "Summarize the release notes"
      Show available models:
        => ${APP_NAME} ${PLUGIN_NAME} --models
      Reset history before asking:
        => ${APP_NAME} ${PLUGIN_NAME} --reset "List my pending tasks"

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - When piped input is provided, it is used as context for the question.
USAGE

# Read context from ollama history file if not piped
[[ "${IS_PIPED}" -ne 1 && -s "${HHS_OLLAMA_HISTORY_FILE}" ]] && \
  CONTEXT="$(grep . "${HHS_OLLAMA_HISTORY_FILE}")"

# Read context from stdin if piped
[[ "${IS_PIPED}" -eq 1 ]] &&
  read -t 0 < /dev/stdin && CONTEXT="$(cat -)"

# Ollama prompt
HHS_OLLAMA_PROMPT="### INSTRUCTIONS ###
You are an advanced AI assistant integrated into HomeSetup (acronym: hhs)
Your responsibilities include system setup, configuration, diagnostics, and management
You execute inside a ${HHS_MY_SHELL} shell on ${HHS_MY_OS_RELEASE}
Always prefer ${HHS_MY_OS}-specific commands, falling back to generic POSIX/Linux only when unavoidable

### HomeSetup Information ###
- Installation path: ${HHS_HOME}
- Usage docs: ${HHS_HOME}/docs/USAGE.md
- Handbook: ${HHS_HOME}/docs/handbook/handbook.md
- Repository: ${HHS_GITHUB_URL}

### SYSTEM RULES ###

1. You MUST ALWAYS read and analyze the CONTEXT fully before answering, from the most recent to the oldest entries
3. Only when the CONTEXT does not contain the required information, ignore it and rely on your internal knowledge
4. When providing terminal commands:
   - keep them minimal
   - no unnecessary flags
   - add at most a one-line explanation when possible
5. Keep all answers short, direct, and technically accurate
6. Avoid any unnecessary explanations, filler, or narrative text
7. Do NOT guess. If uncertain, respond exactly: **\"Sorry, but I don't know.\"**
8. When the user provides a personal or generic queries: answer politely, briefly, and without bias

### TASK ###
Answer the user’s question accurately and always be helpful. Provide continuation questions when applicable.
"

# Keep response file after execution flag
KEEP=

# Ollama model to use
OLLAMA_MODEL="$(__hhs_toml_get "${HHS_SETUP_FILE}" "hhs_ollama_model" "ollama")"
OLLAMA_MODEL="${OLLAMA_MODEL#*=}"
OLLAMA_MODEL="${OLLAMA_MODEL//\"/}"
OLLAMA_MODEL="${OLLAMA_MODEL//\'/}"

[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# @purpose: HHS plugin required function
function help() {
  usage 0
}

# @purpose: HHS plugin required function
function version() {
  echo "HomeSetup ${PLUGIN_NAME} plugin ${VERSION}"
  quit 0
}

# @purpose: HHS plugin required function
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# @purpose: Check if ollama is installed and offer installation if not
function ensure_ollama() {
  if ! __hhs_has ollama; then
    echo -en "${YELLOW}Offline Ollama is not available. Install it [y]/n? ${NC}"
    read -r -n 1 ans
    echo ''
    if [[ "$ans" =~ ^[yY]$ || -z "$ans" ]]; then
      echo -en "${BLUE}Installing Ollama... "
      if "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/install-ollama.bash"; then
        echo -e "${GREEN}OK${NC}\n"
        echo -e "${YELLOW}${TIP_ICON} Tip: Type \"__hhs ask execute 'what can you do for me?'\"${NC}\n"
        start_ollama &> /dev/null
      else
        echo -e "${RED}FAILED${NC}"
        quit 2 "Offline Ollama failed to install."
      fi
    else
      quit 1 "Offline Ollama is required to use this feature."
    fi
  fi
}

# @purpose: Start ollama server, if not running, in background
function start_ollama() {
  if ! ollama ps &>/dev/null; then
    echo -e "${BLUE}✨ Starting Ollama agent...${NC}"
    nohup ollama serve >"${HHS_LOG_DIR}/ollama.log" 2>&1 &
    pid=$!
    kill -0 "$pid" 2>/dev/null || return 2
  fi

  return 0
}

# @purpose: Show ollama history file contents (context)
function show_context() {
  if [[ -f "${HHS_OLLAMA_HISTORY_FILE}" ]]; then
    [[ -s "${HHS_OLLAMA_HISTORY_FILE}" ]] || quit 0 "${ORANGE}✨ Ollama history file is empty${NC}"
    ${HHS_OLLAMA_MD_VIEWER} < "${HHS_OLLAMA_HISTORY_FILE}"
    quit 0
  fi

  quit 1 "${RED}Ollama history file not found${NC}"
}

# @purpose: Clear ollama history file (context)
function clear_context() {
  if [[ -f "${HHS_OLLAMA_HISTORY_FILE}" ]]; then
    : > "${HHS_OLLAMA_HISTORY_FILE}" || quit 2 "Unable to clear ollama history file"
    quit 0 "${GREEN}✨ Ollama history cleared${NC}"
  fi

  quit 0 "${ORANGE}✨ Ollama history file not found${NC}"
}

# @purpose: Show available ollama models (local and for download)
function show_models() {
  echo -e "${BLUE}Available to download:"
  ${HHS_OLLAMA_MD_VIEWER} < "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/ollama-models.md"
  __hhs_has ollama && ollama ps &>/dev/null && {
    echo -e "${BLUE}Available locally:\n${WHITE}"
    IFS=$'\n'
    for m in $(ollama list | nl); do
      [[ "${m}" =~ .*${OLLAMA_MODEL}.* ]] && echo -e "${HHS_HIGHLIGHT_COLOR}${m}\t (current)${NC}" && continue
      echo -e "${m}"
    done
    IFS="$OLDIFS"
  }
  quit 0
}

# @purpose: Select ollama model to use
# shellcheck disable=SC2120
function select_ollama_model() {
  local model_name="${1}" title all_models model available
  declare -a all_models=() available=()

  if [[ -z "${model_name}" ]]; then
    # Pulled models
    while IFS= read -r line; do available+=( "$line" ); done < <(ollama list | tail -n +2 | awk '{print $1}')
    # All models
    while IFS= read -r model; do
      model_name=$(printf "%s" "$model" | cut -d':' -f1-2)
      [[ $model == "${OLLAMA_MODEL}"* ]] && model="${GREEN}${model}${NC}"
      [[ " ${available[*]} " == *" ${model_name} "* ]] || model="${GRAY}${model}${NC}"
      all_models+=("${model}")
    done < <(grep . "$HHS_HOME/bin/apps/bash/hhs-app/plugins/ask/ollama-models.txt")
    title="${BLUE}Select the Ask ✨ Ollama model${NC}"
    mchoose_file=$(mktemp)
    if __hhs_mselect "${mchoose_file}" "${title}" "${all_models[@]}"; then
      model_name=$(cut -d':' -f1-2 <<< "$(grep . "${mchoose_file}")")
      model_name=$(printf '%s' "${model_name}" | sed 's/\x1b\[[0-9;]*m//g')
      if ! __hhs_toml_set "${HHS_SETUP_FILE}" "hhs_ollama_model=${model_name}" "ollama"; then
        quit 2 "Unable to change ollama model: \"${model}\""
      fi
    else
      quit 1
    fi
  fi

  if [[ -n "${model_name}" ]]; then
    if ! __hhs_toml_set "${HHS_SETUP_FILE}" "hhs_ollama_model=${model_name}" "ollama"; then
      quit 2 "Unable to set ollama model: ${model_name}!"
    fi
  fi

  quit 0 "${GREEN}✨ Ollama model set to '${model_name}'.${NC}"
}

# @purpose: Get context window size for the selected ollama model
function get_context_window() {
  ctx="$(
    awk -F'|' -v p="${OLLAMA_MODEL}" '
    $0 ~ p {
      col=$6
      gsub(/[[:space:]]/, "", col)
      sub(/[A-Za-z]+$/, "", col)
      print col
      exit
    }' <<<"$(< "${HHS_HOME}"/bin/apps/bash/hhs-app/plugins/ask/ollama-models.md)"
  )"
  printf "%d:%d" "${ctx}" "$(printf "%s" "(${ctx} * 0.6)/1" | bc)"
}

# Ensure history file size limit fits within context window
function ensure_context_size() {
  local size kb_size="${1}"

  HHS_OLLAMA_MAX_HIST_FILE_SIZE=$((kb_size * 1024))
  if [[ -s "${HHS_OLLAMA_HISTORY_FILE}" ]]; then
    size=$(stat -c %s "${HHS_OLLAMA_HISTORY_FILE}" 2>/dev/null || wc -c < "${HHS_OLLAMA_HISTORY_FILE}")
    if [[ "${size}" -gt "${HHS_OLLAMA_MAX_HIST_FILE_SIZE}" ]]; then
      tail -c "${HHS_OLLAMA_MAX_HIST_FILE_SIZE}" "${HHS_OLLAMA_HISTORY_FILE}" > "${HHS_OLLAMA_HISTORY_FILE}.tmp"
      mv "${HHS_OLLAMA_HISTORY_FILE}.tmp" "${HHS_OLLAMA_HISTORY_FILE}"
    fi
  fi
}

# @purpose: HHS plugin required function
function execute() {
  local args ans query resp ret_val ctx kb_size ctx_window model hint
  declare -a args=()

  ctx_window=$(get_context_window)
  ctx=${ctx_window%%:*}
  kb_size=${ctx_window#*:}

  ensure_context_size "${kb_size}"

  [[ "$#" -eq 0 ]] && usage 1 "No question provided."

  case "$1" in
    -h|--help) usage 0 ;;
    -v|--version) version ;;
    -c|--context) show_context ;;
    -r|--reset) clear_context ;;
    -m|--models) show_models ;;
    -s|--select-model) shift; select_ollama_model "$@";;
    -k|--keep) KEEP=1 ;;
  esac

  ensure_ollama

  # Check if ollama server is running
  ollama ps&>/dev/null || {
    if [[ "${HHS_MY_OS}" == "Darwin" ]]; then
      hint="brew services start ollama"; else hint="nohup ollama serve >"${HHS_LOG_DIR}/ollama.log" 2>&1 &"; fi
    echo -e "${RED}Ollama service is not running!\n"
    echo -e "${YELLOW}${TIP_ICON} Tip: Type \"${hint}\"${NC}"
    quit 2
  }

  # Prepare question from arguments
  for arg in "$@"; do [[ ! "$arg" =~ ^-[a-zA-Z] ]] && args+=("$arg"); done
  query="${args[*]}"

  # Question & Answer
  start_ollama &> /dev/null
  resp="$(mktemp /tmp/hhs-"${OLLAMA_MODEL}"-response.XXXXXX)" || quit 2 "Failed to create temporary file."
  grep -q '^### Started:' "${HHS_OLLAMA_HISTORY_FILE}" || echo "### Started: $(date +%F)" >> "${HHS_OLLAMA_HISTORY_FILE}"
  echo -e "## [$(date '+%H:%M')] User: \n${query}" >> "${HHS_OLLAMA_HISTORY_FILE}"
  echo -e "✨ ${GREEN}${OLLAMA_MODEL}[${ctx}K]:\n"
  printf '%s### CONTEXT ###\n%s\n\n### USER INPUT ###\n\n%s\n' \
    "$HHS_OLLAMA_PROMPT" "$CONTEXT" "${query}" |
    ollama run "${OLLAMA_MODEL}" |
    tee -a "${resp}"
  ret_val=${PIPESTATUS[1]}

  # Display the response
  if [[ -s "${resp}" ]]; then
    echo -e "## [$(date '+%H:%M')] AI: \n$(cat "${resp}")" >> "${HHS_OLLAMA_HISTORY_FILE}"
    printf '\033[H\033[2J\033[3J'
    echo -e "✨ ${GREEN}${OLLAMA_MODEL}[${ctx}K]:\t${GRAY}${resp}\n${NC}"
    ${HHS_OLLAMA_MD_VIEWER} < "${resp}"
  else
    echo -e "${ERROR_ICN} ${RED}Ollama failed to respond${NC}"
    ret_val=1
  fi

  # Cleanup
  [[ -z "${KEEP}" && -f "${resp}" ]] && rm -f "${resp}" &> /dev/null

  [[ ${ret_val} -eq 0 ]] && quit 0 || quit 2
}
