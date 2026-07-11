"""Command builders and output parsers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import csv
import html
import os
import re
import shlex
import socket
import subprocess
import textwrap
from base64 import b64encode
from functools import lru_cache
from pathlib import Path

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.core.paths import homesetup_home, ollama_history_file, ollama_prompt_file
from hhs_ui.core.runtime import RUN_SHELL
from hhs_ui.features.ssh_core import ssh_config_file, ssh_config_hostname, ssh_config_option
from hhs_ui.core.ui_definitions import (
    FIREBASE_CONFIG_CONTENT_OUTPUT_MARKER,
    FIREBASE_CONFIG_END_OUTPUT_MARKER,
    FIREBASE_CONFIG_FILE_OUTPUT_MARKER,
    FOOTER_VERSION_OUTPUT_MARKER,
    HHS_CONFIG_ENV_OUTPUT_MARKER,
    HHS_FIREBASE_FIELDS,
    HHS_HSPM_ENV_OUTPUT_MARKER,
    HHS_PATHS_RAW_ENTRY_MARKER,
    HHS_SETUP_SETTINGS,
    SHOPT_DESCRIPTIONS,
    STARSHIP_CACHE_OUTPUT_MARKER,
    STARSHIP_CONFIG_CONTENT_OUTPUT_MARKER,
    STARSHIP_CONFIG_OUTPUT_MARKER,
    STARSHIP_END_OUTPUT_MARKER,
    STARSHIP_HHS_DIR_OUTPUT_MARKER,
    STARSHIP_PRESETS_OUTPUT_MARKER,
)


def normalized_top_n(value: object) -> int:
    """Return a valid Top N value using the shared default."""
    if isinstance(value, bool):
        return hhs_ui_constants.DEFAULT_TOP_N
    try:
        top_n = int(value)
    except (TypeError, ValueError):
        return hhs_ui_constants.DEFAULT_TOP_N
    if top_n < hhs_ui_constants.MIN_TOP_N or top_n > hhs_ui_constants.MAX_TOP_N:
        return hhs_ui_constants.DEFAULT_TOP_N
    return top_n


def normalized_monitor_top_n(value: object) -> int:
    """Return a valid monitor Top N value."""
    return normalized_top_n(value)


def normalized_history_stats_top_n(value: object) -> int:
    """Return a valid History Stats Top N value."""
    return normalized_top_n(value)


def normalized_monitor_disk_top_n(value: object) -> int:
    """Return a valid monitor disk Top N value."""
    return normalized_top_n(value)


def normalized_monitor_log_tail_lines(value: object) -> int:
    """Return a valid monitor log bottom-line count."""
    try:
        tail_lines = int(value)
    except (TypeError, ValueError):
        return hhs_ui_constants.DEFAULT_LOG_TAIL_LINES
    return max(
        hhs_ui_constants.MIN_LOG_TAIL_LINES,
        min(tail_lines, hhs_ui_constants.MAX_LOG_TAIL_LINES),
    )


def strip_ansi(value: str) -> str:
    """Remove terminal ANSI color escapes from command output."""
    return hhs_ui.ESCAPED_ANSI_ESCAPE_PATTERN.sub(
        "", hhs_ui.ANSI_ESCAPE_PATTERN.sub("", value)
    )


def clean_command_status_message(value: str) -> str:
    """Return command output suitable for compact UI status messages."""
    clean_value = strip_ansi(value).strip()
    clean_value = re.sub(r"^\s*[✘✖✗×]\s*", "", clean_value)
    clean_value = re.sub(r"^\s*Fatal:\s*", "", clean_value)
    clean_value = re.sub(r"^\s*__[A-Za-z0-9_]+\s*", "", clean_value)
    return clean_value.strip()


def service_action_success_message(operation: str, service_name: str) -> str:
    """Return a normalized success message for a completed service action."""
    labels = {
        "start": "Started",
        "stop": "Stopped",
        "restart": "Restarted",
    }
    label = labels.get(operation.strip().lower(), "Updated")
    return f"{label} service: {service_name}"


def clean_service_action_error(output: str, operation: str, service_name: str) -> str:
    """Return a concise error message from service-action command output."""
    clean_output = clean_command_status_message(output).replace("`", "").strip()
    clean_output = re.sub(
        rf'^\s*{re.escape(operation.title())}\s+service\s+"{re.escape(service_name)}"\.\.\.\s*',
        "",
        clean_output,
        flags=re.IGNORECASE,
    )
    clean_output = re.sub(r"\s*=>\s*", " ", clean_output)
    clean_output = re.sub(r"\s+OK\s+FAILED\s*$", "", clean_output, flags=re.IGNORECASE)
    clean_output = re.sub(r"\s+", " ", clean_output).strip()
    if clean_output and "successfully" not in clean_output.lower():
        return clean_output
    return f"Unable to {operation} service: {service_name}"


def service_action_status_message(
    result: subprocess.CompletedProcess[str], operation: str, service_name: str
) -> str:
    """Return the footer status message for a completed service action."""
    if result.returncode == 0:
        return service_action_success_message(operation, service_name)
    return clean_service_action_error(
        result.stderr or result.stdout or "", operation, service_name
    )


def updater_output_has_updates(output: str) -> bool:
    """Return whether updater command output reports available updates."""
    clean_output = strip_ansi(output).lower()
    no_update_markers = (
        "up-to-date",
        "up to date",
        "already latest",
        "latest version",
        "no update",
        "no updates",
    )
    if any(marker in clean_output for marker in no_update_markers):
        return False
    update_markers = (
        "updates available",
        "update available",
        "new version",
        "repository:",
    )
    return any(marker in clean_output for marker in update_markers)


def overlaps_existing_range(
    start: int, end: int, ranges: list[tuple[int, int, str]]
) -> bool:
    """Return whether a candidate highlight range overlaps an existing range."""
    return any(
        start < existing_end and end > existing_start
        for existing_start, existing_end, _ in ranges
    )


def log_tailor_highlight_ranges(value: str) -> list[tuple[int, int, str]]:
    """Return highlight ranges using the same regex rules as __hhs_tailor."""
    ranges: list[tuple[int, int, str]] = []
    for pattern, css_class in hhs_ui.LOG_TAILOR_RULES:
        for match in pattern.finditer(value):
            start, end = match.span(1) if css_class == "thread" else match.span(0)
            if start == end or overlaps_existing_range(start, end, ranges):
                continue
            ranges.append((start, end, css_class))
    return sorted(ranges, key=lambda item: item[0])


def log_filter_highlight_ranges(
    value: str, text_filter: str = ""
) -> list[tuple[int, int, str]]:
    """Return highlight ranges for Monitor Logs containing-filter matches."""
    needle = text_filter.strip()
    if not needle:
        return []
    pattern = re.compile(re.escape(needle), flags=re.IGNORECASE)
    return [
        (match.start(), match.end(), "filter-match")
        for match in pattern.finditer(value)
        if match.start() != match.end()
    ]


def colorize_log_output(value: str, text_filter: str = "") -> str:
    """Return log output highlighted with __hhs_tailor-compatible CSS classes."""
    clean_value = strip_ansi(value)
    ranges = log_filter_highlight_ranges(clean_value, text_filter)
    for start, end, css_class in log_tailor_highlight_ranges(clean_value):
        if overlaps_existing_range(start, end, ranges):
            continue
        ranges.append((start, end, css_class))
    ranges = sorted(ranges, key=lambda item: item[0])
    html_parts: list[str] = []
    cursor = 0
    for start, end, css_class in ranges:
        if start > cursor:
            html_parts.append(html.escape(clean_value[cursor:start]))
        html_parts.append(
            f'<span class="hhs-log-{css_class}">{html.escape(clean_value[start:end])}</span>'
        )
        cursor = end
    html_parts.append(html.escape(clean_value[cursor:]))
    return "".join(html_parts).replace("\n", "<br>")


def filter_log_output(value: str, log_filter: str, text_filter: str = "") -> str:
    """Return log output matching the selected monitor log text filter."""
    needle = text_filter.strip().lower()
    if log_filter != "Containing" or not needle:
        return value
    return "\n".join(
        line for line in value.splitlines() if needle in strip_ansi(line).lower()
    )


def interpret_terminal_edit_sequences(output: str) -> str:
    """Return output after applying simple terminal cursor edit sequences."""
    lines: list[str] = []
    current: list[str] = []
    cursor = 0
    index = 0
    length = len(output)
    while index < length:
        char = output[index]
        if char in ("\n", "\r"):
            lines.append("".join(current))
            current = []
            cursor = 0
            index += 1
            continue
        if char != "\x1b":
            if cursor >= len(current):
                current.extend(" " for _ in range(cursor - len(current)))
                current.append(char)
            else:
                current[cursor] = char
            cursor += 1
            index += 1
            continue
        match = re.match(r"\x1b\[([0-9;?]*)([A-Za-z])", output[index:])
        if not match:
            index += 1
            continue
        params = match.group(1).replace("?", "")
        command = match.group(2)
        amount = int(params.split(";", 1)[0] or "1") if params else 1
        if command == "D":
            cursor = max(0, cursor - amount)
        elif command == "C":
            cursor += amount
        elif command == "G":
            cursor = max(0, amount - 1)
        elif command == "K":
            current = current[:cursor]
        index += len(match.group(0))
    lines.append("".join(current))
    return "\n".join(lines)


def clean_hhs_ask_output(output: str) -> str:
    """Return user-facing ask output without terminal control decoration."""
    final_output = output
    for marker in ("\x1b[H\x1b[2J\x1b[3J", "\033[H\033[2J\033[3J"):
        if marker in final_output:
            final_output = final_output.rsplit(marker, 1)[-1]
    clean_output = strip_ansi(interpret_terminal_edit_sequences(final_output))
    lines = []
    for line in clean_output.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("✨"):
            continue
        if re.match(r"^/.*/hhs-[^-]+-response\.", stripped):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def current_username() -> str:
    """Return the current UI username."""
    return os.environ.get("USER") or os.environ.get("LOGNAME") or "user"


def parse_current_ollama_model(output: str) -> str:
    """Parse the current Ollama model name from ask -m output."""
    for line in strip_ansi(output).splitlines():
        if "(current)" not in line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            return parts[1]
    return "unknown"


def parse_ollama_model_rows(
    output: str, current_model: str = ""
) -> list[dict[str, str]]:
    """Parse available Ollama model rows from the ask -m Markdown table."""
    rows: list[dict[str, str]] = []
    seen_models: set[str] = set()
    downloaded_models = parse_downloaded_ollama_models(output)
    for line in strip_ansi(output).splitlines():
        markdown_columns = [
            column.strip().strip("`") for column in line.strip().strip("|").split("|")
        ]
        if (
            len(markdown_columns) >= 6
            and markdown_columns[0]
            and markdown_columns[0] != "Pull Name"
            and not markdown_columns[0].startswith(":")
            and ":" in markdown_columns[0]
        ):
            model_name = markdown_columns[0]
            if model_name not in seen_models:
                rows.append(
                    {
                        "Name": model_name,
                        "Params": markdown_columns[2],
                        "Size": markdown_columns[3],
                        "Context": markdown_columns[4],
                        "Capabilities": markdown_columns[5],
                        "Status": ollama_model_status(
                            model_name, current_model, downloaded_models
                        ),
                    }
                )
                seen_models.add(model_name)
            continue
    return rows


def parse_downloaded_ollama_models(output: str) -> set[str]:
    """Return downloaded Ollama model names from the ask -m local model section."""
    models: set[str] = set()
    for line in strip_ansi(output).splitlines():
        parts = line.split()
        if (
            len(parts) >= 2
            and parts[0].isdigit()
            and parts[1] != "NAME"
            and ":" in parts[1]
        ):
            models.add(parts[1])
    return models


def first_downloaded_ollama_model(output: str, excluded_model: str = "") -> str:
    """Return the first downloaded Ollama model listed in the available models table."""
    downloaded_models = parse_downloaded_ollama_models(output)
    for row in parse_ollama_model_rows(output):
        model_name = row["Name"]
        if model_name != excluded_model and model_name in downloaded_models:
            return model_name
    return ""


def ollama_model_status(
    model_name: str, current_model: str, downloaded_models: set[str]
) -> str:
    """Return the UI status for one Ollama model."""
    if model_name == current_model:
        return "Active"
    if model_name in downloaded_models:
        return "Downloaded"
    return ""


def ollama_model_context_size(ollama_model: str) -> str:
    """Return the context size for an Ollama model from HomeSetup model metadata."""
    models_file = (
        homesetup_home() / "bin/apps/bash/hhs-app/plugins/ask/ollama-models.md"
    )
    if not models_file.is_file():
        return "?"
    clean_model = ollama_model.strip("`")
    for line in models_file.read_text(encoding="utf-8").splitlines():
        columns = [
            column.strip().strip("`") for column in line.strip().strip("|").split("|")
        ]
        if len(columns) >= 5 and columns[0] == clean_model:
            return columns[4] or "?"
    return "?"


def parse_context_window_kib(context_size: str) -> int:
    """Return an Ollama context window label as KiB for history-file budgeting."""
    normalized_context = context_size.strip().upper().replace(",", "")
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMG]?)", normalized_context)
    if not match:
        return 0
    value = float(match.group(1))
    unit = match.group(2)
    multiplier = {"": 1, "K": 1, "M": 1024, "G": 1024 * 1024}[unit]
    return max(int(value * multiplier), 0)


def file_size_bytes(file_path: Path) -> int:
    """Return a file size in bytes, or zero when the file is missing."""
    try:
        return file_path.stat().st_size if file_path.is_file() else 0
    except OSError:
        return 0


def percent_of_context(file_size: int, context_window_bytes: int) -> int:
    """Return a clamped percentage of an Ollama context window."""
    return max(0, min(round((file_size / context_window_bytes) * 100), 100))


def ai_context_usage_percentages(context_size: str) -> dict[str, int] | None:
    """Return prompt, history context, and total context usage percentages."""
    context_window_kib = parse_context_window_kib(context_size)
    if context_window_kib <= 0:
        return None
    context_window_bytes = context_window_kib * 1024
    prompt_size = file_size_bytes(ollama_prompt_file())
    history_size = file_size_bytes(ollama_history_file())
    return {
        "prompt": percent_of_context(prompt_size, context_window_bytes),
        "context": percent_of_context(history_size, context_window_bytes),
        "total": percent_of_context(prompt_size + history_size, context_window_bytes),
    }


def ai_context_used_percent(context_size: str) -> int | None:
    """Return the percent of the selected model context used by prompt and history."""
    usage_percentages = ai_context_usage_percentages(context_size)
    if usage_percentages is None:
        return None
    return usage_percentages["total"]


def ai_context_used_color(percent_used: int) -> str:
    """Return the CSS color token for an AI context usage percentage."""
    if percent_used >= 90:
        return "var(--hhs-danger)"
    if percent_used >= 40:
        return "var(--hhs-warning)"
    return "var(--hhs-success)"


def html_tooltip_chip(label: str, value_html: str, tooltip_html: str) -> str:
    """Return a chat metadata chip with an HTML tooltip."""
    return (
        f'<span class="hhs-tooltip" tabindex="0">{html.escape(label)}: '
        f"{value_html}"
        f'<span class="hhs-tooltip-content">{tooltip_html}</span></span>'
    )


def ai_context_used_tooltip_html(context_size: str) -> str:
    """Return prompt and history context usage tooltip HTML."""
    usage_percentages = ai_context_usage_percentages(context_size)
    if usage_percentages is None:
        return "Prompt: -<br>Context: -"
    return (
        f"Prompt: {usage_percentages['prompt']}%<br>"
        f"Context: {usage_percentages['context']}%"
    )


def ai_context_used_meta_html(context_size: str) -> str:
    """Return the AI context usage meta row HTML."""
    percent_used = ai_context_used_percent(context_size)
    tooltip_html = ai_context_used_tooltip_html(context_size)
    if percent_used is None:
        return html_tooltip_chip(
            "Ctx Used",
            '<strong class="hhs-ai-chat-model hhs-ai-context-used">-</strong>',
            tooltip_html,
        )
    formatted_percent = html.escape(f"{percent_used}%")
    context_color = ai_context_used_color(percent_used)
    return html_tooltip_chip(
        "Ctx Used",
        '<strong class="hhs-ai-chat-model hhs-ai-context-used" '
        f'style="color: {context_color};">'
        f"{formatted_percent}</strong>",
        tooltip_html,
    )


def format_ai_request_duration(duration_seconds: float) -> str:
    """Return an AI request duration using millis, seconds, or minutes."""
    if duration_seconds < 1:
        return f"{max(round(duration_seconds * 1000), 1)} millis"
    if duration_seconds < 60:
        return f"{duration_seconds:.1f} sec"
    return f"{duration_seconds / 60:.1f} minutes"


def format_ai_chat_prefix(
    role: str, username: str, ollama_model: str, context_size: str
) -> str:
    """Format an AI chat message with icon, speaker, and content."""
    if role == "assistant":
        return f'<span class="hhs-ai-assistant-text">{html.escape(ollama_model)}&#91;{html.escape(context_size)}&#93;:</span><br>'
    if role == "system":
        return '<span class="hhs-ai-system-text">HomeSetup:</span><br>'
    return (
        f'<span class="hhs-ai-user-text">{html.escape(username)}&#91;You&#93;:</span>'
    )


def wrap_ai_code_line(line: str) -> list[str]:
    """Wrap one code-block line to keep AI markdown inside the chat layout."""
    if len(line) <= hhs_ui.AI_CODE_BLOCK_WRAP_COLUMNS:
        return [line]
    indent = re.match(r"^\s*", line).group(0)
    wrapped = textwrap.wrap(
        line,
        width=hhs_ui.AI_CODE_BLOCK_WRAP_COLUMNS,
        initial_indent="",
        subsequent_indent=indent,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False,
    )
    return wrapped or [line]


def normalize_ai_code_blocks(content: str) -> str:
    """Normalize assistant Markdown code fences and wrap long code lines."""
    lines = content.splitlines()
    normalized: list[str] = []
    in_code_block = False
    fence_marker = "```"

    for line in lines:
        malformed_fence = re.match(r"^(```+|~~~+)([A-Za-z0-9_.+-]+)\s+(.+)$", line)
        if not in_code_block and malformed_fence:
            fence_marker = malformed_fence.group(1)
            normalized.append(f"{fence_marker}{malformed_fence.group(2)}")
            normalized.extend(wrap_ai_code_line(malformed_fence.group(3)))
            normalized.append(fence_marker)
            continue

        code_fence = re.match(r"^(```+|~~~+)(?:[A-Za-z0-9_.+-]+)?\s*$", line)
        if code_fence:
            in_code_block = not in_code_block
            fence_marker = code_fence.group(1)
            normalized.append(line)
            continue

        if in_code_block:
            normalized.extend(wrap_ai_code_line(line))
        else:
            normalized.append(line)

    if in_code_block:
        normalized.append(fence_marker)
    return "\n".join(normalized)


def prepare_ai_chat_content(role: str, content: str) -> str:
    """Return chat content normalized for the selected AI message role."""
    if role == "assistant":
        return normalize_ai_code_blocks(content)
    return content


def human_size_to_bytes(value: str) -> float:
    """Convert a human-readable disk size into bytes for chart sorting."""
    match = re.match(r"^\s*([0-9.]+)\s*([A-Za-z]*)\s*$", value)
    if not match:
        return 0.0
    number = float(match.group(1))
    unit = match.group(2).lower().rstrip("b")
    unit_multipliers = {
        "": 1,
        "k": 1024,
        "ki": 1024,
        "m": 1024**2,
        "mi": 1024**2,
        "g": 1024**3,
        "gi": 1024**3,
        "t": 1024**4,
        "ti": 1024**4,
        "p": 1024**5,
        "pi": 1024**5,
    }
    return number * unit_multipliers.get(unit, 1)


def metric_value(value: str) -> float:
    """Convert a top/ps metric value into a numeric chart value."""
    clean_value = value.strip().replace("%", "")
    if re.search(r"[A-Za-z]", clean_value):
        return human_size_to_bytes(clean_value)
    try:
        return float(clean_value)
    except ValueError:
        return 0.0


def escape_markdown_table_cell(value: str) -> str:
    """Return a cell value escaped for a Markdown table."""
    return value.replace("|", "\\|")


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Return a Markdown table for the provided headers and rows."""
    if not headers or not rows:
        return ""
    safe_headers = [escape_markdown_table_cell(header) for header in headers]
    safe_rows = [
        [escape_markdown_table_cell(cell) for cell in row[: len(headers)]]
        for row in rows
    ]
    header_line = "| " + " | ".join(safe_headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(row) + " |" for row in safe_rows]
    return "\n".join([header_line, separator_line, *row_lines])


