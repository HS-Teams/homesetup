#!/usr/bin/env bash
#
# Script Name: video-gen.bash
# Purpose: Extracts last frames, renames sequentially (zero-padded),
#          applies optional crossfades, concatenates videos, logs,
#          and provides detailed summaries.
# Created Date: Oct 26, 2025
# Author: yorevs
# Required Packages: ffmpeg, ffprobe, unzip, awk, stat
# Powered by: https://github.com/yorevs/homesetup
# GPT: https://chatgpt.com/g/g-ra0RVB9Jo-homesetup-script-generator
#

# https://semver.org/ ; major.minor.patch
VERSION="0.3.4"

# The default crossfade duration in seconds
CROSSFADE_DURATION=0.3

# The source directory or zip file
SOURCE="."

# The final video output file name
OUTFILE="output.mp4"

# Whether to force overwrite existing video output
FORCE=

# Whether to recreate videos.txt
RECREATE=false

# Array of spinner frames for progress indication
SPINNER_FRAMES=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")

# Control flags for spinner:Stop
SPINNER_STOP=false

# Control flags for spinner:Pause
SPINNER_PAUSED=false

# Offset from the end of the video to extract the last frame (in seconds)
LAST_FRAME_OFFSET=-0.05

# @purpose: Show script usage information.
usage() {
  cat <<EOF
Usage: $(basename "$0") [-s <source>] [-o <output>] [-f] [-r] [-x [seconds]] [-h] [-v]
EOF
}

# @purpose: Display script version number.
version() {
  echo "$(basename "$0") version ${VERSION}";
}

# @purpose: Handle cleanup on interrupt signals.
cleanup() {
  SPINNER_STOP=true
  echo -e "\n\033[33m[WARNING]\033[m Interrupted."
  exit 0
}
trap cleanup SIGINT SIGABRT

# @purpose: Parse CLI arguments for the script.
# @param $1..$N [Opt]: Command-line options and their values.
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
    -s | --source)
      SOURCE="${2:-.}"
      shift 2
      ;;
    -o | --outfile)
      OUTFILE="${2:-output.mp4}"
      shift 2
      ;;
    -f | --force-overwrite)
      FORCE='-y'
      shift
      ;;
    -r | --recreate)
      RECREATE=true
      shift
      ;;
    -x | --cross-fade)
      if [[ "$2" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        CROSSFADE_DURATION="$2"
        shift 2
      else
        CROSSFADE_DURATION=0.3
        shift
      fi
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    -v | --version)
      version
      exit 0
      ;;
    *)
      echo -e "\033[31m[ERROR]\033[m Unknown option: $1"
      exit 2
      ;;
    esac
  done
}

# @purpose: Ensure required tools are installed.
require_tools() {
  for cmd in ffmpeg ffprobe unzip; do
    command -v "$cmd" >/dev/null 2>&1 || {
      echo -e "\033[31m[ERROR]\033[m Missing $cmd"
      exit 1
    }
  done
}

# @purpose: Retrieve the duration (in seconds) of a video.
# @param $1 [Req]: Path to the video file.
get_duration() {
  ffprobe -v error -show_entries format=duration -of csv=p=0 "$1" 2>/dev/null;
}

# @purpose: Convert seconds into HH:MM:SS format.
# @param $1 [Req]: Duration in seconds.
format_time() {
  local d
  d=$(printf "%.0f" "$1")
  printf "%02d:%02d:%02d" $((d / 3600)) $((d % 3600 / 60)) $((d % 60))
}

# @purpose: Preserve file timestamps (both access and modify) in a portable way.
# @param $1 [Req]: Source file path.
# @param $2 [Req]: Destination file path.
preserve_timestamps() {
  local src="$1" dst="$2"
  [[ -e "$src" && -e "$dst" ]] || return 0
  if [[ "$OSTYPE" == "darwin"* ]]; then
    local atime mtime
    atime=$(stat -f "%a" "$src")
    mtime=$(stat -f "%m" "$src")
    touch -a -t "$(date -r "$atime" +"%Y%m%d%H%M.%S")" "$dst"
    touch -m -t "$(date -r "$mtime" +"%Y%m%d%H%M.%S")" "$dst"
  else touch -amr "$src" "$dst" 2>/dev/null || true; fi
}

