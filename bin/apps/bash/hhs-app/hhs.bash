#!/usr/bin/env bash
# shellcheck disable=SC1090,SC2034

#  Script: hhs.bash
# Purpose: HomeSetup application
# Created: Jan 06, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

APP_NAME="hhs"

# Functions to be unset after quit.
UNSETS+=(
  'main' 'cleanup_plugins' 'parse_args' 'list' 'has_function' 'has_plugin' 'has_command'
  'validate_plugin' 'register_plugins' 'register_functions' 'parse_args' 'has_hhs_function'
  'find_hhs_functions' 'get_desc' 'search_hhs_functions' 'invoke_command' 'display_list'
  'search_hhs_commands'
)

# Program version.
VERSION="1.1.0 built on HomeSetup v${HHS_VERSION}"

# Help message to be displayed by the application.
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} {function | plugin {task} <command>} [args...] [options]

 _   _                      ____       _
| | | | ___  _ __ ___   ___/ ___|  ___| |_ _   _ _ __
| |_| |/ _ \\| '_ \` _ \\ / _ \\___ \\ / _ \ __| | | | '_ \\
|  _  | (_) | | | | | |  __/___) |  __/ |_| |_| | |_) |
|_| |_|\\___/|_| |_| |_|\\___|____/ \\___|\\__|\\__,_| .__/
                                                |_|

  HomeSetup Application Manager v${VERSION}.

    options:
      -v | --version             : Display current program version.
      -h | --help                : Display this help message.
      -p | --prefix              : Display the HomeSetup installation directory.

    arguments:
      function                   : Execute a built-in hhs function.
      plugin                     : Plugin name to invoke.
      task                       : Plugin task such as help, version, or execute.
      command                    : Command to run within the plugin.
      args                       : Command arguments (plugin-specific).

    examples:
      List available plugins and functions:
        => ${APP_NAME} list
      Execute a plugin command:
        => ${APP_NAME} plugin updater execute check
      Show plugin-specific help:
        => ${APP_NAME} plugin ask help

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program/plugin execution failures

  Notes:
    - To discover which plugins and functions are available type: ${APP_NAME} list.

EOF

