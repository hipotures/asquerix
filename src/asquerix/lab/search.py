"""Two bounded ask/evaluate/tell methods with JSON-resumable proposal streams."""

from __future__ import annotations

import copy
import hashlib
import random

from .config import Campaign, Generation
from .evaluation import best_eligible
from .strategy import Predicate, ProgramError, compile_program


def _weighted(rng: random.Random, weights: dict[str, int]) -> str:
    keys = sorted(weights)
    return rng.choices(keys, weights=[weights[key] for key in keys], k=1)[0]


def _number(rng: random.Random, interval) -> float:
    return rng.uniform(interval.minimum, interval.maximum)


def action(rng: random.Random, law: Generation, name=None) -> dict:
    op = _weighted(rng, law.weights) if name is None else name
    if op == "COMPRESS":
        return {"op": op, "target_reduction": None if rng.random() < law.legacy_target_probability else _number(rng, law.compress_fraction),
                "attempt_limit": rng.randint(law.attempt_min, law.attempt_max), "sweep_limit": rng.randint(law.sweep_min, law.sweep_max)}
    if op == "EXPAND":
        return {"op": op, "fraction": _number(rng, law.expand_fraction)}
    if op in ("MOVE", "ROTATE"):
        kind = rng.choice(law.selectors)
        selector = {"kind": kind}
        if kind != "ALL":
            selector["k"] = rng.randint(law.k_min, law.k_max)
        magnitude = "max_distance" if op == "MOVE" else "max_angle_rad"
        interval = law.move_distance if op == "MOVE" else law.rotate_angle_rad
        return {"op": op, "selector": selector, magnitude: _number(rng, interval),
                "repair_sweeps": rng.randint(law.sweep_min, law.sweep_max)}
    return {"op": op}


def generate(rng: random.Random, law: Generation) -> dict:
    body = []
    for _ in range(rng.randint(law.min_nodes, law.max_nodes)):
        node = action(rng, law)
        if rng.random() < law.repeat_probability:
            node = {"op": "REPEAT", "count": rng.randint(law.repeat_min, law.repeat_max), "body": [node]}
        if rng.random() < law.condition_probability:
            node = {"op": "IF", "predicate": rng.choice([predicate.name for predicate in Predicate]), "then": [node], "else": []}
        body.append(node)
    body.append({"op": "STOP"})
    return {"schema": "asquerix-strategy-v1", "name": "Generated world strategy", "body": body}


def _nodes(body: list, prefix="body") -> list[tuple[list, int, str]]:
    result = []
    for index, node in enumerate(body):
        if node["op"] == "STOP":
            continue
        path = f"{prefix}[{index}]"
        result.append((body, index, path))
        for key in ("body", "then", "else"):
            if key in node:
                result.extend(_nodes(node[key], path + "." + key))
    return result


def mutate(parent: dict, rng: random.Random, law: Generation) -> tuple[dict, dict]:
    child = copy.deepcopy(parent)
    child["name"] = "Mutated world strategy"
    kind = _weighted(rng, law.mutation_weights)
    available = _nodes(child["body"])
    if not available:
        kind = "insert"
    if kind == "parameter":
        available = [item for item in available if item[0][item[1]]["op"] in ("COMPRESS", "EXPAND", "MOVE", "ROTATE")]
    elif kind == "selector":
        available = [item for item in available if item[0][item[1]]["op"] in ("MOVE", "ROTATE")]
    if kind in ("parameter", "selector") and not available:
        raise ProgramError("mutation", f"no node available for {kind}")
    if kind == "insert":
        index = rng.randrange(len(child["body"]))
        node = action(rng, law)
        child["body"].insert(index, node)
        return child, {"type": kind, "node_path": f"body[{index}]", "before": None, "after": node}
    container, index, path = rng.choice(available)
    before = copy.deepcopy(container[index])
    node = container[index]
    if kind == "delete":
        del container[index]
        after = None
    elif kind == "replace":
        container[index] = action(rng, law)
        after = copy.deepcopy(container[index])
    elif kind == "repeat":
        if node["op"] == "REPEAT":
            node["count"] = rng.randint(law.repeat_min, law.repeat_max)
        else:
            container[index] = {"op": "REPEAT", "count": rng.randint(law.repeat_min, law.repeat_max), "body": [node]}
        after = copy.deepcopy(container[index])
    elif kind == "condition":
        if node["op"] == "IF":
            if rng.random() < .5:
                node["predicate"] = rng.choice([predicate.name for predicate in Predicate])
            else:
                node["then"], node["else"] = node.get("else", []), node["then"]
        else:
            container[index] = {"op": "IF", "predicate": rng.choice([predicate.name for predicate in Predicate]), "then": [node], "else": []}
        after = copy.deepcopy(container[index])
    elif kind == "selector":
        selector = rng.choice(law.selectors)
        node["selector"] = {"kind": selector}
        if selector != "ALL":
            node["selector"]["k"] = rng.randint(law.k_min, law.k_max)
        after = copy.deepcopy(node)
    else:
        replacement = action(rng, law, node["op"])
        fields = [field for field in replacement if field not in ("op", "selector")]
        field = rng.choice(fields)
        node[field] = replacement[field]
        after = copy.deepcopy(node)
    return child, {"type": kind, "node_path": path, "before": before, "after": after}


