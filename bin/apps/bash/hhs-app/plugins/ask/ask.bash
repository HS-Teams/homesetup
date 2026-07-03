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
VERSION="1.2.0"

# Namespace cleanup
UNSETS=(
  help version cleanup execute render_ollama_prompt_template render_ollama_response
  load_ollama_prompt show_context show_prompt clear_context is_text_context_file
  ingest_context show_models start_ollama select_ollama_model ensure_ollama
)

# Usage message
read -r -d '' USAGE <<EOF
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
      -p | --prompt                    : Show the main Ollama system prompt and exit.
      -i | --ingest [file]             : Set Ollama context from a text-based file and exit.
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
      Ingest context from a Markdown file:
        => ${APP_NAME} ${PLUGIN_NAME} --ingest notes.md
      Reset history before asking:
        => ${APP_NAME} ${PLUGIN_NAME} --reset

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - When piped input is provided, it is used as context for the question.

EOF

# Read context from ollama history file if not piped
[[ "${IS_PIPED}" -ne 1 && -s "${HHS_OLLAMA_HISTORY_FILE}" ]] && \
  CONTEXT="$(grep . "${HHS_OLLAMA_HISTORY_FILE}")"

# Read context from stdin if piped
[[ "${IS_PIPED}" -eq 1 ]] &&
  read -t 0 < /dev/stdin && CONTEXT="$(cat -)"

# Ollama prompt files.
HHS_OLLAMA_PROMPT_SOURCE="${HHS_OLLAMA_PROMPT_SOURCE:-${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md}"
HHS_OLLAMA_PROMPT_FILE="${HHS_OLLAMA_PROMPT_FILE:-${HHS_DIR}/hhs-ask-ollama.md}"

# Keep response file after execution flag
KEEP=

# Ollama model to use
OLLAMA_MODEL="$(__hhs_toml_get "${HHS_SETUP_FILE}" "hhs_ollama_model" "ollama")"
OLLAMA_MODEL="${OLLAMA_MODEL#*=}"
OLLAMA_MODEL="${OLLAMA_MODEL//\"/}"
OLLAMA_MODEL="${OLLAMA_MODEL//\'/}"

