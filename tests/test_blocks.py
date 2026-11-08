import pytest

from robot_ide.blocks.block_editor import BlockProgram
from robot_ide.blocks.block_models import Block, BlockKind, Branch, ValueBlock, ValueKind
from robot_ide.blocks.code_generator import generate_code
from robot_ide.core.enums import Operator
from robot_ide.core.exceptions import BlockEditError, MineScriptSyntaxError
from robot_ide.parser.parser import parse_source
from robot_ide.services.project_service import ProjectService


def add(
    program: BlockProgram,
    kind: BlockKind,
    parentId: int | None = None,
    branch: Branch = Branch.MAIN,
    index: int | None = None,
) -> Block:
    block = program.new_block(kind)
    program.add_block(block, parentId, branch, index)
    return block


def text_of(program: BlockProgram) -> list[str]:
    return generate_code(program.blocks).lines


def test_default_blocks_generate_valid_parsable_code() -> None:
    program = BlockProgram()
    for kind in BlockKind:
        add(program, kind)
    lines = text_of(program)
    assert lines[0] == "set x to 0"
    assert "mine here" in lines and "step forward 1" in lines and "turn by 1" in lines
    for block in program.blocks:
        if block.kind.is_control:
            program.add_block(program.new_block(BlockKind.MINE_HERE), block.blockId)
            if block.kind is BlockKind.IF_ELSE:
                program.add_block(
                    program.new_block(BlockKind.MINE_HERE), block.blockId, Branch.ELSE
                )
    parse_source(text_of(program))


def test_empty_control_block_is_allowed_while_editing_but_fails_at_run() -> None:
    program = BlockProgram()
    add(program, BlockKind.WHILE)
    with pytest.raises(MineScriptSyntaxError):
        parse_source(text_of(program))


def test_insert_between_blocks() -> None:
    program = BlockProgram()
    first = add(program, BlockKind.MINE_HERE)
    add(program, BlockKind.PRINT)
    add(program, BlockKind.STEP_FORWARD, index=1)
    assert text_of(program) == ["mine here", "step forward 1", "print 0"]
    assert program.locate(first.blockId).index == 0


def test_delete_removes_subtree() -> None:
    program = BlockProgram()
    loop = add(program, BlockKind.WHILE)
    add(program, BlockKind.PRINT, loop.blockId)
    program.remove_block(loop.blockId)
    assert program.blocks == []
    with pytest.raises(BlockEditError):
        program.find(loop.blockId)


def test_move_into_and_out_of_control_block() -> None:
    program = BlockProgram()
    loop = add(program, BlockKind.WHILE)
    step = add(program, BlockKind.STEP_FORWARD)
    program.move_block(step.blockId, loop.blockId)
    assert text_of(program) == ["while true", "  step forward 1"]
    program.move_block(step.blockId, None, index=0)
    assert text_of(program) == ["step forward 1", "while true"]


def test_move_within_same_list_uses_index_before_removal() -> None:
    program = BlockProgram()
    first = add(program, BlockKind.MINE_HERE)
    add(program, BlockKind.PRINT)
    add(program, BlockKind.TURN_BY)
    program.move_block(first.blockId, None, index=3)
    assert text_of(program) == ["print 0", "turn by 1", "mine here"]
    program.move_block(first.blockId, None, index=0)
    assert text_of(program)[0] == "mine here"


def test_cannot_move_block_into_itself() -> None:
    program = BlockProgram()
    outer = add(program, BlockKind.WHILE)
    inner = add(program, BlockKind.IF, outer.blockId)
    with pytest.raises(BlockEditError):
        program.move_block(outer.blockId, inner.blockId)
    assert text_of(program) == ["while true", "  if true"]


def test_else_branch() -> None:
    program = BlockProgram()
    branching = add(program, BlockKind.IF_ELSE)
    add(program, BlockKind.PRINT, branching.blockId)
    add(program, BlockKind.MINE_HERE, branching.blockId, Branch.ELSE)
    assert text_of(program) == ["if true", "  print 0", "else", "  mine here"]
    plain = add(program, BlockKind.IF)
    with pytest.raises(BlockEditError):
        add(program, BlockKind.PRINT, plain.blockId, Branch.ELSE)
    with pytest.raises(BlockEditError):
        program.set_has_else(branching.blockId, False)


def test_three_level_nesting_allowed_fourth_refused() -> None:
    program = BlockProgram()
    first = add(program, BlockKind.WHILE)
    second = add(program, BlockKind.IF, first.blockId)
    third = add(program, BlockKind.IF, second.blockId)
    add(program, BlockKind.PRINT, third.blockId)
    with pytest.raises(BlockEditError):
        add(program, BlockKind.WHILE, third.blockId)
    with pytest.raises(BlockEditError):
        add(program, BlockKind.IF_ELSE, third.blockId, Branch.MAIN)
    assert generate_code(program.blocks).lines[-1] == "      print 0"


def test_else_counts_as_same_level() -> None:
    program = BlockProgram()
    first = add(program, BlockKind.WHILE)
    second = add(program, BlockKind.IF_ELSE, first.blockId)
    third = add(program, BlockKind.IF, second.blockId, Branch.ELSE)
    assert program.locate(third.blockId).branch is Branch.ELSE
    with pytest.raises(BlockEditError):
        add(program, BlockKind.WHILE, third.blockId)


def test_move_that_breaks_nesting_limit_is_refused_and_undone() -> None:
    program = BlockProgram()
    first = add(program, BlockKind.WHILE)
    second = add(program, BlockKind.IF, first.blockId)
    third = add(program, BlockKind.IF, second.blockId)
    loose = add(program, BlockKind.WHILE)
    add(program, BlockKind.IF, loose.blockId)
    before = text_of(program)
    with pytest.raises(BlockEditError):
        program.move_block(loose.blockId, third.blockId)
    assert text_of(program) == before


