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

## Ask

The Ask plug-in integrates the HomeSetup AskAI assistant. It requires the HomeSetup Python virtual environment (`__hhs_is_venv`)
and the AskAI package to be installed locally. HomeSetup AI integration.

### "help"

#### **Purpose**

Display the Ask plug-in usage banner and argument description. HomeSetup AI integration.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs ask help`

**Output**

```bash
usage: hhs ask <question> [options]

    _        _
   / \   ___| | __
  / _ \ / __| |/ /
 / ___ \__ \   <
/_/   \_\___/_|\_\...Ollama-AI

  Offline ollama-AI agent integration for HomeSetup.

    options:
      -h | --help                      : Show this help message and exit.
      -v | --version                   : Show version and exit.
      -c | --context                   : Show current Ollama context (history) and exit.
      -i | --ingest [file]             : Set Ollama context from a text-based file and exit.
      -r | --reset                     : Reset history before executing (fresh new session) and exit.
      -m | --models                    : List available Ollama models and exit.
      -s | --select-model [model_name] : Select the Ollama model to use.
      -k | --keep                      : Keep the response file after execution.

    arguments:
      question                         : The prompt to ask Ollama.
```

### "version"

#### **Purpose**

Print the installed Ask plug-in version.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs ask version`

### "execute"

#### **Purpose**

Forward the provided question to the AskAI engine using Retrieval Augmented Generation (`python3 -m askai -r rag`).

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

- $1..$N _Required_ : The natural-language question about HomeSetup (options beginning with `-` are treated as flags and stripped
  before being sent to AskAI).

#### **Examples**

`__hhs ask execute How can I use starship?`

**Output**

```bash
  Taius: You can use Starship by executing commands in your terminal. Here are some examples:

 1 To set a specific preset for your Starship prompt:

    __hhs starship execute preset 'no-nerd-font'

   This changes your Starship prompt to the "no-nerd-font" preset.
 2 To view help information about Starship commands:

    __hhs starship help

   This will display usage information and available commands.
 3 To edit your Starship configuration file:

    __hhs starship edit

 4 To restore HomeSetup defaults:

    __hhs starship restore


For more detailed information, you can refer to the HomeSetup Developer Handbook, specifically the section on Starship. You can
also visit the Starship website at [starship.rs]( https://starship.rs/).
```

#### **Notes**

- The Ask plug-in is available only when the HomeSetup Python virtual environment is active.
- If AskAI is not installed locally, the command exits with an error directing you to `${HHS_ASKAI_URL}` for installation instructions.
