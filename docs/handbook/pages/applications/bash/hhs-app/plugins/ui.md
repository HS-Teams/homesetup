<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup Developer Handbook
>
> Applications handbook

## Table of contents

<!-- toc -->

- [Bash Applications](../../../../applications.md)
  - [Check-IP](../../check-ip.md#check-ip)
  - [Fetch](../../fetch.md#fetch)
  - [HHS-App](../../hhs-app.md#homesetup-application)
    - [Functions](../../hhs-app.md#functions)
      - [Built-Ins](../functions/built-ins.md)
      - [Misc](../functions/misc.md)
      - [Tests](../functions/tests.md)
      - [Web](../functions/web.md)
    - [Plugins](../../hhs-app.md#plug-ins)
      - [Ask](ask.md)
      - [Firebase](firebase.md)
      - [HSPM](hspm.md)
      - [Services](services.md)
      - [Settings](settings.md)
      - [Setup](setup.md)
      - [Starship](starship.md)
      - [Taius](taius.md)
      - [UI](ui.md)
      - [Updater](updater.md)

<!-- tocstop -->

## UI

### "help"

#### **Purpose**

Display the HomeSetup Streamlit UI launcher help.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs execute ui help`

**Output**

```bash
usage: __hhs execute ui [command] [options]

  HomeSetup Streamlit UI launcher v0.0.3.

    commands:
      start                      : Start the UI if it is not already running.
      status                     : Show whether the UI is running.
      stop                       : Stop the running UI process.
      restart                    : Stop and start the UI.

    options:
      -h | --help                : Display this help message.
      -v | --version             : Display current plugin version.

    arguments:
      args                       : Optional arguments passed to Streamlit start/restart.

    examples:
      Open HomeSetup UI, starting it first if needed:
        => __hhs execute ui
      Start HomeSetup UI without restarting an existing process:
        => __hhs execute ui start
      Restart HomeSetup UI:
        => __hhs execute ui restart
      Show HomeSetup UI status:
        => __hhs execute ui status
      Launch HomeSetup UI on another port:
        => HHS_STREAMLIT_UI_PORT=18502 __hhs execute ui

  Notes:
    - The HomeSetup Python virtual environment must be active.
    - The UI port is controlled by HHS_STREAMLIT_UI_PORT.
```

------

### "execute"

#### **Purpose**

Open the HomeSetup Streamlit UI, starting it first if the configured port is not already accepting connections.
The launcher runs `bin/apps/py/hhs_ui/streamlit_ui.py` with `python3 -m streamlit`.

#### **Returns**

**0** if the UI is started or opened; **non-zero** otherwise.

#### **Parameters**

- $1..$N _Optional_ : Extra arguments passed to Streamlit.

#### **Examples**

`__hhs execute ui`

**Output**

```bash
Starting HomeSetup UI on port 18501...
HomeSetup UI started with PID: 12345
HomeSetup UI is running at http://localhost:18501
```

------

### "start"

#### **Purpose**

Start the HomeSetup Streamlit UI if it is not already running. This command does not restart an existing process.

#### **Examples**

`__hhs execute ui start`

------

### "status"

#### **Purpose**

Show whether the HomeSetup Streamlit UI is running on the configured port.

#### **Examples**

`__hhs execute ui status`

------

### "stop"

#### **Purpose**

Stop the running HomeSetup Streamlit UI process.

#### **Examples**

`__hhs execute ui stop`

------

### "restart"

#### **Purpose**

Stop and start the HomeSetup Streamlit UI. Use this command when a running UI must be refreshed.

#### **Examples**

`__hhs execute ui restart`

------

## Streamlit UI

The Streamlit interface has Home, Configurations, Services, and History views. The Home view includes `System` and
`Tools` panels. `System` displays `__hhs_sysinfo` as Markdown, while `Tools` displays parsed `__hhs_tools` output. The
sidebar can open `README.md` or `docs/handbook/handbook.md` in the main panel.

The Configurations view uses segmented tabs:

| Tab | Source command | Behavior |
|-----|----------------|----------|
| ENV | `__hhs_envs` | Editable environment variable values. |
| PATH | `__hhs_paths` | Editable `PATH` entries with type glyphs and source labels. |
| DIR | `__hhs_load_dir -l` | Read-only saved directory list. |
| CMD | `__hhs_command -l` | Read-only saved command list. |
| ALIAS | `__hhs_aliases -l` | Read-only alias list. |

The Services view uses `__hhs services execute` to render a service status list with `All`, `Started`, `Stopped`, and
`Other` filters.

The History view uses segmented tabs:

| Tab | Source command | Behavior |
|-----|----------------|----------|
| COMMANDS | `__hhs_history` | Read-only shell command history list. |
| DIRECTORIES | `__hhs_dirs -l` | Read-only remembered directory list. |
| STATS | `__hhs_hist_stats <top_n>` | Bar chart of the most used commands in shell history. |

Both History tabs provide `All` and `Others` filters. Selecting `Others` enables a text input that filters table rows.

The UI uses the bundled Droid Sans Mono Nerd Font and a Dracula-based Streamlit theme so glyphs from the shell output
render consistently in tables and status fields.

Selection state, active tabs, filters, and editable ENV/PATH overrides are restored from
`bin/apps/py/hhs_ui/.streamlit-ui-state`.
