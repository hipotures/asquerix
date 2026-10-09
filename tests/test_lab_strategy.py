"""Compiler rejection, source mapping, semantic hashing, and finite flow."""

import copy
import math

import pytest

from asquerix.lab.config import Campaign
from asquerix.lab.strategy import Instruction, Op, ProgramError, compile_program, control_program, verify


def program(body):
    return {"schema": "asquerix-strategy-v1", "body": [*body, {"op": "STOP"}]}


def test_controls_round_trip_and_semantic_name_independence():
    for name in ("legacy_compress", "pulse_rotate"):
        authored = control_program(name)
        compiled = compile_program(authored)
        assert compile_program(compiled.document()["authored"]) == compiled
        authored["name"] = "Another display name"
        assert compile_program(authored).program_hash == compiled.program_hash
        assert len(compiled.source_map) == len(compiled.code)
    pulse = compile_program(control_program("pulse_rotate"))
    assert pulse.source_map[0] == pulse.source_map[3]


@pytest.mark.parametrize("node", [
    {"op": "UNKNOWN"}, {"op": "EXPAND", "fraction": float("nan")},
    {"op": "EXPAND", "fraction": float("inf")}, {"op": "EXPAND", "fraction": True},
    {"op": "EXPAND", "fraction": -0.0}, {"op": "EXPAND", "fraction": 1e-100},
    {"op": "COMPRESS", "target_reduction": 1, "attempt_limit": 8, "sweep_limit": 120},
    {"op": "COMPRESS", "target_reduction": None, "attempt_limit": True, "sweep_limit": 120},
    {"op": "COMPRESS", "target_reduction": None, "attempt_limit": -1, "sweep_limit": 120},
    {"op": "COMPRESS", "target_reduction": None, "attempt_limit": 2**32, "sweep_limit": 120},
    {"op": "MOVE", "selector": {"kind": "BAD", "k": 1}, "max_distance": .1, "repair_sweeps": 120},
    {"op": "MOVE", "selector": {"kind": "ALL", "k": 1}, "max_distance": .1, "repair_sweeps": 120},
    {"op": "REPEAT", "count": 9, "body": [{"op": "RELAX"}]},
    {"op": "JUMP", "target": 0}, {"op": "STOP", "repair_sweeps": 10},
])
def test_reject_bad_authored_nodes(node):
    with pytest.raises(ProgramError):
        compile_program(program([node]))


def test_expansion_and_depth_limits():
    node = {"op": "RELAX"}
    for _ in range(3):
        node = {"op": "REPEAT", "count": 8, "body": [node]}
    with pytest.raises(ProgramError):
        compile_program(program([node]))
    with pytest.raises(ProgramError):
        compile_program(program([{"op": "RELAX"}] * 64))
    with pytest.raises(ProgramError):
        compile_program(program([{"op": "REPEAT", "count": 8, "body": [{"op": "RELAX"}] * 16}]))


@pytest.mark.parametrize("code", [
    (Instruction(99), Instruction(7)),
    (Instruction(9, i1=0), Instruction(7)),
    (Instruction(9, i1=2), Instruction(7)),
    (Instruction(8, i0=9, i1=1), Instruction(7)),
    (Instruction(7, b=-0.0),),
    (Instruction(2, a=math.inf), Instruction(7)),
    (Instruction(5),),
])
def test_bad_bytecode(code):
    with pytest.raises(ProgramError):
        verify(code)


def test_forward_conditions_end_at_stop_for_every_predicate():
    compiled = compile_program(program([{"op": "IF", "predicate": "LAST_REJECTED",
                                        "then": [{"op": "RELAX"}], "else": [{"op": "RESTORE_BEST"}]}]))
    for predicate in (False, True):
        pc = 0
        visits = []
        while True:
            visits.append(pc)
            ins = compiled.code[pc]
            if ins.op == Op.STOP:
                break
            pc = ins.i1 if ins.op == Op.JUMP or (ins.op == Op.IF_FALSE and not predicate) else pc + 1
        assert visits == sorted(set(visits))
        assert len(visits) <= len(compiled.code)


def test_campaign_identity_and_plan():
    campaign = Campaign(name="Reference")
    assert campaign.plan()["training_episodes"] == 4224
    assert campaign.plan()["holdout_episodes_before_deduplication"] == 256
    spec = campaign.document()
    spec["datasets"]["training"]["first_id"] = "18446744073709550000"
    assert Campaign.model_validate(spec).datasets.training.first_id == "18446744073709550000"
    for value in (True, -1, 2**64, "18446744073709551616", "01"):
        bad = copy.deepcopy(spec)
        bad["operator_seed"] = value
        with pytest.raises(ValueError):
            Campaign.model_validate(bad)


def test_campaign_rejects_overlapping_banks_and_quota():
    spec = Campaign(name="Reference").document()
    spec["datasets"]["holdout"]["first_id"] = spec["datasets"]["training"]["first_id"]
    with pytest.raises(ValueError, match="disjoint"):
        Campaign.model_validate(spec)
    spec = Campaign(name="Reference").document()
    spec["limits"]["max_artifact_mib"] = 0.0001
    with pytest.raises(ValueError, match="quota"):
        Campaign.model_validate(spec)
