"""Bounded generators, exact ask/tell resume, and fair deterministic selection."""

import json
import random

import pytest

from asquerix.lab.config import Campaign, Generation
from asquerix.lab.evaluation import score
from asquerix.lab.search import Controller, generate, initial_pool, mutate
from asquerix.lab.strategy import Op, ProgramError, compile_program


def _flow(compiled, truth):
    pc = 0
    for _ in range(128):
        ins = compiled.code[pc]
        if ins.op == Op.STOP:
            return
        pc = ins.i1 if ins.op == Op.JUMP or (ins.op == Op.IF_FALSE and not truth) else pc + 1
    pytest.fail("Control flow did not terminate")


def test_generated_and_mutated_accepted_programs_fit_bounds_and_terminate():
    law = Generation()
    rng = random.Random(20261009)
    accepted, rejected = 0, 0
    for _ in range(250):
        authored = generate(rng, law)
        try:
            compiled = compile_program(authored)
            for truth in (False, True):
                _flow(compiled, truth)
            child, mutation = mutate(authored, rng, law)
            compiled_child = compile_program(child)
            _flow(compiled_child, False)
            _flow(compiled_child, True)
            assert mutation["node_path"].startswith("body[")
            accepted += 1
        except ProgramError:
            rejected += 1
    assert accepted > 200


def _evaluated(candidate, value, *, eligible=True, complete=True):
    return {**candidate, "state": "EVALUATED", "score": {"eligible": eligible, "complete": complete,
            "ranking_tuple": [value, value, 100, candidate["program"]["instruction_count"], candidate["program"]["hash"]] if eligible else None}}


def test_shared_pool_and_exact_json_controller_resume():
    campaign = Campaign(name="Test")
    pool = initial_pool(campaign)
    assert pool == initial_pool(campaign)
    random_arm = Controller(campaign, "random_program_search", pool, "campaign")
    mutation_arm = Controller(campaign, "one_plus_lambda", pool, "campaign")
    assert [candidate["program"] for candidate in random_arm.ask()] == [candidate["program"] for candidate in mutation_arm.ask()]
    group = mutation_arm.ask()
    mutation_arm.tell([_evaluated(candidate, 10 - index / 10) for index, candidate in enumerate(group)])
    state = json.loads(json.dumps(mutation_arm.checkpoint()))
    resumed = Controller(campaign, "one_plus_lambda", pool, "campaign", state=state)
    assert mutation_arm.ask() == resumed.ask()
    pending_state = json.loads(json.dumps(mutation_arm.checkpoint()))
    resumed_pending = Controller(campaign, "one_plus_lambda", pool, "campaign", state=pending_state)
    assert mutation_arm.ask() == resumed_pending.ask()
    assert all(candidate["parent_id"] == mutation_arm.parent_id for candidate in mutation_arm.ask())


def test_parent_group_barrier_and_invalid_ineligible_children():
    campaign = Campaign(name="Test")
    controller = Controller(campaign, "one_plus_lambda", initial_pool(campaign), "campaign")
    group = controller.ask()
    with pytest.raises(ValueError, match="every scheduled"):
        controller.tell([_evaluated(group[0], 1)])
    controller.tell([_evaluated(candidate, 9) for candidate in group])
    parent = controller.parent_id
    children = controller.ask()
    selection = controller.tell([_evaluated(candidate, 1, eligible=False) for candidate in reversed(children)])
    assert controller.parent_id == parent
    assert not selection["replaced"]
    assert controller.cache_hits == 1


def test_all_ineligible_initial_pool_has_no_handwritten_fallback():
    campaign = Campaign(name="Test")
    controller = Controller(campaign, "one_plus_lambda", initial_pool(campaign), "campaign")
    controller.tell([_evaluated(candidate, 1, eligible=False) for candidate in controller.ask()])
    assert controller.winner() is None
    assert controller.ask() == []
    assert controller.outcome == "NO_ELIGIBLE_INITIAL_PARENT"


def test_duplicate_exhaustion_is_bounded():
    spec = Campaign(name="Test").document()
    spec["generation"].update({"min_nodes": 1, "max_nodes": 1, "weights": {"RELAX": 1},
                               "repeat_probability": 0.0, "condition_probability": 0.0, "proposal_retries": 3})
    rejected = []
    with pytest.raises(ProgramError, match="exhausted"):
        initial_pool(Campaign.model_validate(spec), event=lambda kind, value: rejected.append(kind))
    assert rejected == ["PROPOSAL_DUPLICATE"] * 3


def test_scoring_keeps_early_stop_invalid_and_incomplete_denominators():
    rows = [{"initial_id": str(index), "replicate": "0", "episode_key": str(index), "eligible": True,
             "best_L": value, "charged_work": 10, "validation": {"status": "NUMERICALLY_VALIDATED"}, "termination": "STOPPED"}
            for index, value in enumerate((1., 10., 10.))]
    scored = score(rows, expected_count=3, instruction_count=1, program_hash="hash", thresholds=[5])
    assert scored["mean_best_L"] == 7
    assert scored["threshold_hits"] == {"5": 1}
    assert scored["eligible"]
    rows[0]["eligible"] = False
    rows[0]["validation"]["status"] = "INVALID"
    assert not score(rows, expected_count=3, instruction_count=1, program_hash="hash", thresholds=[])["eligible"]
    assert not score(rows[1:], expected_count=3, instruction_count=1, program_hash="hash", thresholds=[])["complete"]
