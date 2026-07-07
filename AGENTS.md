## Responsibilities

* Generate terminal commands or shell scripts.
* Generate Streamlit based ui interface.
* Adapt output to the target operating system (Linux, macOS, or Windows).
* Respect shell differences (Bash, Zsh, PowerShell).
* Prefer POSIX-compliant solutions whenever practical.
* Produce complete, self-contained scripts when requested.

## Requirement Clarifications

1. Determine:
   * Operating system
   * Shell version
2. Request clarification whenever requirements are ambiguous.


## Script Creation Standards

* Start executable scripts with the appropriate shebang.
* Follow ShellCheck recommendations.
* Use Semantic Versioning (`MAJOR.MINOR.PATCH`).
* Include `--help` and `--version`.
* Validate required external packages.
* Handle errors explicitly.
* Avoid `eval`.
* Keep lines under 120 characters.
* Use uppercase for global variables and lowercase for locals.
* Include concise function documentation.

## General Principles

* Preserve case sensitivity for file paths.
* Integrate user-provided paths correctly.
* Favor standard, maintained tools over deprecated ones.
* Generate concise, production-quality output.
* Prefer following the existing code style and patterns.
* Ensure you always cleanup the unused imports (for python files).

## Avoid Sloppiness

Write production-quality code. Before implementing or modifying anything, inspect the existing architecture, conventions, dependencies, and surrounding code.

Apply SOLID principles pragmatically. Keep responsibilities focused, dependencies explicit, abstractions meaningful, and components replaceable without unexpected side effects.

Use established design patterns only when they solve a concrete problem. Never introduce patterns, abstractions, interfaces, factories, or layers merely for appearance.

Maintain an organized structure:

* Group code by clear responsibility and domain.
* Keep files, classes, and functions small and focused.
* Use consistent naming and formatting.
* Eliminate duplication and dead code.
* Avoid hidden coupling, magic values, and unnecessary complexity.
* Preserve separation of concerns and clear dependency boundaries.

Before finishing:

1. Review the implementation for architectural inconsistencies.
2. Check whether each component has a single clear purpose.
3. Simplify overengineered code.
4. Refactor duplicated or misplaced logic.
5. Verify the solution fits the existing codebase rather than creating an isolated style.

Do not deliver code that merely works. Deliver code that is coherent, maintainable, testable, and structurally consistent.

## Testing and Commiting

* Do not run regression tests all the time
* When the user requests a commit; ask if the user wants to run/fix the regressions tests before the commit.
* Prior to commiting, check older commits and follow the same style and create a maximum of 5 commits (if more are necessary ask the User).

## IMPORTANT NOTE FOR THE UI DESIGN

* RESPECT THE DEFAULT STANDARD GAP OF 1 REM between every and each component, so no componet hugs another
* when you see that a repeating code is not normalized (and it could be) do it!

## Issue-Fixing Reasoning Protocol


When fixing any issue, you MUST follow this diagnostic process:

1. Analyze the symptom clearly.
2. Identify all plausible causes of the issue.
3. Filter out less likely causes using evidence, references, logs, examples, or contradictions.
4. When uncertainty remains, research each remaining cause further.
5. Compare working and non-working examples when available.
6. Narrow the cause until confidence is approximately 90% or higher.
7. Act only after the issue is sufficiently narrowed.
8. If confidence is below 100%, explicitly report the remaining uncertainty.
9. Never present uncertain conclusions as absolute facts.
10. Prefer evidence-based fixes over guesses.

When reporting the fix, include:
- observed symptom
- likely cause
- evidence used
- rejected causes
- confidence level
- final fix
- remaining uncertainty, if any
