"""Static identifiers and display definitions for the HomeSetup Streamlit UI."""

from __future__ import annotations

HHS_PATHS_RAW_ENTRY_MARKER = "__HHS_UI_PATH_ENTRY__"
HHS_HSPM_ENV_OUTPUT_MARKER = "__HHS_HSPM_ENV__"
HHS_HSPM_CATALOG_CACHE_TAG = "hhs_hspm_catalog_recipes_v2"
FOOTER_VERSION_CACHE_TAG = "footer_version"
FOOTER_VERSION_OUTPUT_MARKER = "__HHS_UI_VERSION__"
SHOPT_DESCRIPTIONS = {
    "assoc_expand_once": "Suppresses repeated evaluation of associative array subscripts.",
    "autocd": "Runs a directory name as if it were the argument to cd.",
    "cdable_vars": "Treats a non-directory cd argument as a variable containing the target directory.",
    "cdspell": "Corrects minor spelling errors in directory names used with cd.",
    "checkhash": "Verifies hashed commands still exist before executing them.",
    "checkjobs": "Checks for stopped and running jobs before an interactive shell exits.",
    "checkwinsize": "Updates LINES and COLUMNS after each command when the terminal size changes.",
    "cmdhist": "Stores all lines of a multi-line command in one history entry.",
    "compat31": "Uses Bash 3.1 compatibility for quoted =~ conditional arguments.",
    "compat32": "Uses Bash 3.2 compatibility for conditional and locale-specific behavior.",
    "compat40": "Uses Bash 4.0 compatibility for conditional and locale-specific behavior.",
    "compat41": "Uses Bash 4.1 compatibility for conditional and POSIX mode behavior.",
    "compat42": "Uses Bash 4.2 compatibility for pattern replacement quote handling.",
    "compat43": "Uses Bash 4.3 compatibility for word expansion and loop state behavior.",
    "compat44": "Uses Bash 4.4 compatibility for expansion and unset behavior.",
    "complete_fullquote": "Quotes all shell metacharacters in completion results.",
    "direxpand": "Expands directory names during completion.",
    "dirspell": "Corrects directory name spelling during completion.",
    "dotglob": "Includes filenames beginning with a dot in pathname expansion.",
    "execfail": "Prevents a non-interactive shell from exiting when exec cannot run its target.",
    "expand_aliases": "Expands aliases before command execution.",
    "extdebug": "Enables debugger-oriented shell behavior and tracing.",
    "extglob": "Enables extended pathname pattern matching operators.",
    "extquote": "Enables ANSI-C and locale-specific quoting inside parameter expansions.",
    "failglob": "Makes non-matching pathname patterns raise an expansion error.",
    "force_fignore": "Applies FIGNORE suffixes even when they are the only completion matches.",
    "globasciiranges": "Uses ASCII ordering for bracket expression ranges in pattern matching.",
    "globstar": "Makes ** recursively match files and directories during pathname expansion.",
    "gnu_errfmt": "Formats shell error messages in GNU style.",
    "histappend": "Appends history to HISTFILE instead of overwriting it on shell exit.",
    "histreedit": "Lets readline re-edit a failed history substitution.",
    "histverify": "Loads history substitutions into readline before execution for review.",
    "hostcomplete": "Completes hostnames when a word containing @ is completed.",
    "huponexit": "Sends SIGHUP to jobs when an interactive login shell exits.",
    "inherit_errexit": "Preserves errexit in command substitutions.",
    "interactive_comments": "Allows # to begin comments in interactive shells.",
    "lastpipe": "Runs the last foreground pipeline command in the current shell when possible.",
    "lithist": "Stores multi-line history entries with embedded newlines when cmdhist is enabled.",
    "localvar_inherit": "Lets local variables inherit prior visible values and attributes.",
    "localvar_unset": "Makes unset local variables hide same-named outer variables.",
    "login_shell": "Indicates that the shell was started as a login shell.",
    "mailwarn": "Warns when a checked mail file has been read since the last check.",
    "no_empty_cmd_completion": "Skips PATH completion attempts on an empty command line.",
    "nocaseglob": "Matches filenames case-insensitively during pathname expansion.",
    "nocasematch": "Matches case and [[ patterns case-insensitively.",
    "noexpand_translation": "Prevents translated strings from being single-quoted.",
    "nullglob": "Expands non-matching pathname patterns to nothing.",
    "progcomp": "Enables programmable completion.",
    "progcomp_alias": "Tries programmable completion through an alias target.",
    "promptvars": "Expands variables and command substitutions in prompt strings.",
    "restricted_shell": "Indicates that the shell is running in restricted mode.",
    "shift_verbose": "Reports an error when shift exceeds the number of positional parameters.",
    "sourcepath": "Uses PATH to find files passed to source or dot.",
    "varredir_close": "Automatically closes file descriptors opened with varredir redirections.",
    "xpg_echo": "Makes echo expand backslash escape sequences by default.",
}
HOME_TOOL_ACTION_JOB = "home_tool_action"
HOME_TOOL_TLDR_JOB = "home_tool_tldr"
CONFIG_ACTION_JOB = "config_action"
HHS_SETUP_ACTION_JOB = "hhs_setup_action"
HHS_RESET_ACTION_JOB = "hhs_reset_action"
HHS_SETTINGS_ACTION_JOB = "hhs_settings_action"
HHS_STARSHIP_ACTION_JOB = "hhs_starship_action"
HHS_FIREBASE_ACTION_JOB = "hhs_firebase_action"
HHS_HSPM_ACTION_JOB = "hhs_hspm_action"
DOCKER_ACTION_JOB = "docker_action"
ALIAS_LIST_JOB = "alias_list"
SERVICE_LIST_JOB = "service_list"
SERVICE_ACTION_JOB = "service_action"
MONITOR_CPU_JOB = "monitor_cpu"
MONITOR_MEM_JOB = "monitor_mem"
MONITOR_PROCESS_LIST_JOB = "monitor_process_list"
MONITOR_PROCESS_ACTION_JOB = "monitor_process_action"
AI_CONTEXT_ACTION_JOB = "ai_context_action"
AI_PROMPT_ACTION_JOB = "ai_prompt_action"
AI_MODEL_SELECT_JOB = "ai_model_select"
AI_MODEL_DELETE_JOB = "ai_model_delete"
UPDATER_UPDATE_JOB = "updater_update"
UPDATER_CHECK_JOB = "updater_check"
AI_ASK_JOB = "ai_ask"
TERMINAL_AI_DEFAULT_PROMPT = "Explain me this"
FOOTER_VERSION_JOB = "footer_hhs_version"
FOOTER_WORKING_DIR_JOB = "footer_working_dir"
SSH_CONNECT_JOB = "ssh_connect"
SSH_DISCONNECT_JOB = "ssh_disconnect"
SSH_FILE_TRANSFER_JOB = "ssh_file_transfer"
SSH_EXPLORER_ACTION_JOB = "ssh_explorer_action"
SSH_EXPLORER_DELETE_JOB = "ssh_explorer_delete"
SEARCH_COMMAND_JOB = "search_command"
SEARCH_OPEN_JOB = "search_open"
PATH_PICKER_LISTING_JOB_PREFIX = "path_picker_listing"
BACKGROUND_JOB_STATE_KEY_PREFIX = "_hhs_background_job_"
PATH_PICKER_LISTING_LOADER_MESSAGE = "Loading directories and files..."
HHS_SETUP_SETTINGS = (
    "hhs_set_locales",
    "hhs_export_settings",
    "hhs_restore_last_dir",
    "hhs_load_shell_options",
    "homebrew_no_auto_update",
    "hhs_no_auto_update",
    "hhs_load_completions",
    "hhs_load_key_bindings",
    "hhs_python_venv_enabled",
    "hhs_use_starship",
    "hhs_use_blesh",
    "hhs_use_atuin",
    "hhs_verbose_logs",
    "hhs_ollama_ai_autostart",
)
HHS_FIREBASE_FIELDS = (
    (
        "UID",
        "UID",
        "hhs.firebase.user.uid",
        "hhs_firebase_uid",
        "Firebase auth UID",
    ),
    (
        "PROJECT_ID",
        "PROJECT_ID",
        "hhs.firebase.project.id",
        "hhs_firebase_project_id",
        "Firebase project ID",
    ),
    (
        "EMAIL",
        "EMAIL",
        "hhs.firebase.username",
        "hhs_firebase_email",
        "Firebase account email",
    ),
    (
        "DATABASE",
        "DATABASE",
        "hhs.firebase.database",
        "hhs_firebase_database",
        "Realtime database name",
    ),
)
STARSHIP_CACHE_OUTPUT_MARKER = "__HHS_STARSHIP_CACHE__"
STARSHIP_CONFIG_OUTPUT_MARKER = "__HHS_STARSHIP_CONFIG__"
STARSHIP_HHS_DIR_OUTPUT_MARKER = "__HHS_STARSHIP_HHS_DIR__"
STARSHIP_PRESETS_OUTPUT_MARKER = "__HHS_STARSHIP_PRESETS__"
STARSHIP_CONFIG_CONTENT_OUTPUT_MARKER = "__HHS_STARSHIP_CONFIG_CONTENT__"
STARSHIP_END_OUTPUT_MARKER = "__HHS_STARSHIP_END__"
HHS_CONFIG_ENV_OUTPUT_MARKER = "__HHS_CONFIG_ENV__"
FIREBASE_CONFIG_FILE_OUTPUT_MARKER = "__HHS_FIREBASE_CONFIG_FILE__"
FIREBASE_CONFIG_CONTENT_OUTPUT_MARKER = "__HHS_FIREBASE_CONFIG_CONTENT__"
FIREBASE_CONFIG_END_OUTPUT_MARKER = "__HHS_FIREBASE_END__"
COMMAND_PRELOADER_BUS = "hhs-ui-command-preloader"
COMMAND_PRELOADER_START_EVENT = "command:start"
COMMAND_PRELOADER_FINISH_EVENT = "command:finish"
COMMAND_PRELOADER_EVENT_QUEUE_KEY = "_hhs_command_preloader_events"
COMMAND_PRELOADER_SUBSCRIBER_MARKER = "_hhs_command_preloader_subscriber"
COMMAND_PRELOADER_EVENT_BUS_REGISTRY_KEY = "command_preloader_event_bus"
HOST_SWITCH_VIEW_STATE_KEY = "_hhs_host_switch_view_state"
HOST_SWITCH_CACHE_TAGS = (
    FOOTER_VERSION_CACHE_TAG,
    "env",
    "services",
    "monitor_disk",
    "monitor_process",
    "ssh_files",
)
HOST_SWITCH_BACKGROUND_JOBS = (
    SSH_CONNECT_JOB,
    SSH_DISCONNECT_JOB,
    SSH_FILE_TRANSFER_JOB,
    SSH_EXPLORER_ACTION_JOB,
    SSH_EXPLORER_DELETE_JOB,
    SEARCH_COMMAND_JOB,
    SEARCH_OPEN_JOB,
    CONFIG_ACTION_JOB,
    HHS_FIREBASE_ACTION_JOB,
    DOCKER_ACTION_JOB,
    FOOTER_VERSION_JOB,
    HOME_TOOL_ACTION_JOB,
    HOME_TOOL_TLDR_JOB,
    SERVICE_LIST_JOB,
    SERVICE_ACTION_JOB,
    MONITOR_CPU_JOB,
    MONITOR_MEM_JOB,
    MONITOR_PROCESS_LIST_JOB,
    MONITOR_PROCESS_ACTION_JOB,
    AI_CONTEXT_ACTION_JOB,
    AI_PROMPT_ACTION_JOB,
)
CACHE_CLEAR_BACKGROUND_JOBS = (
    SSH_CONNECT_JOB,
    SSH_DISCONNECT_JOB,
    SSH_FILE_TRANSFER_JOB,
    SSH_EXPLORER_ACTION_JOB,
    SSH_EXPLORER_DELETE_JOB,
    SEARCH_COMMAND_JOB,
    SEARCH_OPEN_JOB,
    CONFIG_ACTION_JOB,
    HHS_FIREBASE_ACTION_JOB,
    DOCKER_ACTION_JOB,
    FOOTER_VERSION_JOB,
    HOME_TOOL_ACTION_JOB,
    HOME_TOOL_TLDR_JOB,
    ALIAS_LIST_JOB,
    SERVICE_LIST_JOB,
    SERVICE_ACTION_JOB,
    MONITOR_CPU_JOB,
    MONITOR_MEM_JOB,
    MONITOR_PROCESS_LIST_JOB,
    MONITOR_PROCESS_ACTION_JOB,
    AI_CONTEXT_ACTION_JOB,
    AI_PROMPT_ACTION_JOB,
)
HOST_SWITCH_STATE_KEYS = (
    "monitor_cpu_error",
    "monitor_mem_error",
    "monitor_process_action_message",
    "monitor_process_action_succeeded",
    "monitor_process_list_error",
    "service_list_error",
)

__all__ = tuple(name for name in globals() if name.isupper())
