# Design notes and open-point decisions

- Log line numbers are relative to the first program line (first line after the map = 1).
- Log entry = line number + optional parts: API name, evaluated argument, return value,
  error code. API names: `isThere`, `step forward`, `turn by`, `mine here`, `print`.
- Non-API errors log as `<line> <ERROR_CODE>`. Error closes the log without `EOR`.
- Expressions are flat: operand, `not operand`, `isThere operand`, `operand op operand`.
- Operands are read left to right, then the operator checks types. No short-circuit.
- `step forward n` moves cell by cell. On a wall the robot stays on the last free cell.
- Wrong-type or out-of-range API argument (bool, negative, `isThere` not 0..2) -> `E_BAD_ARG`.
- Arithmetic results are not range-checked. Literals outside 0..100 are syntax errors.
- Syntax errors produce an empty log file and exit code 2 in `-q` mode.
- Executed lines counter includes `else` and every `while` check; limit is central
  (`MAX_EXECUTED_LINES`).
- Not run in the authoring sandbox: real pytest, Ruff, mypy (no network). Tests were run
  with a minimal stand-in runner; run the real tools once locally.

## Phases 6-8 decisions

- Block tree (`BlockProgram`) is the only editable state. Source view is generated, read-only.
- Operands are single tokens (number, `true`/`false`, variable name). A condition like `a = 1`
  must be set into a variable first. Loading a file whose `if`/`while` condition is an
  expression is refused with a message (blocks cannot represent it).
- Empty control block is allowed while editing. Running it gives a syntax error.
- Nesting limit (3) counts control blocks only. `else` shares the level of its `if`.
- Run control is a Qt timer in the GUI thread (`RunController`). A run is capped at 1000
  lines, so GUI stays responsive without a worker thread. Speed slider 1..10.
- Debugger: `DebugSession` stops BEFORE each line. Current line is highlighted in source
  view and in the block tree. Blocks and variables are locked/readable accordingly.
- GUI log file: written when a run ends, if an output path was given on the command line.
- Not verified: PySide6 is not installed in the authoring sandbox. UI files compile, but
  were never started. First GUI launch may reveal bugs. Manual robot control (phase 9) not built.
