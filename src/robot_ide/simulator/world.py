"""Maze grid with per-cell discovery tracking."""

from dataclasses import dataclass, field

from robot_ide.core.enums import CellType


@dataclass
class World:
    """Rectangular maze. Cells outside the grid count as walls."""

    width: int
    height: int
    cells: list[list[CellType]]
    discoveredCells: set[tuple[int, int]] = field(default_factory=set)

    def is_inside(self, x: int, y: int) -> bool:
        """True if (x, y) lies on the map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def cell_at(self, x: int, y: int) -> CellType:
        """Cell content; positions off the map read as WALL."""
        if not self.is_inside(x, y):
            return CellType.WALL
        return self.cells[y][x]

    def mark_discovered(self, x: int, y: int) -> None:
        """Remember a cell as discovered (off-map positions are ignored)."""
        if self.is_inside(x, y):
            self.discoveredCells.add((x, y))

    def is_discovered(self, x: int, y: int) -> bool:
        """True if the cell was visited or sensed."""
        return (x, y) in self.discoveredCells

    def clear_gold(self, x: int, y: int) -> None:
        """Turn a mined cell into an empty one."""
        self.cells[y][x] = CellType.EMPTY

    def copy(self) -> "World":
        """Independent deep copy."""
        return World(
            self.width,
            self.height,
            [list(row) for row in self.cells],
            set(self.discoveredCells),
        )
