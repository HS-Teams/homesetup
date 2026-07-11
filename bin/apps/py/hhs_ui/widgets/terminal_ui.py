#!/usr/bin/env python3
"""ttyd-backed terminal UI runtime helpers for HomeSetup."""

from __future__ import annotations

import atexit
import html
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.execution.command_catalog import open_file
from hhs_ui.core.process_resources import process_resource_registry, process_resource_state
from hhs_ui.core.runtime import RUN_SHELL
from hhs_ui.features.ssh_core import (
    build_ssh_disconnect_command,
    ssh_config_option_args,
    ssh_control_path,
)

TTYD_CLEANUP_REGISTRY: dict[str, dict[str, object]] = process_resource_registry(
    "ttyd_cleanup_registry"
)
TTYD_EVENT_REGISTRY: dict[str, list[dict[str, object]]] = process_resource_registry(
    "ttyd_event_registry"
)
_PROCESS_RESOURCE_STATE = process_resource_state()
_PROCESS_TTYD_CLEANUP_SERVER = _PROCESS_RESOURCE_STATE.get("ttyd_cleanup_server")
TTYD_CLEANUP_SERVER: ThreadingHTTPServer | None = (
    _PROCESS_TTYD_CLEANUP_SERVER
    if isinstance(_PROCESS_TTYD_CLEANUP_SERVER, ThreadingHTTPServer)
    else None
)
TTYD_CLEANUP_SERVER_PORT = (
    int(_PROCESS_RESOURCE_STATE.get("ttyd_cleanup_server_port") or 0)
    if TTYD_CLEANUP_SERVER is not None
    else 0
)
TTYD_EXIT_COMMANDS = {"exit", "logout"}


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"terminal runtime dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")
render_command_preloader_events = _unconfigured_dependency(
    "render_command_preloader_events"
)
footer_working_directory = _unconfigured_dependency("footer_working_directory")
connected_ssh_host = _unconfigured_dependency("connected_ssh_host")
selected_host_is_local = _unconfigured_dependency("selected_host_is_local")
clear_registered_ssh_connection = _unconfigured_dependency(
    "clear_registered_ssh_connection"
)
terminal_document_view_is_active = _unconfigured_dependency(
    "terminal_document_view_is_active"
)
close_document_view = _unconfigured_dependency("close_document_view")
deactivate_terminal_document_view = _unconfigured_dependency(
    "deactivate_terminal_document_view"
)
push_floating_status = _unconfigured_dependency("push_floating_status")


def configure_terminal_runtime(
    *,
    render_script_html: Callable[..., None],
    render_command_preloader_events: Callable[[], None],
    footer_working_directory: Callable[[], str],
    connected_ssh_host: Callable[[], str],
    selected_host_is_local: Callable[..., bool],
    clear_registered_ssh_connection: Callable[[], None],
    terminal_document_view_is_active: Callable[[], bool],
    close_document_view: Callable[..., None],
    deactivate_terminal_document_view: Callable[[], None],
    push_floating_status: Callable[[str, str], None],
) -> None:
    """Configure Streamlit UI callbacks required by the terminal runtime."""
    globals().update(
        {
            "render_script_html": render_script_html,
            "render_command_preloader_events": render_command_preloader_events,
            "footer_working_directory": footer_working_directory,
            "connected_ssh_host": connected_ssh_host,
            "selected_host_is_local": selected_host_is_local,
            "clear_registered_ssh_connection": clear_registered_ssh_connection,
            "terminal_document_view_is_active": terminal_document_view_is_active,
            "close_document_view": close_document_view,
            "deactivate_terminal_document_view": deactivate_terminal_document_view,
            "push_floating_status": push_floating_status,
        }
    )