def normalize_markdown_table_row(headers: list[str], parts: list[str]) -> list[str]:
    """Return a row normalized to the provided Markdown table headers."""
    if headers == ["NAME", "LINE", "TIME", "FROM"] and len(parts) >= 5:
        return [parts[0], parts[1], " ".join(parts[2:5]), " ".join(parts[5:])]
    if len(parts) > len(headers):
        return [*parts[: len(headers) - 1], " ".join(parts[len(headers) - 1 :])]
    return [*parts, *([""] * (len(headers) - len(parts)))]


def format_hhs_sysinfo_markdown(output: str) -> str:
    """Format __hhs_sysinfo terminal output as Markdown."""
    markdown_lines: list[str] = []
    table_headers: list[str] = []
    table_rows: list[list[str]] = []

    def flush_table() -> None:
        """Append any pending Markdown table to the output."""
        nonlocal table_headers, table_rows
        table = markdown_table(table_headers, table_rows)
        if table:
            markdown_lines.extend(["", table, ""])
        table_headers = []
        table_rows = []

    for raw_line in strip_ansi(output).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("-=-") or set(line) == {"-"}:
            continue

        section_match = hhs_ui.SYSINFO_SECTION_PATTERN.match(line)
        if section_match:
            flush_table()
            markdown_lines.extend(["", f"##### {section_match.group(1).strip()}", ""])
            continue

        key_value_match = hhs_ui.SYSINFO_KEY_VALUE_PATTERN.match(raw_line)
        if key_value_match:
            flush_table()
            name = key_value_match.group(1).strip()
            value = key_value_match.group(2).strip()
            markdown_lines.append(f"- **{name}**: `{value}`")
            continue

        parts = line.split()
        if len(parts) > 1:
            if not table_headers:
                table_headers = parts
            else:
                table_rows.append(normalize_markdown_table_row(table_headers, parts))
            continue

        flush_table()
        markdown_lines.append(line)

    flush_table()
    return "\n".join(markdown_lines).strip()


def parse_fixed_width_cli_table(output: str) -> tuple[list[str], list[list[str]]]:
    """Parse a whitespace-aligned command table into headers and rows."""
    lines = [
        line.rstrip()
        for line in strip_ansi(output).splitlines()
        if line.strip() and set(line.strip()) != {"-"}
    ]
    if not lines:
        return [], []

    headers = (
        [part.strip() for part in lines[0].split("\t")]
        if "\t" in lines[0]
        else re.split(r"\s{2,}", lines[0].strip())
    )
    if len(headers) < 2:
        return [], []

    rows: list[list[str]] = []
    for line in lines[1:]:
        parts = (
            [part.strip() for part in line.split("\t")]
            if "\t" in line
            else re.split(r"\s{2,}", line.strip(), maxsplit=len(headers) - 1)
        )
        rows.append(normalize_markdown_table_row(headers, parts))
    return headers, rows


def docker_cli_table_output(output: str) -> str:
    """Return Docker CLI table output with remote shell startup banners removed."""
    lines = [
        line.rstrip()
        for line in strip_ansi(output).splitlines()
        if line.strip() and set(line.strip()) != {"-"}
    ]
    for index, line in enumerate(lines):
        headers = (
            [part.strip() for part in line.split("\t")]
            if "\t" in line
            else re.split(r"\s{2,}", line.strip())
        )
        if headers and headers[0] in {"CONTAINER ID", "REPOSITORY"}:
            return "\n".join(lines[index:])
    return ""


def filter_markdown_table_columns(
    headers: list[str], rows: list[list[str]], omitted_columns: tuple[str, ...]
) -> tuple[list[str], list[list[str]]]:
    """Return Markdown table data without the named columns."""
    omitted_column_names = set(omitted_columns)
    if not omitted_column_names:
        return headers, rows

    kept_indexes = [
        index
        for index, header in enumerate(headers)
        if header not in omitted_column_names
    ]
    return (
        [headers[index] for index in kept_indexes],
        [
            [row[index] if index < len(row) else "" for index in kept_indexes]
            for row in rows
        ],
    )


def docker_cli_table_rows(
    output: str, omitted_columns: tuple[str, ...] = ()
) -> list[dict[str, str]]:
    """Return Docker CLI table output as row dictionaries."""
    headers, rows = parse_fixed_width_cli_table(docker_cli_table_output(output))
    headers, rows = filter_markdown_table_columns(headers, rows, omitted_columns)
    return [
        {
            header: row[index] if index < len(row) else ""
            for index, header in enumerate(headers)
        }
        for row in rows
    ]


def docker_container_is_up(row: dict[str, str]) -> bool:
    """Return whether a Docker container row reports a running status."""
    return row.get("STATUS", "").strip().lower().startswith("up")


