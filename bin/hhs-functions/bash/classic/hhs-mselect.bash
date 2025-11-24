#!/usr/bin/env bash

#  Script: hhs-mselect.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: yorevs@hotmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Select an option from a list using a navigable menu.
# @param $1 [Req] : The response file.
# @param $3 [Req] : The array of items.
function __hhs_classic_mselect() {

  local outfile title ret_val=1 all_options=() sel_index=0 show_from=0 re_render=1 selector
  local index_len len show_to diff_index typed_index max_columns option_line col_offset=8

  if [[ $# -eq 0 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <output_file> <title> <items...>"
    echo ''
    echo '    Arguments: '
    echo '      output_file : The output file where the result will be stored.'
    echo '            title : The text to be displayed before rendering the items.'
    echo '            items : The items to be displayed for selecting.'
    echo ''
    echo '    Examples: '
    echo '      Select a number from 1 to 100:'
    echo "        => ${FUNCNAME[0]} /tmp/out.txt {1..100} && cat /tmp/out.txt"
    echo ''
    echo '  Notes: '
    echo '    - If only one option is available, mselect will select it and return.'
    echo '    - A temporary file is suggested to used with this command: $ mktemp.'
    echo '    - The outfile must not exist or it be an empty file.'
    return 1
  fi

  HHS_HIGHLIGHT_COLOR=${HHS_HIGHLIGHT_COLOR:-${CYAN}}
  HHS_TUI_MAX_ROWS=${HHS_TUI_MAX_ROWS:=10}
  outfile="${1}" && shift
  title="${1}" && shift
  show_to="$((HHS_TUI_MAX_ROWS - 1))"
  diff_index="$((show_to - show_from))"
  all_options=("${@}")
  len=${#all_options[*]}
  max_columns="$(($(tput cols) - col_offset))"

  # When only one option is provided, select the typed_index 0 and return
  [[ "$len" -eq 1 ]] && echo "0" >"$outfile" && return 0

  tput rmam
  echo -e "\033[2J"
  echo -e "\033[H${ORANGE}${title}${NC}\033[K"
  tput sc

  while :; do

    # Menu Renderization {
    if [[ -n "$re_render" ]]; then
      tput civis
      # Restore the cursor to the home position
      tput rc
      echo -e "${NC}"
      for idx in $(seq "${show_from}" "${show_to}"); do
        selector=' '
        [[ $idx -ge $len ]] && break # When the number of items is lower than the max rows, skip the other lines
        option_line="${all_options[idx]:0:$max_columns}"
        # Erase current line before repaint
        echo -ne "\033[2K\r"
        [[ $idx -eq $sel_index ]] && echo -en "${HHS_HIGHLIGHT_COLOR}" && selector="${POINTER_ICN}"
        printf "  %${#len}s  %0.4b  %s" "$((idx + 1))" "${selector}" "${option_line}"
        # Check if the text fits the screen and print it, otherwise print '...'
        [[ ${#option_line} -ge $max_columns ]] && echo -en "\033[4D\033[K..."
        echo -e "${NC}"
      done
      echo ''
      echo -ne "${YELLOW}[Enter] Accept  [↑↓] Navigate  [Space] Mark  [I] Invert  [Esc] Quit  [1..${len:0:5}] Goto: \033[K${NC}"
      unset re_render
      tput cnorm
    fi
    # } Menu Renderization

    # Navigation input {
    IFS= read -rsn 1 keypress
    case "${keypress}" in
    [[:digit:]]) # An index was typed
      typed_index="${keypress}"
      echo -en "${keypress}" && index_len=1
      while [[ ${#typed_index} -lt ${#len} ]]; do
        read -rs -n 1 numpress
        [[ -z "${numpress}" ]] && break
        [[ ! "${numpress}" =~ ^[0-9]*$ ]] && unset typed_index && break
        typed_index="${typed_index}${numpress}"
        echo -en "${numpress}" && index_len=$((index_len + 1))
      done
      echo -ne "\033[${index_len}D\033[K"
      if [[ $typed_index -ge 1 && $typed_index -le $len ]]; then
        show_to=$((typed_index - 1))
        [[ $show_to -le $diff_index ]] && show_to=$diff_index
        show_from=$((show_to - diff_index))
        sel_index=$((typed_index - 1)) && re_render=1
      fi
      ;;
    $'\033') # Handle escape '\e[nX' codes
      IFS= read -rsn2 -t 1 keypress
      case "${keypress}" in
      [A) # Cursor up
        if [[ $sel_index -eq $show_from && $show_from -gt 0 ]]; then
          show_from=$((show_from - 1))
          show_to=$((show_to - 1))
        elif [[ $sel_index -eq 0 ]]; then
          continue
        fi
        if [[ $((sel_index - 1)) -ge 0 ]]; then
          sel_index=$((sel_index - 1)) && re_render=1
        fi
        ;;
      [B) # Cursor down
        if [[ $sel_index -eq $show_to && $((show_to + 1)) -lt $len ]]; then
          show_from=$((show_from + 1))
          show_to=$((show_to + 1))
        elif [[ $((sel_index + 1)) -ge $len ]]; then
          continue
        fi
        if [[ $((sel_index + 1)) -lt $len ]]; then
          sel_index=$((sel_index + 1)) && re_render=1
        fi
        ;;
      *)
        ret_val=127
        echo -e "\n${NC}"
        break
        ;;
      esac
      ;;
    $'') # Keep the current index and exit
      ret_val=0
      echo ''
      break
      ;;
    esac
    # } Navigation input

  done

  [[ ${ret_val} -eq 0 ]] && echo "${all_options[sel_index]}" >"$outfile"

  return ${ret_val}
}
