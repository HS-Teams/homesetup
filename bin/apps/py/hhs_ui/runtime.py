"""Runtime shell selection for the HomeSetup Streamlit UI."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from . import constants as hhs_ui_constants


def resolve_run_shell() -> str:
    """Return the Bash executable used for all HomeSetup UI commands."""
    run_shell = ""
    brew_commands = (
        ["brew", "--prefix", "bash"],
        ["/opt/homebrew/bin/brew", "--prefix", "bash"],
        ["/usr/local/bin/brew", "--prefix", "bash"],
    )
    for brew_command in brew_commands:
        try:
            brew_result = subprocess.run(
                brew_command,
                capture_output=True,
                check=False,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            if brew_result.returncode == 0:
                run_shell = brew_result.stdout.strip()
                break
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue

    candidates = []
    if run_shell:
        candidates.extend((Path(run_shell) / "bin" / "bash", Path(run_shell)))
    candidates.extend(
        (
            Path("/opt/homebrew/opt/bash/bin/bash"),
            Path("/usr/local/opt/bash/bin/bash"),
            Path("/bin/bash"),
        )
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return "/bin/bash"


def shell_version_command() -> str:
    """Return the command that prints the active target Bash version."""
    return r"${BASH:-bash} --version"


RUN_SHELL = resolve_run_shell()
os.environ[hhs_ui_constants.RUN_SHELL_ENV_KEY] = RUN_SHELL