def ssh_shared_connection_closed(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether a failed SSH command reports a closed shared connection."""
    if result.returncode != 255:
        return False
    output = strip_ansi(f"{result.stdout or ''}\n{result.stderr or ''}").lower()
    return "shared connection to " in output and " closed" in output


def remote_command_startup_line_is_noise(line: str) -> bool:
    """Return whether a remote command line is HomeSetup shell startup chatter."""
    clean_line = strip_ansi(line).strip()
    if not clean_line:
        return False
    if clean_line.startswith("[bash] HomeSetup is starting"):
        return True
    if remote_command_motd_line_is_boundary(clean_line):
        return True
    return bool(re.fullmatch(r"Shell option \S+ set to (?:on|off)", clean_line))


@lru_cache(maxsize=1)
def homesetup_motd_template() -> str:
    """Return the local HomeSetup MOTD template text."""
    try:
        return (homesetup_home() / ".MOTD").read_text(encoding="utf-8")
    except OSError:
        return ""


def skip_shell_expansion(value: str, index: int) -> int:
    """Return the index after a shell expansion that starts at index."""
    if value.startswith("${", index):
        end_index = value.find("}", index + 2)
        return len(value) if end_index < 0 else end_index + 1
    if value.startswith("$(", index):
        depth = 1
        current_index = index + 2
        quote = ""
        escaped = False
        while current_index < len(value):
            character = value[current_index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif quote:
                if character == quote:
                    quote = ""
            elif character in {"'", '"'}:
                quote = character
            elif value.startswith("$(", current_index):
                depth += 1
                current_index += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    return current_index + 1
            current_index += 1
        return len(value)
    match = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*", value[index:])
    if match:
        return index + len(match.group(0))
    return index


def motd_literal_template_text(template: str) -> str:
    """Return MOTD template text with shell expansions replaced by separators."""
    value = re.sub(r"\\[ \t]*\r?\n", " ", template)
    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "$":
            next_index = skip_shell_expansion(value, index)
            if next_index > index:
                output.append("\0")
                index = next_index
                continue
        output.append(value[index])
        index += 1
    return "".join(output)


def motd_template_fragment_groups(template: str) -> tuple[tuple[str, ...], ...]:
    """Return stable literal fragment groups from one MOTD template."""
    groups: list[tuple[str, ...]] = []
    literal_template = motd_literal_template_text(template)
    for line in literal_template.splitlines():
        fragments = []
        for fragment in line.split("\0"):
            clean_fragment = re.sub(r"[^A-Za-z0-9._ -]+", " ", fragment)
            clean_fragment = re.sub(r"\s+", " ", clean_fragment).strip()
            if len(clean_fragment) >= 3 and re.search(r"[A-Za-z]", clean_fragment):
                fragments.append(clean_fragment)
        if fragments:
            groups.append(tuple(fragments))
    return tuple(groups)


def homesetup_motd_fragment_groups() -> tuple[tuple[str, ...], ...]:
    """Return stable literal fragment groups from the local HomeSetup MOTD."""
    return motd_template_fragment_groups(homesetup_motd_template())


def remote_command_motd_line_is_boundary(line: str) -> bool:
    """Return whether a remote command line is the HomeSetup MOTD boundary."""
    clean_line = re.sub(r"\s+", " ", strip_ansi(line)).strip()
    if not clean_line:
        return False
    return any(
        all(fragment in clean_line for fragment in group)
        for group in homesetup_motd_fragment_groups()
    )


def strip_remote_command_motd_block(value: str) -> str:
    """Return remote command output after the leading HomeSetup MOTD block."""
    lines = value.splitlines(keepends=True)
    scan_line_limit = 80
    for index, line in enumerate(lines[:scan_line_limit]):
        if not remote_command_motd_line_is_boundary(line):
            continue
        remaining_lines = lines[index + 1 :]
        while remaining_lines and not strip_ansi(remaining_lines[0]).strip():
            remaining_lines = remaining_lines[1:]
        return "".join(remaining_lines)
    return value


def strip_remote_command_startup_chatter(value: str) -> str:
    """Return remote command output without HomeSetup shell startup chatter."""
    value = strip_remote_command_motd_block(value)
    output_lines: list[str] = []
    removed_chatter = False
    for line in value.splitlines(keepends=True):
        if remote_command_startup_line_is_noise(line):
            removed_chatter = True
            continue
        if removed_chatter and not output_lines and not strip_ansi(line).strip():
            continue
        output_lines.append(line)
    return "".join(output_lines)


def sanitize_remote_command_result(
    host: str, result: subprocess.CompletedProcess[str]
) -> subprocess.CompletedProcess[str]:
    """Return a remote command result with HomeSetup startup chatter stripped."""
    if not host:
        return result
    stdout = strip_remote_command_startup_chatter(result.stdout or "")
    stderr = strip_remote_command_startup_chatter(result.stderr or "")
    if stdout == (result.stdout or "") and stderr == (result.stderr or ""):
        return result
    return subprocess.CompletedProcess(result.args, result.returncode, stdout, stderr)


def ssh_output_is_only_shared_close(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether failed SSH output only contains the shared-close notice."""
    if not ssh_shared_connection_closed(result):
        return False
    lines = [
        line.strip().lower()
        for line in strip_ansi(
            f"{result.stdout or ''}\n{result.stderr or ''}"
        ).splitlines()
        if line.strip()
    ]
    remaining_lines = [
        line
        for line in lines
        if not (line.startswith("shared connection to ") and line.endswith(" closed."))
    ]
    return not remaining_lines


def completed_disconnected_ssh_process(
    command: str, host: str
) -> subprocess.CompletedProcess[str]:
    """Build a failed command result for a detected stale SSH connection."""
    return subprocess.CompletedProcess(
        [RUN_SHELL, "-lc", command],
        255,
        "",
        f"Shared connection to {ssh_config_hostname(host)} closed.",
    )


def build_hhs_env_environment_command() -> str:
    """Build a non-interactive shell prefix that loads HomeSetup environment values."""
    return (
        'export HHS_HOME="${HHS_HOME:-${HOME}/HomeSetup}"; '
        'export HHS_DIR="${HHS_DIR:-${HOME}/.config/hhs}"; '
        'export HHS_MY_OS="${HHS_MY_OS:-$(uname -s)}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-${SHELL##*/}}"; '
        'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'export HHS_CACHE_DIR="${HHS_CACHE_DIR:-${HHS_DIR}/cache}"; '
        'export HHS_LOG_FILE="${HHS_LOG_FILE:-${HHS_LOG_DIR}/streamlit-ui-shell.log}"; '
        'export HHS_SETUP_FILE="${HHS_SETUP_FILE:-${HHS_DIR}/.homesetup.toml}"; '
        'export HHS_PATHS_FILE="${HHS_PATHS_FILE:-${HHS_DIR}/.path}"; '
        'export HHS_VENV_PATH="${HHS_VENV_PATH:-${HHS_DIR}/venv}"; '
        'mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}" "${HHS_CACHE_DIR}"; '
        'if [[ -s "${HHS_SETUP_FILE}" ]]; then '
        "while IFS= read -r hhs_pref; do "
        'if [[ "${hhs_pref}" =~ ^([a-zA-Z0-9_.]+)[[:space:]]*=[[:space:]]*(.*)$ ]]; then '
        'hhs_key="$(tr "[:lower:]." "[:upper:]_" <<<"${BASH_REMATCH[1]}")"; '
        'hhs_val="${BASH_REMATCH[2]//\\"/}"; hhs_val="${hhs_val//\\\'/}"; '
        'case "$(tr "[:lower:]" "[:upper:]" <<<"${hhs_val}")" in TRUE) hhs_val=1 ;; FALSE) hhs_val="" ;; esac; '
        'export "${hhs_key}=${hhs_val}"; '
        "fi; "
        'done < "${HHS_SETUP_FILE}"; '
        "fi; "
        "unset HHS_ACTIVE_DOTFILES; "
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_colors.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_icons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_env.bash"; '
        '[[ -s "${HHS_ENV_FILE}" ]] && source "${HHS_ENV_FILE}"; '
        'if [[ "${HHS_PYTHON_VENV_ENABLED:-}" == "1" && -s "${HHS_VENV_PATH}/bin/activate" ]]; then '
        'source "${HHS_VENV_PATH}/bin/activate" >/dev/null 2>&1 || true; '
        "fi; "
        'for hhs_path in "${HOME}/bin" "${HOME}/.local/bin" '
        '"${HHS_DIR}/bin" "${HHS_HOME}/tests/bats/bats-core/bin"; do '
        '[[ -d "${hhs_path}" ]] && PATH="${PATH}:${hhs_path}"; '
        "done; "
        'if [[ -f "${HHS_PATHS_FILE}" ]]; then '
        "while IFS= read -r hhs_path; do "
        '[[ -n "${hhs_path}" ]] && PATH="${hhs_path}:${PATH}"; '
        'done < <(grep . "${HHS_PATHS_FILE}" | grep -v -e "^$"); '
        "fi; "
        '[[ -d "${HHS_VENV_PATH}/bin" ]] && PATH="${HHS_VENV_PATH}/bin:${PATH}"; '
        "PATH=\"$(awk -v RS=: 'NF && !seen[$0]++ {"
        'printf "%s%s", sep, $0; sep=":"'
        '}\' <<<"${PATH}")"; '
        "export PATH; "
    )


def build_hhs_envs_command(prefix_filter: str | None) -> str:
    """Build the Bash command used to run the __hhs_envs HomeSetup function."""
    filter_arg = f" {shlex.quote(prefix_filter)}" if prefix_filter else ""
    return (
        build_hhs_env_environment_command()
        + 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_envs{filter_arg}"
    )


def build_homesetup_version_command() -> str:
    """Build the lightweight command used to print the HomeSetup product version."""
    return (
        build_hhs_env_environment_command()
        + f'printf "{FOOTER_VERSION_OUTPUT_MARKER}%s\\n" "${{HHS_VERSION}}"'
    )


def build_hhs_env_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a custom environment value."""
    safe_operation = "del" if operation == "del" else "add"
    safe_name = shlex.quote(name)
    if safe_operation == "del":
        action_args = f"--del {safe_name}"
    else:
        action_args = f"-a {shlex.quote(f'{name}={value}')}"
    return (
        build_hhs_env_environment_command()
        + 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_envs {action_args}"
    )


def build_hhs_sysinfo_command() -> str:
    """Build the Bash command used to run the __hhs_sysinfo HomeSetup function."""
    return (
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-sys-utils.bash"; '
        "__hhs_sysinfo"
    )


def open_file(filepath: str) -> str:
    """Build a local HomeSetup command that opens a file or directory."""
    safe_filepath = shlex.quote(filepath.strip())
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_open {safe_filepath}"
    )


def build_footer_working_directory_command() -> str:
    """Build the Bash command used to print the footer working directory."""
    return r'printf "__HHS_UI_PWD__"; \pwd'


def build_hhs_updater_command(operation: str) -> str:
    """Build the Bash command used to run the HomeSetup updater plug-in."""
    safe_operation = re.sub(r"[^A-Za-z_-]+", "", operation) or "check"
    update_prefix = 'printf "y\\n" | ' if safe_operation == "update" else ""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/updater/updater.bash"; '
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; exit "${exit_code}"; }; '
        'function __hhs() { if [[ "$1" == "updater" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f'{update_prefix}__hhs updater execute "{safe_operation}"'
    )


def build_hhs_setup_plugin_command(arguments: list[str]) -> str:
    """Build a Bash command that invokes the HomeSetup setup plug-in."""
    safe_arguments = " ".join(shlex.quote(argument) for argument in arguments)
    setup_dispatch = (
        "function __hhs() { "
        'if [[ "$1" == "setup" ]]; then '
        "shift; "
        'execute "$@"; '
        "else "
        "return 127; "
        "fi; "
        "}; "
    )
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_SETUP_FILE="${HHS_SETUP_FILE:-${HHS_DIR}/.homesetup.toml}"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'export HHS_LOG_FILE="${HHS_LOG_FILE:-${HHS_LOG_DIR}/hhs-ui.log}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        "export IS_PIPED=0; "
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_colors.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toml.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/setup/setup.bash"; '
        f"{setup_dispatch}"
        f"__hhs setup {safe_arguments}"
    )


def build_hhs_setup_settings_command() -> str:
    """Build the Bash command used to read HomeSetup setup settings."""
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_SETUP_FILE="${HHS_SETUP_FILE:-${HHS_DIR}/.homesetup.toml}"; '
        '[[ -s "${HHS_SETUP_FILE}" ]] || cp -f "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toml.bash"; '
        '__hhs_toml_get_all "${HHS_SETUP_FILE}" "setup"'
    )


def build_hhs_setup_apply_command(settings: dict[str, bool]) -> str:
    """Build the setup plug-in apply command for a settings mapping."""
    values = ["1" if settings.get(name, False) else "0" for name in HHS_SETUP_SETTINGS]
    return build_hhs_setup_plugin_command(["-apply", *values])


def build_hhs_setup_restore_command() -> str:
    """Build the setup plug-in command that restores default settings."""
    return build_hhs_setup_plugin_command(["-restore"])


def build_hhs_starship_info_command() -> str:
    """Build the Bash command used to read Starship paths, presets, and config."""
    return (
        build_hhs_env_environment_command()
        + 'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        + 'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/starship/starship.bash"; '
        + 'if [[ ! -s "${STARSHIP_CONFIG}" ]]; then '
        + 'cp -f "${HHS_STARSHIP_PRESETS_DIR}/hhs-starship.toml" "${STARSHIP_CONFIG}" 2>/dev/null || true; '
        + "fi; "
        + "add_hhs_presets >/dev/null 2>&1 || true; "
        + f'printf "%s\\n%s\\n" "{STARSHIP_CACHE_OUTPUT_MARKER}" "${{STARSHIP_CACHE}}"; '
        + f'printf "%s\\n%s\\n" "{STARSHIP_CONFIG_OUTPUT_MARKER}" "${{STARSHIP_CONFIG}}"; '
        + f'printf "%s\\n%s\\n" "{STARSHIP_HHS_DIR_OUTPUT_MARKER}" "${{HHS_DIR}}"; '
        + f'printf "%s\\n" "{HHS_CONFIG_ENV_OUTPUT_MARKER}"; '
        + 'printf "HHS_DIR\\t%s\\nHOME\\t%s\\nHHS_HOME\\t%s\\nSTARSHIP_CONFIG\\t%s\\n" '
        + '"${HHS_DIR}" "${HOME:-}" "${HHS_HOME}" "${STARSHIP_CONFIG}"; '
        + f'printf "%s\\n" "{STARSHIP_PRESETS_OUTPUT_MARKER}"; '
        + 'printf "%s\\n" "${STARSHIP_PRESETS[@]}" | awk \'NF && !seen[$0]++\' | sort; '
        + f'printf "%s\\n" "{STARSHIP_CONFIG_CONTENT_OUTPUT_MARKER}"; '
        + 'cat "${STARSHIP_CONFIG}" 2>/dev/null || true; '
        + f'printf "\\n%s\\n" "{STARSHIP_END_OUTPUT_MARKER}"'
    )


def build_hhs_firebase_info_command() -> str:
    """Build the Bash command used to read Firebase config file details."""
    return (
        build_hhs_env_environment_command()
        + 'export HHS_FIREBASE_CONFIG_FILE="${HHS_FIREBASE_CONFIG_FILE:-${HHS_DIR}/firebase.properties}"; '
        + 'export HHS_FIREBASE_CREDS_FILE="${HHS_FIREBASE_CREDS_FILE:-${HOME}/firebase-credentials.json}"; '
        + 'config_file="${HHS_FIREBASE_CONFIG_FILE}"; '
        + f'printf "%s\\n%s\\n" "{FIREBASE_CONFIG_FILE_OUTPUT_MARKER}" "${{config_file}}"; '
        + f'printf "%s\\n" "{HHS_CONFIG_ENV_OUTPUT_MARKER}"; '
        + 'printf "HHS_DIR\\t%s\\nHOME\\t%s\\nHHS_HOME\\t%s\\nHHS_FIREBASE_CONFIG_FILE\\t%s\\nHHS_FIREBASE_CREDS_FILE\\t%s\\n" '
        + '"${HHS_DIR}" "${HOME:-}" "${HHS_HOME}" "${HHS_FIREBASE_CONFIG_FILE}" "${HHS_FIREBASE_CREDS_FILE}"; '
        + f'printf "%s\\n" "{FIREBASE_CONFIG_CONTENT_OUTPUT_MARKER}"; '
        + 'cat "${config_file}" 2>/dev/null || true; '
        + f'printf "\\n%s\\n" "{FIREBASE_CONFIG_END_OUTPUT_MARKER}"'
    )


def build_hhs_firebase_plugin_command(arguments: list[str]) -> str:
    """Build a Bash command that invokes the HomeSetup Firebase plug-in."""
    safe_arguments = " ".join(shlex.quote(argument) for argument in arguments)
    firebase_dispatch = (
        "function __hhs() { "
        'if [[ "$1" == "firebase" ]]; then '
        "shift; "
        'local hhs_firebase_fn="${1:-execute}"; '
        'if declare -F "${hhs_firebase_fn}" >/dev/null 2>&1; then '
        "shift || true; "
        '"${hhs_firebase_fn}" "$@"; '
        "else "
        'execute "${hhs_firebase_fn}" "$@"; '
        "fi; "
        "else "
        "return 127; "
        "fi; "
        "}; "
    )
    return (
        build_hhs_env_environment_command()
        + 'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        + 'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        + 'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/firebase/firebase.bash"; '
        + f"{firebase_dispatch}"
        + f"__hhs firebase {safe_arguments}"
    )


def build_hhs_firebase_alias_action_command(operation: str, alias_name: str) -> str:
    """Build the Firebase alias upload/download command."""
    return build_hhs_firebase_plugin_command(["execute", operation, alias_name])


def build_hhs_starship_plugin_command(arguments: list[str]) -> str:
    """Build a Bash command that invokes the HomeSetup Starship plug-in."""
    safe_arguments = " ".join(shlex.quote(argument) for argument in arguments)
    starship_dispatch = (
        "function __hhs() { "
        'if [[ "$1" == "starship" ]]; then '
        "shift; "
        'execute "$@"; '
        "else "
        "return 127; "
        "fi; "
        "}; "
    )
    return (
        build_hhs_env_environment_command()
        + 'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        + 'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        + 'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/starship/starship.bash"; '
        + f"{starship_dispatch}"
        + f"__hhs starship {safe_arguments}"
    )


def build_hhs_settings_plugin_prefix() -> str:
    """Build the common Bash prefix for invoking the HomeSetup Settings plug-in."""
    settings_dispatch = (
        "function __hhs() { "
        'if [[ "$1" == "settings" ]]; then '
        "shift; "
        'local hhs_settings_fn="${1:-execute}"; '
        'if declare -F "${hhs_settings_fn}" >/dev/null 2>&1; then '
        "shift || true; "
        '"${hhs_settings_fn}" "$@"; '
        "else "
        'execute "${hhs_settings_fn}" "$@"; '
        "fi; "
        "else "
        "return 127; "
        "fi; "
        "}; "
    )
    return (
        build_hhs_env_environment_command()
        + 'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        + '[[ -s "${HHS_VENV_PATH}/bin/activate" ]] && source "${HHS_VENV_PATH}/bin/activate" >/dev/null 2>&1 || true; '
        + 'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        + 'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/settings/settings.bash"; '
        + 'mkdir -p "$(dirname "${HHS_SETMAN_CONFIG_FILE}")"; '
        + 'printf "hhs.setman.database = %s\\n" "${HHS_SETMAN_DB_FILE}" >"${HHS_SETMAN_CONFIG_FILE}"; '
        + f"{settings_dispatch}"
    )


def build_hhs_settings_plugin_command(arguments: list[str]) -> str:
    """Build a Bash command that invokes the HomeSetup Settings plug-in."""
    safe_arguments = " ".join(shlex.quote(argument) for argument in arguments)
    return build_hhs_settings_plugin_prefix() + f"__hhs settings {safe_arguments}"


def build_hhs_settings_list_command() -> str:
    """Build the command that lists overridden system settings."""
    return (
        build_hhs_settings_plugin_prefix()
        + 'export_file="$(mktemp "${TMPDIR:-/tmp}/hhs-settings.XXXXXX")" || exit 2; '
        + 'csv_file="${export_file}.csv"; '
        + 'if python3 -m setman export "${export_file}" >/dev/null; then '
        + 'cat "${csv_file}"; '
        + "ret_val=0; "
        + "else "
        + 'ret_val="$?"; '
        + "fi; "
        + 'rm -f "${export_file}" "${csv_file}"; '
        + 'exit "${ret_val}"'
    )


def build_hhs_settings_add_command(setting: str, value: str) -> str:
    """Build the command that stores an environment setting override."""
    return build_hhs_settings_plugin_command(
        ["execute", "set", "-n", setting, "-x", "", "-v", value, "-t", "environment"]
    )


def build_hhs_settings_delete_command(setting: str) -> str:
    """Build the command that deletes one overridden system setting."""
    return build_hhs_settings_plugin_command(["execute", "del", setting])


def build_hhs_settings_delete_many_command(settings: list[str]) -> str:
    """Build the command that deletes selected overridden system settings."""
    delete_commands = " ".join(
        f"__hhs settings execute del {shlex.quote(setting)} || exit $?;"
        for setting in settings
    )
    return build_hhs_settings_plugin_prefix() + delete_commands


def build_hhs_settings_truncate_command() -> str:
    """Build the command that deletes all overridden system settings."""
    return build_hhs_settings_plugin_command(["execute", "truncate", "-f"])


def build_hhs_starship_preset_command(preset: str) -> str:
    """Build the Starship plug-in command that applies one preset."""
    return build_hhs_starship_plugin_command(["preset", preset])


def build_hhs_save_starship_config_command(config_content: str) -> str:
    """Build the Bash command used to save the editable Starship config file."""
    encoded_config = b64encode(config_content.encode("utf-8")).decode("ascii")
    return (
        build_hhs_env_environment_command()
        + 'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        + 'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/starship/starship.bash"; '
        + f"encoded_config={shlex.quote(encoded_config)}; "
        + 'config_file="${STARSHIP_CONFIG}"; '
        + 'mkdir -p "$(dirname "${config_file}")" || exit 2; '
        + 'tmp_config="$(mktemp "${TMPDIR:-/tmp}/hhs-starship-config.XXXXXX")" || exit 2; '
        + 'if printf "%s" "${encoded_config}" | base64 --decode >"${tmp_config}" 2>/dev/null '
        + '|| printf "%s" "${encoded_config}" | base64 -d >"${tmp_config}" 2>/dev/null '
        + '|| printf "%s" "${encoded_config}" | base64 -D >"${tmp_config}" 2>/dev/null; then '
        + 'mv "${tmp_config}" "${config_file}" || exit 2; '
        + 'printf "Saved Starship config: %s\\n" "${config_file}"; '
        + "else "
        + 'rm -f "${tmp_config}"; '
        + 'echo "Unable to decode Starship config content." >&2; '
        + "exit 2; "
        + "fi"
    )


def build_hhs_save_firebase_config_command(config_content: str) -> str:
    """Build the Bash command used to save the Firebase config file."""
    encoded_config = b64encode(config_content.encode("utf-8")).decode("ascii")
    return (
        build_hhs_env_environment_command()
        + f"encoded_config={shlex.quote(encoded_config)}; "
        + 'export HHS_FIREBASE_CONFIG_FILE="${HHS_FIREBASE_CONFIG_FILE:-${HHS_DIR}/firebase.properties}"; '
        + 'config_file="${HHS_FIREBASE_CONFIG_FILE}"; '
        + 'mkdir -p "$(dirname "${config_file}")" || exit 2; '
        + 'tmp_config="$(mktemp "${TMPDIR:-/tmp}/hhs-firebase-config.XXXXXX")" || exit 2; '
        + 'if printf "%s" "${encoded_config}" | base64 --decode >"${tmp_config}" 2>/dev/null '
        + '|| printf "%s" "${encoded_config}" | base64 -d >"${tmp_config}" 2>/dev/null '
        + '|| printf "%s" "${encoded_config}" | base64 -D >"${tmp_config}" 2>/dev/null; then '
        + 'mv "${tmp_config}" "${config_file}" || exit 2; '
        + 'printf "Saved Firebase configuration: %s\\n" "${config_file}"; '
        + "else "
        + 'rm -f "${tmp_config}"; '
        + 'echo "Unable to decode Firebase config content." >&2; '
        + "exit 2; "
        + "fi"
    )


def build_ssh_tunnels_command(host: str) -> str:
    """Build a local command that lists configured and active SSH tunnel data."""
    safe_host = shlex.quote(host)
    safe_config_option = ssh_config_option()
    return (
        'printf "%s\\n" "__HHS_SSH_CONFIG__"; '
        f"ssh {safe_config_option} -G {safe_host} 2>/dev/null || true; "
        'printf "%s\\n" "__HHS_SSH_PROCESSES__"; '
        "ps -axo pid=,command= 2>/dev/null || true"
    )


def build_hhs_tools_command() -> str:
    """Build the Bash command used to run the __hhs_tools HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_OS="$(uname -s)"; '
        "unset HHS_ACTIVE_DOTFILES; "
        "shopt -s expand_aliases; "
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_icons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_env.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_aliases.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toolcheck.bash"; '
        "__hhs_tools"
    )


