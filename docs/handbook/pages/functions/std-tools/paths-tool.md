<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup Developer Handbook
>
> Standard-Tools

## Table of contents

<!-- toc -->

- [Standard Tools](../../functions.md#standard-tools)
  - [Aliases Related](aliases-related.md#aliases-related-functions)
  - [Built-ins](built-ins.md#built-ins-functions)
  - [CLI Terminal Tools](clitt.md#cli-terminal-tools)
  - [Command Tool](command-tool.md#command-tool)
  - [Directory Related](directory-related.md#directory-related-functions)
  - [File Related](file-related.md#file-related-functions)
  - [Network Related](network-related.md#network-related-functions)
  - [Paths Tool](paths-tool.md#paths-tool)
  - [Profile Related](profile-related.md#profile-related-functions)
  - [Search Related](search-related.md#search-related-functions)
  - [Security Related](security-related.md#security-related-functions)
  - [Shell Utilities](shell-utilities.md#shell-utilities)
  - [System Utilities](system-utilities.md#system-utilities)
  - [Taylor Tool](taylor-tool.md#taylor-tool)
  - [Text Utilities](text-utilities.md#text-utilities)
  - [TOML Utilities](toml-utilities.md#toml-utilities)
  - [Toolchecks](toolchecks.md#tool-checks-functions)
- [Development Tools](../../functions.md#development-tools)
  - [Gradle](../dev-tools/gradle-tools.md#gradle-functions)
  - [Docker](../dev-tools/docker-tools.md#docker-functions)
  - [Git](../dev-tools/git-tools.md#git-functions)

<!-- tocstop -->


### Paths tool

#### __hhs_paths

```bash
usage: __hhs_paths [options] <args>

    Options:
      -a <path> : Add to the current <path> to PATH.
      -r <path> : Remove from the current <path> from PATH.
      -e        : Edit current HHS_PATHS_FILE.
      -c        : Attempt to clear non-existing paths. System paths are not affected.
      -q        : Quiet mode on.

  Notes:
    - When no arguments are provided it will list all PATH payload.
```

##### **Purpose**

Manage your custom PATH entries.

##### **Returns**

**0** on success; **non-zero** otherwise.

##### **Parameters**

  - $1 _Conditional_     : The path to be added or removed.

##### **Examples**

`__hhs_paths`

**Output**

```bash
Listing all PATH entries:

/usr/local/opt/ruby/bin...............................................  => Custom paths
/usr/local/bin........................................................  => Shell export
/System/Cryptexes/App/usr/bin.........................................  => Shell export
/usr/bin..............................................................  => Shell export
/bin..................................................................  => Shell export
/usr/sbin.............................................................  => Shell export
/sbin.................................................................  => Shell export
/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/lo....  => Shell export
/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bi....  => Shell export
/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/ap....  => Shell export
/Users/hjunior/.local/bin.............................................  => Shell export
/Users/hjunior/.config/hhs/bin........................................  => Shell export
/Users/hjunior/HomeSetup/tests/bats/bats-core/bin.....................  => Shell export
```

The listing uses a leading glyph to identify the path type: a folder for directories, a symlink glyph for links, and a
question glyph for missing entries. The source label is one of `Shell export`, `Custom path`, `Private system path`, or
`General system path`.

`__hhs_paths -a /tmp`

**Output**

```bash
Path was added: "/tmp"
```

`__hhs_paths -r /tmp`

**Output**

```bash
Path was removed: "/tmp"
```
