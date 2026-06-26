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

## HSPM

### "help"

#### **Purpose**

Display HHS-HSPM help message.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs hspm help`

**Output**

```bash
usage: hspm [option] {install,uninstall,list,recover}

 _   _ ____  ____  __  __
| | | / ___||  _ \|  \/  |
| |_| \___ \| |_) | |\/| |
|  _  |___) |  __/| |  | |
|_| |_|____/|_|   |_|  |_|

  HomeSetup package manager

    options:
      -v  |   --version     : Display current program version.
      -h  |      --help     : Display this help message.

    arguments:
      list                  : List all available, OS based, installation recipes.
      install   <package>   : Install packages using a matching installation recipe.
      uninstall <package>   : Uninstall the package using a matching uninstallation recipe.
      recover [-i,-t,-e]    : Install or list all packages previously installed by hspm. If -i is provided, then hspm
                              will attempt to install all packages, otherwise the list is displayed. If -t is provided
                              hspm will check ${HHS_DEV_TOOLS} instead of previously installed packages. If -e is
                              provided, then the default editor will open the recovery file.
```

------

### "list"

#### **Purpose**

List all available, OS based, installation recipes.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

  - N/A

#### **Examples**

`__hhs hspm execute list`

**Output**

```bash
Listing all available hspm 'Darwin' packages ...

  0 - ant ................. => Our mission is to drive processes described in build files as targets and extension points dependent upon each other.
  1 - bats ................ => Bats is a TAP-compliant testing framework for Bash.
  2 + colima .............. => Container runtimes on macOS (and Linux) with minimal setup.
  3 - dialog .............. => Dialog allows creating text-based color dialog boxes from any shell script language.
  4 - direnv .............. => Shell extension that enabled loading and unloading of environment variables depending on the current directory.
  5 - docker .............. => Docker makes container capabilities approachable and easy to use.
  6 - doxygen ............. => Generate documentation from source code.
  7 - eslint .............. => Linter tool for identifying and reporting on patterns in JavaScript.
  8 - figlet .............. => FIGlet is a program for making large letters out of ordinary text.
  9 - go .................. => Go is an open source programming language that makes it easy to build simple, reliable, and efficient software.
 10 - gpg ................. => Compute SHA message digests.
 11 - gradle .............. => Gradle helps teams build, automate and deliver better software, faster.
 12 - groovy .............. => A multi-faceted language for the Java platform.
 13 - htop ................ => An interactive process viewer for Unix.
 14 - jenkins ............. => An open source automation server which enables developers to reliably build, test, and deploy their software.
 15 + jenv ................ => Is a command line tool to help you forget how to set the JAVA_HOME environment variable.
 16 - jq .................. => Jq is a lightweight and flexible command-line JSON processor.
 17 - mvn ................. => Maven is a software project management and comprehension tool.
 18 + node ................ => Node.js® is a JavaScript runtime built on Chromes V8 JavaScript engine.
 19 + nvm ................. => Simple bash script to manage multiple active node.js versions.
 20 - pbcopy .............. => Allows copying the output of a command right into your clipboard.
 21 - pcregrep ............ => Searches files for character patterns, but it uses the PCRE regular expression library.
 22 - perl ................ => Perl is a highly capable, feature-rich programming language with over 30 years of development.
 23 - pylint .............. => Pylint is a static code analyser for Python 2 or 3.
 24 - python .............. => Python is a programming language that lets you work quickly and integrate systems more effectively.
 25 + qt .................. => Qt | Cross-platform software development for embedded & desktop.
 26 + rvm ................. => Ruby environment (Version) Manager (RVM).
 27 - shellcheck .......... => Is an open source static analysis tool that automatically finds bugs in your shell scripts.
 28 - shfmt ............... => Auto-formatter for shellscript source code.
 29 - sqlite3 ............. => SQLite is a C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine.
 30 - svn ................. => Subversion is an open source version control system.
 31 - telnet .............. => Provide a bidirectional interactive text-oriented communication facility using a virtual terminal.
 32 - tree ................ => Tree is a recursive directory listing program that produces a depth-indented listing of files.
 33 - vim ................. => Vim is a highly configurable text editor for efficiently creating and changing any kind of text.
 34 + vue ................. => Vue is an approachable, performant and versatile framework for building web user interfaces.

Found (9) custom recipes.
Packages enlisted with '+' have a custom installation recipe
```

------

### "install"

#### **Purpose**

Install packages using a matching installation recipe.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

  - N/A

#### **Examples**

`__hhs hspm execute install figlet`

**Output**

```bash
Using [brew] default installation for "figlet"!
Installing "figlet", please wait ...
Installation successful => "figlet"
```

------

### "uninstall"

#### **Purpose**

Uninstall the package using a matching uninstallation recipe.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

  - N/A

#### **Examples**

`__hhs hspm execute uninstall figlet`

**Output**

```bash
Using [brew] default uninstallation recipe for "figlet"!
Uninstalling "figlet", please wait ...
Uninstallation successful => "figlet"
```

------

### "recover"

#### **Purpose**

Install or list all packages previously installed by hspm.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

  - N/A

#### **Examples**

`__hhs hspm execute recover`

**Output**

```bash
Listing recovered [Darwin/macOS] packages ...

  0 - figlet ........................ INSTALLED
  1 - eza ........................... INSTALLED
  2 - tree .......................... INSTALLED
...
...
```

`__hhs hspm execute recover -t -i`

**Output**

```bash
Listing development tools ...

  0 - base64 ........................ INSTALLED
  1 - brew .......................... INSTALLED
  2 - colima ........................ INSTALLED
  3 - direnv ........................ INSTALLED
  4 - docker ........................ INSTALLED
  5 - eslint ........................ INSTALLED
  6 - eza ........................... NOT INSTALLED
  7 - gcc ........................... INSTALLED
  8 - git ........................... INSTALLED
  9 - go ............................ NOT INSTALLED
...
...
```