def build_hhs_shopt_setup_command() -> str:
    """Build the common Bash setup command used by __hhs_shopt UI calls."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_SHOPTS_FILE="${HHS_SHOPTS_FILE:-${HHS_DIR}/shell-opts.toml}"; '
        'mkdir -p "${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_icons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toml.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-shell-utils.bash"; '
        'if [[ ! -s "${HHS_SHOPTS_FILE}" ]]; then '
        '\\shopt | awk \'{print $1" = "$2}\' >"${HHS_SHOPTS_FILE}"; '
        "fi; "
    )


def build_hhs_shopt_load_saved_command() -> str:
    """Build a Bash command that applies saved shell options to this process."""
    return (
        'if [[ -s "${HHS_SHOPTS_FILE}" ]]; then '
        "while IFS= read -r line; do "
        'if [[ "${line}" =~ ^([a-zA-Z0-9_]+)[[:space:]]*='
        "[[:space:]]*([Oo][Nn]|[Oo][Ff][Ff])$ ]]; then "
        'option="${BASH_REMATCH[1]}"; state="${BASH_REMATCH[2]}"; '
        'if [[ "${state}" =~ ^[Oo][Nn]$ ]]; then '
        'shopt -s "${option}" 2>/dev/null || true; '
        "else "
        'shopt -u "${option}" 2>/dev/null || true; '
        "fi; "
        "fi; "
        'done < "${HHS_SHOPTS_FILE}"; '
        "fi; "
    )


def build_hhs_shopt_command() -> str:
    """Build the Bash command used to run the __hhs_shopt listing function."""
    return (
        build_hhs_shopt_setup_command()
        + build_hhs_shopt_load_saved_command()
        + "__hhs_shopt -p"
    )


def build_hhs_shopt_action_command(operation: str, option_name: str) -> str:
    """Build the Bash command used to set or unset a shell option."""
    action = "-s" if operation == "set" else "-u"
    return (
        build_hhs_shopt_setup_command()
        + f"__hhs_shopt {action} {shlex.quote(option_name)}"
    )


def build_docker_ps_command() -> str:
    """Build the Bash command used to list Docker containers."""
    return (
        "docker ps -a --format "
        "'table {{.ID}}\t{{.Image}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}'"
    )


def build_docker_images_command() -> str:
    """Build the Bash command used to list Docker images."""
    return (
        "docker images --format "
        "'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}'"
    )


def build_docker_agent_check_command() -> str:
    """Build the Bash command used to check whether Docker is running."""
    return "docker ps -q >/dev/null 2>&1"


def build_docker_container_action_command(operation: str, container_id: str) -> str:
    """Build the Bash command used to run an action against a Docker container."""
    if operation not in {"start", "stop", "rm"}:
        raise ValueError(f"Unsupported Docker container operation: {operation}")
    return f"docker {operation} {shlex.quote(container_id)}"


def build_docker_image_delete_command(image_id: str) -> str:
    """Build the Bash command used to remove a Docker image."""
    return f"docker image rm -f {shlex.quote(image_id)}"


def _build_hhs_hspm_command_prefix() -> str:
    """Build the shell setup shared by HSPM commands and metadata output."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_OS="$(uname -s)"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'export PLUGINS_DIR="${HHS_HOME}/bin/apps/bash/hhs-app/plugins"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_colors.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_env.bash"; '
    )


