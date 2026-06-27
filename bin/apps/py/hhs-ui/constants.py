"""Constants used by the HomeSetup Streamlit UI."""

from __future__ import annotations

import os
import re
from pathlib import Path

# NOTE: Follow SemVer for this script. Any UI behavior change must bump VERSION,
# at minimum by incrementing the patch number.
VERSION = "0.0.69"
DISPLAY_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
APP_DIR = Path(__file__).resolve().parent
APP_CSS_FILE = APP_DIR / "streamlit_ui.css"
APP_THEME_CSS_FILE = APP_DIR / "themes/dracula.css"
APP_FONT_FAMILY = "Droid Sans Mono for Powerline Nerd Font Complete"
APP_FONT_FILE = (
    APP_DIR / "assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
)
APP_AI_USER_AVATAR_FILE = APP_DIR / "assets/images/user.png"
APP_AI_OLLAMA_AVATAR_FILE = APP_DIR / "assets/images/ollama.png"
APP_AI_HOMESETUP_AVATAR_FILE = APP_DIR / "assets/images/homesetup.png"
APP_THEME_OPTIONS_BY_THEME = {
    "azurite": {
        "theme.base": "dark",
        "theme.primaryColor": "#2563eb",
        "theme.backgroundColor": "#0f172a",
        "theme.secondaryBackgroundColor": "#1e293b",
        "theme.textColor": "#f8fafc",
        "theme.linkColor": "#38bdf8",
        "theme.borderColor": "#94a3b8",
        "theme.dataframeBorderColor": "#94a3b8",
        "theme.dataframeHeaderBackgroundColor": "#1e293b",
        "theme.codeBackgroundColor": "#111827",
    },
    "dracula": {
        "theme.base": "dark",
        "theme.primaryColor": "#bd93f9",
        "theme.backgroundColor": "#282a36",
        "theme.secondaryBackgroundColor": "#44475a",
        "theme.textColor": "#f8f8f2",
        "theme.linkColor": "#8be9fd",
        "theme.borderColor": "#6272a4",
        "theme.dataframeBorderColor": "#6272a4",
        "theme.dataframeHeaderBackgroundColor": "#44475a",
        "theme.codeBackgroundColor": "#21222c",
    },
    "tokyo-night": {
        "theme.base": "dark",
        "theme.primaryColor": "#bb9af7",
        "theme.backgroundColor": "#1a1b26",
        "theme.secondaryBackgroundColor": "#24283b",
        "theme.textColor": "#c0caf5",
        "theme.linkColor": "#7dcfff",
        "theme.borderColor": "#565f89",
        "theme.dataframeBorderColor": "#565f89",
        "theme.dataframeHeaderBackgroundColor": "#24283b",
        "theme.codeBackgroundColor": "#16161e",
    },
}
APP_THEME_OPTIONS = APP_THEME_OPTIONS_BY_THEME["dracula"]
UI_STATE_FILE = Path(os.environ.get("HHS_DIR", APP_DIR)) / ".streamlit-ui-state"
UI_CACHE_FILE = Path(os.environ.get("HHS_CACHE_DIR", APP_DIR)) / ".streamlit-ui-cache"
UI_CACHE_REALTIME_TTL_SECONDS = 15
UI_CACHE_NORMAL_TTL_SECONDS = 60
UI_CACHE_LOW_CHANGE_TTL_SECONDS = 120
UI_CACHE_DEFAULT_TTL_SECONDS = UI_CACHE_NORMAL_TTL_SECONDS
APP_CSS = ""
VIEWS = ("Home", "Configs", "Services", "Monitor", "History")
AI_VIEW = "AI"
AI_VIEWS = ("CHAT", "SETTINGS")
HOME_VIEWS = ("System", "Tools")
CONFIG_VIEWS = ("ENV", "PATH", "DIR", "CMD", "ALIAS")
HISTORY_VIEWS = ("COMMANDS", "DIRECTORIES", "STATS")
MONITOR_VIEWS = ("DISK", "MEM", "CPU", "PROCESSES", "LOGS")
ENV_FILTERS = ("All", "HHS", "Other")
LIST_FILTERS = ("All", "Other")
HISTORY_FILTERS = ("All", "Others")
PATH_FILTERS = ("All", "Shell", "Private", "Custom", "Other")
SERVICE_FILTERS = ("All", "Started", "Stopped", "Other")
THEME_SELECTED_KEY = "theme_selected"
AI_CODE_BLOCK_WRAP_COLUMNS = 96
PROCESS_TABLE_KEY = "monitor_process_table"
PERSISTED_UI_KEYS = (
    "active_view",
    "ai_chat_messages",
    "ai_clear_chat_execute_pending",
    "ai_model_delete_execute_pending",
    "ai_model_select_execute_pending",
    "ai_view",
    "alias_filter",
    "alias_other_filter",
    "cmds_filter",
    "cmds_other_filter",
    "config_view",
    "dirs_filter",
    "dirs_other_filter",
    "env_filter",
    "env_other_filter",
    "env_value_overrides",
    "home_view",
    "history_commands_filter",
    "history_commands_other_filter",
    "history_directories_filter",
    "history_directories_other_filter",
    "history_stats_top_n",
    "history_view",
    "monitor_disk_directory",
    "monitor_disk_top_n",
    "monitor_log_file",
    "monitor_logs_tail",
    "monitor_process_filter",
    "monitor_view",
    "path_filter",
    "path_other_filter",
    "path_value_overrides",
    "service_filter",
    "service_other_filter",
    "theme_selected",
)
PERSISTED_UI_KEY_PREFIXES = (
    "alias_selected_value_",
    "cmd_selected_value_",
    "dir_selected_value_",
    "env_selected_value_",
    "history_command_selected_value_",
    "history_directory_selected_value_",
    "path_selected_value_",
    "service_selected_value_",
)
ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
)
ALIAS_LINE_PATTERN = re.compile(r"^(.+?)\.{2,}\s+(?:|=>)\s+'?(.*?)'?$")
COMMAND_LINE_PATTERN = re.compile(
    r"^\((\d+)\)\s+(.+?)\.{2,}\s+(?:|=>)\s+'?(.*?)'?(?:\.\.\.)?$"
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
    r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(.+?)\s+(?:[✓✔]\s+)?active process$", re.IGNORECASE
)
TOP_PROCESS_SORT_KEYS = {
    "CPU": {"darwin": "cpu", "linux": "%CPU", "field": "CPU"},
    "MEM": {"darwin": "mem", "linux": "%MEM", "field": "MEM"},
}
TOOL_LINE_PATTERN = re.compile(
    r"^\[(.*?)\]\s+Checking:\s+(.+?)\s+\.{2,}\s+(\S+)\s+(INSTALLED|NOT FOUND|ALIASED|FUNCTION)(?:\s+=>\s+(.*))?$"
)
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
CMD_TABLE_KEY = "cmd_vars_table"
CMD_TABLE_RESET_COUNTER_KEY = "cmd_vars_table_reset_counter"
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
HISTORY_COMMAND_TABLE_KEY = "history_command_vars_table"
HISTORY_COMMAND_TABLE_RESET_COUNTER_KEY = "history_command_vars_table_reset_counter"
HISTORY_COMMAND_VALUE_EDITOR_KEY_PREFIX = "history_command_selected_value"
HISTORY_DIRECTORY_TABLE_KEY = "history_directory_vars_table"
HISTORY_DIRECTORY_TABLE_RESET_COUNTER_KEY = "history_directory_vars_table_reset_counter"
HISTORY_DIRECTORY_VALUE_EDITOR_KEY_PREFIX = "history_directory_selected_value"
PATH_TABLE_HEIGHT = ENV_TABLE_HEIGHT
PATH_TABLE_KEY = "path_vars_table"
PATH_TABLE_RESET_COUNTER_KEY = "path_vars_table_reset_counter"
PATH_TABLE_WIDTH = ENV_TABLE_WIDTH
PATH_VALUE_EDITOR_HEIGHT = ENV_VALUE_EDITOR_HEIGHT
PATH_VALUE_EDITOR_KEY_PREFIX = "path_selected_value"
PATH_VALUE_OVERRIDES_KEY = "path_value_overrides"
SERVICE_TABLE_KEY = "service_vars_table"
SERVICE_TABLE_RESET_COUNTER_KEY = "service_vars_table_reset_counter"
SERVICE_VALUE_EDITOR_KEY_PREFIX = "service_selected_value"
TWO_OPTION_FILTER_COLUMNS = [0.75, 3.25]
THREE_OPTION_FILTER_COLUMNS = [1.1, 2.9]
FOUR_OPTION_FILTER_COLUMNS = [1.75, 2.25]
PATH_FILTER_COLUMNS = [2.25, 1.75]
DOCUMENT_VIEW_ACTIVE_KEY = "document_view_active"
DOCUMENT_PREVIOUS_VIEW_KEY = "document_previous_view"
DOCUMENT_SELECTED_KEY = "document_selected"
DOCUMENTS = {
    "README": ("README", "README.md"),
    "HANDBOOK": ("Handbook", "docs/handbook/handbook.md"),
}
