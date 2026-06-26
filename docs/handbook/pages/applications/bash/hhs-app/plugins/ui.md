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

`__hhs ui help`

**Output**

```bash
usage: __hhs ui [options]

  HomeSetup Streamlit UI launcher v0.0.2.

    options:
      -h | --help                : Display this help message.
      -v | --version             : Display current plugin version.

    arguments:
      args                       : Optional arguments passed to Streamlit.

    examples:
      Launch HomeSetup UI:
        => __hhs ui
      Launch HomeSetup UI with Streamlit arguments:
        => HHS_STREAMLIT_UI_PORT=18502 __hhs ui

  Notes:
    - The HomeSetup Python virtual environment must be active.
    - The UI port is controlled by HHS_STREAMLIT_UI_PORT.
```

------

### "execute"

#### **Purpose**

Launch the HomeSetup Streamlit UI or open the existing server if the configured port is already accepting connections.
The launcher runs `bin/apps/py/hhs-ui/streamlit_ui.py` with `python3 -m streamlit`.

#### **Returns**

**0** if the UI is launched or opened; **non-zero** otherwise.

#### **Parameters**

- $1..$N _Optional_ : Extra arguments passed to Streamlit.

#### **Examples**

`__hhs ui`

**Output**

```bash
Starting HomeSetup UI on port 18501...
HomeSetup UI started with PID: 12345
HomeSetup UI is running at http://localhost:18501
```

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
`bin/apps/py/hhs-ui/.streamlit-ui-state`.
