"""Editable project: map simulation plus block program (the model behind the IDE)."""

from robot_ide.blocks.block_editor import BlockProgram
from robot_ide.blocks.code_generator import GeneratedCode, generate_code
from robot_ide.parser.parser import parse_source
from robot_ide.services.file_service import load_input
from robot_ide.simulator.map_loader import build_simulation, format_map
from robot_ide.simulator.simulation_state import SimulationState

DEFAULT_MAP = ("....@", ".###.", ">...@", ".###.", "@....")


class ProjectService:
    """Owns the simulation and the block program; loads and saves input files."""

    def __init__(self) -> None:
        self.simulation: SimulationState = build_simulation(5, 5, DEFAULT_MAP)
        self.program = BlockProgram()

    def new_project(self) -> None:
        """Default map, empty program."""
        self.simulation = build_simulation(5, 5, DEFAULT_MAP)
        self.program = BlockProgram()

    def load_text(self, inputText: str) -> None:
        """Load map and program from input-file text. Nothing changes if loading fails."""
        simulation, programInput = load_input(inputText)
        statements = parse_source(programInput.programLines)
        newProgram = BlockProgram()
        newProgram.load_statements(statements)
        self.simulation = simulation
        self.program = newProgram

    def generated_code(self) -> GeneratedCode:
        """Text of the current block program."""
        return generate_code(self.program.blocks)

    def to_input_text(self) -> str:
        """Input-file text: map size, initial map rows, generated program."""
        rows = format_map(self.simulation)
        header = f"{len(rows)} {len(rows[0])}"
        return "\n".join([header, *rows, *self.generated_code().lines]) + "\n"