@pytest.mark.parametrize("name", ["while", "set", "true", "9lives", "", "a b", "x+y"])
def test_bad_variable_names_refused(name: str) -> None:
    program = BlockProgram()
    block = add(program, BlockKind.SET)
    with pytest.raises(BlockEditError):
        program.set_variable_name(block.blockId, name)
    assert block.variableName == "x"


def test_unknown_and_future_variables_accepted() -> None:
    program = BlockProgram()
    loop = add(program, BlockKind.WHILE)
    program.set_operand(loop.blockId, "later")
    setter = add(program, BlockKind.SET)
    program.set_variable_name(setter.blockId, "later")
    assert text_of(program) == ["while later", "set later to 0"]


@pytest.mark.parametrize("operand", ["", "9lives", "101", "-1", "a b", "if"])
def test_bad_operands_refused(operand: str) -> None:
    program = BlockProgram()
    block = add(program, BlockKind.PRINT)
    with pytest.raises(BlockEditError):
        program.set_operand(block.blockId, operand)


def test_value_blocks_generate_all_forms() -> None:
    program = BlockProgram()
    block = add(program, BlockKind.SET)
    cases = [
        (ValueBlock(ValueKind.INTEGER, ["7"]), "set x to 7"),
        (ValueBlock(ValueKind.BOOLEAN, ["false"]), "set x to false"),
        (ValueBlock(ValueKind.VARIABLE, ["y"]), "set x to y"),
        (ValueBlock(ValueKind.ARITHMETIC, ["x", "1"], Operator.ADD), "set x to x + 1"),
        (ValueBlock(ValueKind.COMPARISON, ["x", "3"], Operator.NOT_EQUAL), "set x to x <> 3"),
        (ValueBlock(ValueKind.LOGICAL, ["a", "b"], Operator.OR), "set x to a or b"),
        (ValueBlock(ValueKind.NOT, ["a"]), "set x to not a"),
        (ValueBlock(ValueKind.IS_THERE, ["2"]), "set x to isThere 2"),
    ]
    for value, expected in cases:
        program.set_value(block.blockId, value)
        assert text_of(program) == [expected]


def test_bad_values_refused() -> None:
    program = BlockProgram()
    block = add(program, BlockKind.SET)
    for bad in (
        ValueBlock(ValueKind.INTEGER, ["true"]),
        ValueBlock(ValueKind.BOOLEAN, ["1"]),
        ValueBlock(ValueKind.VARIABLE, ["while"]),
        ValueBlock(ValueKind.ARITHMETIC, ["1", "2"], Operator.AND),
        ValueBlock(ValueKind.ARITHMETIC, ["1"], Operator.ADD),
        ValueBlock(ValueKind.NOT, ["1"], Operator.ADD),
    ):
        with pytest.raises(BlockEditError):
            program.set_value(block.blockId, bad)


def test_value_blocks_only_on_set_blocks() -> None:
    program = BlockProgram()
    block = add(program, BlockKind.PRINT)
    with pytest.raises(BlockEditError):
        program.set_value(block.blockId, ValueBlock(ValueKind.INTEGER, ["1"]))
    with pytest.raises(BlockEditError):
        program.set_variable_name(block.blockId, "y")


def test_generated_text_round_trips_through_parser_and_blocks() -> None:
    source = (
        "set count to 0\nset megy to true\nwhile megy\n  set arany to isThere 2\n  if arany\n"
        "    step forward 1\n    mine here\n    set count to count + 1\n  else\n"
        "    step forward 1\n  set fal to isThere 1\n  set megy to not fal\nprint count"
    )
    program = BlockProgram()
    program.load_statements(parse_source(source.splitlines()))
    code = generate_code(program.blocks)
    assert code.text == source
    whileBlock = program.blocks[2]
    assert code.lineByBlockId[whileBlock.blockId] == 3
    ifBlock = whileBlock.children[1]
    assert ifBlock.kind is BlockKind.IF_ELSE
    assert code.elseLineByBlockId[ifBlock.blockId] == 9
    assert code.block_at_line(9) == ifBlock.blockId


def test_load_refuses_too_deep_programs() -> None:
    deep = ["while true", "  while true", "    while true", "      while true", "        print 1"]
    with pytest.raises(BlockEditError):
        BlockProgram().load_statements(parse_source(deep))


def test_conditions_with_operators_cannot_become_blocks() -> None:
    with pytest.raises(BlockEditError):
        BlockProgram().load_statements(parse_source(["if a = 1", "  print 1"]))


def test_failed_load_keeps_old_program() -> None:
    project = ProjectService()
    project.load_text("1 3\n>..\nprint 1")
    good = project.to_input_text()
    with pytest.raises(MineScriptSyntaxError):
        project.load_text("1 3\n>..\nprint 1 +")
    assert project.to_input_text() == good


def test_project_save_and_reload_round_trip() -> None:
    project = ProjectService()
    source = "2 4\n>.@#\n..@.\nset a to 1\nset c to a = 1\nif c\n  print a"
    project.load_text(source)
    saved = project.to_input_text()
    assert saved == source + "\n"
    other = ProjectService()
    other.load_text(saved)
    assert other.to_input_text() == saved


def test_saved_map_is_the_initial_map_not_the_run_state() -> None:
    project = ProjectService()
    project.load_text("1 3\n>@.\nstep forward 1\nmine here")
    project.simulation.robot.x = 2
    project.simulation.world.clear_gold(1, 0)
    assert project.to_input_text().splitlines()[1] == ">@."
