"""Filesystem path helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import os
from pathlib import Path

from . import constants as hhs_ui_constants


def homesetup_home() -> Path:
    """Return the HomeSetup repository root used by this UI."""
    return Path(os.environ.get("HHS_HOME", hhs_ui_constants.APP_DIR.parents[3])).expanduser()


def homesetup_config_dir() -> Path:
    """Return the HomeSetup runtime configuration directory used by this UI."""
    return Path(os.environ.get("HHS_DIR", Path.home() / ".config/hhs")).expanduser()


def ollama_history_file() -> Path:
    """Return the configured HomeSetup Ollama history file path."""
    return Path(
        os.environ.get(
            "HHS_OLLAMA_HISTORY_FILE", homesetup_config_dir() / ".ollama_history"
        )
    ).expanduser()


def ollama_prompt_file() -> Path:
    """Return the configured HomeSetup Ollama prompt file path."""
    return Path(
        os.environ.get(
            "HHS_OLLAMA_PROMPT_FILE", homesetup_config_dir() / "hhs-ask-ollama.md"
        )
    ).expanduser()


def hhs_log_dir() -> Path:
    """Return the HomeSetup log directory used by monitor logs."""
    return Path(
        os.environ.get(
            "HHS_LOG_DIR",
            Path(os.environ.get("HHS_DIR", Path.home() / ".config/hhs")) / "logs",
        )
    ).expanduser()


def hhs_log_files() -> list[str]:
    """Return available HomeSetup log file names."""
    log_dir = hhs_log_dir()
    if not log_dir.is_dir():
        return []
    return sorted(path.name for path in log_dir.glob("*.log") if path.is_file())


def hhs_log_file_path(log_file: str) -> Path:
    """Return the safe path for a HomeSetup log file name."""
    return hhs_log_dir() / Path(log_file).name


def hhs_log_file_info(log_file: str) -> tuple[str, dict[str, str]]:
    """Return the selected log file path and environment used for display."""
    environment_values = {
        "HOME": str(Path.home()),
        "HHS_HOME": str(homesetup_home()),
        "HHS_DIR": str(homesetup_config_dir()),
        "HHS_LOG_DIR": str(hhs_log_dir()),
    }
    return str(hhs_log_file_path(log_file)), environment_values
