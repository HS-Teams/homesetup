#!/usr/bin/env bash

#  Script: term.bash
# Purpose: Contains HHS-App terminal related functions.
# Created: Apr 29, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# @purpose: Retrieve/Get/Set the current hostname.
# @param $1 [opt] : The new hostname. If not provided, current hostname is retrieved.
function host-name() {

  local cur_hostname new_hostname ret

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo -e "usage: ${FUNCNAME[0]} [new_hostname]"
  elif [[ -z "${1}" ]]; then
    cur_hostname=$(hostname)
    [[ $ret -eq 0 ]] && echo -e "${GREEN}Your current hostname is: ${HHS_HIGHLIGHT_COLOR}$(cur_hostname)${NC}"
    quit 0
  else
    if __hhs_has hostname; then
      cur_hostname=$(hostname)
      new_hostname="${1}"
      [[ -z "${new_hostname}" ]] && read -r -p "${YELLOW}Enter new hostname (ENTER to cancel): ${NC}" new_hostname
      if [[ -n "${new_hostname}" && "${cur_hostname}" != "${new_hostname}" ]]; then
        if [[ "$(uname -s)" == "Darwin" ]]; then
          if sudo scutil --set HostName "${new_hostname}"; then
            echo "${GREEN}Your new hostname has changed from \"${cur_hostname}\" to ${PURPLE}\"${new_hostname}\" ${NC} !"
          else
            quit 2 "Failed to change your hostname !"
          fi
        else
          # Change the hostname in /etc/hosts & /etc/hostname
          if sudo esed "s/${cur_hostname}/${new_hostname}/g" /etc/hosts &&
             sudo esed "s/${cur_hostname}/${new_hostname}/g" /etc/hostname; then
            echo "${GREEN}Your new hostname has changed from \"${cur_hostname}\" to ${PURPLE}\"${new_hostname}\" ${NC} !"
            read -rn 1 -p "${YELLOW}Press 'y' key to reboot now: ${NC}" ANS
            if [[ "$ANS" == "y" || "$ANS" == "Y" ]]; then
              sudo reboot
            fi
          else
            quit 2 "Failed to change your hostname !"
          fi
        fi
      else
        echo "${ORANGE}Your hostname hasn't changed !${NC}" && quit 2
      fi
    else
      quit 1 "You need 'hostname' installed to use this function !"
    fi
  fi

  quit 0
}

# @purpose: Set/Unset shell options.
function shopts() {

  local mchoose_file title sel_options name option item all_items=()

  while read -r option; do
    name="${option%%=*}" && value="${option#*=}"
    all_items+=("${name// /}=${value// /}")
  done <"${HHS_SHOPTS_FILE}"

  title="${BLUE}Terminal Options${ORANGE}\n"
  title+="Please check the desired terminal options:"
  mchoose_file=$(mktemp)

  if __hhs_mchoose "${mchoose_file}" "${title}" "${all_items[@]}"; then
    read -r -d '' -a sel_options < <(grep . "${mchoose_file}")
    for item in "${all_items[@]}"; do
      option="${item%%=*}"
      if list_contains "${sel_options[*]}" "${option}"; then
        shopt -s "${option}"
      else
        shopt -u "${option}"
      fi
    done
    \rm -f "${mchoose_file}"&>/dev/null
    \shopt | awk '{print $1" = "$2}' >"${HHS_SHOPTS_FILE}" ||
      quit 2 "Unable to create the Shell Options file !"
  fi

  quit 0
}

# @purpose: Display HomeSetup shortcuts/cheatsheets.
function sheets() {
  local filters=("${@}") all_files all_sheets=() mselect_file sel_sheet filter_re mselect_file sheet
  local cheatsheets_dir="${HHS_HOME}/docs/misc/cheatsheets"

  # shellcheck disable=SC2207,SC2211
  all_files=( $(find "${cheatsheets_dir}" -type f -iname "*.*") )
  for file in "${all_files[@]}"; do
    sheet=$(basename "${file}")
    sheet_name=$(echo "${sheet}" | sed 's/\.[^.]*$//' | tr '-' ' ' | awk '{for(i=1;i<=NF;i++){$i=toupper(substr($i,1,1)) substr($i,2)}; print}')
    filter_re=".*${filters[*]// /|}.*"
    shopt -s nocasematch
    if [[ -z "${filters[*]}" || ${sheet} =~ ${filter_re} || ${sheet_name,,} =~ ${filter_re} ]]; then
      all_sheets+=( "${sheet}" )
    fi
    shopt -u nocasematch
  done

  mselect_file=$(mktemp)
  if __hhs_mselect "${mselect_file}" "Available Cheatsheets (${filter_re}):" "${all_sheets[@]}"; then
    sel_sheet=$(grep . "${mselect_file}")
    sel_file="${cheatsheets_dir}/${sel_sheet}"
    if __hhs_has glow && [[ ${sel_sheet#*.} =~ [Mm][Dd] ]]; then
      glow --style "auto" --mouse --pager --width 120 --all "${sel_file}"
    elif [[ ${sel_sheet#*.} =~ [Pp][Dd][Ff] ]]; then
      open "${sel_file}"
    elif __hhs_has bat; then
      bat --theme "auto" --paging=always --terminal-width=120 "${sel_file}"
    else
      cat "${cheatsheets_dir}/${sel_sheet}"
    fi
    echo ''
    return 0
  fi

  return 1
}

# @purpose: Create symbolic links of HomeSetup scripts into HHS_DIR/bin folder.
# @param $1..$N : Source files/dirs to be linked.
function link() {
  local -a src bash_sources=() next dest

  read -r -a src <<< "${*}"

  [[ "${#src[@]}" -eq 0 || -z "${HHS_DIR}" || $1 =~ -h|--help ]] &&
    quit 1 "usage: ${FUNCNAME[0]} <files/dirs...>"

  echo -e "${BLUE}Creating symbolic links of HomeSetup scripts into '${HHS_DIR}/bin' folder...${NC}"

  while read -r next; do
    if [[ -d "${next}" ]]; then
      echo -e "${BLUE} Processing directory: '${next}'...${NC}"
      while IFS= read -r f; do
        bash_sources+=("$(pwd)/$f")
      done < <(find "${next}" -type f \( -name '*.sh' -o -name '*.bash' -o -name '*.zsh' \))
      continue
    elif [[ ! -f "${next}" ]]; then
      echo -e "${YELLOW} Warning: '${next}' is not a valid file or directory. Skipping...${NC}"
      continue
    fi
    echo -e "${BLUE} Processing file: '${next}'...${NC}"
    bash_sources+=("$(pwd)/${next}")
  done < <(printf '%s\n' "${src[@]}")

  echo -e "${BLUE}Total files to be linked: ${#bash_sources[@]}\n"

  for next in "${bash_sources[@]}"; do
    dest="${HHS_DIR}/bin/$(basename "${next}")"

    if [[ -e "${dest}" || -L "${dest}" ]]; then
      echo -e "${YELLOW} Warning: '${dest}' already exists. It will be replaced.${NC}"
      \rm -f "${dest}" || quit 4 "Failed to remove '${dest}'"
    elif [[ -f "${dest}" ]]; then
      quit 2 "Destination '${dest}' already exists and is not a symlink!"
    fi

    if \ln -sf "${next}" "${HHS_DIR}/bin"; then
      echo -e "${GREEN}Symlink created: '${next}'  '${dest}'${NC}"
    else
      quit 2 "Failed to symlink '${next}'"
    fi
  done

  quit 0
}
