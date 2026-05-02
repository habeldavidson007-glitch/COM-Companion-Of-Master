# Three.js Function Map + Benchmark Loop (Dev H/S)

This utility builds a Three.js-ready project map and runs strict benchmark loops.

## Files
- `tools/dev_h/threejs_function_map.js`
- Output map: `threejs_function_map.json`
- Output loop report: `threejs_benchmark_loop_report.json`

## What it does
1. Scans root, directories, and files (excluding known cache/vendor dirs).
2. Extracts lightweight function lists from `.py/.js/.ts` files.
3. Runs `benchmark.py --strict` in a loop.
4. Every loop writes health summary and improvement suggestions.
5. Every 15th loop adds harder guidance (lower budget + deterministic replay gate suggestion).
6. Classifies each loop blocker as `env`, `logic`, or `perf`, and tracks strict-pass streak + crash slope trend.

## Run
```bash
node tools/dev_h/threejs_function_map.js 30
```

## Why this helps
- Shared visual/system map for Dev H/S to verify coverage and connectivity.
- Repeated strict benchmark signal to catch regressions early.
- Heuristic suggestions keep focus on crash-first and end-to-end pipeline quality.
