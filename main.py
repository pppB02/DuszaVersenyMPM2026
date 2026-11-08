"""Entry point: ``python main.py [-q] input.txt output.txt``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from robot_ide.cli.command_line import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
