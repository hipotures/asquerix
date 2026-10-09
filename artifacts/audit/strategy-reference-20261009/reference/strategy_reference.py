"""Executable reference for a bounded strategy language, NOT a packing solver.

Python 3.11+, standard library only. Compile typed nodes to fixed-width bytecode,
validate even externally supplied bytecode, and exercise finite control flow.
The geometry engine, CUDA interpreter, evolution, and evaluator are NOT here.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum
import hashlib
import math
import random
import struct
from typing import Callable

MAGIC = b"ASQVM001"
WORD = struct.Struct("<4I4f")  # 32 bytes: opcode, i0, i1, i2, a, b, c, d
MAX_CODE = 256
MAX_DEPTH = 8
MAX_REPEAT = 8
MAX_SOURCE_VISITS = 4096


class Op(IntEnum):
    COMPRESS = 1
    EXPAND = 2
    RELAX = 3
    ROTATE = 4
    MOVE = 5
    RESTORE_BEST = 6
    IF_FALSE = 240
    JUMP = 241
    HALT = 255


class Selector(IntEnum):
    ALL = 0
    RANDOM_K = 1
    WALL_K = 2
    INTERIOR_K = 3
    HIGH_CONTACT_K = 4


class Predicate(IntEnum):
    LAST_FAILED = 1
    COMPRESSION_STALLED = 2


@dataclass(frozen=True)
class Instruction:
    op: Op
    i0: int = 0
    i1: int = 0
    i2: int = 0
    a: float = 0.0
    b: float = 0.0
    c: float = 0.0
    d: float = 0.0


@dataclass(frozen=True)
class Action:
    instruction: Instruction


@dataclass(frozen=True)
class Seq:
    items: tuple[Node, ...]


@dataclass(frozen=True)
class Repeat:
    count: int
    body: Seq


@dataclass(frozen=True)
class If:
    predicate: Predicate
    yes: Seq
    no: Seq = Seq(())


Node = Action | Seq | Repeat | If


def _integer(value: object, low: int, high: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _f32(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("Numeric argument must be a real number, not bool")
    try:
        result = struct.unpack("<f", struct.pack("<f", float(value)))[0]
    except (OverflowError, struct.error) as error:
        raise ValueError("Argument is not representable in float32") from error
    if not math.isfinite(result):
        raise ValueError("Nonfinite argument")
    # Canonicalize program constants only, NEVER numerical solver outputs.
    return 0.0 if result == 0.0 else result


def _canonical(raw: Instruction) -> Instruction:
    if not isinstance(raw, Instruction) or not isinstance(raw.op, Op):
        raise ValueError("Instruction and opcode types must be explicit")
    for name in ("i0", "i1", "i2"):
        _integer(getattr(raw, name), 0, 2**32 - 1, name)
    return replace(raw, **{name: _f32(getattr(raw, name)) for name in ("a", "b", "c", "d")})


def _check_arguments(ins: Instruction) -> None:
    if ins.c != 0.0 or ins.d != 0.0:
        raise ValueError("Reserved operands must be zero")
    if ins.op == Op.COMPRESS:
        _integer(ins.i0, 1, 128, "compression attempts")
        _integer(ins.i1, 1, 480, "sweeps per attempt")
        if ins.i2 or not _f32(0.0001) <= ins.a <= _f32(0.2) or ins.b:
            raise ValueError("Invalid COMPRESS parameters")
    elif ins.op == Op.EXPAND:
        if ins.i0 or ins.i1 or ins.i2 or not 0.0 < ins.a <= _f32(0.1) or ins.b:
            raise ValueError("Invalid EXPAND parameters")
    elif ins.op == Op.RELAX:
        _integer(ins.i0, 1, 480, "relaxation sweeps")
        if ins.i1 or ins.i2 or ins.a or ins.b:
            raise ValueError("Invalid RELAX parameters")
    elif ins.op in (Op.ROTATE, Op.MOVE):
        try:
            selector = Selector(ins.i0)
        except ValueError as error:
            raise ValueError("Unknown selector") from error
        if selector == Selector.ALL:
            if ins.i1 != 0:
                raise ValueError("ALL uses k=0")
        else:
            _integer(ins.i1, 1, 32, "selected count")
        _integer(ins.i2, 1, 480, "repair sweeps")
        if ins.op == Op.ROTATE:
            if not 0.0 < ins.a <= _f32(math.pi / 4) or ins.b:
                raise ValueError("Invalid ROTATE angle")
        elif max(abs(ins.a), abs(ins.b)) > _f32(0.25) or (ins.a == 0.0 and ins.b == 0.0):
            raise ValueError("Invalid MOVE vector")
    elif ins.op in (Op.RESTORE_BEST, Op.HALT):
        if ins.i0 or ins.i1 or ins.i2 or ins.a or ins.b:
            raise ValueError("Zero-operand opcode has nonzero arguments")
    elif ins.op == Op.IF_FALSE:
        try:
            Predicate(ins.i0)
        except ValueError as error:
            raise ValueError("Unknown predicate") from error
        if ins.i2 or ins.a or ins.b:
            raise ValueError("Invalid IF_FALSE parameters")
    elif ins.op == Op.JUMP:
        if ins.i0 or ins.i2 or ins.a or ins.b:
            raise ValueError("Invalid JUMP parameters")
    else:
        raise ValueError("Unsupported opcode")


def verify(code: tuple[Instruction, ...]) -> tuple[Instruction, ...]:
    if not isinstance(code, tuple) or not 1 <= len(code) <= MAX_CODE:
        raise ValueError("Bytecode length outside bounds")
    canonical = tuple(_canonical(ins) for ins in code)
    if canonical[-1].op != Op.HALT:
        raise ValueError("Final instruction must be HALT")
    for pc, ins in enumerate(canonical):
        _check_arguments(ins)
        if ins.op in (Op.IF_FALSE, Op.JUMP):
            if not pc < ins.i1 < len(canonical):
                raise ValueError("Jump must target a later instruction within the program")
    return canonical


def _source_size(node: Node, depth: int, visits: list[int]) -> int:
    visits[0] += 1
    if visits[0] > MAX_SOURCE_VISITS or depth > MAX_DEPTH:
        raise ValueError("Source structure exceeds limits")
    if isinstance(node, Action):
        ins = _canonical(node.instruction)
        if ins.op in (Op.IF_FALSE, Op.JUMP):
            raise ValueError("Raw control-flow instructions are compiler-owned")
        _check_arguments(ins)
        return 1
    if isinstance(node, Seq):
        if not isinstance(node.items, tuple):
            raise ValueError("Sequence must contain an immutable tuple")
        size = 0
        for child in node.items:
            size += _source_size(child, depth + 1, visits)
            if size >= MAX_CODE:
                raise ValueError("Expanded program too large")
        return size
    if isinstance(node, Repeat):
        _integer(node.count, 1, MAX_REPEAT, "repeat count")
        if not isinstance(node.body, Seq):
            raise ValueError("Repeat body must be Seq")
        size = node.count * _source_size(node.body, depth + 1, visits)
    elif isinstance(node, If):
        if not isinstance(node.predicate, Predicate) or not isinstance(node.yes, Seq) or not isinstance(node.no, Seq):
            raise ValueError("Typed predicate and Seq arms required")
        size = 2 + _source_size(node.yes, depth + 1, visits) + _source_size(node.no, depth + 1, visits)
    else:
        raise ValueError("Unknown source node")
    if size >= MAX_CODE:
        raise ValueError("Expanded program too large")
    return size


def compile_strategy(root: Seq) -> tuple[Instruction, ...]:
    if not isinstance(root, Seq):
        raise ValueError("Program root must be Seq")
    _source_size(root, 0, [0])  # Validate before unrolling or allocating output.
    code: list[Instruction] = []

    def emit(node: Node) -> None:
        if isinstance(node, Action):
            code.append(_canonical(node.instruction))
        elif isinstance(node, Seq):
            for child in node.items:
                emit(child)
        elif isinstance(node, Repeat):
            for _ in range(node.count):
                emit(node.body)
        elif isinstance(node, If):
            test_pc = len(code)
            code.append(Instruction(Op.IF_FALSE, i0=int(node.predicate)))
            emit(node.yes)
            jump_pc = len(code)
            code.append(Instruction(Op.JUMP))
            code[test_pc] = replace(code[test_pc], i1=len(code))
            emit(node.no)
            code[jump_pc] = replace(code[jump_pc], i1=len(code))
        else:
            raise ValueError("Unknown source node")

    emit(root)
    code.append(Instruction(Op.HALT))
    return verify(tuple(code))


def encode(code: tuple[Instruction, ...]) -> bytes:
    code = verify(code)
    return MAGIC + struct.pack("<I", len(code)) + b"".join(
        WORD.pack(int(x.op), x.i0, x.i1, x.i2, x.a, x.b, x.c, x.d) for x in code
    )


def decode(payload: bytes) -> tuple[Instruction, ...]:
    if not isinstance(payload, bytes) or len(payload) < 12 or payload[:8] != MAGIC:
        raise ValueError("Invalid bytecode header")
    count = struct.unpack_from("<I", payload, 8)[0]
    if not 1 <= count <= MAX_CODE or len(payload) != 12 + count * WORD.size:
        raise ValueError("Invalid bytecode length")
    code = []
    for pc in range(count):
        fields = WORD.unpack_from(payload, 12 + pc * WORD.size)
        try:
            opcode = Op(fields[0])
        except ValueError as error:
            raise ValueError("Unknown opcode") from error
        code.append(Instruction(opcode, *fields[1:]))
    return verify(tuple(code))


def program_digest(code: tuple[Instruction, ...]) -> str:
    return hashlib.sha256(encode(code)).hexdigest()


@dataclass
class Fuel:
    remaining: int
    spent: int = 0

    def __post_init__(self) -> None:
        _integer(self.remaining, 0, 2**63 - 1, "remaining fuel")
        _integer(self.spent, 0, 2**63 - 1 - self.remaining, "spent fuel")

    def charge(self, cost: int) -> bool:
        """Reserve before work; failed reservations perform no work or decrement."""
        _integer(cost, 1, 2**63 - 1, "work cost")
        if cost > self.remaining:
            return False
        self.remaining -= cost
        self.spent += cost
        return True


def dry_run_control(
    code: tuple[Instruction, ...],
    predicate: Callable[[Predicate], bool],
    dispatch_limit: int = MAX_CODE,
) -> tuple[list[Op], str]:
    """Inspect finite control flow only. Does NOT execute or mock geometry."""
    code = verify(code)
    _integer(dispatch_limit, 0, MAX_CODE, "dispatch limit")
    fuel = Fuel(dispatch_limit)
    pc = 0
    operations = []
    while pc < len(code):
        if not fuel.charge(1):
            return operations, "DISPATCH_BUDGET"
        ins = code[pc]
        if ins.op == Op.HALT:
            return operations, "HALTED"
        if ins.op == Op.IF_FALSE:
            decision = predicate(Predicate(ins.i0))
            if not isinstance(decision, bool):
                raise ValueError("Predicate must return bool")
            pc = pc + 1 if decision else ins.i1
        elif ins.op == Op.JUMP:
            pc = ins.i1
        else:
            operations.append(ins.op)
            pc += 1
    raise AssertionError("Verified program must end at HALT")


def generate_program(seed: int) -> Seq:
    """Generate a valid bounded template; this is not an evolutionary optimizer."""
    _integer(seed, 0, 2**64 - 1, "generator seed")
    rng = random.Random(seed)
    compression = Action(Instruction(Op.COMPRESS, i0=rng.choice((16, 32, 64)),
                                     i1=rng.choice((64, 128, 256)), a=rng.uniform(0.005, 0.05)))
    escape = Seq((
        Action(Instruction(Op.EXPAND, a=rng.uniform(0.01, 0.05))),
        Action(Instruction(Op.ROTATE, i0=int(Selector.RANDOM_K), i1=rng.randint(1, 4),
                           i2=64, a=rng.uniform(0.02, 0.25))),
        compression,
    ))
    result = Seq((compression, Repeat(rng.randint(1, 4),
                                     Seq((If(Predicate.COMPRESSION_STALLED, escape),)))))
    compile_strategy(result)  # Never return unverified generated structure.
    return result


def mutate_first_compression(program: Seq, factor: float) -> Seq:
    """One illustrative parameter mutation, not a full AST mutation library."""
    compile_strategy(program)
    if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not math.isfinite(factor) or factor <= 0:
        raise ValueError("Mutation factor must be positive and finite")
    if not program.items or not isinstance(program.items[0], Action):
        raise ValueError("This example expects a leading COMPRESS action")
    first = program.items[0].instruction
    if first.op != Op.COMPRESS:
        raise ValueError("This example expects a leading COMPRESS action")
    changed = replace(first, a=min(0.2, max(0.0001, first.a * factor)))
    child = Seq((Action(changed), *program.items[1:]))
    compile_strategy(child)
    return child


def example_strategy() -> Seq:
    compress = Action(Instruction(Op.COMPRESS, i0=32, i1=128, a=0.02))
    escape = Seq((
        Action(Instruction(Op.EXPAND, a=0.02)),
        Action(Instruction(Op.ROTATE, i0=int(Selector.RANDOM_K), i1=3,
                           i2=64, a=math.radians(8))),
        compress,
    ))
    return Seq((compress, Repeat(3, Seq((If(Predicate.COMPRESSION_STALLED, escape),)))))


if __name__ == "__main__":
    bytecode = compile_strategy(example_strategy())
    print(f"Instructions: {len(bytecode)}; bytes: {len(encode(bytecode))}")
    print(f"Program SHA-256: {program_digest(bytecode)}")
    actions, status = dry_run_control(bytecode, lambda _: True)
    print("Control-flow example (all predicates true):", " -> ".join(op.name for op in actions))
    print("Status:", status)
    print("No packing simulations or GPU benchmarks were performed by this example.")