def render_terminal_document_view() -> None:
    """Render the ttyd-backed terminal document view."""
    title = terminal_document_title()
    st.markdown(
        f"""
        <section class="hhs-view-heading">
          <h2> {html.escape(title)}</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    initialize_terminal_session_state()
    ttyd_url = ensure_ttyd_session()
    if not ttyd_url:
        render_ttyd_unavailable()
        return
    render_ttyd_terminal_frame(ttyd_url)
    render_command_preloader_events()
    show_terminal_ready_status()


def clear_ttyd_exit_request() -> None:
    """Drop any pending ttyd exit request for the current browser session."""
    token = str(
        st.session_state.get(hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY, "")
    ).strip()
    entry = TTYD_CLEANUP_REGISTRY.get(token)
    if isinstance(entry, dict):
        entry.pop("exit_requested", None)


def ttyd_binary() -> str:
    """Return the ttyd executable path when it is available to the UI process."""
    discovered = shutil.which("ttyd")
    if discovered:
        return discovered
    for candidate in (
        os.environ.get("TTYD", ""),
        "/opt/homebrew/bin/ttyd",
        "/opt/homebrew/opt/ttyd/bin/ttyd",
        "/usr/local/bin/ttyd",
        "/usr/local/opt/ttyd/bin/ttyd",
        "/usr/bin/ttyd",
    ):
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return ""


def ttyd_font_family() -> str:
    """Return the terminal font family backed by the bundled font asset."""
    if ttyd_font_file().is_file():
        return hhs_ui.APP_FONT_FAMILY
    return "monospace"


def ttyd_font_file() -> Path:
    """Return the preferred terminal font file for ttyd's isolated iframe."""
    if hhs_ui.APP_FONT_FILE.is_file():
        return hhs_ui.APP_FONT_FILE
    otf_file = (
        Path(os.environ.get("HHS_HOME", hhs_ui.APP_DIR.parents[4]))
        / "assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.otf"
    )
    if otf_file.is_file():
        return otf_file
    return hhs_ui.APP_FONT_FILE


def ttyd_font_mime_type(font_file: Path) -> str:
    """Return the MIME type for the ttyd terminal font file."""
    if font_file.suffix.lower() == ".otf":
        return "font/otf"
    return "font/woff2"


def ttyd_font_format(font_file: Path) -> str:
    """Return the CSS font format for the ttyd terminal font file."""
    if font_file.suffix.lower() == ".otf":
        return "opentype"
    return "woff2"


def ttyd_background_image_file() -> Path:
    """Return the image file used as the ttyd terminal background."""
    return hhs_ui.APP_TERMINAL_BACKGROUND_FILE


def ttyd_background_image_data_url() -> str:
    """Return a PNG data URL for the ttyd terminal background image."""
    background_file = ttyd_background_image_file()
    if not background_file.is_file():
        return ""
    encoded_image = b64encode(background_file.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def ttyd_index_signature(binary: str, event_url: str = "") -> str:
    """Return a stable cache signature for the ttyd index and terminal font."""
    font_file = ttyd_font_file()
    background_file = ttyd_background_image_file()
    parts = ["hhs-ttyd-font-index-v23-terminal-scroll-v1", binary, event_url]
    for path in (Path(binary), font_file, background_file):
        try:
            stat = path.stat()
            parts.append(f"{path}:{stat.st_mtime_ns}:{stat.st_size}")
        except OSError:
            parts.append(f"{path}:missing")
    return "|".join(parts)


def ttyd_index_is_current(binary: str, event_url: str) -> bool:
    """Return whether the generated ttyd index matches the current font and binary."""
    try:
        first_line = hhs_ui.TTYD_INDEX_FILE.read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines()[0]
    except (IndexError, OSError):
        return False
    return first_line == f"<!-- {ttyd_index_signature(binary, event_url)} -->"


def fetch_ttyd_default_index(binary: str) -> str:
    """Fetch the default HTML index served by the installed ttyd binary."""
    port = allocate_ttyd_port()
    process = subprocess.Popen(
        [
            binary,
            "-i",
            hhs_ui.TTYD_HOST,
            "-p",
            str(port),
            "/bin/sh",
            "-lc",
            "sleep 30",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    try:
        url = f"http://{hhs_ui.TTYD_HOST}:{port}/"
        for _ in range(20):
            if not ttyd_process_is_running(process):
                return ""
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    return response.read().decode("utf-8")
            except (OSError, urllib.error.URLError):
                time.sleep(0.05)
        return ""
    finally:
        stop_process(process)


def ttyd_font_face_style() -> str:
    """Return the CSS that loads the HomeSetup terminal font inside ttyd."""
    font_file = ttyd_font_file()
    family = html.escape(ttyd_font_family(), quote=True)
    font_face = ""
    if font_file.is_file():
        encoded_font = b64encode(font_file.read_bytes()).decode("ascii")
        mime_type = ttyd_font_mime_type(font_file)
        font_format = ttyd_font_format(font_file)
        font_face = (
            "@font-face{"
            f'font-family:"{family}";'
            f'src:url("data:{mime_type};base64,{encoded_font}") format("{font_format}");'
            "font-weight:normal;"
            "font-style:normal;"
            "font-display:block;"
            "}"
        )
    background_image = html.escape(ttyd_background_image_data_url(), quote=True)
    background_layer = (
        "background-image:linear-gradient(rgba(0,0,0,0.90),rgba(0,0,0,0.90)),"
        f'url("{background_image}")!important;'
        "background-position:center center!important;"
        "background-size:cover!important;"
        "background-repeat:no-repeat!important;"
    )
    if not background_image:
        background_layer = ""
    return (
        "<style>"
        f"{font_face}"
        "html,body,#terminal,.terminal,.xterm,.xterm-screen,.xterm-rows{"
        f'font-family:"{family}",monospace!important;'
        "}"
        "html,body{"
        "background:#000000!important;"
        "min-height:100%!important;"
        "}"
        "body::before{"
        'content:"";'
        "position:fixed!important;"
        "inset:0!important;"
        "pointer-events:none!important;"
        "z-index:0!important;"
        f"{background_layer}"
        "}"
        "#terminal,.terminal,.xterm{"
        "background:transparent!important;"
        "position:relative!important;"
        "z-index:1!important;"
        "}"
        ".xterm .xterm-screen,.xterm .xterm-rows,.xterm .xterm-screen canvas{"
        "background:transparent!important;"
        "}"
        "#terminal,.terminal,.xterm{"
        "box-sizing:border-box!important;"
        "padding:0!important;"
        "}"
        ".xterm .xterm-viewport{"
        "background:transparent!important;"
        "overflow-y:scroll!important;"
        "left:0!important;"
        "top:0!important;"
        "right:0!important;"
        "bottom:0!important;"
        "scrollbar-gutter:stable!important;"
        "}"
        ".xterm .xterm-viewport::-webkit-scrollbar{"
        "background:#000000!important;"
        "width:12px!important;"
        "}"
        ".xterm .xterm-viewport::-webkit-scrollbar-track{"
        "background:#000000!important;"
        "}"
        ".xterm .xterm-viewport::-webkit-scrollbar-thumb{"
        "background:#6b7280!important;"
        "border:2px solid #000000!important;"
        "border-radius:999px!important;"
        "}"
        "</style>"
    )


def ttyd_bridge_script(event_url: str) -> str:
    """Return JavaScript that bridges ttyd terminal events back to the UI."""
    return (
        "<script>"
        "(()=>{"
        f"const eventUrl={json.dumps(event_url)};"
        f"const maxContentLength={int(hhs_ui.AI_TERMINAL_CONTEXT_MAX_CHARS)};"
        "const prefix='HHS_TTYD_EVENT|';"
        "const transparentBackground='rgba(0,0,0,0)';"
        "const selectionSnapshotAgeMs=300000;"
        "let lastSelectedContent='';"
        "let lastSelectedAt=0;"
        "let lastMiddlePasteAt=0;"
        "let transparentBackgroundTimer=null;"
        "let transparentBackgroundAttempts=0;"
        "const decode=(value)=>{try{return decodeURIComponent(escape(atob(value)));}catch(_error){return '';}};"
        "const cleanContent=(value)=>String(value||'').replace(/\\r\\n?/g,'\\n').trim();"
        "const limitContent=(value)=>{const content=cleanContent(value);"
        "if(content.length<=maxContentLength){return {content,truncated:false};}"
        "return {content:content.slice(content.length-maxContentLength),truncated:true};};"
        "const applyTransparentTerminalBackground=()=>{"
        "const term=window.term;"
        "if(!term||!term.options){return false;}"
        "const theme=(term.options.theme&&typeof term.options.theme==='object')?term.options.theme:{};"
        "if(theme.background!==transparentBackground){"
        "term.options.theme={...theme,background:transparentBackground};"
        "}"
        "if(typeof term.refresh==='function'){"
        "try{term.refresh(0,Math.max(0,Number(term.rows||1)-1));}catch(_error){}"
        "}"
        "return true;"
        "};"
        "const scheduleTransparentTerminalBackground=()=>{"
        "if(transparentBackgroundTimer){return;}"
        "transparentBackgroundAttempts=0;"
        "transparentBackgroundTimer=window.setInterval(()=>{"
        "transparentBackgroundAttempts+=1;"
        "applyTransparentTerminalBackground();"
        "if(transparentBackgroundAttempts>=20){"
        "window.clearInterval(transparentBackgroundTimer);"
        "transparentBackgroundTimer=null;"
        "}"
        "},250);"
        "};"
        "const parse=(data)=>{"
        "if(!data||!data.startsWith(prefix)){return null;}"
        "const parts=data.split('|');"
        "if(parts.length<6){return null;}"
        "return {type:parts[1],command:parts[2],status:Number(parts[3]||0),cwd:decode(parts[4]),time:Number(parts[5]||Date.now())};"
        "};"
        "const publish=(event)=>{"
        "if(!event){return;}"
        "try{window.parent.postMessage({type:'hhs-ttyd-event',event},'*');}catch(_error){}"
        "try{fetch(eventUrl,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(event),keepalive:true}).catch(()=>{});}catch(_error){}"
        "};"
        "const replyToRequester=(requestEvent,event)=>{"
        "try{if(requestEvent&&requestEvent.source&&requestEvent.source!==window.parent){"
        "requestEvent.source.postMessage({type:'hhs-ttyd-event',event},'*');}}catch(_error){}"
        "};"
        "const visibleBuffer=()=>{"
        "const term=window.term;"
        "const buffer=term&&term.buffer&&term.buffer.active;"
        "if(!term||!buffer||typeof buffer.getLine!=='function'){return '';}"
        "const rows=Number(term.rows||24);"
        "const length=Number(buffer.length||0);"
        "const viewportY=Number(buffer.viewportY||Math.max(0,(buffer.baseY||0)-rows+1));"
        "const start=Math.max(0,Math.min(length,viewportY));"
        "const end=Math.max(start,Math.min(length,start+rows));"
        "const lines=[];"
        "for(let index=start;index<end;index+=1){"
        "const line=buffer.getLine(index);"
        "if(line&&typeof line.translateToString==='function'){lines.push(line.translateToString(true));}"
        "}"
        "return lines.join('\\n');"
        "};"
        "const selectionContent=()=>{"
        "const term=window.term;"
        "return term&&typeof term.getSelection==='function'?cleanContent(term.getSelection()):'';"
        "};"
        "const cacheSelection=(value)=>{"
        "const selected=cleanContent(value);"
        "if(selected){lastSelectedContent=selected;lastSelectedAt=Date.now();}"
        "return selected;"
        "};"
        "const rememberSelection=()=>{"
        "cacheSelection(selectionContent());"
        "};"
        "const recentSelection=()=>{"
        "const current=cacheSelection(selectionContent());"
        "if(current){return current;}"
        "if(lastSelectedContent&&Date.now()-lastSelectedAt<=selectionSnapshotAgeMs){return lastSelectedContent;}"
        "return '';"
        "};"
        "const terminalContext=()=>{"
        "const selected=recentSelection();"
        "if(selected){const limited=limitContent(selected);return {...limited,mode:'selection'};}"
        "const limited=limitContent(visibleBuffer());"
        "return {...limited,mode:limited.content?'visible':'empty'};"
        "};"
        "const sendTerminalInput=(text)=>{"
        "const term=window.term;"
        "if(term&&typeof term.focus==='function'){term.focus();}"
        "const coreService=term&&term._core&&term._core.coreService;"
        "if(coreService&&typeof coreService.triggerDataEvent==='function'){"
        "coreService.triggerDataEvent(String(text||''),true);return true;}"
        "if(term&&typeof term.paste==='function'){term.paste(String(text||''));return true;}"
        "const textarea=window.document&&window.document.querySelector('.xterm-helper-textarea');"
        "if(textarea){textarea.focus();textarea.value+=String(text||'');"
        "textarea.dispatchEvent(new InputEvent('input',{inputType:'insertText',data:String(text||''),bubbles:true}));"
        "return true;}"
        "return false;"
        "};"
        "const pasteSelectedTerminalText=()=>{"
        "const selected=selectionContent();"
        "if(!selected){return false;}"
        "lastSelectedContent=selected;"
        "lastSelectedAt=Date.now();"
        "try{if(navigator.clipboard&&navigator.clipboard.writeText){"
        "navigator.clipboard.writeText(selected).catch(()=>{});}}catch(_error){}"
        "return sendTerminalInput(selected);"
        "};"
        "const middleClickPasteHandler=(event)=>{"
        "if(Number(event.button)!==1){return;}"
        "event.preventDefault();"
        "event.stopPropagation();"
        "if(event.type!=='mousedown'){return;}"
        "const now=Date.now();"
        "if(now-lastMiddlePasteAt<250){return;}"
        "if(pasteSelectedTerminalText()){lastMiddlePasteAt=now;}"
        "};"
        "const submitTerminalCommand=(command)=>{"
        "const cleanCommand=String(command||'').trim();"
        "if(!cleanCommand){return false;}"
        "if(!sendTerminalInput('\\x03')){return false;}"
        "window.setTimeout(()=>{sendTerminalInput(`${cleanCommand}\\r`);},90);"
        "return true;"
        "};"
        "window.addEventListener('message',(messageEvent)=>{"
        "const data=messageEvent.data||{};"
        "if(data.type==='hhs-ttyd-command-submit'){submitTerminalCommand(data.command);return;}"
        "if(data.type!=='hhs-ttyd-context-request'){return;}"
        "const requestId=String(data.requestId||'').replace(/[^A-Za-z0-9_.:-]/g,'').slice(0,80);"
        "const context=terminalContext();"
        "const event={type:'terminal-context',command:'ask-ai',status:context.content?0:1,cwd:'',"
        "time:Date.now(),requestId,mode:context.mode,content:context.content,truncated:context.truncated};"
        "publish(event);"
        "replyToRequester(messageEvent,event);"
        "});"
        "const install=()=>{"
        "const term=window.term;"
        "if(!term){return false;}"
        "applyTransparentTerminalBackground();"
        "scheduleTransparentTerminalBackground();"
        "if(!term.parser||window.__hhsTtydBridgeInstalled){return !!window.__hhsTtydBridgeInstalled;}"
        "window.__hhsTtydBridgeInstalled=true;"
        "term.parser.registerOscHandler(777,(data)=>{const event=parse(String(data||''));if(event){publish(event);return true;}return false;});"
        "const scheduleRememberSelection=()=>{window.setTimeout(rememberSelection,0);};"
        "window.addEventListener('mouseup',scheduleRememberSelection,true);"
        "window.addEventListener('mousedown',middleClickPasteHandler,true);"
        "window.addEventListener('auxclick',middleClickPasteHandler,true);"
        "window.addEventListener('keyup',scheduleRememberSelection,true);"
        "window.addEventListener('touchend',scheduleRememberSelection,true);"
        "if(typeof term.onSelectionChange==='function'){"
        "window.__hhsTtydSelectionChangeDisposable=term.onSelectionChange(scheduleRememberSelection);}"
        "if(window.document){window.document.addEventListener('selectionchange',scheduleRememberSelection,true);}"
        "window.addEventListener('keydown',(event)=>{"
        "if((event.metaKey||event.ctrlKey)&&String(event.key||'').toLowerCase()==='k'){"
        "event.preventDefault();event.stopPropagation();"
        "if(window.term&&typeof window.term.clear==='function'){window.term.clear();}"
        "}"
        "},true);"
        "return true;"
        "};"
        "if(!install()){const timer=window.setInterval(()=>{if(install()){window.clearInterval(timer);}},100);}"
        "})();"
        "</script>"
    )


def inject_ttyd_font(index_html: str, binary: str, event_url: str) -> str:
    """Return ttyd index HTML with HomeSetup terminal customizations injected."""
    signature = f"<!-- {ttyd_index_signature(binary, event_url)} -->\n"
    style = ttyd_font_face_style()
    script = ttyd_bridge_script(event_url)
    injection = style + script
    if not injection:
        return f"{signature}{index_html}"
    if "</head>" in index_html:
        return f"{signature}{index_html.replace('</head>', injection + '</head>', 1)}"
    return f"{signature}{injection}{index_html}"


def ensure_ttyd_index_file(binary: str, event_url: str) -> str:
    """Create or reuse the generated ttyd index that embeds the terminal font."""
    if ttyd_index_is_current(binary, event_url):
        return str(hhs_ui.TTYD_INDEX_FILE)
    index_html = fetch_ttyd_default_index(binary)
    if not index_html:
        return ""
    patched_index = inject_ttyd_font(index_html, binary, event_url)
    try:
        hhs_ui.TTYD_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = hhs_ui.TTYD_INDEX_FILE.with_suffix(".tmp")
        temporary_file.write_text(patched_index, encoding="utf-8")
        temporary_file.replace(hhs_ui.TTYD_INDEX_FILE)
        return str(hhs_ui.TTYD_INDEX_FILE)
    except OSError:
        return ""


def stop_process(process: object) -> None:
    """Terminate a process object if it is still running."""
    if not ttyd_process_is_running(process):
        return
    process_group = 0
    process_id = int(getattr(process, "pid", 0) or 0)
    if process_id:
        try:
            process_group = os.getpgid(process_id)
        except OSError:
            process_group = 0
    try:
        if process_group and process_group != os.getpgrp():
            os.killpg(process_group, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        if process_group and process_group != os.getpgrp():
            os.killpg(process_group, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=1)
    except OSError:
        return


def ttyd_process_is_running(process: object) -> bool:
    """Return whether a stored ttyd process is still alive."""
    if not hasattr(process, "poll"):
        return False
    try:
        return process.poll() is None
    except OSError:
        return False


def allocate_ttyd_port() -> int:
    """Return an available local TCP port for a ttyd session."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((hhs_ui.TTYD_HOST, 0))
        return int(server_socket.getsockname()[1])


def ttyd_session_signature(cwd: str, binary: str, event_url: str) -> str:
    """Return the session signature used to decide whether ttyd must restart."""
    host = connected_ssh_host()
    mode = f"ssh:{host}" if host else "local"
    return f"{mode}:{cwd}:{ttyd_index_signature(binary, event_url)}"


def ttyd_process_working_directory(cwd: str) -> str:
    """Return the local working directory used to launch the ttyd process."""
    if connected_ssh_host():
        return os.getcwd()
    if cwd and os.path.isdir(cwd):
        return cwd
    return os.getcwd()


def ttyd_shell_hook_script() -> str:
    """Return the Bash startup script that emits ttyd command hook events."""
    return r"""
if [[ -r "${HOME}/.bash_profile" ]]; then
  . "${HOME}/.bash_profile"
elif [[ -r "${HOME}/.bash_login" ]]; then
  . "${HOME}/.bash_login"
elif [[ -r "${HOME}/.profile" ]]; then
  . "${HOME}/.profile"
elif [[ -r "${HOME}/.bashrc" ]]; then
  . "${HOME}/.bashrc"
fi

__hhs_ttyd_base64() {
  if command -v base64 >/dev/null 2>&1; then
    printf "%s" "$1" | base64 | tr -d "\n"
  elif command -v python3 >/dev/null 2>&1; then
    HHS_TTYD_VALUE="$1" python3 - <<'PY'
import base64
import os
print(base64.b64encode(os.environ.get("HHS_TTYD_VALUE", "").encode()).decode(), end="")
PY
  else
    printf "%s" "$1"
  fi
}

__hhs_ttyd_emit_event() {
  local event_type="${1:-cwd}"
  local command_name="${2:-prompt}"
  local status_code="${3:-0}"
  local cwd_payload
  local event_time
  cwd_payload="$(__hhs_ttyd_base64 "${PWD}")"
  event_time="$(date +%s%3N 2>/dev/null || date +%s)"
  printf "\033]777;HHS_TTYD_EVENT|%s|%s|%s|%s|%s\007" \
    "${event_type}" "${command_name}" "${status_code}" "${cwd_payload}" "${event_time}"
}

__hhs_ttyd_emit_cwd() {
  local command_name="${1:-prompt}"
  local status_code="${2:-0}"
  __hhs_ttyd_emit_event "cwd" "${command_name}" "${status_code}"
}

__hhs_ttyd_emit_exit() {
  local status_code="${1:-0}"
  __hhs_ttyd_emit_event "exit" "exit" "${status_code}"
}

__hhs_ttyd_last_pwd="${PWD}"
__hhs_ttyd_emit_cwd "init" 0

__hhs_ttyd_after_command() {
  local status_code="$?"
  if [[ "${PWD}" != "${__hhs_ttyd_last_pwd}" ]]; then
    __hhs_ttyd_last_pwd="${PWD}"
    __hhs_ttyd_emit_cwd "prompt" "${status_code}"
  fi
  return "${status_code}"
}

if [[ -n "${PROMPT_COMMAND:-}" ]]; then
  PROMPT_COMMAND="__hhs_ttyd_after_command; ${PROMPT_COMMAND}"
else
  PROMPT_COMMAND="__hhs_ttyd_after_command"
fi

trap '__hhs_ttyd_emit_exit "$?"' EXIT
    """


def build_ttyd_hooked_bash_command(cwd: str, shell: str = "bash") -> str:
    """Build a Bash command that starts an interactive shell with ttyd hooks."""
    startup_script = ttyd_shell_hook_script()
    safe_cwd = shlex.quote(cwd)
    safe_shell = shlex.quote(shell)
    safe_script = shlex.quote(startup_script)
    return (
        f"cd {safe_cwd} 2>/dev/null || cd; "
        f"exec {safe_shell} --rcfile <(printf %s {safe_script}) -i"
    )


def build_ttyd_remote_command(host: str, cwd: str) -> list[str]:
    """Build the SSH command run by ttyd for remote terminal sessions."""
    remote_command = build_ttyd_hooked_bash_command(cwd)
    ssh_options = [
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "ConnectionAttempts=1",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "ServerAliveCountMax=1",
        "-o",
        f"ControlPath={ssh_control_path(host)}",
    ]
    return [
        "ssh",
        "-tt",
        *ssh_config_option_args(),
        *ssh_options,
        host,
        f"bash -lc {shlex.quote(remote_command)}",
    ]


def build_ttyd_shell_command(cwd: str) -> list[str]:
    """Build the shell command served by ttyd for the active execution host."""
    host = connected_ssh_host()
    if host:
        return build_ttyd_remote_command(host, cwd)
    return [RUN_SHELL, "-lc", build_ttyd_hooked_bash_command(cwd, RUN_SHELL)]


def build_ttyd_command(
    binary: str, port: int, cwd: str, index_file: str = ""
) -> list[str]:
    """Build the ttyd server command for the active terminal session."""
    command = [
        binary,
        "-W",
        "-q",
        "-i",
        hhs_ui.TTYD_HOST,
        "-p",
        str(port),
        "-w",
        ttyd_process_working_directory(cwd),
        "-t",
        f"fontFamily={ttyd_font_family()}, monospace",
        "-t",
        'theme={"background":"#000000"}',
        "-t",
        "fontSize=14",
        "-t",
        "cursorStyle=underline",
        "-t",
        "cursorBlink=true",
        "-t",
        "disableLeaveAlert=true",
        "-t",
        "disableResizeOverlay=true",
        "-t",
        "titleFixed=HomeSetup Terminal",
    ]
    if index_file:
        command.extend(("-I", index_file))
    command.extend(build_ttyd_shell_command(cwd))
    return command


def stop_ttyd_session() -> None:
    """Stop any ttyd process owned by the current Streamlit session."""
    process = st.session_state.pop(hhs_ui_constants.TTYD_PROCESS_KEY, None)
    st.session_state.pop(hhs_ui_constants.TTYD_PORT_KEY, None)
    st.session_state.pop(hhs_ui_constants.TTYD_SIGNATURE_KEY, None)
    stop_process(process)


def ensure_ttyd_session() -> str:
    """Start or reuse a ttyd server and return the iframe URL."""
    binary = ttyd_binary()
    if not binary:
        stop_ttyd_session()
        return ""
    cwd = footer_working_directory()
    event_url = ttyd_event_url()
    update_browser_cleanup_registration()
    signature = ttyd_session_signature(cwd, binary, event_url)
    process = st.session_state.get(hhs_ui_constants.TTYD_PROCESS_KEY)
    port = st.session_state.get(hhs_ui_constants.TTYD_PORT_KEY)
    if (
        ttyd_process_is_running(process)
        and isinstance(port, int)
        and st.session_state.get(hhs_ui_constants.TTYD_SIGNATURE_KEY) == signature
    ):
        return f"http://{hhs_ui.TTYD_HOST}:{port}/"

    stop_ttyd_session()
    port = allocate_ttyd_port()
    index_file = ensure_ttyd_index_file(binary, event_url)
    command = build_ttyd_command(binary, port, cwd, index_file)
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    time.sleep(0.15)
    if not ttyd_process_is_running(process):
        return ""
    st.session_state[hhs_ui_constants.TTYD_PROCESS_KEY] = process
    st.session_state[hhs_ui_constants.TTYD_PORT_KEY] = port
    st.session_state[hhs_ui_constants.TTYD_SIGNATURE_KEY] = signature
    update_browser_cleanup_registration()
    return f"http://{hhs_ui.TTYD_HOST}:{port}/"


def render_ttyd_terminal_frame(ttyd_url: str) -> None:
    """Render the active ttyd terminal in an iframe."""
    iframe_height = int(hhs_ui.TTYD_IFRAME_HEIGHT)
    st.markdown(
        f"""
        <div
          id="hhs-ttyd-terminal-anchor"
          class="hhs-ttyd-terminal-shell"
          style="--hhs-ttyd-max-height: {iframe_height}px;"
        >
          <div class="hhs-ttyd-terminal-placeholder"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_script_html(
        f"""
        <script>
          (() => {{
            const doc = window.parent.document;
            const src = {json.dumps(ttyd_url)};
            const frameId = "hhs-persistent-ttyd-frame";
            const anchor = doc.getElementById("hhs-ttyd-terminal-anchor");
            if (!anchor) {{
              return;
            }}
            let frame = doc.getElementById(frameId);
            if (!frame || frame.dataset.src !== src) {{
              if (frame) {{
                frame.remove();
              }}
              frame = doc.createElement("iframe");
              frame.id = frameId;
              frame.dataset.src = src;
              frame.src = src;
              frame.title = "HomeSetup Terminal";
              frame.loading = "eager";
              frame.className = "hhs-ttyd-terminal-frame hhs-ttyd-terminal-frame-persistent";
              frame.style.position = "fixed";
              frame.style.border = "0";
              frame.style.zIndex = "20";
              frame.style.display = "none";
              doc.body.appendChild(frame);
            }}
            const syncFrame = () => {{
              const rect = anchor.getBoundingClientRect();
              const inset = 10;
              const visible = rect.width > 0 && rect.height > 0;
              frame.style.display = visible ? "block" : "none";
              frame.style.left = `${{rect.left + inset}}px`;
              frame.style.top = `${{rect.top + inset}}px`;
              frame.style.width = `${{Math.max(0, rect.width - (inset * 2))}}px`;
              frame.style.height = `${{Math.max(0, rect.height - (inset * 2))}}px`;
            }};
            if (window.parent.__hhsTtydFrameSyncCleanup) {{
              window.parent.__hhsTtydFrameSyncCleanup();
            }}
            const observer = "ResizeObserver" in window.parent
              ? new window.parent.ResizeObserver(syncFrame)
              : null;
            if (observer) {{
              observer.observe(anchor);
            }}
            window.parent.addEventListener("resize", syncFrame);
            window.parent.addEventListener("scroll", syncFrame, true);
            window.parent.__hhsTtydFrameSyncCleanup = () => {{
              if (observer) {{
                observer.disconnect();
              }}
              window.parent.removeEventListener("resize", syncFrame);
              window.parent.removeEventListener("scroll", syncFrame, true);
            }};
            syncFrame();
          }})();
        </script>
        """,
        height=1,
        width=1,
    )


def render_ttyd_terminal_frame_cleanup_script() -> None:
    """Remove the browser-persistent ttyd iframe after a Terminal session reset."""
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (parentWindow.__hhsTtydFrameSyncCleanup) {
              parentWindow.__hhsTtydFrameSyncCleanup();
              parentWindow.__hhsTtydFrameSyncCleanup = null;
            }
            if (parentWindow.__hhsTtydExitBackHandler) {
              parentWindow.removeEventListener("message", parentWindow.__hhsTtydExitBackHandler);
              parentWindow.__hhsTtydExitBackHandler = null;
            }
            const frame = doc.getElementById("hhs-persistent-ttyd-frame");
            if (frame) {
              frame.remove();
            }
          })();
        </script>
        """,
        height=1,
        width=1,
    )


def render_ttyd_terminal_frame_hide_script() -> None:
    """Hide the browser-persistent ttyd iframe while preserving its session."""
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (parentWindow.__hhsTtydFrameSyncCleanup) {
              parentWindow.__hhsTtydFrameSyncCleanup();
              parentWindow.__hhsTtydFrameSyncCleanup = null;
            }
            if (parentWindow.__hhsTtydExitBackHandler) {
              parentWindow.removeEventListener("message", parentWindow.__hhsTtydExitBackHandler);
              parentWindow.__hhsTtydExitBackHandler = null;
            }
            const frame = doc.getElementById("hhs-persistent-ttyd-frame");
            if (frame) {
              frame.style.display = "none";
            }
          })();
        </script>
        """,
        height=1,
        width=1,
    )


def render_ttyd_unavailable() -> None:
    """Render a dependency message when ttyd cannot be started."""
    st.error("ttyd is not available to the UI process.")


def cleanup_session_resources(token: str, *, disconnect_ssh: bool = True) -> None:
    """Close resources registered for a browser session token."""
    entry = TTYD_CLEANUP_REGISTRY.pop(token, None)
    if not entry:
        return
    stop_process(entry.get("ttyd_process"))
    ssh_host = str(entry.get("ssh_host", "")).strip()
    if disconnect_ssh and ssh_host and not selected_host_is_local(ssh_host):
        if ssh_host_has_other_cleanup_registration(ssh_host):
            return
        run_cleanup_bash_command(build_ssh_disconnect_command(ssh_host), 10)
        clear_registered_ssh_connection()


def ssh_host_has_other_cleanup_registration(ssh_host: str) -> bool:
    """Return whether another browser session still owns the SSH host."""
    return any(
        str(entry.get("ssh_host", "")).strip() == ssh_host
        for entry in list(TTYD_CLEANUP_REGISTRY.values())
    )


def cleanup_session_resources_after_grace(token: str, requested_at: float) -> None:
    """Wait for a refreshed browser session before closing its resources."""
    time.sleep(hhs_ui_constants.BROWSER_CLEANUP_GRACE_SECONDS)
    entry = TTYD_CLEANUP_REGISTRY.get(token, {})
    if float(entry.get("lease_updated_at", 0.0) or 0.0) > requested_at:
        return
    cleanup_session_resources(token)


def schedule_cleanup_session_resources(token: str) -> None:
    """Close browser-session resources without blocking the unload request."""
    clean_token = token.strip()
    if not clean_token:
        return
    requested_at = time.monotonic()
    thread = threading.Thread(
        target=cleanup_session_resources_after_grace,
        args=(clean_token, requested_at),
        name=f"hhs-ttyd-session-cleanup-{clean_token[:8]}",
        daemon=True,
    )
    thread.start()


def store_ttyd_event(token: str, event: dict[str, object]) -> None:
    """Store a ttyd browser event for later UI synchronization."""
    if not token:
        return
    events = TTYD_EVENT_REGISTRY.setdefault(token, [])
    events.append(event)
    del events[:-25]
    event_requests_close = ttyd_event_requests_document_close(event)
    if event.get("type") != "cwd" and not event_requests_close:
        return
    entry = TTYD_CLEANUP_REGISTRY.setdefault(token, {})
    cwd = str(event.get("cwd", "")).strip()
    if cwd:
        entry["cwd"] = cwd
    if event_requests_close:
        entry["exit_requested"] = True
    entry["last_event"] = event


def ttyd_event_requests_document_close(event: dict[str, object]) -> bool:
    """Return whether a ttyd event should close the Terminal document view."""
    event_type = str(event.get("type", "")).strip().lower()
    command = str(event.get("command", "")).strip().lower()
    return event_type == "exit" or command in TTYD_EXIT_COMMANDS


def normalize_ttyd_event(value: object) -> dict[str, object]:
    """Return a sanitized ttyd event dictionary."""
    if not isinstance(value, dict):
        return {}
    event_type = re.sub(r"[^A-Za-z0-9_-]+", "", str(value.get("type", "")))
    command = re.sub(r"[^A-Za-z0-9_-]+", "", str(value.get("command", "")))
    cwd = str(value.get("cwd", "")).strip()
    try:
        status = int(value.get("status", 0) or 0)
    except (TypeError, ValueError):
        status = 0
    try:
        event_time = int(value.get("time", 0) or 0)
    except (TypeError, ValueError):
        event_time = int(time.time() * 1000)
    if not event_type:
        return {}
    event = {
        "type": event_type,
        "command": command or "unknown",
        "status": status,
        "cwd": cwd,
        "time": event_time,
    }
    if event_type == "terminal-context":
        content = str(value.get("content", "")).replace("\r\n", "\n")
        content = content.replace("\r", "\n").strip()
        truncated = bool(value.get("truncated", False))
        max_chars = int(hhs_ui.AI_TERMINAL_CONTEXT_MAX_CHARS)
        if len(content) > max_chars:
            content = content[-max_chars:]
            truncated = True
        event["content"] = content
        event["mode"] = re.sub(r"[^A-Za-z0-9_-]+", "", str(value.get("mode", "")))[:32]
        event["requestId"] = re.sub(
            r"[^A-Za-z0-9_.:-]+", "", str(value.get("requestId", ""))
        )[:80]
        event["truncated"] = truncated
    return event


def sync_ttyd_event_state() -> None:
    """Synchronize latest ttyd hook events into Streamlit session state."""
    token = str(
        st.session_state.get(hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY, "")
    ).strip()
    if not token:
        return
    entry = TTYD_CLEANUP_REGISTRY.get(token)
    if not isinstance(entry, dict):
        return
    if bool(entry.pop("exit_requested", False)):
        if terminal_document_view_is_active():
            close_document_view(reset_terminal=True)
            st.rerun()
        else:
            deactivate_terminal_document_view()
        return
    cwd = str(entry.get("cwd", "")).strip()
    if not cwd:
        return
    st.session_state[hhs_ui.TERMINAL_CWD_KEY] = cwd
    if connected_ssh_host():
        st.session_state[hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY] = cwd
    else:
        st.session_state[hhs_ui_constants.FOOTER_LOCAL_WORKING_DIR_KEY] = cwd


def run_cleanup_bash_command(
    command: str, timeout_seconds: int
) -> subprocess.CompletedProcess[str]:
    """Run a local cleanup command outside the normal Streamlit render flow."""
    try:
        return subprocess.run(
            [RUN_SHELL, "-lc", command],
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        return subprocess.CompletedProcess(
            [RUN_SHELL, "-lc", command],
            124,
            error.stdout or "",
            error.stderr or f"Command timed out after {timeout_seconds} seconds.",
        )
    except OSError as error:
        return subprocess.CompletedProcess(
            [RUN_SHELL, "-lc", command],
            127,
            "",
            str(error),
        )


class TtydCleanupRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler used by browser unload beacons to close ttyd and SSH."""

    def log_message(self, _format: str, *_args: object) -> None:
        """Suppress cleanup server access logs."""
        return

    def end_headers(self) -> None:
        """Send CORS headers for browser unload beacons."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        """Handle browser preflight requests."""
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        """Handle image/fetch fallback cleanup requests."""
        self.handle_cleanup_request()

    def do_POST(self) -> None:
        """Handle navigator.sendBeacon cleanup requests."""
        request_path = urllib.parse.urlparse(self.path).path
        if request_path == "/ttyd-event":
            self.handle_ttyd_event_request()
            return
        if request_path == "/open-working-directory":
            self.handle_open_working_directory_request()
            return
        self.handle_cleanup_request()

    def handle_cleanup_request(self) -> None:
        """Close resources for the token provided in the request query string."""
        parsed_url = urllib.parse.urlparse(self.path)
        token = urllib.parse.parse_qs(parsed_url.query).get("token", [""])[0]
        self.send_response(204)
        self.end_headers()
        if token:
            schedule_cleanup_session_resources(token)

    def handle_ttyd_event_request(self) -> None:
        """Store a ttyd event sent by the browser bridge."""
        parsed_url = urllib.parse.urlparse(self.path)
        token = urllib.parse.parse_qs(parsed_url.query).get("token", [""])[0]
        try:
            content_length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            content_length = 0
        try:
            payload = self.rfile.read(content_length).decode("utf-8")
            event = normalize_ttyd_event(json.loads(payload or "{}"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            event = {}
        if token and event:
            store_ttyd_event(token, event)
        self.send_response(204)
        self.end_headers()

    def handle_open_working_directory_request(self) -> None:
        """Open the registered local working directory without a Streamlit rerun."""
        parsed_url = urllib.parse.urlparse(self.path)
        token = urllib.parse.parse_qs(parsed_url.query).get("token", [""])[0]
        entry = TTYD_CLEANUP_REGISTRY.get(token, {})
        if not token or entry.get("ssh_host"):
            self.send_response(409)
            self.end_headers()
            return
        directory = (
            str(entry.get("cwd") or entry.get("working_dir") or os.getcwd()).strip()
            or os.getcwd()
        )
        result = run_cleanup_bash_command(open_file(directory), 10)
        self.send_response(204 if result.returncode == 0 else 500)
        self.end_headers()


def cleanup_all_registered_sessions() -> None:
    """Close all registered ttyd and SSH resources on Streamlit process exit."""
    for token in list(TTYD_CLEANUP_REGISTRY):
        cleanup_session_resources(token)


def ensure_ttyd_cleanup_server() -> int:
    """Start the localhost cleanup server and return its port."""
    global TTYD_CLEANUP_SERVER, TTYD_CLEANUP_SERVER_PORT
    if TTYD_CLEANUP_SERVER is not None:
        return TTYD_CLEANUP_SERVER_PORT
    state = process_resource_state()
    cached_server = state.get("ttyd_cleanup_server")
    cached_port = int(state.get("ttyd_cleanup_server_port") or 0)
    if cached_server is not None and cached_port > 0:
        TTYD_CLEANUP_SERVER = cached_server
        TTYD_CLEANUP_SERVER_PORT = cached_port
        return TTYD_CLEANUP_SERVER_PORT
    server = ThreadingHTTPServer((hhs_ui.TTYD_HOST, 0), TtydCleanupRequestHandler)
    server.daemon_threads = True
    port = int(server.server_address[1])
    TTYD_CLEANUP_SERVER = server
    TTYD_CLEANUP_SERVER_PORT = port
    state["ttyd_cleanup_server"] = server
    state["ttyd_cleanup_server_port"] = port
    thread = threading.Thread(
        target=server.serve_forever,
        name="hhs-ttyd-cleanup",
        daemon=True,
    )
    thread.start()
    if not bool(state.get("ttyd_cleanup_atexit_registered", False)):
        atexit.register(cleanup_all_registered_sessions)
        state["ttyd_cleanup_atexit_registered"] = True
    return TTYD_CLEANUP_SERVER_PORT


def browser_cleanup_token() -> str:
    """Return the per-browser-session cleanup token."""
    token = str(
        st.session_state.get(hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY, "")
    ).strip()
    if not token:
        token = secrets.token_urlsafe(24)
        st.session_state[hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY] = token
    return token


def update_browser_cleanup_registration() -> str:
    """Register the current ttyd and SSH resources for browser unload cleanup."""
    token = browser_cleanup_token()
    entry = TTYD_CLEANUP_REGISTRY.setdefault(token, {})
    ssh_host = connected_ssh_host()
    if not ssh_host:
        ssh_host = str(
            st.session_state.get("ssh_connect_pending")
            or st.session_state.get("ssh_connection_host")
            or ""
        ).strip()
        if selected_host_is_local(ssh_host):
            ssh_host = ""
    entry.update(
        {
            "ttyd_process": st.session_state.get(hhs_ui_constants.TTYD_PROCESS_KEY),
            "ssh_host": ssh_host,
            "working_dir": footer_working_directory(),
            "lease_updated_at": time.monotonic(),
        }
    )
    return token


def ttyd_event_url() -> str:
    """Return the local browser-to-UI ttyd event endpoint URL."""
    token = browser_cleanup_token()
    port = ensure_ttyd_cleanup_server()
    return f"http://{hhs_ui.TTYD_HOST}:{port}/ttyd-event?token={token}"


def render_browser_cleanup_script() -> None:
    """Install a browser unload hook that closes session resources after a grace."""
    token = update_browser_cleanup_registration()
    port = ensure_ttyd_cleanup_server()
    cleanup_url = f"http://{hhs_ui.TTYD_HOST}:{port}/cleanup?token={token}"
    ttyd_event_request_url = (
        f"http://{hhs_ui.TTYD_HOST}:{port}/ttyd-event?token={token}"
    )
    render_script_html(
        f"""
        <script>
          (() => {{
            const cleanupUrl = {cleanup_url!r};
            const ttydEventUrl = {ttyd_event_request_url!r};
            const parentWindow = window.parent;
            parentWindow.__hhsTtydEventUrl = ttydEventUrl;
            if (
              parentWindow.__hhsTtydCleanupUrl === cleanupUrl &&
              parentWindow.__hhsTtydCleanupHandler
            ) {{
              return;
            }}
            if (parentWindow.__hhsTtydCleanupHandler) {{
              parentWindow.removeEventListener(
                "pagehide",
                parentWindow.__hhsTtydCleanupHandler
              );
              parentWindow.removeEventListener(
                "beforeunload",
                parentWindow.__hhsTtydCleanupHandler
              );
              parentWindow.__hhsTtydCleanupHandler = null;
            }}
            parentWindow.__hhsTtydCleanupUrl = cleanupUrl;
            const cleanup = () => {{
              try {{
                if (parentWindow.__hhsTtydCleanupSent === cleanupUrl) {{
                  return;
                }}
                parentWindow.__hhsTtydCleanupSent = cleanupUrl;
                if (navigator.sendBeacon) {{
                  navigator.sendBeacon(cleanupUrl, "");
                  return;
                }}
                fetch(cleanupUrl, {{
                  method: "POST",
                  mode: "no-cors",
                  keepalive: true,
                }}).catch(() => {{}});
              }} catch (_error) {{
                const image = new Image();
                image.src = cleanupUrl;
              }}
            }};
            parentWindow.addEventListener("pagehide", cleanup, {{ once: true }});
            parentWindow.addEventListener("beforeunload", cleanup, {{ once: true }});
            parentWindow.__hhsTtydCleanupHandler = cleanup;
            if (parentWindow.__hhsTtydTerminalContextCacheHandler) {{
              parentWindow.removeEventListener(
                "message",
                parentWindow.__hhsTtydTerminalContextCacheHandler
              );
            }}
            parentWindow.__hhsTtydTerminalContextCacheHandler = (event) => {{
              const data = event.data || {{}};
              if (
                data.type === "hhs-ttyd-event" &&
                data.event &&
                data.event.type === "terminal-context"
              ) {{
                parentWindow.__hhsTtydTerminalContextEvent = data.event;
              }}
            }};
            parentWindow.addEventListener(
              "message",
              parentWindow.__hhsTtydTerminalContextCacheHandler
            );
            if (!parentWindow.__hhsTtydEventListenerInstalled) {{
              parentWindow.__hhsTtydEventListenerInstalled = true;
              parentWindow.addEventListener("message", (event) => {{
                const data = event.data || {{}};
                if (data.type !== "hhs-ttyd-event" || !data.event) {{
                  return;
                }}
                if (data.event.type === "terminal-context") {{
                  parentWindow.__hhsTtydTerminalContextEvent = data.event;
                  try {{
                    fetch(parentWindow.__hhsTtydEventUrl || ttydEventUrl, {{
                      method: "POST",
                      headers: {{"Content-Type": "application/json"}},
                      body: JSON.stringify(data.event),
                      keepalive: true,
                    }}).catch(() => {{}});
                  }} catch (_error) {{}}
                  return;
                }}
                if (data.event.type !== "cwd") {{
                  return;
                }}
                const cwd = String(data.event.cwd || "").trim();
                if (!cwd) {{
                  return;
                }}
                const link = parentWindow.document.querySelector(".hhs-footer-working-dir-link");
                const node = parentWindow.document.querySelector(".hhs-footer-working-dir-value");
                if (node) {{
                  node.textContent = cwd;
                }}
                if (link) {{
                  link.dataset.hhsWorkingDir = cwd;
                  link.title = `Working dir: ${{cwd}}`;
                }}
              }});
            }}
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def terminal_document_title() -> str:
    """Return the terminal document title for local or SSH-connected sessions."""
    if str(st.session_state.get("ssh_connection_status", "")).strip() == "connected":
        return "Remote Terminal"
    return "Terminal"


def initialize_terminal_session_state() -> None:
    """Initialize ttyd terminal working directory state."""
    st.session_state.setdefault(hhs_ui.TERMINAL_CWD_KEY, footer_working_directory())


def show_terminal_ready_status() -> None:
    """Queue the terminal ready status once the ttyd terminal is rendered."""
    if not bool(st.session_state.get(hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY, False)):
        push_floating_status("HomeSetup terminal is ready.", "info")
        st.session_state[hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY] = True
