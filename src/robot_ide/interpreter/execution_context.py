"""Mutable state of one program run."""

from dataclasses import dataclass, field

from robot_ide.interpreter.environment import Environment
from robot_ide.logging.execution_logger import ExecutionLogger
from robot_ide.simulator.robot import Robot
from robot_ide.simulator.sensor import Sensor


@dataclass
class ExecutionContext:
    """Everything the evaluator and executor share during a run."""

    environment: Environment
    robot: Robot
    sensor: Sensor
    logger: ExecutionLogger
    maxExecutedLines: int
    executedCount: int = 0
    currentLine: int = 0
    printedOutput: list[str] = field(default_factory=list)
