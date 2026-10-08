"""Diagnostic source-body replay with NumPy FP32 primitives, NOT Warp/CUDA.

This is an audit instrument, not a production CPU solver or benchmark. It
removes Warp decorators/type annotations and executes the existing function
bodies. Compiler transformations, FMA, device math, and performance are NOT
reproduced. Validate conclusions on the actual CUDA backend before merging.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np


class Record:
    floats = {"side", "min_gap", "min_wall", "max_penetration", "final_step"}
    ints = {"termination", "feasible", "attempts", "sweeps", "accepted", "rejected", "proposals"}

    def __init__(self):
        for key in self.floats | self.ints:
            setattr(self, key, 0)

    def __setattr__(self, key, value):
        super().__setattr__(key, np.float32(value) if key in self.floats else int(value))


def load_functions(source):
    tree = ast.parse(source)
    functions = []
    defaults = {}
    for item in tree.body:
        if isinstance(item, ast.ClassDef) and item.name == "Config":
            defaults = {field.target.id: ast.literal_eval(field.value)
                        for field in item.body if isinstance(field, ast.AnnAssign)}
        if isinstance(item, ast.FunctionDef) and item.name != "parameters":
            item.decorator_list = []
            item.returns = None
            for arg in item.args.args:
                arg.annotation = None
            functions.append(item)
    wp = SimpleNamespace(
        vec2=lambda *x: np.array(x, dtype=np.float32),
        vec3=lambda *x: np.array(x, dtype=np.float32),
        cos=np.cos, sin=np.sin, abs=np.abs, dot=np.dot,
        min=np.minimum, max=np.maximum, length=np.linalg.norm,
        isfinite=np.isfinite, uint64=np.uint64, tid=lambda: 0,
    )
    env = {"wp": wp, "float": np.float32, "int": int, "Result": Record}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "scalar_source_body", "exec"), env)
    return env, defaults


def vertex_check(poses, side):
    """Independent float64 vertex projections; not a rigorous certificate."""
    local = np.array([[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]])
    vertices = []
    for x, y, theta in np.asarray(poses, dtype=np.float64):
        c, s = np.cos(theta), np.sin(theta)
        vertices.append(local @ np.array([[c, s], [-s, c]]) + np.array([x, y]))
    vertices = np.asarray(vertices)
    wall = float(side / 2 - np.abs(vertices).max())
    gap = None
    for i in range(len(poses)):
        for j in range(i + 1, len(poses)):
            separation = -float("inf")
            for polygon in (vertices[i], vertices[j]):
                for edge in np.roll(polygon, -1, axis=0) - polygon:
                    axis = np.array([-edge[1], edge[0]]) / np.linalg.norm(edge)
                    p, q = vertices[i] @ axis, vertices[j] @ axis
                    separation = max(separation, q.min() - p.max(), p.min() - q.max())
            gap = float(separation) if gap is None else min(gap, float(separation))
    return {"min_wall_clearance": wall, "min_pair_separation": gap,
            "strictly_clear_at_1e-8": wall > 1e-8 and (gap is None or gap > 1e-8)}


def replay(source, document, *, step, attempts, sweeps):
    env, defaults = load_functions(source)
    pose = np.asarray(document["poses"], dtype=np.float32)
    if pose.shape != (document["n"], 3) or not np.isfinite(pose).all():
        raise ValueError("Expected finite (n,3) saved poses")
    if not 1 <= attempts <= 2048 or not 1 <= sweeps <= 2000 or not np.isfinite(step) or step <= 0:
        raise ValueError("Invalid diagnostic budget or compression step")
    defaults.update(n=len(pose), max_attempts=attempts, max_sweeps=sweeps)
    cfg = SimpleNamespace(**{k: np.float32(v) if isinstance(v, float) else v
                             for k, v in defaults.items()})
    accepted = pose[:, None, :].copy()
    work = np.zeros_like(accepted)
    result = Record()
    result.side = document["side"]
    result.final_step = step
    results = [result]
    trace = np.zeros((attempts, 1), dtype=np.float32)
    # Resume saved geometry, rather than regenerating an initial state.
    env["simulate"](cfg, 0, accepted, work, results, trace, 1, 1, attempts)
    result = results[0]
    final_pose = accepted[:, 0, :]
    scalars = {k: float(getattr(result, k)) for k in Record.floats}
    scalars.update({k: int(getattr(result, k)) for k in Record.ints})
    return {
        "method": "source-body NumPy FP32 diagnostic; NOT compiled Warp/CUDA",
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "trial_id": document.get("trial_id"), "n": len(pose),
        "initial_side": document["side"], "trial_step": step,
        "max_attempts": attempts, "max_sweeps": sweeps,
        "result": scalars, "poses": final_pose.tolist(),
        "validation": vertex_check(final_pose, float(result.side)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("src/asquerix/gpu.py"))
    parser.add_argument("--fixture", type=Path, default=Path(
        "artifacts/audit/campaign/retained-n11/poses/trial-4124.json"))
    parser.add_argument("--step", type=float, default=0.0001953125)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--sweeps", type=int, default=120)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = replay(args.source.read_text(), json.loads(args.fixture.read_text()),
                   step=args.step, attempts=args.attempts, sweeps=args.sweeps)
    text = json.dumps(value, indent=2, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
