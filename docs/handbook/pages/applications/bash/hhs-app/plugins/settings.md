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
      - [Settings](settings.md)
      - [Setup](setup.md)
      - [Starship](starship.md)
      - [Updater](updater.md)

<!-- tocstop -->

## Settings

The Settings plug-in exposes the `hspylib-settings` command-line tooling. It requires the HomeSetup Python virtual environment and
the `settings`/`setman` packages to be installed.

### "help"

#### **Purpose**

Display the upstream `python3 -m settings -h` usage screen.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs settings help`

### "version"

#### **Purpose**

Print the Settings plug-in version reported by `python3 -m settings -v`.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs settings version`

### "execute"

#### **Purpose**

Run the Settings manager operations. Execution is delegated to the Python modules provided by HomeSetup.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

- `$1` _Optional_ : When omitted, the command shows the `python3 -m setman -h` help output.
- `source` task : Exports selected settings to a file or `.envrc` for `direnv` consumption.
  - `-f <file>` _Optional_ : Override the output file name. Defaults to `settings-export-<timestamp>`.
  - `-n <namespace>` _Optional_ : Restrict the exported namespace.
  - Remaining arguments are interpreted as `KEY VALUE` pairs.
- Any other arguments : Passed verbatim to `python3 -m setman` for normal operation.

#### **Examples**

```bash
__hhs settings execute              # display setman usage
__hhs settings execute list         # list configured settings
__hhs settings execute source -f .envrc HSPM_TOKEN abcd1234
```

#### **Notes**

- The plug-in exits with an error if the HomeSetup Python virtual environment is not active.
- When using the `source` task, duplicate entries are removed and the tool reports how many settings were exported.