# Directory containing all HHS plug-ins.
PLUGINS_DIR="$(dirname "${0//${HHS_DIR}/$HHS_HOME}")/apps/${HHS_MY_SHELL//zsh/bash}/hhs-app/plugins"

# Directory containing all local HHS functions.
FUNCTIONS_DIR="$(dirname "${0//${HHS_DIR}/$HHS_HOME}")/apps/${HHS_MY_SHELL//zsh/bash}/hhs-app/functions"

# List of local hhs functions that can be executed.
HHS_APP_FUNCTIONS=()

# List of HomeSetup functions available.
HHS_FUNCTIONS=()

# List of HomeSetup commands available.
HHS_COMMANDS=()

# List of HomeSetup aliases available.
HHS_ALIASES=()

# List of required functions a plugin must have.
PLUGINS_FUNCS=('help' 'cleanup' 'version' 'execute')

# List of valid plugins.
PLUGINS_LIST=()

# List plugin commands.
PLUGINS=()

# When set to non-zero indicates input is being piped.
IS_PIPED=

# @purpose: Checks whether a plugin is registered or not.
# @param $1 [Req] : The plugin name.
function has_function() {

  if [[ -n "${1}" ]] && list_contains "${HHS_APP_FUNCTIONS[*]}" "${1}"; then
    return 0
  fi

  return 1
}

# @purpose: Checks whether a plugin is registered or not.
# @param $1 [Req] : The plugin name.
function has_plugin() {

  echo "${PLUGINS[*]}"
  if [[ -n "${1}" ]] && list_contains "${PLUGINS[*]}" "${1}"; then
    return 0
  fi

  return 1
}

# @purpose: Checks whether a plugin contains the command or not
# @param $1 [Req] : The command name.
function has_command() {

  if [[ -n "${1}" ]] && list_contains "${PLUGINS_FUNCS[*]}" "${1}"; then
    return 0
  fi

  return 1
}

# @purpose: Checks whether the command matches a __hhs function or not and invoke it.
# @param $1..$N [Req] : The command line arguments.
function invoke_hhs_function() {
  local args=("$@") max_words=5 joined

  search_hhs_commands

  # Loop to form combinations starting from max_words down to 1
  for ((i = (max_words < ${#args[@]}) ? max_words : ${#args[@]}; i > 0; i--)); do
      # Wrap to a probable '__hhs' command
      joined="__hhs_$(printf "%s_" "${args[@]:0:i}" | sed 's/_$//')"
      if [[ " ${HHS_COMMANDS[*]} " =~ (^|[[:space:]])${joined}([[:space:]]|$) ]]; then
         # Invoke the matched command with remaining arguments
        if __hhs_has "${joined}"; then
          "${joined}" "${args[@]:i}"
          exit $?
        fi
      fi
  done

  return 1
}

# @purpose: Validates if the plugin contains the required hhs application plugin structure
# @param $1 [Req] : Array of plugin functions.
function validate_plugin() {

  local i=0 j=0 plg_funcs=("$@")

  while [[ "$i" -lt "${#PLUGINS_FUNCS[@]}" ]]; do
    if [[ "${plg_funcs[j]}" == "${PLUGINS_FUNCS[i]}" ]]; then
      ((i += 1))
      j=0
      [[ $i == "${#PLUGINS_FUNCS[@]}" ]] && return 0
    else
      ((j += 1))
      [[ $j == "${#plg_funcs[@]}" ]] && return 1
    fi
  done

  return 1
}

# @purpose: Search and register all hhs application plugins
function register_plugins() {

  local fn_line plg_funcs=() plg_name

  IFS=$'\n'
  while read -r plugin; do
    while read -r fnc; do
      fn_line="${fnc##function }"
      fn_line="${fn_line%\(\) \{}"
      plg_funcs+=("${fn_line}")
    done < <(grep '^function .*()' <"${plugin}")
    if ! validate_plugin "${plg_funcs[@]}"; then
      INVALID+=("$(basename "${plugin}")")
    else
      plg_name=$(basename "${plugin%.*}")
      PLUGINS+=("${plg_name}")
      PLUGINS_LIST+=("${plugin}")
    fi
  done < <(find "${PLUGINS_DIR}" -maxdepth 2 -type f -iname "*.${HHS_MY_SHELL}")
  IFS="${OLDIFS}"

  return 0
}

# @purpose: Read all internal functions and make them available to use
function register_functions() {

  local fn_line

  IFS=$'\n'
  while read -r fnc_file; do
    source "${fnc_file}"
    while read -r fnc; do
      fn_line="${fnc##function }"
      fn_line="${fn_line%\(\) \{}"
      HHS_APP_FUNCTIONS+=("${fn_line}")
    done < <(grep '^function .*()' <"${fnc_file}")
    # Register the functions to be unset when program quits
    UNSETS+=("${HHS_APP_FUNCTIONS[@]}")
  done < <(find "${FUNCTIONS_DIR}" -maxdepth 1 -type f -name '*.bash')
  IFS="${OLDIFS}"

  return 0
}

# @purpose: Invoke the plugin command
# @param $1 [Req] : The plug-in name.
# @param $2..$N [Req] : The plug-in arguments.
function invoke_plugin() {

  local plg_cmd="${1}" ret

  has_plugin "${plg_cmd}" || command_hint "Plugin/Function/Command not found: \"${STRIKE}${plg_cmd}${NC}\"" "${@}"
  shift

  for idx in "${!PLUGINS[@]}"; do
    if [[ "${PLUGINS[idx]}" == "${plg_cmd}" ]]; then
      [[ -s "${PLUGINS_LIST[idx]}" ]] || quit 1
      source "${PLUGINS_LIST[idx]}"
      plg_cmd="${1:-execute}"
      has_command "${plg_cmd}" || command_hint  "Command not available: \"${STRIKE}${plg_cmd}${NC}\"" "${@}"
      shift
      ${plg_cmd} "${@}"  # Execute the specified plugin
      ret=${?}
      cleanup
      exit ${ret}
    else
      [[ $((idx + 1)) -eq ${#PLUGINS[@]} ]] && quit 255
    fi
  done

  ret=${?}
  [[ ${ret} -eq 255 ]] && command_hint "Plugin/Function/Command not found: \"${STRIKE}${plg_cmd}${NC}\"" "${@}"

  return ${ret}
}

# ------------------------------------------
# Local functions

# Functions MUST start with 'function' keyword and
# MUST quit <exit_code> with the proper exit code

# @purpose: Get the description of a function/plug-in or alias from `function' line.
# @param $1 [Req] : The function definition line.
function get_desc() {

  local path filename line_num re

  path=$(awk -F ':function' '{print $1}'  <<<"${1}")
  filename=$(awk -F '.bash:' '{print $1}'  <<<"${path}")
  line_num=$(awk -F '.bash:' '{print $2}'  <<<"${path}")
  line_num=${line_num// /}
  re='^ *(# @(function|purpose|alias):) '

  for i in $(seq "${line_num}" -1 1); do
    line=$(sed -n "${i}p" "${filename}.bash")
    if [[ ${line} =~ ${re} ]]; then
      desc="${line//${BASH_REMATCH[1]}/}"
      desc=$(echo "${desc}" | awk '{$1=$1};1')
      [[ $line =~ $re ]] && echo "${desc}" && break
    fi
  done
}

# @purpose: Search for all hhs-commands from compgen. Remove the aliases from the list.
function search_hhs_commands() {
  local commands aliases

  IFS=$'\n' read -r -d '' -a aliases < <(alias -p | grep '^alias __hhs' | sed -E 's/^alias ([^=]+)=.*/\1/')
  aliases+=('__hhs')

  # Use `compgen` to get all `__hhs` commands, excluding those in `aliases`
  IFS=$'\n' read -r -d '' -a commands < <(compgen -c __hhs | awk -v aliases="${aliases[*]}" '
    BEGIN {
      # Split aliases into an array for exclusion
      split(aliases, alias_array)
      for (i in alias_array) alias_map[alias_array[i]] = 1
    }
    !($0 in alias_map)  # Only include commands not in alias_map
  ')

  HHS_COMMANDS+=("${commands[@]}")
  HHS_ALIASES+=("${aliases[@]}")
}

# @purpose: Search for all hhs-functions and make them available to use.
# @param $1..$N [Req] : The directories to search from.
function search_hhs_functions() {

  local all_hhs_fn filename fn_name desc

  IFS=$'\n' read -r -d '' -a all_hhs_fn < \
    <(grep -nR "^\( *function *__hhs_\)" "${@}" | sed -E 's/: +/:/' | awk 'NR != 0 {print $1" "$2}' | sort | uniq)
  for fn_line in "${all_hhs_fn[@]}"; do
    filename=$(basename "${fn_line}" | awk -F ':function ' '{print $1}')
    filename=$(printf '%-35.35s' "${filename}")
    fn_name=$(awk -F ':function ' '{print $2}' <<<"${fn_line}")
    fn_name=$(printf '%-35.35s' "${fn_name//\(\)/}")
    desc=$(get_desc "${fn_line}")
    HHS_FUNCTIONS+=("${BLUE}${filename// /.} ${GREEN} ${NC}${fn_name// /.} : ${YELLOW}${desc}")
  done
  IFS="${OLDIFS}"

  return 0
}

# @purpose: Get a list, display it in columns according to the terminal width.
# @param: $1 [Req] : The list title
# @param $2..$N [Req] : The array list
function display_list() {
    local title items columns max_width num_columns keep=0

    [[ "${1}" == "-k" || "${1}" == "--keep" ]] && keep=1 && shift

    title="${1}"

    shift
    items=("$@")
    columns=$(tput cols)  # Get terminal width

    if [[ $keep -ne 1 ]]; then
      # Remove '__hhs_' prefix and replace '_' with ' ' in each item
      for i in "${!items[@]}"; do
          items[$i]="${items[$i]//__hhs_/}"   # Remove prefix
          items[$i]="${items[$i]//_/ }"       # Replace underscores with spaces
      done
    fi

    # Calculate max item length + padding
    max_width=$(printf "%s\n" "${items[@]}" | awk '{ if (length > max) max = length } END { print max + 2 }')

    # Determine number of columns that can fit in the terminal
    num_columns=$((columns / (max_width + 5) - 1))
    num_columns=$((num_columns > 0 ? num_columns : 1))  # Ensure at least one column

    echo -e "${ORANGE}${title}${NC}"

    # Print each item with its index in columns
    printf "%s\n" "${items[@]}" | awk -v cols="${num_columns}" -v width="${max_width}" '
    {
        printf "\033[33;1m%4d\033[m. \033[34;1m%-*s\033[m", NR, width, $0  # Print index followed by item
        if (NR % cols == 0) print ""  # Newline after every full row
    }
    END {
        if (NR % cols != 0) print ""  # Ensure proper formatting for partial rows
    }'
    echo ''
}

# @purpose: Display an error message and suggest similar commands based on partial user input.
# @param $1 [Req]: The error message to display.
# @param $2..$N [Req]: The partial command the user entered.
function command_hint() {
    local error_message="$1" user_input commands matches=() search_string index=1
    shift

    user_input=("$@")
    commands=("${PLUGINS[@]}" "${HHS_APP_FUNCTIONS[@]}" "${HHS_COMMANDS[@]}")

    # Try to match commands by progressively reducing the user input words from the end
    while (( ${#user_input[@]} > 0 )); do
        # Join the current user_input array into a single search string
        search_string="__hhs_${user_input[*]}"
        search_string="${search_string// /_}"
        matches=()  # Clear matches for each iteration

        # Find commands that contain the search_string as a substring
        for cmd in "${commands[@]}"; do
            [[ "$cmd" == *"${search_string}"* ]] && matches+=("$cmd")
        done

        # If matches are found, stop reducing the input further
        (( ${#matches[@]} > 0 )) && break

        # Remove the last word from user_input and try again
        unset 'user_input[-1]' &>/dev/null || break
    done

    # Display error message and matching commands or a fallback message if no matches
    __hhs_errcho "${APP_NAME}" "${error_message}\n"

    if (( ${#matches[@]} > 0 )); then
        echo -e "${YELLOW}${TIP_ICON} Tip: Did you mean one of these?${NC}\n"
        for match in "${matches[@]}"; do
          match="${match//__hhs_/}"
          printf "%3d. ${BLUE}%s${NC}\n" "$index" "hhs ${match//_/ }"
          ((index++))
        done
        quit 0 ' '
    fi
    echo -e "${YELLOW}${TIP_ICON} Tip: Type 'hhs list' to find out options.${NC}"

    quit 1  # Exit with an error
}

# ------------------------------------------
# Basics

# @purpose: Parse command line arguments
function parse_args() {

  # If not enough arguments is passed, display usage message.
  if [[ ${#} -eq 0 ]]; then
    usage 0
  fi

  # Loop through the command line options.
  # Short opts: -<C>, Long opts: --<Word>
  while [[ ${#} -gt 0 ]]; do
    case "${1}" in
      -h | --help)
        usage 0
        ;;
      -v | --version)
        version
        ;;
      -p | --prefix)
        echo ''
        echo -e "${HHS_HIGHLIGHT_COLOR}  HomeSetup Version: ${WHITE}${HHS_VERSION}${NC}"
        echo -e "${HHS_HIGHLIGHT_COLOR}Installation Prefix: ${WHITE}${HHS_HOME}${NC}"
        echo -e "${HHS_HIGHLIGHT_COLOR}    HomeSetup Files: ${WHITE}${HHS_DIR}${NC}"
        echo ''
        quit 0
        ;;
      *)
        break
        ;;
    esac
    shift
  done
}

# @purpose: Cleanup plugin functions.
function cleanup_plugins() {
  unset -f "${PLUGINS_FUNCS[@]}"
}

# @purpose: Program entry point.
function main() {

  local fn_name="${1}"

  # enable history in a non-interactive shell.
  history -r "${HISTFILE}"

  # Lazy load application commons.
  source "${HHS_DIR}/bin/app-commons.bash"

  # Execute a cleanup after the application has exited.
  trap cleanup_plugins EXIT

  # Check and invoke any matching '__hhs' function
  invoke_hhs_function "${@}"

  parse_args "${@}"
  register_functions
  register_plugins


  if has_function "${fn_name}"; then
    shift
    ${fn_name} "${@}"  # Invoke internal hhs-function
    quit $?
  fi

  [[ ${#INVALID[@]} -gt 0 ]] && quit 1 "Invalid plugins found: [${INVALID[*]}]"

  fn_name="${fn_name//help/list}"
  invoke_plugin "${@}" || quit 2

  quit 255 "Failed to invoke hhs command: ${*}"
}

if [[ -t 0 ]]; then
  IS_PIPED=0
else
  IS_PIPED=1
fi

main "${@}"
quit 1