def _build_hhs_hspm_environment_output() -> str:
    """Build marked HSPM environment output for catalog and recovery titles."""
    return (
        f'printf "%s\\n" "{HHS_HSPM_ENV_OUTPUT_MARKER}"; '
        'printf "HHS_MY_OS\\t%s\\nHHS_MY_OS_PACKMAN\\t%s\\n" '
        '"${HHS_MY_OS}" "${HHS_MY_OS_PACKMAN}"; '
    )


def build_hhs_hspm_command(
    operation: str,
    tool_name: str | list[str] | tuple[str, ...] = "",
) -> str:
    """Build the Bash command used to run an hspm tool operation."""
    safe_operation = (
        operation
        if operation
        in {"install", "uninstall", "reinstall", "list", "recover", "sync"}
        else ""
    )
    if isinstance(tool_name, str):
        tool_names = [tool_name]
    else:
        tool_names = list(tool_name)
    safe_tool_names = " ".join(
        shlex.quote(name.strip()) for name in tool_names if name.strip()
    )
    safe_tool_args = f" {safe_tool_names}" if safe_tool_names else ""
    return (
        _build_hhs_hspm_command_prefix()
        + 'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/hspm/hspm.bash"; '
        'function __hhs() { if [[ "$1" == "hspm" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        + (
            _build_hhs_hspm_environment_output()
            if safe_operation in {"list", "recover"}
            else ""
        )
        + f"__hhs hspm execute {safe_operation}{safe_tool_args}"
    )


def build_tool_tldr_command(tool_name: str) -> str:
    """Build the Bash command used to read TLDR help for a tool."""
    return f"tldr {shlex.quote(tool_name.strip())}"


def build_hhs_history_command() -> str:
    """Build the Bash command used to run the __hhs_history HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HISTSIZE="${HISTSIZE:-2000}"; '
        'export HISTFILESIZE="${HISTFILESIZE:-2000}"; '
        'export HISTFILE="${HISTFILE:-${HOME}/.bash_history}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-shell-utils.bash"; '
        "__hhs_history"
    )


def build_hhs_history_dirs_command() -> str:
    """Build the Bash command used to run the __hhs_dirs HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_DIRS_FILE="${HHS_DIRS_FILE:-${HHS_DIR}/.dirs}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash"; '
        "__hhs_dirs -l"
    )


def build_hhs_history_stats_command(top_n: int = 10) -> str:
    """Build the Bash command used to run the __hhs_hist_stats HomeSetup function."""
    safe_top_n = max(
        hhs_ui_constants.MIN_TOP_N,
        min(int(top_n), hhs_ui_constants.MAX_TOP_N),
    )
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-shell-utils.bash"; '
        f"__hhs_hist_stats {safe_top_n}"
    )


def build_process_monitor_command(metric: str, top_n: int = 10) -> str:
    """Build the shell command used to load process monitor data."""
    safe_top_n = max(
        hhs_ui_constants.MIN_TOP_N,
        min(int(top_n), hhs_ui_constants.MAX_TOP_N),
    )
    sort_keys = hhs_ui.TOP_PROCESS_SORT_KEYS.get(
        metric, hhs_ui.TOP_PROCESS_SORT_KEYS["CPU"]
    )
    darwin_sort = sort_keys["darwin"]
    linux_sort = sort_keys["linux"]
    ps_sort = "-r" if metric == "CPU" else "-m"
    linux_ps_sort = "pcpu" if metric == "CPU" else "pmem"
    linux_top_sample = (
        f"top -b -n 2 -d 1 -o {linux_sort} -w 512"
        if metric == "CPU"
        else f"top -b -n 1 -o {linux_sort} -w 512"
    )
    return (
        'if [[ "$(uname -s)" == "Darwin" ]]; then '
        f"top -l 2 -s 1 -o {darwin_sort} -n {safe_top_n} 2>/dev/null || "
        f"ps -axo pid,user,%cpu,%mem,comm {ps_sort} 2>/dev/null | head -n {safe_top_n + 1}; "
        "else "
        f"{linux_top_sample} 2>/dev/null || "
        f"ps -eo pid,user,%cpu,%mem,comm --sort=-{linux_ps_sort} 2>/dev/null | head -n {safe_top_n + 1}; "
        "fi"
    )


def build_hhs_process_list_command(process_filter: str) -> str:
    """Build the Bash command used to list processes via HomeSetup."""
    safe_filter = process_filter.strip() or "."
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-sys-utils.bash"; '
        f"__hhs_process_list {shlex.quote(safe_filter)}"
    )


def build_hhs_process_kill_command(process_name: str) -> str:
    """Build the Bash command used to kill a process via HomeSetup."""
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-sys-utils.bash"; '
        f"__hhs_process_kill -f {shlex.quote(process_name)}"
    )


def build_hhs_logs_command(
    log_file: str,
    tail_lines: int = hhs_ui_constants.DEFAULT_LOG_TAIL_LINES,
    log_level: str = "ALL_LEVELS",
) -> str:
    """Build the Bash command used to run the __hhs logs command."""
    safe_log_file = Path(log_file).name
    safe_tail_lines = normalized_monitor_log_tail_lines(tail_lines)
    safe_log_level = log_level if log_level in hhs_ui.LOG_LEVELS else "ALL_LEVELS"
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'export HHS_LOG_FILE="${HHS_LOG_DIR}/hhs.log"; '
        'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-taylor.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/functions/built-ins.bash"; '
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; return "${exit_code}"; }; '
        'function __hhs() { if [[ "$1" == "logs" ]]; then shift; logs "$@"; else return 127; fi; }; '
        f"__hhs logs -n {safe_tail_lines} {shlex.quote(safe_log_file)} {shlex.quote(safe_log_level)}"
    )


def build_hhs_ask_execute_command(arguments: list[str]) -> str:
    """Build the Bash command used to run the __hhs ask execute command."""
    safe_arguments = " ".join(shlex.quote(argument) for argument in arguments)
    return build_hhs_ask_plugin_command(
        'function __hhs() { if [[ "$1" == "ask" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f"__hhs ask execute {safe_arguments}"
    )


def build_hhs_ask_plugin_command(command: str) -> str:
    """Build a Bash command that loads the ask plugin support before running a command."""
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_SETUP_FILE="${HHS_SETUP_FILE:-${HHS_DIR}/.homesetup.toml}"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'export HHS_LOG_FILE="${HHS_LOG_FILE:-${HHS_LOG_DIR}/hhs-ui.log}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'export HHS_MY_OS="$(uname -s)"; '
        'export HHS_MY_OS_RELEASE="${HHS_MY_OS_RELEASE:-${HHS_MY_OS}}"; '
        'export HHS_OLLAMA_HISTORY_FILE="${HHS_OLLAMA_HISTORY_FILE:-${HHS_DIR}/.ollama_history}"; '
        "export HHS_OLLAMA_MD_VIEWER=cat; "
        'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        "export IS_PIPED=0; "
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_colors.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toml.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"; '
        f"{command}"
    )


def build_hhs_ask_command(message: str) -> str:
    """Build the Bash command used to run the __hhs ask command."""
    return build_hhs_ask_execute_command(["-k", message])


def build_hhs_ask_context_command() -> str:
    """Build the Bash command used to show the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-c"])


def build_hhs_ask_prompt_file_command() -> str:
    """Build the Bash command used to read the editable Ollama ask prompt file."""
    return build_hhs_ask_plugin_command(
        '[[ -r "${HHS_OLLAMA_PROMPT_FILE}" ]] || { '
        'echo "Ollama prompt file not found: ${HHS_OLLAMA_PROMPT_FILE}" >&2; '
        "exit 2; "
        "}; "
        'cat "${HHS_OLLAMA_PROMPT_FILE}"'
    )


def build_hhs_save_ask_prompt_file_command(prompt_text: str) -> str:
    """Build the Bash command used to save the editable Ollama ask prompt file."""
    encoded_prompt = b64encode(prompt_text.encode("utf-8")).decode("ascii")
    return build_hhs_ask_plugin_command(
        f"encoded_prompt={shlex.quote(encoded_prompt)}; "
        'prompt_file="${HHS_OLLAMA_PROMPT_FILE}"; '
        'mkdir -p "$(dirname "${prompt_file}")" || exit 2; '
        'tmp_prompt="$(mktemp "${TMPDIR:-/tmp}/hhs-ask-prompt.XXXXXX")" || exit 2; '
        'if printf "%s" "${encoded_prompt}" | base64 --decode >"${tmp_prompt}" 2>/dev/null '
        '|| printf "%s" "${encoded_prompt}" | base64 -d >"${tmp_prompt}" 2>/dev/null '
        '|| printf "%s" "${encoded_prompt}" | base64 -D >"${tmp_prompt}" 2>/dev/null; then '
        'mv "${tmp_prompt}" "${prompt_file}" || exit 2; '
        'printf "Saved prompt: %s\\n" "${prompt_file}"; '
        "else "
        'rm -f "${tmp_prompt}"; '
        'echo "Unable to decode prompt content." >&2; '
        "exit 2; "
        "fi"
    )


def build_hhs_revert_ask_prompt_file_command() -> str:
    """Build the Bash command used to restore the editable Ollama ask prompt file."""
    return build_hhs_ask_plugin_command(
        '[[ -r "${HHS_OLLAMA_PROMPT_SOURCE}" ]] || { '
        'echo "Ollama prompt source file not found: ${HHS_OLLAMA_PROMPT_SOURCE}" >&2; '
        "exit 2; "
        "}; "
        'mkdir -p "$(dirname "${HHS_OLLAMA_PROMPT_FILE}")" || exit 2; '
        'cp -f "${HHS_OLLAMA_PROMPT_SOURCE}" "${HHS_OLLAMA_PROMPT_FILE}" || exit 2; '
        'cat "${HHS_OLLAMA_PROMPT_FILE}"'
    )


def build_hhs_ask_reset_command() -> str:
    """Build the Bash command used to reset the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-r"])


