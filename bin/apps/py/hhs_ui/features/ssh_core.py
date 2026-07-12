"""Pure SSH configuration and command helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import hashlib
import os
import shlex
from pathlib import Path


def local_hostname() -> str:
    """Return the local host name shown by the sidebar host selector."""
    return os.uname().nodename.strip() or "localhost"


def ssh_config_file() -> Path:
    """Return the user's OpenSSH config file path."""
    return Path.home() / ".ssh" / "config"


def parse_ssh_config_hosts(config_text: str) -> tuple[str, ...]:
    """Return concrete Host aliases configured in an OpenSSH config file."""
    hosts: list[str] = []
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts and parts[0].lower() == "host":
            for host in parts[1:]:
                if any(char in host for char in "*?!"):
                    continue
                if host not in hosts:
                    hosts.append(host)
    return tuple(hosts)


def parse_ssh_config_hostnames(config_text: str) -> dict[str, str]:
    """Return concrete SSH Host aliases mapped to their configured HostName."""
    hostnames: dict[str, str] = {}
    active_hosts: list[str] = []
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        keyword = parts[0].lower()
        if keyword == "host":
            active_hosts = [
                host for host in parts[1:] if not any(char in host for char in "*?!")
            ]
            continue
        if keyword == "hostname" and len(parts) > 1:
            hostname = parts[1]
            for host in active_hosts:
                hostnames[host] = hostname
    return hostnames


def parse_ssh_config_ports(config_text: str) -> dict[str, str]:
    """Return concrete SSH Host aliases mapped to their configured Port."""
    ports: dict[str, str] = {}
    active_hosts: list[str] = []
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        keyword = parts[0].lower()
        if keyword == "host":
            active_hosts = [
                host for host in parts[1:] if not any(char in host for char in "*?!")
            ]
            continue
        if keyword == "port" and len(parts) > 1:
            port = parts[1]
            for host in active_hosts:
                ports[host] = port
    return ports


def ssh_config_hosts() -> tuple[str, ...]:
    """Return concrete SSH Host aliases configured in ~/.ssh/config."""
    config_file = ssh_config_file()
    if not config_file.exists():
        return ()
    try:
        return parse_ssh_config_hosts(config_file.read_text(encoding="utf-8"))
    except OSError:
        return ()


def ssh_config_hostname(host: str) -> str:
    """Return the configured HostName for an SSH Host alias."""
    config_file = ssh_config_file()
    if not config_file.exists():
        return host
    try:
        hostnames = parse_ssh_config_hostnames(config_file.read_text(encoding="utf-8"))
    except OSError:
        return host
    return hostnames.get(host, host)


def ssh_config_port(host: str) -> str:
    """Return the configured Port for an SSH Host alias."""
    config_file = ssh_config_file()
    if not config_file.exists():
        return "22"
    try:
        ports = parse_ssh_config_ports(config_file.read_text(encoding="utf-8"))
    except OSError:
        return "22"
    return ports.get(host, "22")


def ssh_connection_display(host: str) -> str:
    """Return the connected SSH host display value."""
    clean_host = host.strip()
    return f"{ssh_config_hostname(clean_host)}:{ssh_config_port(clean_host)}"


def ssh_control_path(host: str) -> str:
    """Return the ControlMaster socket path for a selected SSH host."""
    host_hash = hashlib.sha256(host.encode("utf-8")).hexdigest()[:16]
    return f"/tmp/hhs-ui-ssh-{host_hash}.sock"


def ssh_config_option() -> str:
    """Return the OpenSSH config option used for UI-managed SSH commands."""
    return '-F "${HOME}/.ssh/config"'


def ssh_config_option_args() -> list[str]:
    """Return OpenSSH config arguments for subprocess list commands."""
    return ["-F", str(ssh_config_file())]


def ssh_batch_options() -> str:
    """Return common non-interactive OpenSSH options used by UI commands."""
    return (
        "-o BatchMode=yes -o ConnectTimeout=5 -o ConnectionAttempts=1 "
        "-o ServerAliveInterval=5 -o ServerAliveCountMax=1"
    )


def build_ssh_connect_command(host: str) -> str:
    """Build a local command that opens or validates a ControlMaster connection."""
    safe_host = shlex.quote(host)
    safe_control_path = shlex.quote(ssh_control_path(host))
    safe_config_option = ssh_config_option()
    ssh_options = ssh_batch_options()
    check_command = (
        f"ssh {safe_config_option} {ssh_options} "
        f"-o ControlPath={safe_control_path} -O check {safe_host} "
        ">/dev/null 2>&1"
    )
    connect_command = (
        f"ssh -MNf {safe_config_option} {ssh_options} "
        "-o ControlMaster=auto -o ControlPersist=10m "
        f"-o ControlPath={safe_control_path} {safe_host}"
    )
    return (
        f"{check_command} || {{ "
        f"rm -f {safe_control_path}; "
        f"{connect_command}; "
        "}"
    )


def build_ssh_check_command(host: str) -> str:
    """Build a local command that checks an existing ControlMaster connection."""
    safe_host = shlex.quote(host)
    safe_control_path = shlex.quote(ssh_control_path(host))
    return (
        f"ssh {ssh_config_option()} {ssh_batch_options()} "
        f"-o ControlPath={safe_control_path} -O check {safe_host}"
    )


def build_ssh_disconnect_command(host: str) -> str:
    """Build a local command that terminates a ControlMaster connection."""
    safe_host = shlex.quote(host)
    control_path = ssh_control_path(host)
    safe_control_path = shlex.quote(control_path)
    safe_control_path_pattern = shlex.quote(f"ControlPath={control_path}")
    disconnect_command = (
        f"ssh {ssh_config_option()} -o BatchMode=yes "
        f"-o ControlPath={safe_control_path} -O exit {safe_host} >/dev/null 2>&1 "
        "|| true"
    )
    graceful_cleanup = (
        f"for pid in $(pgrep -f -- {safe_control_path_pattern} 2>/dev/null || true); "
        "do [[ \"${pid}\" != \"$$\" ]] && kill -TERM \"${pid}\" 2>/dev/null || true; done"
    )
    forced_cleanup = (
        f"for pid in $(pgrep -f -- {safe_control_path_pattern} 2>/dev/null || true); "
        "do [[ \"${pid}\" != \"$$\" ]] && kill -KILL \"${pid}\" 2>/dev/null || true; done"
    )
    return (
        f"{disconnect_command}; "
        "if command -v pgrep >/dev/null 2>&1; then "
        f"{graceful_cleanup}; sleep 0.2; {forced_cleanup}; "
        "fi; "
        f"rm -f {safe_control_path}"
    )


def build_ssh_wrapped_command(command: str, host: str) -> str:
    """Build a non-interactive SSH command with explicit HomeSetup defaults."""
    safe_host = shlex.quote(host)
    safe_control_path = shlex.quote(ssh_control_path(host))
    remote_environment = (
        'export HHS_HOME="${HHS_HOME:-${HOME}/HomeSetup}"; '
        'export HHS_DIR="${HHS_DIR:-${HOME}/.config/hhs}"; '
        'export HHS_CACHE_DIR="${HHS_CACHE_DIR:-${HHS_DIR}/cache}"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
    )
    safe_remote_command = shlex.quote(f"{remote_environment}{command}")
    safe_remote_shell = shlex.quote(
        f"bash --noprofile --norc -c {safe_remote_command}"
    )
    return (
        f"ssh -T {ssh_config_option()} {ssh_batch_options()} "
        f"-o ControlPath={safe_control_path} {safe_host} {safe_remote_shell}"
    )
