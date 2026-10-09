"""Data-only strategy compiler with forward control flow and exact FP32 words."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import hashlib
import json
import math
import struct
from typing import Any

SCHEMA = "asquerix-strategy-v1"
OPERATOR_VERSION = "rigid-operators-v1"
MAX_NODES, MAX_DEPTH, MAX_REPEAT, MAX_CODE = 64, 3, 8, 128
WORD = struct.Struct("<4I4f")


class Op(IntEnum):
    COMPRESS = 1
    EXPAND = 2
    MOVE = 3
    ROTATE = 4
    RELAX = 5
    RESTORE_BEST = 6
    STOP = 7
    IF_FALSE = 8
    JUMP = 9


class Selector(IntEnum):
    ALL = 0
    RANDOM_K = 1
    WALL_K = 2


class Predicate(IntEnum):
    LAST_NO_PROGRESS = 1
    LAST_REJECTED = 2
    LAST_IMPROVED_BEST = 3


class ProgramError(ValueError):
    def __init__(self, path: str, message: str):
        self.path, self.message = path, message
        super().__init__(f"{path}: {message}")


def integer(value: Any, low: int, high: int, path: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ProgramError(path, f"expected an integer in [{low}, {high}]")
    return value


def fp32(value: Any, low: float, high: float, path: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        raise ProgramError(path, "expected a finite number, not a boolean or string")
    try:
        converted = struct.unpack("<f", struct.pack("<f", value))[0]
    except (OverflowError, struct.error):
        raise ProgramError(path, "not representable in FP32") from None
    # Range endpoints are compiled too. Preserve all converted bits, including -0.
    lo = struct.unpack("<f", struct.pack("<f", low))[0]
    hi = struct.unpack("<f", struct.pack("<f", high))[0]
    if not math.isfinite(value) or not math.isfinite(converted) or not lo <= converted <= hi:
        raise ProgramError(path, f"expected a finite FP32 value in [{low}, {high}]")
    if positive and (value <= 0 or converted <= 0):
        raise ProgramError(path, "must remain strictly positive in FP32")
    return converted


@dataclass(frozen=True)
class Instruction:
    op: int
    i0: int = 0
    i1: int = 0
    i2: int = 0
    a: float = 0.0
    b: float = 0.0
    c: float = 0.0
    d: float = 0.0

    def words(self) -> tuple:
        return (self.op, self.i0, self.i1, self.i2, self.a, self.b, self.c, self.d)

    def pack(self) -> bytes:
        return WORD.pack(*self.words())


@dataclass(frozen=True)
class Compiled:
    authored_json: str
    code: tuple[Instruction, ...]
    source_map: tuple[str, ...]
    program_hash: str

    def document(self) -> dict:
        return {"schema": SCHEMA, "operator_version": OPERATOR_VERSION,
                "hash": self.program_hash, "authored": json.loads(self.authored_json),
                "instruction_count": len(self.code), "source_map": list(self.source_map),
                "instructions": [{"pc": pc, "op": Op(ins.op).name,
                                  "words": list(ins.words()),
                                  "fp32_bits": [ins.pack()[i:i + 4].hex() for i in range(16, 32, 4)],
                                  "source_node": self.source_map[pc]}
                                 for pc, ins in enumerate(self.code)]}


def _object(value: Any, allowed: set[str], required: set[str], path: str) -> dict:
    if type(value) is not dict:
        raise ProgramError(path, "expected an object")
    if set(value) - allowed:
        raise ProgramError(path, f"unknown fields: {sorted(set(value) - allowed)}")
    if required - set(value):
        raise ProgramError(path, f"missing fields: {sorted(required - set(value))}")
    return value


def verify(code: tuple[Instruction, ...]) -> tuple[Instruction, ...]:
    if not isinstance(code, tuple) or not 1 <= len(code) <= MAX_CODE:
        raise ProgramError("bytecode", f"instruction count must be in [1, {MAX_CODE}]")
    if not isinstance(code[-1], Instruction) or code[-1].op != Op.STOP:
        raise ProgramError("bytecode", "executable fall-through must end in STOP")
    for pc, ins in enumerate(code):
        path = f"bytecode[{pc}]"
        if not isinstance(ins, Instruction):
            raise ProgramError(path, "expected an Instruction")
        for name in ("op", "i0", "i1", "i2"):
            integer(int(getattr(ins, name)) if isinstance(getattr(ins, name), IntEnum) else getattr(ins, name), 0, 2**32 - 1, path + "." + name)
        try:
            op = Op(ins.op)
        except ValueError:
            raise ProgramError(path, "unknown opcode") from None
        for name in ("a", "b", "c", "d"):
            fp32(getattr(ins, name), -3.4028234663852886e38, 3.4028234663852886e38, path + "." + name)
        if ins.pack()[20:] != bytes(12):
            raise ProgramError(path, "reserved FP32 words must contain positive zero bits")
        if op == Op.COMPRESS:
            integer(ins.i0, 1, 128, path + ".attempt_limit")
            integer(ins.i1, 1, 480, path + ".sweep_limit")
            integer(ins.i2, 0, 1, path + ".target_present")
            if ins.i2:
                fp32(ins.a, 0, 1, path + ".target_reduction", positive=True)
                if ins.a >= 1:
                    raise ProgramError(path, "compression must be below 100% after FP32 conversion")
            elif ins.pack()[16:20] != bytes(4):
                raise ProgramError(path, "legacy compression has no target operand")
        elif op == Op.EXPAND:
            fp32(ins.a, 0, 0.25, path + ".fraction", positive=True)
            if ins.i0 or ins.i1 or ins.i2:
                raise ProgramError(path, "reserved integer operands must be zero")
        elif op in (Op.MOVE, Op.ROTATE):
            if ins.i0 not in tuple(Selector):
                raise ProgramError(path, "unknown selector")
            integer(ins.i1, 0, 32, path + ".k")
            if ins.i0 == Selector.ALL and ins.i1:
                raise ProgramError(path, "ALL must use k=0")
            integer(ins.i2, 1, 480, path + ".repair_sweeps")
            fp32(ins.a, 0, 0.5 if op == Op.MOVE else math.pi / 4,
                 path + ".magnitude", positive=True)
        elif op in (Op.IF_FALSE, Op.JUMP):
            integer(ins.i1, pc + 1, len(code) - 1, path + ".target")
            if ins.i2 or ins.pack()[16:20] != bytes(4):
                raise ProgramError(path, "reserved operands must be zero")
            if op == Op.IF_FALSE and ins.i0 not in tuple(Predicate):
                raise ProgramError(path, "unknown predicate")
            if op == Op.JUMP and ins.i0:
                raise ProgramError(path, "reserved jump operand must be zero")
        elif ins.i0 or ins.i1 or ins.i2 or ins.pack()[16:20] != bytes(4):
            raise ProgramError(path, "zero-operand operation contains arguments")
    return code


def compile_program(document: Any) -> Compiled:
    root = _object(document, {"schema", "name", "body"}, {"schema", "body"}, "program")
    if root["schema"] != SCHEMA:
        raise ProgramError("program.schema", f"expected {SCHEMA}")
    if "name" in root and (type(root["name"]) is not str or len(root["name"]) > 160):
        raise ProgramError("program.name", "expected text of at most 160 characters")
    code: list[Instruction] = []
    mapping: list[str] = []
    nodes = 0

    def emit(ins: Instruction, path: str) -> int:
        if len(code) >= MAX_CODE:
            raise ProgramError(path, f"expanded program exceeds {MAX_CODE} instructions")
        code.append(ins)
        mapping.append(path)
        return len(code) - 1

    def body(items: Any, path: str, depth: int, *, count_nodes: bool = True) -> None:
        nonlocal nodes
        if type(items) is not list or len(items) > MAX_NODES:
            raise ProgramError(path, "expected a bounded instruction list")
        if depth > MAX_DEPTH:
            raise ProgramError(path, f"nesting depth exceeds {MAX_DEPTH}")
        for index, raw in enumerate(items):
            node_path = f"{path}[{index}]"
            if count_nodes:
                nodes += 1
            if nodes > MAX_NODES:
                raise ProgramError(node_path, f"authored program exceeds {MAX_NODES} nodes")
            if type(raw) is not dict or type(raw.get("op")) is not str:
                raise ProgramError(node_path, "expected an instruction with a named op")
            name = raw["op"]
            if name == "REPEAT":
                node = _object(raw, {"op", "count", "body"}, {"op", "count", "body"}, node_path)
                count = integer(node["count"], 1, MAX_REPEAT, node_path + ".count")
                for repeat in range(count):
                    body(node["body"], node_path + ".body", depth + 1,
                         count_nodes=count_nodes and repeat == 0)
            elif name == "IF":
                node = _object(raw, {"op", "predicate", "then", "else"}, {"op", "predicate", "then"}, node_path)
                try:
                    predicate = Predicate[node["predicate"]]
                except (KeyError, TypeError):
                    raise ProgramError(node_path + ".predicate", "unknown predicate") from None
                branch = emit(Instruction(int(Op.IF_FALSE), int(predicate)), node_path)
                body(node["then"], node_path + ".then", depth + 1, count_nodes=count_nodes)
                jump = emit(Instruction(int(Op.JUMP)), node_path)
                code[branch] = Instruction(int(Op.IF_FALSE), int(predicate), len(code))
                body(node.get("else", []), node_path + ".else", depth + 1, count_nodes=count_nodes)
                code[jump] = Instruction(int(Op.JUMP), i1=len(code))
            else:
                try:
                    op = Op[name]
                except KeyError:
                    raise ProgramError(node_path + ".op", "unknown opcode") from None
                if op in (Op.IF_FALSE, Op.JUMP):
                    raise ProgramError(node_path, "raw jumps are not authoring operations")
                if op == Op.COMPRESS:
                    node = _object(raw, {"op", "target_reduction", "attempt_limit", "sweep_limit"},
                                   {"op", "target_reduction", "attempt_limit", "sweep_limit"}, node_path)
                    target = node["target_reduction"]
                    ins = Instruction(int(op), integer(node["attempt_limit"], 1, 128, node_path + ".attempt_limit"),
                                      integer(node["sweep_limit"], 1, 480, node_path + ".sweep_limit"),
                                      int(target is not None), 0.0 if target is None else
                                      fp32(target, 0, 1, node_path + ".target_reduction", positive=True))
                elif op == Op.EXPAND:
                    node = _object(raw, {"op", "fraction"}, {"op", "fraction"}, node_path)
                    ins = Instruction(int(op), a=fp32(node["fraction"], 0, 0.25, node_path + ".fraction", positive=True))
                elif op in (Op.MOVE, Op.ROTATE):
                    magnitude = "max_distance" if op == Op.MOVE else "max_angle_rad"
                    node = _object(raw, {"op", "selector", magnitude, "repair_sweeps"},
                                   {"op", "selector", magnitude, "repair_sweeps"}, node_path)
                    selector = _object(node["selector"], {"kind", "k"}, {"kind"}, node_path + ".selector")
                    try:
                        kind = Selector[selector["kind"]]
                    except (KeyError, TypeError):
                        raise ProgramError(node_path + ".selector.kind", "unknown selector") from None
                    if kind != Selector.ALL and "k" not in selector:
                        raise ProgramError(node_path + ".selector.k", "missing k")
                    k = integer(selector.get("k", 0), 0, 32, node_path + ".selector.k")
                    ins = Instruction(int(op), int(kind), k,
                                      integer(node["repair_sweeps"], 1, 480, node_path + ".repair_sweeps"),
                                      fp32(node[magnitude], 0, 0.5 if op == Op.MOVE else math.pi / 4,
                                           node_path + "." + magnitude, positive=True))
                else:
                    _object(raw, {"op"}, {"op"}, node_path)
                    ins = Instruction(int(op))
                emit(ins, node_path)

    body(root["body"], "body", 1)
    verified = verify(tuple(code))
    semantic_bytes = (SCHEMA + "\0" + OPERATOR_VERSION + "\0").encode() + b"".join(i.pack() for i in verified)
    return Compiled(json.dumps(root, allow_nan=False, sort_keys=True, separators=(",", ":")),
                    verified, tuple(mapping), hashlib.sha256(semantic_bytes).hexdigest())


def control_program(name: str, *, attempts: int = 128, sweeps: int = 480) -> dict:
    compress = {"op": "COMPRESS", "target_reduction": None, "attempt_limit": attempts, "sweep_limit": sweeps}
    if name == "legacy_compress":
        body = [compress, {"op": "STOP"}]
    elif name == "pulse_rotate":
        body = [{"op": "REPEAT", "count": 4, "body": [
            {**compress, "target_reduction": 0.05, "attempt_limit": min(8, attempts), "sweep_limit": min(120, sweeps)},
            {"op": "EXPAND", "fraction": 0.04},
            {"op": "ROTATE", "selector": {"kind": "WALL_K", "k": 3}, "max_angle_rad": 0.10,
             "repair_sweeps": min(120, sweeps)}]},
            {**compress, "attempt_limit": min(64, attempts)}, {"op": "STOP"}]
    else:
        raise ProgramError("control", "unknown fixed control")
    return {"schema": SCHEMA, "name": name, "body": body}