[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# @purpose: Render supported HomeSetup placeholders in an ollama prompt template.
function render_ollama_prompt_template() {
  local prompt="${1}"

  prompt="${prompt//\$\{HHS_MY_SHELL\}/${HHS_MY_SHELL}}"
  prompt="${prompt//\$\{HHS_MY_OS_RELEASE\}/${HHS_MY_OS_RELEASE}}"
  prompt="${prompt//\$\{HHS_MY_OS\}/${HHS_MY_OS}}"
  prompt="${prompt//\$\{HHS_HOME\}/${HHS_HOME}}"
  prompt="${prompt//\$\{HHS_GITHUB_URL\}/${HHS_GITHUB_URL}}"
  printf "%s" "${prompt}"
}

# @purpose: Render terminal cursor-control escapes from an ollama response into plain text.
function render_ollama_response() {
  local file_path="${1}"

  awk '
    function write_char(ch) {
      while (length(line) < cursor) {
        line = line " "
      }
      line = substr(line, 1, cursor) ch substr(line, cursor + 2)
      cursor++
    }

    function flush_line() {
      print line
      line = ""
      cursor = 0
    }

    function apply_csi(params, final, parts, count, mode) {
      gsub(/\?/, "", params)
      split(params, parts, ";")
      count = parts[1] == "" ? 1 : parts[1] + 0

      if (final == "D") {
        cursor -= count
        if (cursor < 0) {
          cursor = 0
        }
      } else if (final == "C") {
        cursor += count
        while (length(line) < cursor) {
          line = line " "
        }
      } else if (final == "G") {
        cursor = count > 0 ? count - 1 : 0
        while (length(line) < cursor) {
          line = line " "
        }
      } else if (final == "K") {
        mode = parts[1] == "" ? 0 : parts[1] + 0
        if (mode == 0) {
          line = substr(line, 1, cursor)
        } else if (mode == 1) {
          line = substr(line, cursor + 1)
          cursor = 0
        } else if (mode == 2) {
          line = ""
          cursor = 0
        }
      }
    }

    function has_stripped_csi(position, remaining) {
      remaining = substr(text, position + 1)
      return remaining ~ /^[0-9;?]+[CDGJKm]/ || (stripped_csi_active && remaining ~ /^K/)
    }

    function parse_csi(position, stripped, params) {
      params = ""
      while (position <= length(text)) {
        ch = substr(text, position, 1)
        if (ch ~ /^[0-9;?]$/) {
          params = params ch
          position++
          continue
        }
        apply_csi(params, ch)
        stripped_csi_active = stripped
        return position
      }
      return position
    }

    BEGIN {
      esc = sprintf("%c", 27)
    }

    {
      text = $0
      gsub(/\\033\[/, esc "[", text)
      gsub(/\\x1[Bb]\[/, esc "[", text)
      gsub(/\\e\[/, esc "[", text)
      text = text "\n"

      for (i = 1; i <= length(text); i++) {
        ch = substr(text, i, 1)

        if (ch == esc) {
          if (substr(text, i + 1, 1) == "[") {
            i = parse_csi(i + 2, 0)
          } else {
            i++
          }
        } else if (ch == "[" && has_stripped_csi(i)) {
          i = parse_csi(i + 1, 1)
        } else if (ch == "\r") {
          cursor = 0
          stripped_csi_active = 0
        } else if (ch == "\b") {
          if (cursor > 0) {
            cursor--
          }
          stripped_csi_active = 0
        } else if (ch == "\n") {
          flush_line()
          stripped_csi_active = 0
        } else {
          write_char(ch)
          stripped_csi_active = 0
        }
      }
    }
  ' "${file_path}"
}

# @purpose: Load the ollama prompt from override variable or editable prompt file.
function load_ollama_prompt() {
  [[ -n "${HHS_OLLAMA_PROMPT:-}" ]] && return 0
  [[ -r "${HHS_OLLAMA_PROMPT_FILE}" ]] || quit 2 "Unable to read ollama prompt file: ${HHS_OLLAMA_PROMPT_FILE}"
  HHS_OLLAMA_PROMPT="$(render_ollama_prompt_template "$(< "${HHS_OLLAMA_PROMPT_FILE}")")"
}

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
        quit 1 "Offline Ollama failed to install."
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
    ${HHS_OLLAMA_MD_VIEWER:-cat} < "${HHS_OLLAMA_HISTORY_FILE}"
    quit 0
  fi

  quit 1 "${RED}Ollama history file not found${NC}"
}

# @purpose: Show main ollama system prompt.
function show_prompt() {
  load_ollama_prompt
  printf "%s\n" "${HHS_OLLAMA_PROMPT}"
  quit 0
}

# @purpose: Clear ollama history file (context)
function clear_context() {
  if [[ -f "${HHS_OLLAMA_HISTORY_FILE}" ]]; then
    : > "${HHS_OLLAMA_HISTORY_FILE}" || quit 2 "Unable to clear ollama history file"
    quit 0 "${GREEN}✨ Ollama history cleared${NC}"
  fi

  quit 0 "${ORANGE}✨ Ollama history file not found${NC}"
}

# @purpose: Return whether a file looks like supported text context.
function is_text_context_file() {
  local file_path="${1}" mime extension

  extension="$(printf "%s" "${file_path##*.}" | tr '[:upper:]' '[:lower:]')"
  case "${extension}" in
    txt|md|markdown|csv|tsv|json|jsonl|yaml|yml|toml|ini|conf|cfg|log|xml|html|css|js|ts)
      return 0
    ;;
    py|sh|bash|zsh|java|kt|go|rs|rb|php|sql)
      return 0
    ;;
  esac

  mime="$(file -b --mime-type "${file_path}" 2>/dev/null || true)"
  [[ "${mime}" == text/* || "${mime}" == "application/json" || "${mime}" == "application/xml" ]]
}

# @purpose: Set ollama history file (context) from a text-based file.
function ingest_context() {
  local file_path="${1}" tmp source_size max_context_bytes

  [[ -n "${file_path}" ]] || usage 1 "Missing context file for --ingest."
  [[ -f "${file_path}" ]] || quit 1 "Context file not found: ${file_path}"
  [[ -r "${file_path}" ]] || quit 1 "Context file is not readable: ${file_path}"
  is_text_context_file "${file_path}" || quit 1 "Only text-based context files are supported."

  mkdir -p "$(dirname "${HHS_OLLAMA_HISTORY_FILE}")" || quit 2 "Unable to prepare ollama history directory"
  tmp="$(mktemp /tmp/hhs-ollama-ingest.XXXXXX)" || quit 2 "Unable to prepare ingest file"
  max_context_bytes=$((kb_size * 1024))
  source_size=$(stat -c %s "${file_path}" 2>/dev/null || wc -c < "${file_path}")

  {
    echo "# Current Ask context"
    echo
    echo "## Started: $(date +%F)"
    echo
    echo "### [$(date '+%H:%M')] User:"
    echo "Ingested context from: ${file_path}"
    echo
    echo '```text'
    if [[ "${source_size}" -gt "${max_context_bytes}" ]]; then
      head -c "${max_context_bytes}" "${file_path}"
      echo
      echo
      echo "[Context truncated to 70% of ${OLLAMA_MODEL} context window; 30% reserved for questions.]"
    else
      cat "${file_path}"
    fi
    echo
    echo '```'
  } > "${tmp}" || quit 2 "Unable to prepare ingested context"

  mv "${tmp}" "${HHS_OLLAMA_HISTORY_FILE}" || quit 2 "Unable to set ollama context"
  quit 0 "${GREEN}✨ Ollama context ingested from ${file_path}${NC}"
}

# @purpose: Ensure ollama history uses the expected Markdown heading hierarchy
function ensure_context_header() {
  local tmp

  mkdir -p "$(dirname "${HHS_OLLAMA_HISTORY_FILE}")" || quit 2 "Unable to prepare ollama history directory"
  touch "${HHS_OLLAMA_HISTORY_FILE}" || quit 2 "Unable to prepare ollama history file"
  tmp="$(mktemp /tmp/hhs-ollama-history.XXXXXX)" || quit 2 "Unable to prepare ollama history formatter"

  awk '
    /^# Current Ask context$/ { next }
    /^### Started:/ { sub(/^###/, "##"); print; next }
    /^## Started:/ { print; next }
    /^# \[[0-9][0-9]:[0-9][0-9]\] (User|AI):/ { sub(/^#/, "###"); print; next }
    /^## \[[0-9][0-9]:[0-9][0-9]\] (User|AI):/ { sub(/^##/, "###"); print; next }
    { print }
  ' "${HHS_OLLAMA_HISTORY_FILE}" > "${tmp}.body" || quit 2 "Unable to format ollama history file"

  {
    echo "# Current Ask context"
    echo
    grep -q '^## Started:' "${tmp}.body" || echo "## Started: $(date +%F)"
    cat "${tmp}.body"
  } > "${tmp}" || quit 2 "Unable to update ollama history file"

  mv "${tmp}" "${HHS_OLLAMA_HISTORY_FILE}" || quit 2 "Unable to replace ollama history file"
  rm -f "${tmp}.body"
}

# @purpose: Show available ollama models (local and for download)
function show_models() {
  echo -e "${BLUE}Available to download:"
  ${HHS_OLLAMA_MD_VIEWER:-cat} < "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/ollama-models.md"
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
    if ! ollama list | tail -n +2 | awk '{print $1}' | grep -Fxq "${model_name}"; then
      if ! ollama pull "${model_name}"; then
        quit 2 "Unable to download ollama model: ${model_name}!"
      fi
    fi

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
  printf "%d:%d" "${ctx}" "$(printf "%s" "(${ctx} * 0.7)/1" | bc)"
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
  local args ans query resp rendered_resp ret_val ctx kb_size ctx_window model hint
  declare -a args=()

  ctx_window=$(get_context_window)
  ctx=${ctx_window%%:*}
  kb_size=${ctx_window#*:}

  ensure_context_size "${kb_size}"
  load_ollama_prompt

  [[ "$#" -eq 0 ]] && usage 1 "No question provided."

  case "$1" in
    -h|--help) usage 0 ;;
    -v|--version) version ;;
    -c|--context) show_context ;;
    -p|--prompt) show_prompt ;;
    -i|--ingest) shift; ingest_context "$1" ;;
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
    quit 1
  }

  # Prepare question from arguments
  for arg in "$@"; do [[ ! "$arg" =~ ^-[a-zA-Z] ]] && args+=("$arg"); done
  query="${args[*]}"

  # Question & Answer
  start_ollama &> /dev/null
  resp="$(mktemp /tmp/hhs-"${OLLAMA_MODEL}"-response.XXXXXX)" || quit 1 "Failed to create temporary file."
  ensure_context_header
  echo -e "### [$(date '+%H:%M')] User: \n${query}" >> "${HHS_OLLAMA_HISTORY_FILE}"
  echo -e "✨ ${GREEN}${OLLAMA_MODEL}[${ctx}K]:\n"
  printf '%s### CONTEXT ###\n%s\n\n### USER INPUT ###\n\n%s\n' \
    "$HHS_OLLAMA_PROMPT" "$CONTEXT" "${query}" |
    ollama run "${OLLAMA_MODEL}" |
    tee -a "${resp}"
  ret_val=${PIPESTATUS[1]}

  # Interpret escape codes and display the response
  if [[ -s "${resp}" ]]; then
    rendered_resp="$(mktemp /tmp/hhs-"${OLLAMA_MODEL}"-rendered.XXXXXX)" || quit 1 "Failed to create rendered response."
    if ! render_ollama_response "${resp}" > "${rendered_resp}"; then
      rm -f "${rendered_resp}" &> /dev/null
      quit 2 "Unable to render ollama response."
    fi
    {
      printf '### [%s] AI: \n' "$(date '+%H:%M')"
      cat "${rendered_resp}"
    } >> "${HHS_OLLAMA_HISTORY_FILE}"
    printf '\033[H\033[2J\033[3J'
    echo -e "✨ ${GREEN}${OLLAMA_MODEL}[${ctx}K]:"
    echo -e "${GRAY}${resp}${NC}"
    ${HHS_OLLAMA_MD_VIEWER:-cat} < "${rendered_resp}"
  else
    echo -e "${ERROR_ICN} ${RED}Ollama failed to respond${NC}"
    ret_val=1
  fi

  # Cleanup
  [[ -f "${rendered_resp:-}" ]] && rm -f "${rendered_resp}" &> /dev/null
  [[ -z "${KEEP}" && -f "${resp}" ]] && rm -f "${resp}" &> /dev/null

  quit "${ret_val}"
}