# @purpose: Sanitize leftover last-frame images, keeping only the most recent by name, then timestamp.
sanitize_last_frames() {
  local best_frame="" best_score=-1
  mapfile -t last_frames < <(find "${WORKDIR}" -maxdepth 1 -type f \( -iname "*-last.jpg" -o -iname "*-last.jpeg" \))

  [[ ${#last_frames[@]} -le 1 ]] && return 0

  for img in "${last_frames[@]}"; do
    # Extract numeric value from name (e.g., part-003-last.jpg → 3)
    filename=$(basename "$img")
    num=$(echo "$filename" | grep -oE '[0-9]+' | tail -1)
    [[ -z "$num" ]] && num=0

    # Get modification time in epoch
    mod_time=$(stat -c %Y "$img" 2>/dev/null || stat -f %m "$img")

    # Calculate a score: 1000000 * name-based-num + mod_time
    score=$((10#$num * 1000000 + mod_time))

    if (( score > best_score )); then
      best_score=$score
      best_frame="$img"
    fi
  done

  for img in "${last_frames[@]}"; do
    [[ "$img" == "$best_frame" ]] && continue
    rm -f "$img" 2>/dev/null
  done

  log_message INFO "Sanitized last-frame images — kept: $(basename "$best_frame")"
}

# @purpose: Unified logging function with colored labels.
# @param $1 [Req]: Log level (INFO, ERROR, SUCCESS, etc.).
# @param $2..$N [Req]: Message text to log.
log_message() {
  local level="$1"
  shift
  local msg="$*"
  SPINNER_PAUSED=true
  echo -ne "\033[2K\r"
  case "$level" in
  INFO | SUCCESS | ADD) color="\033[34m[INFO]\033[m" ;;
  SKIPPED) color="\033[33m[SKIPPED]\033[m" ;;
  ERROR) color="\033[31m[ERROR]\033[m" ;;
  SUMMARY) color="\033[36m[SUMMARY]\033[m" ;;
  *) color="\033[36m[$(echo "$level" | tr '[:lower:]' '[:upper:]')]\033[m" ;;
  esac
  echo -e "${color} ${msg}"
  SPINNER_PAUSED=false
}

# @purpose: Display a live progress spinner with elapsed time.
spinner_progress() {
  local s=$SECONDS i=0
  while [[ "${SPINNER_STOP}" != true ]]; do
    [[ "${SPINNER_PAUSED}" == false ]] && {
      local e=$((SECONDS - s))
      echo -ne "\r\033[34m${SPINNER_FRAMES[$((i % 10))]}\033[m \033[32mRunning...\033[m ($(format_time "$e"))"
      ((i++))
    }
    sleep 0.1
  done
}

# @purpose: Prepare the working directory or extract a zip file.
prepare_source() {
  if [[ "${SOURCE}" == *.zip ]]; then
    WORKDIR="${SOURCE%.zip}"; LOG_FILE="${WORKDIR}/video-gen-err.log"
    mkdir -p "${WORKDIR}"
    log_message INFO "Extracting zip '${SOURCE}' → '${WORKDIR}'..."
    unzip -jo "${SOURCE}" -x "*/.*" -d "${WORKDIR}" >>"${LOG_FILE}" 2>&1
    log_message INFO "Extracted contents to ${WORKDIR}"
  else
    WORKDIR="${SOURCE}"; LOG_FILE="${WORKDIR}/video-gen-err.log"
  fi
}