def build_hhs_ask_ingest_command(file_path: str) -> str:
    """Build the Bash command used to ingest the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-i", file_path])


def build_hhs_ask_models_command() -> str:
    """Build the Bash command used to list Ollama ask models."""
    return build_hhs_ask_execute_command(["-m"])


def build_hhs_ask_select_model_command(model_name: str) -> str:
    """Build the Bash command used to select the active Ollama ask model."""
    return build_hhs_ask_execute_command(["-s", model_name])


def build_ollama_delete_model_command(model_name: str) -> str:
    """Build the Bash command used to delete an Ollama model."""
    return f"ollama rm {shlex.quote(model_name)}"


def build_hhs_path_environment_command() -> str:
    """Build the shell prefix that reconstructs the HomeSetup PATH environment."""
    return (
        'export HHS_HOME="${HHS_HOME:-${HOME}/HomeSetup}"; '
        'export HHS_DIR="${HHS_DIR:-${HOME}/.config/hhs}"; '
        'export HHS_PATHS_FILE="${HHS_PATHS_FILE:-${HHS_DIR}/.path}"; '
        'export HHS_VENV_PATH="${HHS_VENV_PATH:-${HHS_DIR}/venv}"; '
        'for hhs_path in "${HOME}/bin" "${HOME}/.local/bin" '
        '"${HHS_DIR}/bin" "${HHS_HOME}/tests/bats/bats-core/bin"; do '
        '[[ -d "${hhs_path}" ]] && PATH="${PATH}:${hhs_path}"; '
        "done; "
        'if [[ -f "${HHS_PATHS_FILE}" ]]; then '
        "while IFS= read -r hhs_path; do "
        '[[ -n "${hhs_path}" ]] && PATH="${hhs_path}:${PATH}"; '
        'done < <(grep . "${HHS_PATHS_FILE}" | grep -v -e "^$"); '
        "fi; "
        '[[ -d "${HHS_VENV_PATH}/bin" ]] && PATH="${HHS_VENV_PATH}/bin:${PATH}"; '
        "PATH=\"$(awk -v RS=: 'NF && !seen[$0]++ {"
        'printf "%s%s", sep, $0; sep=":"'
        '}\' <<<"${PATH}")"; '
        "export PATH; "
    )


def build_hhs_paths_raw_entries_command() -> str:
    """Build the shell suffix that emits parse-safe PATH entries for the UI."""
    return (
        'printf "\\n"; '
        "while IFS= read -r hhs_path; do "
        f'printf "{HHS_PATHS_RAW_ENTRY_MARKER}\\t%s\\n" "${{hhs_path}}"; '
        'done < <(printf "%s\\n" "${PATH}" | tr ":" "\\n")'
    )


def build_hhs_paths_command() -> str:
    """Build the Bash command used to run the __hhs_paths HomeSetup function."""
    return (
        build_hhs_path_environment_command() + 'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-paths.bash"; '
        "__hhs_paths; " + build_hhs_paths_raw_entries_command()
    )


def build_hhs_path_action_command(
    operation: str, path_value: str, old_path_value: str = ""
) -> str:
    """Build the Bash command used to add, edit, or delete a persistent PATH value."""
    safe_path = shlex.quote(path_value)
    if operation == "del":
        action_args = f"-r {safe_path}"
    elif operation == "edit" and old_path_value and old_path_value != path_value:
        safe_old_path = shlex.quote(old_path_value)
        action_args = f"-r {safe_old_path}; __hhs_paths -a {safe_path}"
    else:
        action_args = f"-a {safe_path}"
    return (
        build_hhs_path_environment_command() + 'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-paths.bash"; '
        f"__hhs_paths {action_args}"
    )


def build_hhs_dirs_command() -> str:
    """Build the Bash command used to run the __hhs_load_dir HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash"; '
        "__hhs_load_dir -l"
    )


def build_hhs_dir_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a saved directory."""
    safe_name = shlex.quote(name)
    if operation == "del":
        action_args = f"-r {safe_name}"
    else:
        action_args = f"{shlex.quote(value)} {safe_name}"
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash"; '
        f"__hhs_save_dir {action_args}"
    )


def build_hhs_commands_command() -> str:
    """Build the Bash command used to run the __hhs_command HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-command.bash"; '
        "__hhs_command -l"
    )


def build_hhs_command_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a saved command."""
    safe_name = shlex.quote(name)
    if operation == "del":
        action_args = f"-r {safe_name}"
    else:
        action_args = f"-a {safe_name} {shlex.quote(value)}"
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-command.bash"; '
        f"__hhs_command {action_args}"
    )


def build_hhs_aliases_command() -> str:
    """Build the Bash command used to run the __hhs_aliases HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-aliases.bash"; '
        "__hhs_aliases -l"
    )


def build_hhs_alias_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a custom alias."""
    safe_name = shlex.quote(name)
    action_args = (
        f"-r {safe_name}" if operation == "del" else f"{safe_name} {shlex.quote(value)}"
    )
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-aliases.bash"; '
        f"__hhs_aliases {action_args}"
    )


def build_hhs_services_command(
    operation: str = "status", service_name: str = ""
) -> str:
    """Build the Bash command used to run the __hhs_services HomeSetup function."""
    safe_operation = re.sub(r"[^A-Za-z_-]+", "", operation) or "status"
    safe_service_name = service_name.replace("\\", "\\\\").replace('"', '\\"')
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/services/services.bash"; '
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; exit "${exit_code}"; }; '
        'function __hhs() { if [[ "$1" == "services" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f'__hhs services execute "{safe_operation}" "{safe_service_name}"'
    )


def row_matches_text_filter(row: dict[str, str], text_filter: str) -> bool:
    """Return whether a row contains the selected free-text filter."""
    clean_filter = text_filter.strip().lower()
    if not clean_filter:
        return True
    searchable_value = " ".join(str(value).lower() for value in row.values())
    return clean_filter in searchable_value


def filter_env_rows(
    rows: list[dict[str, str]], env_filter: str = "All", other_filter: str = ""
) -> list[dict[str, str]]:
    """Return environment rows matching the selected UI filter."""
    if env_filter == "HHS":
        return [row for row in rows if row.get("Name", "").startswith("HHS_")]
    if env_filter in ("Other", "Containing"):
        return [row for row in rows if row_matches_text_filter(row, other_filter)]
    return rows


def filter_shopt_rows(
    rows: list[dict[str, str]], shopt_filter: str = "All", other_filter: str = ""
) -> list[dict[str, str]]:
    """Return shell option rows matching the selected UI filter."""
    if shopt_filter == "ON":
        return [row for row in rows if row.get("State") == "ON"]
    if shopt_filter == "OFF":
        return [row for row in rows if row.get("State") == "OFF"]
    if shopt_filter in ("Other", "Containing"):
        return [row for row in rows if row_matches_text_filter(row, other_filter)]
    return rows


def path_row_matches_filter(
    row: dict[str, str], path_filter: str, other_filter: str = ""
) -> bool:
    """Return whether a PATH row matches the selected UI filter."""
    if path_filter == "All":
        return True
    searchable_origin = row.get("Origin", "").lower()
    if path_filter == "Shell":
        return "shell" in searchable_origin
    if path_filter == "Private":
        return "private" in searchable_origin
    if path_filter == "Custom":
        return "custom" in searchable_origin
    if path_filter in ("Other", "Containing"):
        return row_matches_text_filter(row, other_filter)
    return True


def filter_path_rows(
    rows: list[dict[str, str]],
    path_filter: str,
    other_filter: str = "",
) -> list[dict[str, str]]:
    """Return PATH rows that match the selected UI filter."""
    return [
        row for row in rows if path_row_matches_filter(row, path_filter, other_filter)
    ]


def filter_rows_by_text(
    rows: list[dict[str, str]], list_filter: str, text_filter: str = ""
) -> list[dict[str, str]]:
    """Return rows that match the selected all/text filter."""
    if list_filter not in ("Other", "Others", "Containing"):
        return rows
    return [row for row in rows if row_matches_text_filter(row, text_filter)]


def filter_process_rows(
    rows: list[dict[str, str]],
    process_filter: str,
    text_filter: str = "",
) -> list[dict[str, str]]:
    """Return process rows matching the selected process status filter."""
    if process_filter in ("Other", "Containing"):
        return [row for row in rows if row_matches_text_filter(row, text_filter)]
    if process_filter == "All":
        return rows
    return [
        row
        for row in rows
        if row.get("Status", "").lower() == process_filter.strip().lower()
    ]


def parse_hhs_envs(output: str) -> list[dict[str, str]]:
    """Parse __hhs_envs terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.ENV_LINE_PATTERN.match(line.strip())
        if match:
            rows.append({"Name": match.group(1), "Value": match.group(2).strip()})
    return rows


def parse_hhs_tools(output: str) -> list[dict[str, str]]:
    """Parse __hhs_tools terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.TOOL_LINE_PATTERN.match(line.strip())
        if match:
            status = match.group(4).strip()
            glyph = match.group(3).strip()
            rows.append(
                {
                    "Tool": match.group(2).strip(),
                    "Status": f"{glyph} {status}",
                    "Path": (match.group(5) or "").strip(),
                }
            )
    return rows


def shopt_status_value(state: str) -> str:
    """Return the visible shell option status with an on/off glyph."""
    clean_state = state.strip().upper()
    return f" {clean_state}" if clean_state == "ON" else f" {clean_state}"


def shopt_description(option_name: str) -> str:
    """Return a compact Bash shell option description."""
    return SHOPT_DESCRIPTIONS.get(
        option_name.strip(),
        "Shell option available in this Bash version.",
    )


def parse_hhs_shopt(output: str) -> list[dict[str, str]]:
    """Parse __hhs_shopt terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.SHOPT_LINE_PATTERN.match(line.strip())
        if match:
            state = match.group(2).strip().upper()
            rows.append(
                {
                    "Status": shopt_status_value(state),
                    "Option": match.group(3).strip(),
                    "Description": shopt_description(match.group(3).strip()),
                    "State": state,
                }
            )
    return rows


def parse_hhs_dirs(output: str) -> list[dict[str, str]]:
    """Parse __hhs_load_dir list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.DIR_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {"Name": match.group(1).strip(), "Value": match.group(2).strip()}
            )
    return rows


def parse_hhs_commands(output: str) -> list[dict[str, str]]:
    """Parse __hhs_command list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.COMMAND_LINE_PATTERN.match(line.strip())
        if match:
            command_name = re.sub(r"^Command\s+", "", match.group(2).strip())
            rows.append(
                {
                    "Index": match.group(1).strip(),
                    "Name": command_name,
                    "Value": match.group(3).strip(),
                }
            )
    return rows


