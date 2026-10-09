"""Diagnose compiler changes caused by sharing trigonometric axis values."""
from pathlib import Path
import argparse
import numpy as np
import warp as wp
from asquerix import gpu
from kernel_benchmark import digest, load_source, save_json

baseline = None


@wp.kernel
def original(theta: wp.array(dtype=float), values: wp.array2d(dtype=float)):
    i = wp.tid()
    u, v = baseline.axes(theta[i])
    values[i, 0] = u[0]
    values[i, 1] = u[1]
    values[i, 2] = v[0]
    values[i, 3] = v[1]
    values[i, 4] = wp.dot(u, u)
    values[i, 5] = wp.dot(u, v)
    values[i, 6] = wp.dot(v, u)
    values[i, 7] = wp.dot(v, v)


@wp.kernel
def shared(theta: wp.array(dtype=float), values: wp.array2d(dtype=float)):
    i = wp.tid()
    u, v = gpu.axes(theta[i])
    values[i, 0] = u[0]
    values[i, 1] = u[1]
    values[i, 2] = v[0]
    values[i, 3] = v[1]
    values[i, 4] = wp.dot(u, u)
    values[i, 5] = wp.dot(u, v)
    values[i, 6] = wp.dot(v, u)
    values[i, 7] = wp.dot(v, v)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline-source', type=Path, required=True)
    parser.add_argument('--device', required=True)
    args = parser.parse_args()
    baseline = load_source(args.baseline_source, 'asquerix_axes_probe_baseline')
    wp.init()
    theta_host = np.random.default_rng(20261009).uniform(-10, 10, 65536).astype(np.float32)
    theta = wp.array(theta_host, dtype=float, device=args.device)
    results = []
    for kernel in (original, shared):
        output = wp.zeros((len(theta_host), 8), dtype=float, device=args.device)
        wp.launch(kernel, dim=len(theta_host), inputs=[theta, output], device=args.device, block_dim=32)
        wp.synchronize_device(args.device)
        results.append(output.numpy())
    a, b = results
    counts = np.sum(a.view(np.uint32) != b.view(np.uint32), axis=0)
    report = {'input_count':len(theta_host), 'columns':['u.x','u.y','v.x','v.y','dot(u,u)','dot(u,v)','dot(v,u)','dot(v,v)'],
              'differing_bit_patterns_per_column':counts.tolist()}
    report.update(device=args.device, device_uuid=wp.get_device(args.device).uuid)
    report.update(baseline_source_sha256=digest(args.baseline_source),
                  candidate_source_sha256=digest(gpu.__file__))
    print(f"Axis probe saved: {args.output}")
    save_json(args.output, report)
    np.savez_compressed(args.output.with_suffix('.npz'),
                        theta=theta_host, baseline=a, candidate=b)
