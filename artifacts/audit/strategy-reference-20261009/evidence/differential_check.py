"""Independent AST-versus-bytecode verification for the supplied CPU reference.

This audit harness does not execute geometry or use CUDA.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from strategy_reference import (
    Action, If, Instruction, Op, Predicate, Repeat, Seq,
    compile_strategy, decode, dry_run_control, encode,
)


def evaluate_tree(node, decisions, trace):
    """Walk source statements directly; return True on an explicit stop."""
    if isinstance(node, Action):
        if node.instruction.op == Op.HALT:
            return True
        trace.append(node.instruction.op)
    elif isinstance(node, Seq):
        for child in node.items:
            if evaluate_tree(child, decisions, trace):
                return True
    elif isinstance(node, Repeat):
        for _ in range(node.count):
            if evaluate_tree(node.body, decisions, trace):
                return True
    elif isinstance(node, If):
        arm = node.yes if next(decisions) else node.no
        return evaluate_tree(arm, decisions, trace)
    else:
        raise AssertionError(type(node))
    return False


rng = random.Random(20261009)
actions = (
    Instruction(Op.COMPRESS, i0=16, i1=64, a=0.02),
    Instruction(Op.EXPAND, a=0.02),
    Instruction(Op.RELAX, i0=32),
    Instruction(Op.ROTATE, i0=1, i1=3, i2=64, a=0.1),
    Instruction(Op.MOVE, i0=0, i2=64, a=0.1, b=-0.05),
    Instruction(Op.RESTORE_BEST),
    Instruction(Op.HALT),
)


def make_seq(level):
    return Seq(tuple(make_node(level) for _ in range(rng.randrange(4))))


def make_node(level):
    if level == 0 or rng.random() < 0.45:
        return Action(rng.choice(actions))
    kind = rng.randrange(3)
    if kind == 0:
        return make_seq(level - 1)
    if kind == 1:
        return Repeat(rng.randint(1, 8), make_seq(level - 1))
    return If(rng.choice(tuple(Predicate)), make_seq(level - 1), make_seq(level - 1))


accepted = rejected = compared = 0
for case in range(1000):
    source = make_seq(4)
    try:
        code = compile_strategy(source)
    except ValueError:
        rejected += 1
        continue
    accepted += 1
    assert decode(encode(code)) == code
    for path in range(8):
        choices = [bool(rng.getrandbits(1)) for _ in range(256)]
        tree_choices = iter(choices)
        bytecode_choices = iter(choices)
        expected = []
        evaluate_tree(source, tree_choices, expected)
        actual, status = dry_run_control(code, lambda _: next(bytecode_choices))
        assert status == 'HALTED', (case, path, status)
        assert actual == expected, (case, path, actual, expected)
        # Match condition consumption too, including branches before an early stop.
        assert list(tree_choices) == list(bytecode_choices), (case, path)
        compared += 1

print(f'Generated source trees: 1000; accepted: {accepted}; rejected by limits: {rejected}')
print(f'Independent AST/bytecode path comparisons: {compared}; mismatches: 0')
print('Binary round trips passed for every accepted tree.')
print('Geometry, GPU execution, finalization, and evolution were not exercised.')