def parse_hhs_aliases(output: str) -> list[dict[str, str]]:
    """Parse __hhs_aliases list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.ALIAS_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {"Name": match.group(1).strip(), "Value": match.group(2).strip()}
            )
    return rows


def parse_hhs_setup_settings(output: str) -> dict[str, bool]:
    """Parse setup TOML key/value output into a settings mapping."""
    settings: dict[str, bool] = {}
    for line in strip_ansi(output).splitlines():
        clean_line = line.strip()
        if "=" not in clean_line:
            continue
        name, value = clean_line.split("=", 1)
        clean_name = name.strip()
        if clean_name not in HHS_SETUP_SETTINGS:
            continue
        settings[clean_name] = value.strip().lower() in {"1", "true", "yes", "on"}
    return settings


def hhs_settings_ini_file() -> Path:
    """Return the bundled settings catalog file."""
    return homesetup_home() / "assets" / "settings.ini"


def load_hhs_settings_defaults() -> dict[str, str]:
    """Load dotted setting names and default values from assets/settings.ini."""
    settings_file = hhs_settings_ini_file()
    if not settings_file.is_file():
        return {}
    settings: dict[str, str] = {}
    for raw_line in settings_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("[") or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        clean_name = name.strip()
        if clean_name and clean_name not in settings:
            settings[clean_name] = value.strip() if separator else ""
    return settings


def hhs_setting_variable_name(setting: str) -> str:
    """Return the environment variable name for a dotted setting."""
    return re.sub(r"[\s.-]+", "_", setting.strip()).upper()


def setman_table_cells(line: str) -> list[str]:
    """Return cells from one Setman box-table row."""
    clean_line = line.strip()
    if not clean_line.startswith("|") or not clean_line.endswith("|"):
        return []
    cells = [cell.strip() for cell in clean_line.strip("|").split("|")]
    if len(cells) < 5:
        return []
    if cells[0].upper() == "NAME" or "<empty>" in cells[0].lower():
        return []
    return cells[:5]


def hhs_settings_row_setting(prefix: str, name: str) -> str:
    """Return one dotted HHS setting name from Setman prefix and name fields."""
    return ".".join(part for part in (prefix.strip(), name.strip()) if part)


def hhs_settings_csv_row(row: dict[str, str]) -> dict[str, str]:
    """Return one Settings UI table row from a Setman CSV row."""
    setting = hhs_settings_row_setting(
        row.get("prefix", ""),
        row.get("name", ""),
    )
    return {
        "Setting": setting,
        "Variable": hhs_setting_variable_name(setting),
        "Value": row.get("value", ""),
    }


def parse_hhs_settings_list(output: str) -> list[dict[str, str]]:
    """Parse Setman list output into Settings table rows."""
    clean_output = strip_ansi(output)
    csv_lines = [
        line
        for line in clean_output.splitlines()
        if line.strip() and not line.lstrip().startswith("[")
    ]
    if csv_lines and csv_lines[0].strip().lower().startswith("uuid,name,prefix,value,"):
        return [
            hhs_settings_csv_row(row)
            for row in csv.DictReader(csv_lines)
            if row.get("name", "").strip()
        ]

    rows: list[dict[str, str]] = []
    for line in clean_output.splitlines():
        cells = setman_table_cells(line)
        if not cells:
            continue
        name, prefix, value, _settings_type, _modified = cells
        setting = hhs_settings_row_setting(prefix, name)
        if not setting:
            continue
        rows.append(
            {
                "Setting": setting,
                "Variable": hhs_setting_variable_name(setting),
                "Value": value,
            }
        )
    return rows


def parse_hhs_config_environment(lines: list[str]) -> dict[str, str]:
    """Parse marked HomeSetup config environment lines into name/value pairs."""
    values: dict[str, str] = {}
    for line in "".join(lines).splitlines():
        if "\t" not in line:
            continue
        name, value = line.split("\t", 1)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            values[name] = value
    return values


def parse_hhs_starship_info(output: str) -> dict[str, object]:
    """Parse marker-delimited Starship info and config output."""
    markers = {
        STARSHIP_CACHE_OUTPUT_MARKER,
        STARSHIP_CONFIG_OUTPUT_MARKER,
        STARSHIP_HHS_DIR_OUTPUT_MARKER,
        HHS_CONFIG_ENV_OUTPUT_MARKER,
        STARSHIP_PRESETS_OUTPUT_MARKER,
        STARSHIP_CONFIG_CONTENT_OUTPUT_MARKER,
        STARSHIP_END_OUTPUT_MARKER,
    }
    sections: dict[str, list[str]] = {marker: [] for marker in markers}
    current_marker = ""
    for line in strip_ansi(output).splitlines(keepends=True):
        clean_line = line.rstrip("\r\n")
        if clean_line in markers:
            current_marker = clean_line
            continue
        if current_marker and current_marker != STARSHIP_END_OUTPUT_MARKER:
            sections[current_marker].append(line)

    cache_path = "".join(sections[STARSHIP_CACHE_OUTPUT_MARKER]).strip()
    config_path = "".join(sections[STARSHIP_CONFIG_OUTPUT_MARKER]).strip()
    hhs_dir = "".join(sections[STARSHIP_HHS_DIR_OUTPUT_MARKER]).strip()
    environment = parse_hhs_config_environment(sections[HHS_CONFIG_ENV_OUTPUT_MARKER])
    if hhs_dir and "HHS_DIR" not in environment:
        environment["HHS_DIR"] = hhs_dir
    if config_path and "STARSHIP_CONFIG" not in environment:
        environment["STARSHIP_CONFIG"] = config_path
    presets = [
        preset.strip()
        for preset in "".join(sections[STARSHIP_PRESETS_OUTPUT_MARKER]).splitlines()
        if preset.strip()
    ]
    config_content = "".join(sections[STARSHIP_CONFIG_CONTENT_OUTPUT_MARKER])
    return {
        "cache": cache_path,
        "config": config_path,
        "hhs_dir": hhs_dir,
        "environment": environment,
        "presets": presets,
        "content": config_content.rstrip("\n"),
    }


def parse_hhs_properties(content: str) -> dict[str, str]:
    """Parse simple Java-style property assignments into a dictionary."""
    properties: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";", "[")):
            continue
        match = re.match(r"^([^:=\s][^:=]*?)\s*[:=]\s*(.*)$", line)
        if not match:
            continue
        properties[match.group(1).strip()] = match.group(2).strip()
    return properties


def hhs_firebase_config_aliases() -> dict[str, str]:
    """Return Firebase config file property aliases mapped to canonical keys."""
    aliases: dict[str, str] = {}
    for _label, property_name, fallback_property_name, _state_key, _placeholder in (
        HHS_FIREBASE_FIELDS
    ):
        aliases[property_name] = property_name
        aliases[fallback_property_name] = property_name
    return aliases


def parse_hhs_firebase_info(output: str) -> dict[str, object]:
    """Parse marker-delimited Firebase config file info."""
    markers = {
        FIREBASE_CONFIG_FILE_OUTPUT_MARKER,
        HHS_CONFIG_ENV_OUTPUT_MARKER,
        FIREBASE_CONFIG_CONTENT_OUTPUT_MARKER,
        FIREBASE_CONFIG_END_OUTPUT_MARKER,
    }
    sections: dict[str, list[str]] = {marker: [] for marker in markers}
    current_marker = ""
    for line in strip_ansi(output).splitlines(keepends=True):
        clean_line = line.rstrip("\r\n")
        if clean_line in markers:
            current_marker = clean_line
            continue
        if current_marker and current_marker != FIREBASE_CONFIG_END_OUTPUT_MARKER:
            sections[current_marker].append(line)

    config_file = "".join(sections[FIREBASE_CONFIG_FILE_OUTPUT_MARKER]).strip()
    content = "".join(sections[FIREBASE_CONFIG_CONTENT_OUTPUT_MARKER]).rstrip("\n")
    environment = parse_hhs_config_environment(sections[HHS_CONFIG_ENV_OUTPUT_MARKER])
    if config_file and "HHS_FIREBASE_CONFIG_FILE" not in environment:
        environment["HHS_FIREBASE_CONFIG_FILE"] = config_file
    properties = parse_hhs_properties(content)
    values = {
        property_name: properties.get(
            property_name,
            properties.get(fallback_property_name, ""),
        )
        for _label, property_name, fallback_property_name, _state_key, _placeholder in (
            HHS_FIREBASE_FIELDS
        )
    }
    return {
        "config_file": config_file,
        "environment": environment,
        "content": content,
        "values": values,
    }


def normalize_hhs_firebase_value(value: object) -> str:
    """Return one safe single-line Firebase property value."""
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def render_hhs_firebase_config_content(
    original_content: str,
    values: dict[str, str],
) -> str:
    """Return Firebase config content with form values merged into it."""
    remaining_fields = {
        property_name
        for _label, property_name, _fallback, _state_key, _placeholder in (
            HHS_FIREBASE_FIELDS
        )
    }
    config_aliases = hhs_firebase_config_aliases()
    rendered_lines: list[str] = []
    property_pattern = re.compile(r"^(\s*)([^:=\s][^:=]*?)(\s*[:=]\s*)(.*)$")
    for raw_line in original_content.splitlines():
        match = property_pattern.match(raw_line)
        if not match:
            rendered_lines.append(raw_line)
            continue
        prefix, property_name, separator, _old_value = match.groups()
        source_property_name = property_name.strip()
        canonical_property_name = config_aliases.get(source_property_name)
        if canonical_property_name not in values:
            rendered_lines.append(raw_line)
            continue
        if source_property_name != canonical_property_name:
            rendered_lines.append(
                f"{prefix}{source_property_name}{separator}"
                f"{normalize_hhs_firebase_value(values[canonical_property_name])}"
            )
            continue
        if canonical_property_name not in remaining_fields:
            continue
        rendered_lines.append(
            f"{prefix}{source_property_name}{separator}"
            f"{normalize_hhs_firebase_value(values[canonical_property_name])}"
        )
        remaining_fields.remove(canonical_property_name)

    for _label, property_name, _fallback, _state_key, _placeholder in HHS_FIREBASE_FIELDS:
        if property_name in remaining_fields:
            rendered_lines.append(
                f"{property_name}={normalize_hhs_firebase_value(values.get(property_name, ''))}"
            )

    return "\n".join(rendered_lines).rstrip("\n") + "\n"


def parse_hhs_services(output: str) -> list[dict[str, str]]:
    """Parse HomeSetup services list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.SERVICE_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {
                    "Name": match.group(2).strip(),
                    "Value": f"{match.group(3).strip()} {match.group(4).strip()}",
                }
            )
    return rows


def split_ssh_command(command: str) -> list[str]:
    """Return shell tokens for an SSH process command."""
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def ssh_command_executable_name(args: list[str]) -> str:
    """Return the executable name from a parsed SSH command."""
    if not args:
        return ""
    return Path(args[0]).name


def ssh_forward_spec_parts(spec: str, dynamic: bool = False) -> tuple[str, str]:
    """Return display bind and destination values for an SSH forward spec."""
    if dynamic:
        return spec, "SOCKS"
    parts = spec.split(":")
    if len(parts) >= 4:
        return ":".join(parts[:-2]), ":".join(parts[-2:])
    if len(parts) == 3:
        return parts[0], ":".join(parts[1:])
    return spec, ""


def ssh_config_forward_parts(
    parts: list[str], dynamic: bool = False
) -> tuple[str, str]:
    """Return display bind and destination values from SSH config forward values."""
    if not parts:
        return "", ""
    if dynamic:
        return parts[0], "SOCKS"
    if len(parts) >= 2:
        return parts[0], parts[1]
    return ssh_forward_spec_parts(parts[0])


def ssh_process_host(args: list[str]) -> str:
    """Return the destination host argument for a parsed SSH command."""
    options_with_values = {
        "-B",
        "-b",
        "-c",
        "-D",
        "-E",
        "-e",
        "-F",
        "-I",
        "-i",
        "-J",
        "-L",
        "-l",
        "-m",
        "-O",
        "-o",
        "-p",
        "-Q",
        "-R",
        "-S",
        "-W",
        "-w",
    }
    index = 1
    while index < len(args):
        value = args[index]
        if value == "--":
            return args[index + 1] if index + 1 < len(args) else ""
        if value in options_with_values:
            index += 2
            continue
        if value.startswith("-"):
            index += 1
            continue
        return value
    return ""


def ssh_tunnel_row(
    forward_type: str,
    bind: str,
    destination: str,
    ssh_host: str,
    source: str,
    pid: str = "",
    command: str = "",
) -> dict[str, str]:
    """Return one SSH tunnel table row."""
    return {
        "Type": forward_type,
        "Bind": bind,
        "Destination": destination,
        "SSH Host": ssh_host,
        "Source": source,
        "Status": "",
        "PID": pid,
        "Command": command,
    }


def append_ssh_forward_row(
    rows: list[dict[str, str]],
    pid: str,
    command: str,
    ssh_host: str,
    option: str,
    spec: str,
) -> None:
    """Append one SSH forwarding row parsed from a process command."""
    forward_types = {
        "-L": "Local",
        "-R": "Remote",
        "-D": "Dynamic",
    }
    forward_type = forward_types.get(option, option)
    bind, destination = ssh_forward_spec_parts(spec, dynamic=option == "-D")
    rows.append(
        ssh_tunnel_row(
            forward_type, bind, destination, ssh_host, "Process", pid, command
        )
    )


def parse_ssh_config_tunnels(output: str, host: str) -> list[dict[str, str]]:
    """Parse SSH tunnel and port-forward rows from resolved OpenSSH config output."""
    rows: list[dict[str, str]] = []
    forward_types = {
        "localforward": "Local",
        "remoteforward": "Remote",
        "dynamicforward": "Dynamic",
    }
    for raw_line in strip_ansi(output).splitlines():
        parts = raw_line.strip().split()
        if not parts:
            continue
        keyword = parts[0].lower()
        if keyword not in forward_types:
            continue
        dynamic = keyword == "dynamicforward"
        bind, destination = ssh_config_forward_parts(parts[1:], dynamic=dynamic)
        if not bind:
            continue
        rows.append(
            ssh_tunnel_row(
                forward_types[keyword],
                bind,
                destination,
                host,
                "Config",
                command=str(ssh_config_file()),
            )
        )
    return rows


def parse_ssh_tunnel_process(pid: str, command: str) -> list[dict[str, str]]:
    """Parse SSH tunnel and port-forward rows from one process command."""
    args = split_ssh_command(command)
    if ssh_command_executable_name(args) != "ssh":
        return []
    rows: list[dict[str, str]] = []
    ssh_host = ssh_process_host(args)
    index = 1
    while index < len(args):
        value = args[index]
        if value in ("-L", "-R", "-D"):
            if index + 1 < len(args):
                append_ssh_forward_row(
                    rows, pid, command, ssh_host, value, args[index + 1]
                )
            index += 2
            continue
        if len(value) > 2 and value[:2] in ("-L", "-R", "-D"):
            append_ssh_forward_row(rows, pid, command, ssh_host, value[:2], value[2:])
        index += 1
    return rows


