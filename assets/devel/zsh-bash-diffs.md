# Bash vs Zsh — Scripting Cheatsheet

## General
| Feature            | Bash           | Zsh           |
|--------------------|----------------|---------------|
| Default shell      | Linux standard | macOS default |
| Script portability | High           | Medium        |
| POSIX compliance   | Partial        | Partial       |

---

## Syntax
| Topic        | Bash           | Zsh            |
|--------------|----------------|----------------|
| Comments     | `#`            | `#`            |
| Functions    | `f() { ...; }` | `f() { ...; }` |
| Conditionals | `if [[ ... ]]` | `if [[ ... ]]` |

---

## Arrays
| Feature     | Bash          | Zsh           |
|-------------|---------------|---------------|
| Index start | 0             | 1             |
| Declare     | `arr=(a b c)` | `arr=(a b c)` |
| Access      | `${arr[0]}`   | `$arr[1]`     |

---

## Associative Arrays
| Feature | Bash             | Zsh              |
|---------|------------------|------------------|
| Enable  | `declare -A map` | `typeset -A map` |
| Native  | No (4+)          | Yes              |

---

## Globbing
| Feature           | Bash                      | Zsh                    |
|-------------------|---------------------------|------------------------|
| Recursive `**`    | Needs `shopt -s globstar` | Native                 |
| Extended glob     | Limited                   | `setopt extended_glob` |
| No-match behavior | Empty                     | Error (default)        |

---

## Options
| Feature | Bash       | Zsh                   |
|---------|------------|-----------------------|
| Toggle  | `shopt -s` | `setopt` / `unsetopt` |
| Scope   | Limited    | Extensive             |

---

## Parameter Expansion
| Feature       | Bash       | Zsh    |
|---------------|------------|--------|
| Remove suffix | `${f%/*}`  | `$f:h` |
| Filename      | `${f##*/}` | `$f:t` |
| Extension     | `${f##*.}` | `$f:e` |

---

## Completion
| Feature      | Bash              | Zsh        |
|--------------|-------------------|------------|
| Built-in     | Basic             | Advanced   |
| Setup        | `bash-completion` | `compinit` |
| Custom rules | Hard              | Native     |

---

## Prompt
| Feature      | Bash       | Zsh        |
|--------------|------------|------------|
| Prompt var   | `PS1`      | `PROMPT`   |
| Right prompt | No         | `RPROMPT`  |
| Tokens       | `\u \h \w` | `%n %m %~` |

---

## History
| Feature        | Bash | Zsh |
|----------------|------|-----|
| Append live    | No   | Yes |
| Share sessions | No   | Yes |
| Rich metadata  | No   | Yes |

---

## Arithmetic
| Feature        | Bash    | Zsh      |
|----------------|---------|----------|
| `$(( ))`       | Yes     | Yes      |
| Floating point | No      | Yes      |
| Math functions | Limited | Built-in |

---

## Autoloading
| Feature           | Bash | Zsh             |
|-------------------|------|-----------------|
| Function autoload | No   | `autoload func` |

---

## Script Compatibility
- Bash scripts usually run in Zsh:
  ```sh
  emulate bash -c "./script.sh"
  ```
- Zsh-only features break in Bash.

## Recommendation
- **Portable scripting**: Bash
- **Interactive / power scripting**: Zsh
