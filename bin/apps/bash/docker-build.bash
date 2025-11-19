#!/usr/bin/env bash
# shellcheck disable=2034

#  Script: docker-build.bash
# Purpose: Validate and check information about a provided IP address.
# Created: Mar 20, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current script version.
VERSION=2.0.0

# Application name.
APP_NAME="$(basename "$0")"

# Read folders containing images.
IFS=$'\n'
read -r -d '' -a images < <(find "${HHS_HOME}/docker" -mindepth 1 -type d -exec basename {} \;)
IFS="${OLDIFS}"

USAGE="$(cat <<EOF
usage: ${APP_NAME} [options] <image_type...>
    Build the curated HomeSetup docker images using buildx.
    Can optionally push multi-arch tags after a successful build.

    options:
      -p | --push                   : Push the freshly built images to the registry.
      -h | --help                   : Display this help message and exit.

    arguments:
      image_type                    : One or more image folders from [${images[*]}].

  Notes:
    - Images are built for linux/arm64 and linux/amd64 via buildx.
    - Use --push to publish both tags (amd64/arm64) after building locally.
EOF
)"

declare -a platforms

# Common application functions
[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# We need to load the dotfiles below due to non-interactive shell.
[[ -f "${HOME}"/.bash_commons ]] && source "${HOME}"/.bash_commons


if [[ $# -lt 1 || "${1}" == -h || "${1}" == --help ]]; then
  echo "${USAGE}"
  exit 1
else
  [[ "${1}" == "-p" || "${1}" == "--push" ]] && push_image=1 && shift
  for next_image in "${@}"; do
    # shellcheck disable=SC2199
    if [[ ${images[@]} =~ ${next_image} ]]; then
      image_dir="${HHS_HOME}/docker/${next_image}"
      [[ -d "${image_dir}/" ]] || { __hhs_errcho "${APP_NAME}" "Unable to find directory: ${image_dir}/"; exit 1; }
      # Docker build tag: ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
      echo ''
      echo -e "${PURPLE}Building ${BLUE}[${next_image}-arm64:latest] ... ${NC}"
      echo ''
      if ! docker buildx build --no-cache --progress=plain -t "yorevs/hhs-${next_image}-arm64:latest" \
           --platform linux/arm64/v8 "${image_dir}/"; then
            __hhs_errcho "${APP_NAME}" "Failed to build image: \"${next_image}\" !"
            exit 1
      fi
      echo ''
      echo -e "${PURPLE}Building ${BLUE}[${next_image}-amd64:latest] ... ${NC}"
      echo ''
      if ! docker buildx build --no-cache --progress=plain -t "yorevs/hhs-${next_image}-amd64:latest" \
           --platform linux/amd64 "${image_dir}/"; then
            __hhs_errcho "${APP_NAME}" "Failed to build image: \"${next_image}\" !"
            exit 1
      else
        echo "Finished building \"${next_image}\""
      fi
    else
      __hhs_errcho "${APP_NAME}" "Invalid container type: \"${next_image}\". Please use one of [${images[*]}] !"
      exit 1
    fi
  done
fi

exit 0