def merge_ssh_tunnel_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return SSH tunnel rows merged by forwarding endpoint."""
    merged: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("Type", ""),
            row.get("Bind", ""),
            row.get("Destination", ""),
            row.get("SSH Host", ""),
        )
        if key not in merged:
            merged[key] = dict(row)
            continue
        existing = merged[key]
        sources = {
            source.strip()
            for source in (existing.get("Source", ""), row.get("Source", ""))
            if source.strip()
        }
        existing["Source"] = ", ".join(sorted(sources))
        if row.get("PID"):
            existing["PID"] = row["PID"]
        if row.get("Command") and row.get("Source") == "Process":
            existing["Command"] = row["Command"]
    return list(merged.values())


def parse_ssh_tunnels(output: str, host: str = "") -> list[dict[str, str]]:
    """Parse configured and active SSH tunnel and port-forward rows."""
    config_lines: list[str] = []
    process_lines: list[str] = []
    section = "process"
    for line in strip_ansi(output).splitlines():
        if line.strip() == "__HHS_SSH_CONFIG__":
            section = "config"
            continue
        if line.strip() == "__HHS_SSH_PROCESSES__":
            section = "process"
            continue
        if section == "config":
            config_lines.append(line)
        else:
            process_lines.append(line)

    rows: list[dict[str, str]] = []
    rows.extend(parse_ssh_config_tunnels("\n".join(config_lines), host) if host else [])
    for line in process_lines:
        match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", line)
        if not match:
            continue
        rows.extend(parse_ssh_tunnel_process(match.group(1), match.group(2)))
    return merge_ssh_tunnel_rows(rows)


def normalized_bind_host(host: str) -> str:
    """Return a reachable host name for a tunnel bind address."""
    clean_host = host.strip().strip("[]")
    if clean_host in {"", "*", "0.0.0.0", "::", "::0"}:
        return "127.0.0.1"
    return clean_host


def split_bind_address(bind: str) -> tuple[str, int | None]:
    """Return host and port from a tunnel bind value."""
    clean_bind = bind.strip()
    if not clean_bind:
        return "127.0.0.1", None
    if clean_bind.startswith("[") and "]:" in clean_bind:
        host, port = clean_bind[1:].split("]:", 1)
        return normalized_bind_host(host), int(port) if port.isdigit() else None
    if ":" in clean_bind:
        host, port = clean_bind.rsplit(":", 1)
        return normalized_bind_host(host), int(port) if port.isdigit() else None
    return "127.0.0.1", int(clean_bind) if clean_bind.isdigit() else None


def split_host_port(value: str) -> tuple[str, int | None]:
    """Return host and port from a host:port value."""
    clean_value = value.strip()
    if not clean_value or clean_value.upper() == "SOCKS":
        return clean_value, None
    if clean_value.startswith("[") and "]:" in clean_value:
        host, port = clean_value[1:].split("]:", 1)
        return host, int(port) if port.isdigit() else None
    if ":" in clean_value:
        host, port = clean_value.rsplit(":", 1)
        return host, int(port) if port.isdigit() else None
    return clean_value, int(clean_value) if clean_value.isdigit() else None


@lru_cache(maxsize=1)
def default_port_kinds() -> dict[int, str]:
    """Return default port usage labels loaded from the bundled CSV asset."""
    port_kinds: dict[int, str] = {}
    try:
        with hhs_ui.PORTS_DEFAULT_FILE.open(newline="", encoding="utf-8") as csv_file:
            for row in csv.DictReader(csv_file):
                port = str(row.get("Port", "")).strip()
                kind = str(row.get("Kind", "")).strip()
                if port.isdigit() and kind:
                    port_kinds[int(port)] = kind
    except OSError:
        return {}
    return port_kinds


def ssh_tunnel_kind_port(row: dict[str, str]) -> int | None:
    """Return the service port used to identify an SSH tunnel kind."""
    if row.get("Type", "").lower() == "dynamic":
        _, bind_port = split_bind_address(row.get("Bind", ""))
        return bind_port
    _, destination_port = split_host_port(row.get("Destination", ""))
    if destination_port is not None:
        return destination_port
    _, bind_port = split_bind_address(row.get("Bind", ""))
    return bind_port


def ssh_tunnel_kind(row: dict[str, str]) -> str:
    """Return the default app usage label for an SSH tunnel row."""
    port = ssh_tunnel_kind_port(row)
    if port is None:
        return ""
    return default_port_kinds().get(port, "")


def local_port_is_reachable(host: str, port: int | None) -> bool:
    """Return whether a local TCP host and port accepts connections."""
    if port is None:
        return False
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except OSError:
        return False


def build_port_reachability_command(host: str, port: int) -> str:
    """Build a shell command that checks whether a TCP port is reachable."""
    safe_host = shlex.quote(host)
    safe_port = shlex.quote(str(port))
    return (
        f"host={safe_host}; port={safe_port}; "
        "if command -v nc >/dev/null 2>&1; then "
        'nc -z -w 1 "$host" "$port"; '
        "else "
        'bash -c "</dev/tcp/${host}/${port}" >/dev/null 2>&1; '
        "fi"
    )


def ssh_tunnel_link(bind: str) -> str:
    """Return the local loopback link value for a tunnel bind value."""
    _, port = split_bind_address(bind)
    return f"http://127.0.0.1:{port}" if port is not None else ""


def display_ssh_tunnel_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return SSH tunnel rows shaped for the visible table columns."""
    return [
        {
            "Local Port": row.get("Bind", ""),
            "Remote Host:Port": row.get("Destination", ""),
            "Kind": ssh_tunnel_kind(row),
            "Status": row.get("Status", ""),
            "Link": ssh_tunnel_link(row.get("Bind", "")),
        }
        for row in rows
    ]


def filter_ssh_tunnel_rows(
    rows: list[dict[str, str]],
    tunnel_filter: str,
    text_filter: str = "",
) -> list[dict[str, str]]:
    """Return SSH tunnel rows matching the selected displayed Kind filter."""
    clean_filter = text_filter.strip().lower()
    if tunnel_filter in ("Other", "Containing"):
        return [
            row
            for row in rows
            if not clean_filter or clean_filter in ssh_tunnel_kind(row).lower()
        ]
    if tunnel_filter == "All":
        return rows
    return [
        row
        for row in rows
        if ssh_tunnel_kind(row).lower() == tunnel_filter.strip().lower()
    ]


def ssh_tunnel_status_cell_style(value: object) -> str:
    """Return the dataframe cell style for SSH tunnel status values."""
    value_text = str(value).strip().lower()
    base_style = "font-weight: 800;"
    if value_text == "reachable":
        return f"{base_style} color: #50fa7b;"
    if value_text == "not reachable":
        return f"{base_style} color: #ff5555;"
    if value_text == "checking":
        return f"{base_style} color: var(--hhs-comment);"
    return base_style


def parse_legacy_hhs_history_line(line: str) -> dict[str, str] | None:
    """Parse one decorative __hhs_history terminal row into a table row."""
    match = hhs_ui.HISTORY_COMMAND_LINE_PATTERN.match(line.strip())
    if not match:
        return None
    command_value = match.group(2).strip()
    if re.fullmatch(r"#\d+", command_value):
        return None
    return {
        "Index": match.group(1).strip(),
        "Value": command_value,
    }


def parse_hhs_history(output: str) -> list[dict[str, str]]:
    """Parse __hhs_history terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        row = parse_legacy_hhs_history_line(line)
        if row is not None:
            rows.append(row)
    return rows


def parse_hhs_history_dirs(output: str) -> list[dict[str, str]]:
    """Parse __hhs_dirs list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.HISTORY_DIRECTORY_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {
                    "Type": match.group(2).strip(),
                    "Value": match.group(3).strip(),
                }
            )
    return rows


def parse_hhs_history_stats(output: str) -> list[dict[str, int | str]]:
    """Parse __hhs_hist_stats output into chart rows."""
    rows: list[dict[str, int | str]] = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.HISTORY_STATS_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {
                    "Command": match.group(1).strip(),
                    "Count": int(match.group(2)),
                }
            )
    return rows


def parse_hhs_disk_usage(output: str) -> list[dict[str, float | str]]:
    """Parse __hhs_du output into disk usage chart rows."""
    rows: list[dict[str, float | str]] = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.DISK_USAGE_LINE_PATTERN.match(line)
        if match:
            size = match.group(2).strip()
            rows.append(
                {
                    "Path": match.group(1).strip(),
                    "Size": size,
                    "Bytes": human_size_to_bytes(size),
                }
            )
    return rows


def parse_process_monitor(output: str, metric: str) -> list[dict[str, float | str]]:
    """Parse top or ps process output into monitor chart rows."""
    rows: list[dict[str, float | str]] = []
    headers: list[str] = []
    selected_field = str(
        hhs_ui.TOP_PROCESS_SORT_KEYS.get(metric, hhs_ui.TOP_PROCESS_SORT_KEYS["CPU"])[
            "field"
        ]
    )
    for line in strip_ansi(output).splitlines():
        parts = line.split()
        if not parts:
            continue
        normalized_parts = [part.upper() for part in parts]
        if "PID" in normalized_parts and (
            "%CPU" in normalized_parts or "CPU" in normalized_parts
        ):
            headers = normalized_parts
            rows = []
            continue
        if not headers or not parts[0].isdigit():
            continue
        index_by_name = {name: index for index, name in enumerate(headers)}
        pid_index = index_by_name.get("PID", 0)
        user_index = index_by_name.get("USER")
        command_index = index_by_name.get("COMMAND", len(parts) - 1)
        cpu_index = index_by_name.get("%CPU", index_by_name.get("CPU"))
        mem_index = index_by_name.get("%MEM", index_by_name.get("MEM"))
        value_index = cpu_index if selected_field == "CPU" else mem_index
        if value_index is None or value_index >= len(parts):
            continue
        command = (
            " ".join(parts[command_index:])
            if command_index == len(headers) - 1
            else parts[command_index]
        )
        raw_value = parts[value_index]
        rows.append(
            {
                "PID": parts[pid_index] if pid_index < len(parts) else "",
                "User": (
                    parts[user_index]
                    if user_index is not None and user_index < len(parts)
                    else ""
                ),
                "Command": command,
                "CPU": (
                    parts[cpu_index]
                    if cpu_index is not None and cpu_index < len(parts)
                    else ""
                ),
                "MEM": (
                    parts[mem_index]
                    if mem_index is not None and mem_index < len(parts)
                    else ""
                ),
                "Value": metric_value(raw_value),
                "ValueLabel": raw_value,
            }
        )
    return rows


def parse_hhs_process_list(output: str) -> list[dict[str, str]]:
    """Parse __hhs_process_list output into process rows."""
    rows: list[dict[str, str]] = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.PROCESS_LIST_LINE_PATTERN.match(line)
        if not match:
            continue
        rows.append(
            {
                "UID": match.group(1),
                "PID": match.group(2),
                "PPID": match.group(3),
                "Command": match.group(4).strip(),
                "Status": match.group(5).strip().title(),
            }
        )
    return rows


def path_sources(output: str) -> list[str]:
    """Parse __hhs_paths output into path source labels."""
    sources = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.PATH_SOURCE_PATTERN.search(line.strip())
        if match:
            sources.append(match.group(1).strip())
    return sources


def path_types(output: str) -> list[str]:
    """Parse __hhs_paths output into path type glyphs."""
    types = []
    for line in strip_ansi(output).splitlines():
        clean_line = line.strip()
        if not hhs_ui.PATH_SOURCE_PATTERN.search(clean_line):
            continue
        match = hhs_ui.PATH_TYPE_PATTERN.search(clean_line)
        if match:
            types.append(match.group(1).strip())
    return types


def path_statuses(output: str) -> list[str]:
    """Parse __hhs_paths output into path status glyphs."""
    statuses = []
    for line in strip_ansi(output).splitlines():
        clean_line = line.strip()
        if not hhs_ui.PATH_SOURCE_PATTERN.search(clean_line):
            continue
        if "" in clean_line:
            statuses.append("")
        elif "" in clean_line:
            statuses.append("")
        else:
            statuses.append("")
    return statuses


def path_entries(output: str = "") -> list[str]:
    """Return PATH entries emitted by __hhs_paths or fall back to the UI process."""
    entries = []
    marker_prefix = f"{HHS_PATHS_RAW_ENTRY_MARKER}\t"
    for line in strip_ansi(output).splitlines():
        clean_line = line.rstrip("\r")
        if clean_line.startswith(marker_prefix):
            entries.append(clean_line[len(marker_prefix) :])
    if entries:
        return entries
    return [entry for entry in os.environ.get("PATH", "").split(":") if entry]


def parse_hhs_paths(output: str) -> list[dict[str, str]]:
    """Parse __hhs_paths terminal output into PATH rows."""
    sources = path_sources(output)
    types = path_types(output)
    statuses = path_statuses(output)
    rows = []
    for index, path_entry in enumerate(path_entries(output)):
        source = sources[index] if index < len(sources) else "PATH entry"
        path_type = types[index] if index < len(types) else ""
        status = statuses[index] if index < len(statuses) else ""
        rows.append(
            {
                "Type": path_type,
                "Origin": source,
                "Path Value": path_entry,
                "_Path Status": status,
            }
        )
    return rows


def env_widget_key_fragment(name: str) -> str:
    """Return a safe Streamlit widget key fragment for an environment name."""
    safe_name = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
    return safe_name or "unnamed"


def env_value_editor_key(name: str) -> str:
    """Return the Streamlit widget key for a selected environment value editor."""
    return f"{hhs_ui.ENV_VALUE_EDITOR_KEY_PREFIX}_{env_widget_key_fragment(name)}"


def dir_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected directory value viewer."""
    return f"{hhs_ui.DIR_VALUE_EDITOR_KEY_PREFIX}_{index}"


def cmd_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected command value viewer."""
    return f"{hhs_ui.CMD_VALUE_EDITOR_KEY_PREFIX}_{index}"


def alias_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected alias value viewer."""
    return f"{hhs_ui.ALIAS_VALUE_EDITOR_KEY_PREFIX}_{index}"