# @purpose: Determine the next available numeric sequence for part files.
get_next_part_number() {
  local last_part
  last_part=$(find "${WORKDIR}" -maxdepth 1 -type f -name "part-[0-9]*.mp4" | sed -E 's/.*part-(0*([0-9]+)-{0,1})+\.mp4/\1/' | sort -n | tail -1)
  [[ -z "$last_part" ]] && echo "1" || echo $((10#$last_part + 1))
}

# @purpose: Perform crossfade by preprocessing each part with fade-in/out, then chaining with xfade.
cross_fade() {
  if (($(echo "$CROSSFADE_DURATION <= 0" | bc -l))); then
    log_message INFO "Crossfading disabled (CROSSFADE_DURATION=${CROSSFADE_DURATION})"
    log_message INFO "Concatenating videos without crossfade..."
    ffmpeg -nostdin -f concat -safe 0 -i "${VIDEOS_TXT}" -c copy ${FORCE} "${OUTFILE_PATH}" >>"${LOG_FILE}" 2>&1
    if [[ $? -eq 0 && -s "${OUTFILE_PATH}" ]]; then
      log_message SUCCESS "Created ${OUTFILE_PATH} successfully (no crossfade)"
    else
      log_message ERROR "Concatenation failed (no crossfade)"
    fi
    return 0
  fi

  log_message INFO "Preprocessing videos with fade-in/out..."

  mapfile -t files < <(grep "^file '" "${VIDEOS_TXT}" | sed -E "s/file '(.+)'/\1/")

  local count=${#files[@]}
  [[ $count -lt 2 ]] && {
    log_message SKIPPED "Crossfade skipped (need at least 2 videos)"
    return 0
  }

  local fade_files=()
  for i in "${!files[@]}"; do
    local input="${WORKDIR}/${files[$i]}"
    local output="${WORKDIR}/xfade_part_${i}.mp4"
    local dur
    dur=$(get_duration "$input")
    [[ -z "$dur" || "$dur" == "N/A" ]] && {
      log_message ERROR "Could not get duration for $input"
      continue
    }

    local fade_out_start
    fade_out_start=$(awk -v d="$dur" -v x="$CROSSFADE_DURATION" 'BEGIN{print (d > x ? d - x : 0)}')

    ffmpeg -nostdin -y -loglevel error -i "$input" -filter_complex \
      "fade=t=in:st=0:d=${CROSSFADE_DURATION},fade=t=out:st=${fade_out_start}:d=${CROSSFADE_DURATION}" \
      -c:v libx264 -crf 18 -preset veryfast -c:a aac -b:a 192k "$output" >>"${LOG_FILE}" 2>&1

    if [[ -s "$output" ]]; then
      fade_files+=("$output")
      log_message INFO "Created faded: $(basename "$output")"
    else
      log_message ERROR "Failed to fade: $input"
    fi
  done

  [[ ${#fade_files[@]} -lt 2 ]] && {
    log_message ERROR "Not enough fade-processed videos for crossfade."
    return 1
  }

  log_message INFO "Building crossfade filter chain..."

  # Build input and filter_complex
  local inputs=()
  for f in "${fade_files[@]}"; do inputs+=("-i" "$f"); done

  local filter=""
  local offset=0
  local lastv="[v0]"
  local lasta="[a0]"

  for ((i=0; i<${#fade_files[@]}; i++)); do
    filter+="[$i:v]format=yuv420p[v$i];"
    filter+="[$i:a]anull[a$i];"
  done

  for ((i=1; i<${#fade_files[@]}; i++)); do
    dur=$(get_duration "${fade_files[$((i-1))]}")
    offset=$(awk -v o="$offset" -v d="$dur" -v x="$CROSSFADE_DURATION" 'BEGIN{print o + d - x}')
    offset_fmt=$(printf "%.2f" "$offset")

    filter+="${lastv}[v$i]xfade=transition=fade:duration=${CROSSFADE_DURATION}:offset=${offset_fmt}[vxf$i];"
    filter+="${lasta}[a$i]acrossfade=d=${CROSSFADE_DURATION}[axf$i];"

    lastv="[vxf$i]"
    lasta="[axf$i]"
  done

  ffmpeg -nostdin "${inputs[@]}" -filter_complex "${filter%?}" \
    -map "${lastv}" -map "${lasta}" -c:v libx264 -preset veryfast -crf 18 \
    -c:a aac -b:a 192k ${FORCE} "${OUTFILE_PATH}" >>"${LOG_FILE}" 2>&1

  if [[ $? -eq 0 && -s "${OUTFILE_PATH}" ]]; then
    log_message SUCCESS "Created ${OUTFILE_PATH} with crossfades"
  else
    log_message ERROR "Crossfade generation failed"
  fi

  # Clean up temp fades
  for f in "${fade_files[@]}"; do rm -f "$f"; done
}

# @purpose: Remove duplicate video entries from videos.txt.
remove_video_duplicates() {
  # Remove old entry from videos.txt before rename
  # --- Safe removal of old entry from videos.txt before rename ---
  if [[ -f "${VIDEOS_TXT}" ]]; then
    tmpfile="${VIDEOS_TXT}.tmp"
    grep -v "file '${base}'" "${VIDEOS_TXT}" >"${tmpfile}" 2>/dev/null || true
    mv -f "${tmpfile}" "${VIDEOS_TXT}" 2>/dev/null || true
  fi
}

# @purpose: Main program entry point.
# @param $1..$N [Opt]: Command-line arguments.
main() {
  local added_count=0 skipped_count=0 total_duration_sec=0 total_videos width
  parse_args "$@"
  require_tools
  prepare_source
  # Recreate error log file.
  : >"${LOG_FILE}"
  VIDEOS_TXT="${WORKDIR}/videos.txt"
  OUTFILE_PATH="${WORKDIR}/${OUTFILE}"
  [[ -f "$OUTFILE_PATH" && -z "${FORCE}" ]] && {
    echo -e "\033[33m⚠️ Output exists.\033[m"
    read -rp $'\033[36mOverwrite? [y/N]: \033[m' ans
    [[ "$ans" =~ ^[yY]$ ]] || exit 1
  }
  [[ "${RECREATE}" == true ]] && {
    log_message INFO "Recreating videos.txt"
    rm -f "${VIDEOS_TXT}"
  }
  [[ -f "${VIDEOS_TXT}" ]] || touch "${VIDEOS_TXT}"
  log_message INFO "Source: ${WORKDIR}"
  log_message INFO "Output: ${OUTFILE_PATH}"
  mapfile -t all_videos < <(find "${WORKDIR}" -maxdepth 1 -type f -name "*.mp4" ! -name "$(basename "${OUTFILE}")" ! -name "*_fade.mp4" | sort)
  total_videos=${#all_videos[@]}
  width=${#total_videos}
  log_message INFO "Found ${total_videos} videos. Padding width=${width}"
  spinner_progress &
  spinner_pid=$!
  [[ $total_videos -eq 0 ]] && {
    SPINNER_STOP=true
    sleep 0.2
    kill "${spinner_pid}" >/dev/null 2>&1 || true
    echo -e '\n' 1>&2
    log_message SUMMARY "No videos found in source."
    exit 0
  }
  for v in "${all_videos[@]}"; do
    [[ ! -f "$v" ]] && continue
    base=$(basename "$v")
    dur=$(get_duration "$v")
    dsec=$(printf "%.0f" "$dur")
    total_duration_sec=$((total_duration_sec + dsec))
    duration_fmt=$(format_time "$dsec")

    if [[ "$base" =~ ^part-[0-9]+\.mp4$ ]]; then
      num=$(echo "$base" | sed -E 's/part-0*([0-9]+)\.mp4/\1/')
      printf -v padded "%0${width}d" "$num"
      new="part-${padded}.mp4"
      if [[ "$base" != "$new" ]]; then
        remove_video_duplicates
        mv "${WORKDIR}/${base}" "${WORKDIR}/${new}" 2>>"${LOG_FILE}"
        preserve_timestamps "${WORKDIR}/${new}" "${WORKDIR}/${new}"
        rm -f "${WORKDIR}/${base}" 2>/dev/null
        base="$new"
        v="${WORKDIR}/${new}"
        log_message INFO "Normalized → ${base}"
      fi
    else
      seq=$(get_next_part_number)
      seq=$((10#$seq))
      printf -v seq "%0${width}d" "$seq"
      new="part-${seq}.mp4"
      remove_video_duplicates
      mv "$v" "${WORKDIR}/${new}" 2>>"${LOG_FILE}"
      preserve_timestamps "$v" "${WORKDIR}/${new}"
      rm -f "$v" 2>/dev/null
      base="$new"
      v="${WORKDIR}/${new}"
      log_message INFO "Renamed → ${base}"
    fi

    entry="file '${base}'"
    grep -qxF "${entry}" "${VIDEOS_TXT}" || {
      echo "${entry}" >>"${VIDEOS_TXT}"
      log_message INFO "${base} | Duration: ${duration_fmt}"
    }

    last_frame="${WORKDIR}/${base%.mp4}-last.jpg"
    ffmpeg -nostdin -sseof "${LAST_FRAME_OFFSET}" -i "${v}" -frames:v 1 -q:v 2 "${last_frame}" -y >>"${LOG_FILE}" 2>&1
    if [[ -s "${last_frame}" ]]; then
      log_message INFO "Extracted last frame → ${last_frame}"
      ((added_count++))
    else
      log_message ERROR "Failed extracting last frame from ${base}"
    fi
  done

  sort -u "${VIDEOS_TXT}" -o "${VIDEOS_TXT}"
  [[ $(tail -c1 "${VIDEOS_TXT}") ]] && echo "" >>"${VIDEOS_TXT}"
  SPINNER_STOP=true
  sleep 0.2
  kill "${spinner_pid}" >/dev/null 2>&1 || true
  cross_fade
  total_dur_fmt=$(format_time "$total_duration_sec")
  total_videos=$(grep -c "^file" "${VIDEOS_TXT}")
  echo -e "\n--------------------------------------------------------------------------------"
  log_message SUMMARY "  Added videos: ${added_count}"
  log_message SUMMARY "Skipped videos: ${skipped_count}"
  log_message SUMMARY "  Total videos: ${total_videos}"
  log_message SUMMARY "Total duration: ${total_dur_fmt}"
  echo -e "--------------------------------------------------------------------------------"
  [[ -s "${LOG_FILE}" ]] && log_message INFO "Error logs saved to: ${WORKDIR}/video-gen-err.log"
  echo -e "\033[32m✅ DONE — All videos processed successfully!\033[0m"
  sanitize_last_frames
}

main "$@"