def initial_pool(campaign: Campaign, *, event=lambda kind, payload: None) -> list[dict]:
    rng = random.Random(int(campaign.search.seed) ^ 0xA5D13C2B9901)
    pool, hashes = [], set()
    for position in range(campaign.search.initial_pool):
        for retry in range(campaign.generation.proposal_retries):
            try:
                compiled = compile_program(generate(rng, campaign.generation))
            except ProgramError as error:
                event("PROPOSAL_REJECTED", {"phase": "shared_initial_pool", "position": position, "retry": retry, "reason": str(error)})
                continue
            if compiled.program_hash in hashes:
                event("PROPOSAL_DUPLICATE", {"phase": "shared_initial_pool", "position": position, "retry": retry, "hash": compiled.program_hash})
                continue
            hashes.add(compiled.program_hash)
            pool.append(compiled.document())
            break
        else:
            raise ProgramError("generator", "common initial pool exhausted its bounded proposal retries")
    return pool


class Controller:
    """A group barrier prevents GPU completion order from influencing selection.

    The controller keeps only what the search needs: the candidate count, the current incumbent or
    parent, the pending group and the hashes already proposed. Evaluated candidates are stored by the
    worker, so the checkpoint stays small however many programs a search tries.
    """

    def __init__(self, campaign: Campaign, method: str, shared_pool: list[dict], campaign_id: str,
                 *, state: dict | None = None, event=lambda kind, payload: None):
        if method not in campaign.search.methods:
            raise ValueError("Controller method is not in this frozen campaign")
        self.campaign, self.method, self.shared_pool, self.campaign_id = campaign, method, shared_pool, campaign_id
        self.event = event
        stream = int.from_bytes(hashlib.sha256(method.encode()).digest()[:8], "little")
        self.rng = random.Random(int(campaign.search.seed) ^ stream)
        self.count, self.pending, self.seen, self.parent = 0, [], set(), None
        self.generation, self.completed, self.cache_hits = 0, 0, 0
        self.outcome, self.proposal_count = "RUNNING", 0
        if state is not None:
            if state["method"] != method or state.get("schema") != "asquerix-search-controller-v2":
                raise ValueError("Controller checkpoint method or schema mismatch")
            random_state = state["rng_state"]
            self.rng.setstate((random_state[0], tuple(random_state[1]), random_state[2]))
            self.pending = copy.deepcopy(state["pending"])
            self.parent = copy.deepcopy(state["parent"])
            self.seen = set(state["seen"])
            for field in ("count", "generation", "completed", "cache_hits", "outcome", "proposal_count"):
                setattr(self, field, state[field])

    @property
    def parent_id(self) -> str | None:
        return self.parent["id"] if self.parent else None

    def checkpoint(self) -> dict:
        return {"schema": "asquerix-search-controller-v2", "method": self.method,
                "rng_state": self.rng.getstate(), "count": self.count, "pending": self.pending,
                "parent": self.parent, "seen": sorted(self.seen), "parent_id": self.parent_id,
                "generation": self.generation, "completed": self.completed, "cache_hits": self.cache_hits,
                "outcome": self.outcome, "proposal_count": self.proposal_count}

    def _candidate(self, program: dict, *, mutation=None, parent=None, origin="independent_generation") -> dict:
        position = self.count
        candidate = {"id": f"{self.campaign_id}:{self.method}:{position}", "arm": self.method,
                     "position": position, "generation": self.generation, "program": program,
                     "parent_id": parent["id"] if parent else None,
                     "parent_hash": parent["program"]["hash"] if parent else None,
                     "mutation": mutation, "origin": origin, "state": "PENDING", "score": {}}
        self.count += 1
        self.seen.add(program["hash"])
        self.pending.append(candidate)
        # The program text is stored with the candidate; the event carries its identity only.
        self.event("CANDIDATE_GENERATED", {key: candidate[key] for key in ("id", "arm", "position", "generation", "parent_id",
                                                                             "parent_hash", "mutation", "origin")}
                   | {"program_hash": program["hash"]})
        return candidate

    def ask(self) -> list[dict]:
        if self.pending:
            return list(self.pending)
        remaining = self.campaign.search.candidate_budget_per_method - self.count
        if remaining <= 0:
            self.outcome = "CANDIDATE_BUDGET_REACHED"
            return []
        if self.outcome != "RUNNING":
            return []
        if not self.count:
            return [self._candidate(program, origin="shared_initial_pool") for program in self.shared_pool[:remaining]]
        self.generation += 1
        parent = self.parent
        if self.method == "one_plus_lambda" and parent is None:
            self.outcome = "NO_ELIGIBLE_INITIAL_PARENT"
            return []
        # Mutation generations have lambda offspring; independent programs fill the batch capacity.
        size = self.campaign.effective_lambda() if self.method == "one_plus_lambda" else self.campaign.random_group_size()
        group = []
        for _ in range(min(size, remaining)):
            for retry in range(self.campaign.generation.proposal_retries):
                self.proposal_count += 1
                mutation = None
                try:
                    if self.method == "one_plus_lambda":
                        authored, mutation = mutate(parent["program"]["authored"], self.rng, self.campaign.generation)
                    else:
                        authored = generate(self.rng, self.campaign.generation)
                    compiled = compile_program(authored)
                except ProgramError as error:
                    self.event("PROPOSAL_REJECTED", {"arm": self.method, "generation": self.generation, "retry": retry,
                                                     "reason": str(error), "mutation": mutation})
                    continue
                if compiled.program_hash in self.seen:
                    self.event("PROPOSAL_DUPLICATE", {"arm": self.method, "generation": self.generation, "retry": retry,
                                                      "hash": compiled.program_hash, "mutation": mutation})
                    continue
                group.append(self._candidate(compiled.document(), mutation=mutation,
                                             parent=parent if self.method == "one_plus_lambda" else None,
                                             origin="mutation" if self.method == "one_plus_lambda" else "independent_generation"))
                break
            else:
                self.outcome = "GENERATOR_EXHAUSTED"
                self.event("SEARCH_EXHAUSTED", {"arm": self.method, "generation": self.generation})
                break
        return group

    def tell(self, evaluated: list[dict]) -> dict:
        if {candidate["id"] for candidate in evaluated} != {candidate["id"] for candidate in self.pending}:
            raise ValueError("Selection requires every scheduled offspring result at its group barrier")
        previous = self.parent
        self.completed += sum(bool(candidate.get("score", {}).get("complete")) for candidate in evaluated)
        self.pending = []
        choices = evaluated + ([previous] if previous else [])
        winner = best_eligible(choices)
        if previous and self.method == "one_plus_lambda":
            self.cache_hits += 1
        self.parent = copy.deepcopy(winner) if winner else None
        if self.generation == 0 and self.method == "one_plus_lambda" and winner is None:
            self.outcome = "NO_ELIGIBLE_INITIAL_PARENT"
        if any(not candidate.get("score", {}).get("complete") for candidate in evaluated):
            self.outcome = "INCOMPLETE_EVALUATION"
        selection = {"arm": self.method, "generation": self.generation,
                     "previous_parent_id": previous["id"] if previous else None,
                     "parent_id": self.parent_id, "replaced": bool(previous and winner and previous["id"] != winner["id"]),
                     "comparisons": [{"candidate_id": candidate["id"], "ranking_tuple": candidate.get("score", {}).get("ranking_tuple"),
                                      "eligible": candidate.get("score", {}).get("eligible", False)} for candidate in choices],
                     "reason": "Lexicographic minimum among complete independently valid candidates; cached parent included.",
                     "completed_candidates": self.completed, "cache_hits": self.cache_hits, "outcome": self.outcome}
        self.event("PARENT_SELECTION" if self.method == "one_plus_lambda" else "INCUMBENT_SELECTION", selection)
        return selection

    def winner(self) -> dict | None:
        return self.parent
