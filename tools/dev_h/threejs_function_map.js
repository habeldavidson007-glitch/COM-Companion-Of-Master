#!/usr/bin/env node
/**
 * DEV H/S Function Map + Benchmark Loop Runner
 *
 * Outputs a Three.js-ready hierarchical map (root/directories/files/functions)
 * and optionally runs benchmark loops with increasing difficulty every 15 loops.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = process.cwd();
const IGNORE_DIRS = new Set(['.git', '__pycache__', '.pytest_cache', 'node_modules', 'venv', '.venv']);

function walk(dir, out = []) {
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const full = path.join(dir, item.name);
    const rel = path.relative(ROOT, full);
    if (item.isDirectory()) {
      if (IGNORE_DIRS.has(item.name)) continue;
      out.push({ type: 'dir', path: rel });
      walk(full, out);
    } else {
      out.push({ type: 'file', path: rel });
    }
  }
  return out;
}

function extractFunctions(filePath, content) {
  const ext = path.extname(filePath);
  const found = [];
  if (ext === '.py') {
    const rx = /^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(/gm;
    let m;
    while ((m = rx.exec(content)) !== null) found.push(m[1]);
  } else if (ext === '.js' || ext === '.ts') {
    const rx = /function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(|const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\(/gm;
    let m;
    while ((m = rx.exec(content)) !== null) found.push(m[1] || m[2]);
  }
  return found;
}

function buildMap() {
  const nodes = walk(ROOT);
  const tree = {
    root: path.basename(ROOT),
    generated_at: new Date().toISOString(),
    directories: [],
    files: [],
    stats: { dir_count: 0, file_count: 0, function_count: 0 },
  };

  for (const n of nodes) {
    if (n.type === 'dir') {
      tree.directories.push(n.path);
      tree.stats.dir_count += 1;
      continue;
    }

    const abs = path.join(ROOT, n.path);
    let size = 0;
    let functions = [];
    try {
      const st = fs.statSync(abs);
      size = st.size;
      if (size <= 512000) {
        const content = fs.readFileSync(abs, 'utf-8');
        functions = extractFunctions(n.path, content);
      }
    } catch (_) {}

    tree.files.push({ path: n.path, size_bytes: size, functions });
    tree.stats.file_count += 1;
    tree.stats.function_count += functions.length;
  }
  return tree;
}

function runBenchmark(strictMode) {
  const args = ['benchmark.py'];
  if (strictMode) args.push('--strict');
  return spawnSync('python', args, { encoding: 'utf-8' });
}

function deriveSuggestions(resultJson, loopIndex) {
  const suggestions = [];
  if (!resultJson) {
    suggestions.push('benchmark_results.json missing; ensure benchmark runner writes artifact.');
    return suggestions;
  }
  if (!resultJson.strict_pass) {
    suggestions.push('Enable dependency bootstrap before loop start (pydantic/pandas/tool deps).');
    suggestions.push('Keep strict mode default so crashed suites are blocking.');
  }
  if ((resultJson.suite_crashes || 0) > 0) {
    suggestions.push('Prioritize crash triage list first; no score optimization before crash count is zero.');
  }
  if ((loopIndex + 1) % 15 === 0) {
    suggestions.push('Increase difficulty gate: lower token budget 15% and require deterministic replay pass.');
  }
  suggestions.push('Track end-to-end: route -> context build -> LLM call -> execution -> logger metrics.');
  return suggestions;
}

function main() {
  const loops = Number(process.argv[2] || 1);
  const map = buildMap();
  fs.writeFileSync('threejs_function_map.json', JSON.stringify(map, null, 2));

  const loopSummary = [];
  for (let i = 0; i < loops; i++) {
    const strictMode = true;
    const res = runBenchmark(strictMode);

    let parsed = null;
    try {
      parsed = JSON.parse(fs.readFileSync('benchmark_results.json', 'utf-8'));
    } catch (_) {}

    loopSummary.push({
      loop: i + 1,
      strict_mode: strictMode,
      exit_code: res.status,
      suite_crashes: parsed?.suite_crashes ?? null,
      strict_pass: parsed?.strict_pass ?? null,
      suggestions: deriveSuggestions(parsed, i),
    });
  }

  const output = {
    generated_at: new Date().toISOString(),
    loops,
    map_file: 'threejs_function_map.json',
    summary: loopSummary,
  };
  fs.writeFileSync('threejs_benchmark_loop_report.json', JSON.stringify(output, null, 2));
  console.log('Generated: threejs_function_map.json');
  console.log('Generated: threejs_benchmark_loop_report.json');
}

main();
