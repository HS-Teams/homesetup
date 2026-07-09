"""Constants used by the HomeSetup Streamlit UI."""

from __future__ import annotations

import os
import re
from pathlib import Path

# NOTE: Follow SemVer for this script. Any UI behavior change must bump VERSION,
# at minimum by incrementing the patch number.
VERSION = "0.1.83"
DISPLAY_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
APP_DIR = Path(__file__).resolve().parent
APP_CSS_FILE = APP_DIR / "streamlit_ui.css"
APP_THEME_CSS_FILE = APP_DIR / "themes/dracula.css"
SSH_EXPLORER_COMPONENT_DIR = APP_DIR / "components/ssh_explorer"
FIREBASE_CONFIG_COMPONENT_DIR = APP_DIR / "components/firebase_config_form"
APP_FONT_FAMILY = "Droid Sans Mono for Powerline Nerd Font Complete"
APP_FONT_FILE = (
    APP_DIR / "assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
)
TTYD_HOST = "127.0.0.1"
TTYD_IFRAME_HEIGHT = 760
APP_AI_USER_AVATAR_FILE = APP_DIR / "assets/images/user.png"
APP_AI_OLLAMA_AVATAR_FILE = APP_DIR / "assets/images/ollama.png"
APP_AI_HOMESETUP_AVATAR_FILE = APP_DIR / "assets/images/homesetup.png"
APP_FAVICON_FILE = APP_DIR / "assets/images/favicon.png"
APP_TERMINAL_BACKGROUND_FILE = APP_DIR / "assets/images/term-bg.png"
PORTS_DEFAULT_FILE = (
    Path(os.environ.get("HHS_HOME", APP_DIR.parents[4]))
    / "assets/devel/ports-default.csv"
)
HHS_DIR = Path(os.environ.get("HHS_DIR", str(APP_DIR)))
HHS_CACHE_DIR = Path(os.environ.get("HHS_CACHE_DIR", str(HHS_DIR / "cache")))
UI_STATE_FILE = HHS_CACHE_DIR / "streamlit-ui-state.json"
UI_CACHE_FILE = HHS_CACHE_DIR / "streamlit-ui-cache.json"
UI_CACHE_SSH_CONNECTION_KEY = "ui:ssh_connection"
SSH_RECONNECT_HOST_KEY = "ssh_reconnect_host"
TTYD_INDEX_FILE = HHS_CACHE_DIR / "streamlit-ttyd-index.html"
UI_CACHE_REALTIME_TTL_SECONDS = 30
UI_CACHE_NORMAL_TTL_SECONDS = 300
UI_CACHE_LOW_CHANGE_TTL_SECONDS = 900
UI_CACHE_DEFAULT_TTL_SECONDS = UI_CACHE_NORMAL_TTL_SECONDS
UI_COMMAND_LOCAL_TIMEOUT_SECONDS = 30
UI_COMMAND_REMOTE_TIMEOUT_SECONDS = 60
UI_COMMAND_DEFAULT_TIMEOUT_SECONDS = UI_COMMAND_LOCAL_TIMEOUT_SECONDS
UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS = 30
UI_COMMAND_SEARCH_TIMEOUT_SECONDS = 300
UI_COMMAND_DISK_TIMEOUT_SECONDS = 45
UI_COMMAND_SERVICE_ACTION_TIMEOUT_SECONDS = 180
UI_COMMAND_LONG_ACTION_TIMEOUT_SECONDS = 1800
UI_COMMAND_MODEL_DOWNLOAD_TIMEOUT_SECONDS = 3600
DEFAULT_TOP_N = 10
MIN_TOP_N = 1
MAX_TOP_N = 100
DEFAULT_LOG_TAIL_LINES = 50
LEGACY_DEFAULT_LOG_TAIL_LINES = 10
MIN_LOG_TAIL_LINES = 5
MAX_LOG_TAIL_LINES = 5000
LOG_TAIL_LINES_STEP = 5
FLOATING_STATUS_QUEUE_KEY = "_hhs_floating_status_queue"
FLOATING_STATUS_LEGACY_KEY = "_hhs_floating_status"
FLOATING_STATUS_QUEUE_LIMIT = 20
FLOATING_STATUS_AUTO_DISPOSE_EXTENSION_SECONDS = 1.0
FOOTER_REMOTE_WORKING_DIR_KEY = "_hhs_footer_remote_working_dir"
FOOTER_LOCAL_WORKING_DIR_KEY = "_hhs_footer_local_working_dir"
TABLE_SELECTION_SNAPSHOT_KEY = "_hhs_table_selection_snapshots"
COMMAND_RESULT_SNAPSHOT_KEY = "_hhs_command_result_snapshots"
COMMAND_RESULT_SNAPSHOT_LIMIT = 100
PARSED_ROWS_CACHE_KEY = "_hhs_parsed_rows_cache"
PARSED_ROWS_CACHE_LIMIT = 100
LOG_RENDER_CACHE_KEY = "_hhs_log_render_cache"
LOG_RENDER_CACHE_LIMIT = 20
AI_SERVICE_AVAILABLE_KEY = "_hhs_ai_service_available"
AI_SERVICE_AVAILABILITY_LOADED_KEY = "_hhs_ai_service_availability_loaded"
AI_SERVICE_AVAILABILITY_CONTEXT_KEY = "_hhs_ai_service_availability_context"
AI_SERVICE_AVAILABILITY_REFRESHED_AT_KEY = "_hhs_ai_service_availability_refreshed_at"
AI_SERVICE_AVAILABILITY_REFRESH_INTERVAL_SECONDS = 30.0
AI_TERMINAL_CONTEXT_MAX_CHARS = 12000
TTYD_PROCESS_KEY = "_hhs_ttyd_process"
TTYD_PORT_KEY = "_hhs_ttyd_port"
TTYD_SIGNATURE_KEY = "_hhs_ttyd_signature"
TTYD_CLEANUP_TOKEN_KEY = "_hhs_ttyd_cleanup_token"
AI_CONTEXT_UPLOAD_TYPES = (
    "txt",
    "md",
    "markdown",
    "csv",
    "tsv",
    "json",
    "jsonl",
    "yaml",
    "yml",
    "toml",
    "ini",
    "conf",
    "cfg",
    "log",
    "xml",
    "html",
    "css",
    "js",
    "ts",
    "py",
    "sh",
    "bash",
    "zsh",
    "java",
    "kt",
    "go",
    "rs",
    "rb",
    "php",
    "sql",
)
RUN_SHELL_ENV_KEY = "RUN_SHELL"
APP_CSS = ""
VIEWS = ("Home", "Configs", "HHS", "Services", "Monitor", "Search", "History")
AI_VIEW = "AI"
SSH_VIEW = "SSH"
VIEW_LABELS = {
    "Home": " System",
    "Configs": " Configs",
    "HHS": " HHS",
    "Services": " Services",
    "Monitor": " Monitor",
    "Search": " Search",
    "History": " History",
    SSH_VIEW: " SSH",
    AI_VIEW: " AI",
}
AI_VIEWS = ("CHAT", "CONTEXT", "SETTINGS")
AI_VIEW_LABELS = {
    "CHAT": " Chat",
    "CONTEXT": " Context",
    "SETTINGS": " Settings",
}
HOME_VIEWS = ("System", "Docker", "Tools", "SHOPTS")
HOME_VIEW_LABELS = {
    "System": " Summary",
    "Docker": " Docker",
    "Tools": " Tools",
    "SHOPTS": " Shell Options",
}
HHS_VIEWS = ("SETUP", "STARSHIP", "SETTINGS", "HSPM", "Firebase")
HHS_VIEW_LABELS = {
    "SETUP": " Setup",
    "STARSHIP": "留 Starship",
    "SETTINGS": "שּׂ Settings",
    "HSPM": " HSPM",
    "Firebase": " Firebase",
}
CONFIG_VIEWS = ("ENV", "PATH", "DIR", "CMD", "ALIAS")
CONFIG_VIEW_LABELS = {
    "ENV": " Environment",
    "PATH": " Paths",
    "DIR": " Saved Dirs",
    "CMD": "ﮒ Saved Cmds",
    "ALIAS": " Aliases",
}
HISTORY_VIEWS = ("COMMANDS", "DIRECTORIES", "STATS")
HISTORY_VIEW_LABELS = {
    "COMMANDS": " Commands",
    "DIRECTORIES": " Directories",
    "STATS": " Stats",
}
MONITOR_VIEWS = ("DISK", "MEM", "CPU", "PROCESSES", "LOGS")
MONITOR_VIEW_LABELS = {
    "DISK": " Disks",
    "CPU": " Cpu",
    "MEM": " Memory",
    "PROCESSES": " Processes",
    "LOGS": " Logs",
}
SEARCH_TYPES = ("Files", "Folders", "Strings")
SEARCH_TYPE_LABELS = {
    "Files": "Files",
    "Folders": "Folders",
    "Strings": "Strings",
}
SEARCH_FILTERS = ("All", "Containing")
SEARCH_PAGE_SIZE = 20
SEARCH_DIRECTORY_HISTORY_LIMIT = 20
SEARCH_TERM_HISTORY_LIMIT = 20
SEARCH_TERM_HISTORY_CACHE_KEY = "search_terms:history"
SEARCH_TERM_HISTORY_TTL_SECONDS = UI_CACHE_LOW_CHANGE_TTL_SECONDS
SSH_VIEWS = ("TUNNELS", "FILES")
SSH_VIEW_LABELS = {
    "TUNNELS": " Tunnels",
    "FILES": " Explorer",
}
SSH_TUNNEL_FILTERS = ("All", "Reachable", "Containing")
ENV_FILTERS = ("All", "HHS", "Containing")
LIST_FILTERS = ("All", "Containing")
HOME_TOOLS_FILTERS = ("All", "Installed", "Not Installed", "Aliased", "Containing")
LOG_FILTERS = ("All", "Containing")
HISTORY_FILTERS = ("All", "Containing")
PATH_FILTERS = ("All", "Shell", "Private", "Custom", "Containing")
PROCESS_FILTERS = ("All", "Active", "Inactive", "Ghost", "Containing")
SERVICE_FILTERS = ("All", "Up", "Down", "Containing")
SHOPTS_FILTERS = ("All", "ON", "OFF", "Containing")
LOG_LEVELS = (
    "ALL_LEVELS",
    "CRITICAL",
    "DEBUG",
    "ERROR",
    "FATAL",
    "FINE",
    "INFO",
    "OUT",
    "TRACE",
    "WARNING",
    "WARN",
    "SEVERE",
)
TABLE_CONTROLS_PANEL_TITLE = "Filters & Controls"
THEME_SELECTED_KEY = "theme_selected"
AI_CODE_BLOCK_WRAP_COLUMNS = 96
AI_PERFORMANCE_MIN_SAMPLES = 3
AI_PERFORMANCE_RECALC_INTERVAL = 5
AI_PERFORMANCE_TIMING_LIMIT = 100
PROCESS_TABLE_KEY = "monitor_process_table"
HHS_STARSHIP_CURRENT_PRESET_KEY = "hhs_starship_current_preset"
PERSISTED_UI_KEYS = (
    "active_view",
    "ai_chat_messages",
    "ai_clear_chat_execute_pending",
    "ai_context_error",
    "ai_context_output",
    "ai_model_performance_averages",
    "ai_model_performance_sample_counts",
    "ai_model_performance_timings",
    "ai_model_delete_execute_pending",
    "ai_model_select_execute_pending",
    "ai_prompt_editor",
    "ai_prompt_error",
    "ai_prompt_loaded",
    "ai_view",
    "alias_filter",
    "alias_other_filter",
    "cmds_filter",
    "cmds_other_filter",
    "config_view",
    "dirs_filter",
    "dirs_other_filter",
    "document_previous_view",
    "document_selected",
    "document_view_active",
    "env_filter",
    "env_other_filter",
    "env_value_overrides",
    "home_view",
    "ssh_host_selected",
    "ssh_explorer_local_path",
    "ssh_explorer_remote_path",
    "home_tools_filter",
    "home_tools_other_filter",
    "home_shopts_filter",
    "home_shopts_other_filter",
    "hhs_view",
    HHS_STARSHIP_CURRENT_PRESET_KEY,
    "history_commands_filter",
    "history_commands_other_filter",
    "history_directories_filter",
    "history_directories_other_filter",
    "history_stats_top_n",
    "history_view",
    "monitor_cpu_top_n",
    "monitor_disk_directory",
    "monitor_disk_top_n",
    "monitor_log_file",
    "monitor_log_filter",
    "monitor_log_level",
    "monitor_log_other_filter",
    "monitor_log_tail_lines",
    "monitor_log_tail_lines_default_migrated",
    "monitor_logs_tail",
    "monitor_mem_top_n",
    "monitor_process_filter",
    "monitor_process_other_filter",
    "monitor_view",
    "path_filter",
    "path_other_filter",
    "service_filter",
    "service_other_filter",
    "search_binary",
    "search_directories",
    "search_filter",
    "search_ignore_case",
    "search_other_filter",
    "search_path",
    "search_replace",
    "search_replacement",
    "search_type",
    "search_words",
    SSH_RECONNECT_HOST_KEY,
    "ssh_tunnel_filter",
    "ssh_tunnel_other_filter",
    "ssh_view",
    "theme_selected",
    "updater_last_check_output",
    "updater_update_available",
)
PERSISTED_UI_KEY_PREFIXES = (
    "alias_selected_value_",
    "cmd_selected_value_",
    "dir_selected_value_",
    "env_selected_value_",
    "history_command_selected_value_",
    "history_directory_selected_value_",
    "service_selected_value_",
)
ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
)
ALIAS_LINE_PATTERN = re.compile(r"^(.+?)\.{2,}\s+(?:|=>)\s+'?(.*?)'?$")
COMMAND_LINE_PATTERN = re.compile(
    r"^\((\d+)\)\s+(.+?)\.{2,}\s+(?:|=>)\s+'?(.*?)'?(?:\.\.\.)?$"
)
ESCAPED_ANSI_ESCAPE_PATTERN = re.compile(
    r"(?:\\033|\\x1b|\\e)(?:\[[0-?]*[ -/]*[@-~]|\][^\\]*(?:\\a|\\033\\|\\x1b\\)|[()][A-Za-z0-9])"
)
DIR_LINE_PATTERN = re.compile(r"^(.+?)\.{2,}\s+(?:|=>)\s+'?(.*?)'?$")
ENV_LINE_PATTERN = re.compile(r"^([A-Za-z0-9_]+)\s+\.{2,}\s+(?:|=>)\s+(.*)$")
PATH_SOURCE_PATTERN = re.compile(r"(?:|=>)\s+(.*)$")
PATH_TYPE_PATTERN = re.compile(r"^(\S+)\s+")
SERVICE_LINE_PATTERN = re.compile(r"^(\d+):\s+(.+?)\.{2,}\s*(\S+)\s+(.+)$")
HISTORY_COMMAND_LINE_PATTERN = re.compile(r"^(\d+)\.{2,}\s+(?:|➜|→|=>)\s+(.*)$")
HISTORY_DIRECTORY_LINE_PATTERN = re.compile(r"^(\d+):\s+(\S+)\s+(.*)$")
HISTORY_STATS_LINE_PATTERN = re.compile(r"^\d+:\s+(.+?)\.{2,}\s+(\d+)\s+\|")
DISK_USAGE_LINE_PATTERN = re.compile(
    r"^\s*\d+:\s+(.+?)\.{2,}\s+([0-9.]+[A-Za-z]*)\s+\|"
)
PROCESS_LIST_LINE_PATTERN = re.compile(
    r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(.+?)\s+(?:\S+\s+)?(active|inactive|ghost) process$",
    re.IGNORECASE,
)
TOP_PROCESS_SORT_KEYS = {
    "CPU": {"darwin": "cpu", "linux": "%CPU", "field": "CPU"},
    "MEM": {"darwin": "mem", "linux": "%MEM", "field": "MEM"},
}
TOOL_LINE_PATTERN = re.compile(
    r"^\[(.*?)\]\s+Checking:\s+(.+?)\s+\.{2,}\s+(\S+)\s+(INSTALLED|NOT FOUND|ALIASED|FUNCTION)(?:\s+=>\s+(.*))?$"
)
SHOPT_LINE_PATTERN = re.compile(r"^(?:(\S+)\s+)?(ON|OFF)\s+(.+)$")
SYSINFO_KEY_VALUE_PATTERN = re.compile(r"^\s*([A-Za-z0-9_. -]+?)\.{2,}\s*:\s*(.*)$")
SYSINFO_SECTION_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9 -]+):$")
LOG_TAILOR_RULES = (
    (re.compile(r"\[( *[-a-zA-Z0-9_ =]+ *)\]"), "thread"),
    (re.compile(r" [a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+ ?"), "fqdn"),
    (re.compile(r"INFO|OUT"), "info"),
    (re.compile(r"DEBUG|FINE|TRACE"), "debug"),
    (re.compile(r"WARN[ING]*"), "warn"),
    (re.compile(r"CRITICAL|SEV[ERE]*|FATAL|ERR[OR]*"), "error"),
    (
        re.compile(
            r"([0-9]{1,4}[-/]?){3}[T ]([0-9]{1,2}[-:]?){2,3}((\.[0-9]+([+-][0-9]{1,2}[-:][0-9]{1,2}|Z))|([,.][0-9]+))?"
        ),
        "date",
    ),
    (
        re.compile(
            r"(((https?|ftp|file):/)|(/?[a-zA-Z0-9]+))/[-A-Za-z0-9+&@#/%?=~_|!:,.;]*\.*[-A-Za-z0-9+&@#/%=~_|]"
        ),
        "uri",
    ),
)
COMMAND_COLUMNS = "10000"
BAR_CHART_HEIGHT = 420
BAR_CHART_HEIGHT_REDUCTION = 40
TABLE_HEIGHT_REDUCTION = 45
AI_MODEL_TABLE_KEY = "ai_model_table"
AI_MODEL_TABLE_RESET_COUNTER_KEY = "ai_model_table_reset_counter"
ALIAS_TABLE_KEY = "alias_vars_table"
ALIAS_TABLE_RESET_COUNTER_KEY = "alias_vars_table_reset_counter"
ALIAS_VALUE_EDITOR_KEY_PREFIX = "alias_selected_value"
HHS_SETTINGS_TABLE_KEY = "hhs_settings_table"
HHS_SETTINGS_TABLE_RESET_COUNTER_KEY = "hhs_settings_table_reset_counter"
MARKDOWN_TABLE_HEIGHT = 360
MARKDOWN_TABLE_MARK_COLUMN_WIDTH = 80
MARKDOWN_TABLE_LAYOUT_VERSION = 3
CMD_TABLE_KEY = "cmd_vars_table"
CMD_TABLE_RESET_COUNTER_KEY = "cmd_vars_table_reset_counter"
CMD_INDEX_COLUMN_WIDTH = 80
CMD_VALUE_EDITOR_KEY_PREFIX = "cmd_selected_value"
DIR_TABLE_KEY = "dir_vars_table"
DIR_TABLE_RESET_COUNTER_KEY = "dir_vars_table_reset_counter"
DIR_VALUE_EDITOR_KEY_PREFIX = "dir_selected_value"
ENV_TABLE_HEIGHT = 420
ENV_TABLE_KEY = "env_vars_table"
ENV_TABLE_RESET_COUNTER_KEY = "env_vars_table_reset_counter"
ENV_TABLE_WIDTH = "stretch"
AI_MODEL_ACTION_SCROLL_HELPER_HEIGHT = 0
ENV_VALUE_EDITOR_SCROLL_HELPER_HEIGHT = 0
ENV_VALUE_EDITOR_HEIGHT = 40
ENV_VALUE_EDITOR_KEY_PREFIX = "env_selected_value"
ENV_VALUE_OVERRIDES_KEY = "env_value_overrides"
DOCKER_CONTAINER_TABLE_KEY = "docker_container_table"
DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY = "docker_container_table_reset_counter"
DOCKER_IMAGE_TABLE_KEY = "docker_image_table"
DOCKER_IMAGE_TABLE_RESET_COUNTER_KEY = "docker_image_table_reset_counter"
HOME_TOOLS_TABLE_KEY = "home_tools_table"
HOME_TOOLS_TABLE_RESET_COUNTER_KEY = "home_tools_table_reset_counter"
HOME_SHOPTS_TABLE_KEY = "home_shopts_table"
HOME_SHOPTS_TABLE_RESET_COUNTER_KEY = "home_shopts_table_reset_counter"
HISTORY_COMMAND_TABLE_KEY = "history_command_vars_table"
HISTORY_COMMAND_TABLE_RESET_COUNTER_KEY = "history_command_vars_table_reset_counter"
HISTORY_COMMAND_VALUE_EDITOR_KEY_PREFIX = "history_command_selected_value"
HISTORY_INDEX_COLUMN_DIGIT_WIDTH = 9
HISTORY_INDEX_COLUMN_MIN_WIDTH = 36
HISTORY_INDEX_COLUMN_PADDING = 24
HISTORY_DIRECTORY_TYPE_COLUMN_WIDTH = HISTORY_INDEX_COLUMN_DIGIT_WIDTH * 3
HISTORY_DIRECTORY_TABLE_KEY = "history_directory_vars_table"
HISTORY_DIRECTORY_TABLE_RESET_COUNTER_KEY = "history_directory_vars_table_reset_counter"
HISTORY_DIRECTORY_VALUE_EDITOR_KEY_PREFIX = "history_directory_selected_value"
PATH_TABLE_HEIGHT = ENV_TABLE_HEIGHT
PATH_TABLE_KEY = "path_vars_table"
PATH_TABLE_RESET_COUNTER_KEY = "path_vars_table_reset_counter"
PATH_TYPE_COLUMN_WIDTH = 80
PATH_TABLE_WIDTH = ENV_TABLE_WIDTH
SERVICE_TABLE_KEY = "service_vars_table"
SERVICE_TABLE_RESET_COUNTER_KEY = "service_vars_table_reset_counter"
SERVICE_VALUE_EDITOR_KEY_PREFIX = "service_selected_value"
SSH_TUNNEL_TABLE_KEY = "ssh_tunnel_table"
TWO_OPTION_FILTER_COLUMNS = [0.75, 3.25]
THREE_OPTION_FILTER_COLUMNS = [1.1, 2.9]
FOUR_OPTION_FILTER_COLUMNS = [1.75, 2.25]
FIVE_OPTION_FILTER_COLUMNS = [2.75, 1.25]
PATH_FILTER_COLUMNS = [2.25, 1.75]
PROCESS_FILTER_COLUMNS = [2.65, 1.35]
DOCUMENT_VIEW_ACTIVE_KEY = "document_view_active"
DOCUMENT_PREVIOUS_VIEW_KEY = "document_previous_view"
DOCUMENT_SELECTED_KEY = "document_selected"
TERMINAL_CWD_KEY = "terminal_cwd"
TERMINAL_READY_STATUS_SHOWN_KEY = "terminal_ready_status_shown"
DOCUMENTS = {
    "README": ("README", "README.md"),
    "HANDBOOK": ("Handbook", "docs/handbook/handbook.md"),
}
FOOTER_OPEN_WORKING_DIR_QUERY_PARAM = "hhs_open_working_dir"
FOOTER_RUN_UPDATER_QUERY_PARAM = "hhs_run_updater_update"
FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM = "hhs_show_shell_version"
FOOTER_CLEAR_CACHE_QUERY_PARAM = "hhs_clear_cache"
FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM = "hhs_clear_application_cache"
FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM = "hhs_clear_application_states"
FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM = "hhs_clear_ai_history"
COMMAND_PRELOADER_CANCEL_QUERY_PARAM = "hhs_cancel_preloader"
SEARCH_OPEN_RESULT_QUERY_PARAM = "hhs_open_search_result"
PROCESS_RESOURCE_STATE_KEY = "_hhs_ui_process_resource_state"
FOOTER_STATUS_LOG_HANDLER_REGISTRY_KEY = "footer_status_log_handler"
FOOTER_STATUS_LOG_RECORDS_REGISTRY_KEY = "footer_status_log_records"
