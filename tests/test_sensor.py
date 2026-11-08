import pytest

from robot_ide.core.exceptions import BadArgError
from robot_ide.simulator.map_loader import build_simulation
from robot_ide.simulator.sensor import Sensor


def test_detects_each_cell_kind_ahead() -> None:
    for row, kind in (([">."], 0), ([">#"], 1), ([">@"], 2)):
        state = build_simulation(1, 2, row)
        assert Sensor(state).is_there(kind) is True


def test_wrong_kind_is_false() -> None:
    state = build_simulation(1, 2, [">@"])
    assert Sensor(state).is_there(1) is False


def test_sensed_cell_becomes_discovered_and_state_updated() -> None:
    state = build_simulation(1, 3, [">@."])
    Sensor(state).is_there(2)
    assert state.world.is_discovered(1, 0)
    assert not state.world.is_discovered(2, 0)
    assert state.robot.sensorResult is True
    assert state.robot.sensorTarget == (1, 0)


def test_off_map_counts_as_wall_and_is_not_marked() -> None:
    state = build_simulation(1, 2, [".>"])
    sensor = Sensor(state)
    assert sensor.is_there(1) is True
    assert sensor.is_there(0) is False
    assert len(state.world.discoveredCells) == 1


@pytest.mark.parametrize("kind", [3, -1, 100])
def test_bad_kind_rejected(kind: int) -> None:
    with pytest.raises(BadArgError):
        Sensor(build_simulation(1, 2, [">."])).is_there(kind)
