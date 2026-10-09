"""Diagnose compiler changes caused by sharing trigonometric axis values."""
from pathlib import Path
import argparse
import numpy as np
import warp as wp
from asquerix import gpu
from kernel_benchmark import load_source, save_json

baseline = load_source(Path(__file__).resolve().parents[1] / 'artifacts/performance/cuda-20261009/baseline/gpu.py',
                       'asquerix_axes_probe_baseline')


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
    args = parser.parse_args()
    wp.init()
    theta_host = np.random.default_rng(20261009).uniform(-10, 10, 65536).astype(np.float32)
    theta = wp.array(theta_host, dtype=float, device='cuda:0')
    results = []
    for kernel in (original, shared):
        output = wp.zeros((len(theta_host), 8), dtype=float, device='cuda:0')
        wp.launch(kernel, dim=len(theta_host), inputs=[theta, output], device='cuda:0', block_dim=32)
        wp.synchronize_device('cuda:0')
        results.append(output.numpy())
    a, b = results
    counts = np.sum(a.view(np.uint32) != b.view(np.uint32), axis=0)
    report = {'input_count':len(theta_host), 'columns':['u.x','u.y','v.x','v.y','dot(u,u)','dot(u,v)','dot(v,u)','dot(v,v)'],
              'differing_bit_patterns_per_column':counts.tolist()}
    print(report)
    save_json(args.output, report)
    np.savez_compressed(Path('runs/performance-cuda-20261009') / (args.output.stem + '.npz'),
                        theta=theta_host, baseline=a, candidate=b)
