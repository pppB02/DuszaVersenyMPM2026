# MineScript Robot IDE

Phases 1-8 written. Phases 1-5 and block/debug logic are tested. The PySide6 UI was never launched in the authoring sandbox.
thin `-q` CLI. The PySide6 GUI, block editor, debugger and packaging come in later phases.

## Run

```bash
pip install -r requirements.txt
python main.py -q examples/collect_gold.txt out.txt
pytest
ruff check .
mypy src
```

## Layout

`core` models/enums/errors, `simulator` map+robot+sensor (single source of robot state),
`parser` tokenizer/AST/parser, `interpreter` generator-based executor, `logging` run log,
`services` file + execution flow, `cli` argument handling.

## Decisions on points the spec leaves open (see ai.md)

See `ai.md`.
"# DuszaVersenyMPM2026" 
