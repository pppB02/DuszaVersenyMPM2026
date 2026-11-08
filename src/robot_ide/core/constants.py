"""Project-wide constants."""

MIN_MAP_SIZE = 1
MAX_MAP_SIZE = 15
MIN_NUMBER = 0
MAX_NUMBER = 100
MAX_EXECUTED_LINES = 1000
MAX_CONTROL_NESTING = 3

END_OF_RUN_MARKER = "EOR"
LIMIT_EXCEEDED_MARKER = "INSTRUCTION_COUNT_LIMIT_EXCEEDED"

CHAR_EMPTY = "."
CHAR_GOLD = "@"
CHAR_WALL = "#"

SENSOR_EMPTY = 0
SENSOR_WALL = 1
SENSOR_GOLD = 2

KEYWORDS = frozenset(
    {
        "set", "to", "if", "else", "while", "step", "forward", "turn", "by",
        "mine", "here", "print", "isThere", "true", "false", "not", "and", "or",
    }
)
