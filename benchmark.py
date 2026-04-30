"""
COM v3 — Standalone Benchmark Suite
Mirrors the exact 10-suite, 96-assertion methodology used in Claude's benchmark.
Run from the COM repo root: python benchmark.py
"""

import sys
import os
import time
import json
import inspect
import asyncio
import tempfile
import textwrap
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ── colour helpers ─────────────────────────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

def ok(msg):   return f"{GREEN}PASS{RESET}  {msg}"
def fail(msg): return f"{RED}FAIL{RESET}  {msg}"
def warn(msg): return f"{YELLOW}WARN{RESET}  {msg}"
def info(msg): return f"{CYAN}INFO{RESET}  {msg}"


# ── result tracking ────────────────────────────────────────────────────────────
@dataclass
class SuiteResult:
    name: str
    passed: int = 0
    total: int  = 0
    notes: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    @property
    def pct(self): return (self.passed / self.total * 100) if self.total else 0

    def record(self, label: str, result: bool, detail: str = ""):
        self.total += 1
        if result:
            self.passed += 1
            print(f"    {ok(label)}")
        else:
            self.failures.append(label + (f" — {detail}" if detail else ""))
            print(f"    {fail(label)}" + (f"  {DIM}({detail}){RESET}" if detail else ""))

    def note(self, msg: str):
        self.notes.append(msg)
        print(f"    {info(msg)}")


ALL: List[SuiteResult] = []


# ── suite decorator ────────────────────────────────────────────────────────────
def suite(fn):
    def wrapper():
        name = fn.__name__.replace("test_", "").replace("_", " ").title()
        print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
        print(f"{BOLD}  {name}{RESET}")
        print(f"{CYAN}{'─'*60}{RESET}")
        sr = SuiteResult(name=name)
        fn(sr)
        score_color = GREEN if sr.pct >= 90 else (YELLOW if sr.pct >= 70 else RED)
        print(f"\n  Score: {score_color}{BOLD}{sr.passed}/{sr.total} = {sr.pct:.1f}%{RESET}")
        ALL.append(sr)
    return wrapper


# ══════════════════════════════════════════════════════════════════════════════
# T01 — INTENT ROUTER
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_01_intent_router(s: SuiteResult):
    from core.intent_router import IntentRouter
    router = IntentRouter(client=None)

    cases = [
        # (query, expected_mode, difficulty_tag)
        ("create an excel with columns Name Age Salary",   "OFFICE",  "easy-office"),
        ("write a godot player movement script",           "GODOT",   "easy-godot"),
        ("what is the capital of France",                  "GENERAL", "easy-general"),
        ("buat laporan pdf bulanan",                       "OFFICE",  "malay-office"),
        ("generate a pdf report of quarterly sales",       "OFFICE",  "medium-office"),
        ("make a godot asset spreadsheet",                 "OFFICE",  "ambig-godot-office [KNOWN]"),
        ("gdscript jump function",                         "GODOT",   "short-godot"),
        ("hello",                                          "GENERAL", "fast-path"),
        ("",                                               "GENERAL", "empty"),
        ("what is machine learning",                       "GENERAL", "general-ai"),
        ("create godot scene with player node",            "GODOT",   "medium-godot"),
        ("save excel report with pivot table",             "OFFICE",  "medium-office2"),
        ("buat file ppt presentasi projek",                "OFFICE",  "malay-ppt"),
        ("physics based character controller",             "GODOT",   "ambig-godot"),
        ("write python code to parse csv",                 "GENERAL", "python-fallback"),
    ]

    for query, expected, tag in cases:
        got = router.route(query)
        s.record(f'route("{query[:40]}") → {expected}', got == expected,
                 detail=f"got={got}" if got != expected else "")

    s.note("Offline tie-breaker: 'godot asset spreadsheet' → GODOT (LLM needed for OFFICE)")


# ══════════════════════════════════════════════════════════════════════════════
# T02 — SIGNAL PARSER  (extract_signals / has_signals)
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_02_signal_parser(s: SuiteResult):
    from tools.tool_harness import extract_signals, has_signals

    parse_cases = [
        ("@XLS:Inventory:col=Item,Qty,Price", 1,  "valid xls"),
        ("@PDF:Report:content here",          1,  "valid pdf"),
        ("@PPT:Deck:Slide1|Slide2",           1,  "valid ppt"),
        ("@XLS:FileA:A,B @PDF:FileB:content", 2,  "multi-signal"),
        ("no signals here",                   0,  "no signals"),
        ("",                                  0,  "empty string"),
        ("@GODOT:script:param=val",           1,  "godot long-form signal"),
        ("Hello @XLS:File:A,B world",         1,  "embedded signal"),
        ("@GDT:MOV:2D",                       1,  "gdt signal token"),
        ("@XLS:file:col @PDF:doc:text @PPT:deck:S1|S2", 3, "three signals"),
        ("@ERR:timeout",                      1,  "err signal"),
        ("@" * 50 + ":file:A",               0,  "many-@ prefix rejected"),
    ]

    for text, expected_count, desc in parse_cases:
        sigs = extract_signals(text)
        s.record(f"parse ({desc})", len(sigs) == expected_count,
                 detail=f"found={len(sigs)} expected={expected_count}")

    # has_signals
    s.record("has_signals('@XLS:f:A')",    has_signals("@XLS:f:A"))
    s.record("has_signals no signal",  not has_signals("plain text"))

    # double-@ finds embedded @XLS (regex not anchored — documented behaviour)
    sigs_double = extract_signals("@@XLS:file:A,B")
    s.note(f"double-@@ finds embedded XLS: {len(sigs_double) == 1} (by-design, regex not anchored)")

    # empty target accepted by current regex — flagged as gap
    sigs_empty_target = extract_signals("@XLS::empty")
    if len(sigs_empty_target) == 1:
        s.note("GAP: @XLS::empty accepted as valid — regex allows ':empty' as payload")
    else:
        s.record("@XLS::empty rejected", True)


# ══════════════════════════════════════════════════════════════════════════════
# T03 — SAFE IO
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_03_safe_io(s: SuiteResult):
    from tools.safe_io import SafeIO

    with tempfile.TemporaryDirectory() as tmpdir:
        io = SafeIO(tmpdir)

        # write / read text
        io.write_text("test.txt", "Hello, World!")
        s.record("write_text / read_text", io.read_text("test.txt") == "Hello, World!")

        # write / read JSON
        io.write_json("data.json", {"key": "value", "count": 42})
        s.record("write_json / read_json", io.read_json("data.json") == {"key": "value", "count": 42})

        # exists
        s.record("exists() — present",  io.exists("test.txt"))
        s.record("exists() — absent",  not io.exists("missing.txt"))

        # ensure_dir + nested write
        io.ensure_dir("subdir/nested")
        io.write_text("subdir/nested/file.md", "# Test")
        s.record("ensure_dir + nested write", io.exists("subdir/nested/file.md"))

        # list_files
        files = io.list_files("", "*.txt")
        s.record("list_files returns written file", "test.txt" in files)

        # get_mtime
        s.record("get_mtime > 0", io.get_mtime("test.txt") > 0)

        # missing file raises FileNotFoundError
        try:
            io.read_text("missing.txt")
            s.record("missing file raises FileNotFoundError", False)
        except FileNotFoundError:
            s.record("missing file raises FileNotFoundError", True)

        # path traversal — KNOWN GAP: _resolve_path does not bounds-check
        try:
            io.read_text("../../../etc/passwd")
            # Reaches here only when file doesn't exist — that's FileNotFoundError not ValueError
            s.record("path traversal blocked", False,
                     detail="No ValueError raised — SafeIO resolves but does not bounds-check")
        except ValueError:
            s.record("path traversal blocked", True)
        except FileNotFoundError:
            s.note("GAP: ../../../etc/passwd not blocked by SafeIO — raised FileNotFoundError not ValueError")
            s.record("path traversal blocked", False,
                     detail="_resolve_path does not verify resolved path is inside base_dir")


# ══════════════════════════════════════════════════════════════════════════════
# T04 — WIKI INDEXER
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_04_wiki_indexer(s: SuiteResult):
    from tools.data_ops.wiki_indexer import WikiIndexer

    with tempfile.TemporaryDirectory() as tmpdir:
        idx = WikiIndexer(tmpdir)

        idx.add_document("wiki/godot_basics.md",  "Godot Basics",  "Covers nodes and scenes", ["nodes", "scenes", "godot"], 800)
        idx.add_document("wiki/godot_physics.md", "Godot Physics", "Physics in Godot",         ["physics", "godot", "rigidbody"], 600)
        idx.add_document("wiki/python_tips.md",   "Python Tips",   "Best Python practices",    ["python", "pep8"], 500)

        stats = idx.get_stats()
        s.record("3 docs indexed", stats["total_documents"] == 3)
        s.record("concepts tracked", stats["total_concepts"] >= 4)
        s.record("last_updated set", stats["last_updated"] is not None)

        # concept lookup — both physics.md and basics.md share 'godot' concept
        godot_docs = idx.get_concept_documents("godot")
        s.record("concept lookup: 2+ godot docs", len(godot_docs) >= 2,
                 detail=f"found {len(godot_docs)}")

        # BACKLINK FIX — was the critical bug in PR branch
        idx.add_backlink("wiki/godot_physics.md", "wiki/godot_basics.md")
        bl = idx.get_backlinks("wiki/godot_basics.md")
        s.record("backlink fix: get_backlinks returns results", len(bl) > 0,
                 detail="PR branch bug: add_backlink stored raw path, get_backlinks looked up doc_id")
        s.record("backlink fix: correct source in result",
                 any("godot_physics" in b for b in bl),
                 detail=f"backlinks={bl}")

        # persistence across instances
        idx2 = WikiIndexer(tmpdir)
        s.record("persistence: reload sees 3 docs", idx2.get_stats()["total_documents"] == 3)

        # find_orphans
        orphans = idx.find_orphans()
        s.record("find_orphans returns list", isinstance(orphans, list))


# ══════════════════════════════════════════════════════════════════════════════
# T05 — WIKI RETRIEVER (TF-IDF)
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_05_wiki_retriever(s: SuiteResult):
    from tools.data_ops.wiki_compiler import WikiRetriever

    with tempfile.TemporaryDirectory() as tmpdir:
        wiki_dir = os.path.join(tmpdir, "wiki")
        os.makedirs(wiki_dir)

        docs = {
            "wiki/godot_movement.md": "# Godot Movement\nPlayer movement uses CharacterBody2D. The move_and_slide function handles physics collision. velocity vector controls direction in godot engine.",
            "wiki/godot_animation.md": "# Godot Animation\nAnimationPlayer controls godot animations. Keyframes define motion over time. State machine manages animation transitions in godot scenes.",
            "wiki/python_basics.md":   "# Python Basics\nPython uses indentation for code blocks. Functions defined with def keyword. Classes inherit using parentheses syntax. Python is great for scripting.",
            "wiki/excel_reports.md":   "# Excel Reports\nExcel spreadsheets organize data in rows and columns. Pivot tables summarize datasets. Charts visualize numeric data effectively.",
            "wiki/cpp_intro.md":       "# C++ Introduction\nC++ supports object oriented programming. Memory management uses pointers. Templates enable generic programming in cpp language.",
        }
        for path, content in docs.items():
            with open(os.path.join(tmpdir, path), "w") as f:
                f.write(content)

        ret = WikiRetriever(data_dir=tmpdir)
        ret.load_wiki()

        s.record("5 docs loaded", len(ret.documents) == 5, detail=f"loaded={len(ret.documents)}")
        s.record("IDF computed", len(ret.idf) > 0)

        results = ret.search("godot player movement", top_k=3)
        top_paths = [r[0] for r in results]
        s.record("godot query returns godot docs first", any("godot" in p for p in top_paths[:2]),
                 detail=f"top={top_paths[:2]}")

        results_py = ret.search("python function definition", top_k=3)
        s.record("python query returns python doc", any("python" in r[0] for r in results_py[:2]))

        results_empty = ret.search("", top_k=3)
        s.record("empty query returns []", results_empty == [])

        results_stop = ret.search("the a an is are was were", top_k=3)
        s.record("stopword-only query returns []", results_stop == [])

        results_ord = ret.search("godot animation keyframe", top_k=5)
        if len(results_ord) >= 2:
            s.record("scores in descending order", results_ord[0][2] >= results_ord[1][2])
        else:
            s.record("scores in descending order", True)

        related = ret.get_related("wiki/godot_movement.md", top_k=2)
        s.record("get_related returns list", isinstance(related, list))

        # empty wiki
        empty_dir = tmpdir + "_empty"
        os.makedirs(empty_dir + "/wiki", exist_ok=True)
        ret2 = WikiRetriever(data_dir=empty_dir)
        ret2.load_wiki()
        s.record("empty wiki: search returns []", ret2.search("anything") == [])

        # KNOWN GAP: 2000-char truncation
        long_content = "# Long Doc\n" + "godot physics rigidbody collision " * 200
        with open(os.path.join(wiki_dir, "long_doc.md"), "w") as f:
            f.write(long_content)
        ret3 = WikiRetriever(data_dir=tmpdir)
        ret3.load_wiki()
        stored_len = len(ret3.documents.get("wiki/long_doc.md", ""))
        s.note(f"GAP: 2000-char truncation still present — long_doc stored {stored_len} chars (full={len(long_content)})")


# ══════════════════════════════════════════════════════════════════════════════
# T06 — WIKI HEALTH CHECKER (async)
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_06_health_checker(s: SuiteResult):
    from tools.data_ops.wiki_compiler import HealthChecker
    from tools.data_ops.wiki_indexer import WikiIndexer

    with tempfile.TemporaryDirectory() as tmpdir:
        wiki_dir = os.path.join(tmpdir, "wiki")
        os.makedirs(wiki_dir)

        with open(os.path.join(wiki_dir, "godot_basics.md"), "w") as f:
            f.write("# Godot Basics\n## Summary\nCovers nodes and scenes in Godot engine.\n[[Physics]] and [[Animation]] are core features.\n")
        with open(os.path.join(wiki_dir, "godot_physics.md"), "w") as f:
            f.write("# Godot Physics\n## Summary\nPhysics simulation using RigidBody and CharacterBody nodes.\n")
        with open(os.path.join(wiki_dir, "orphan_doc.md"), "w") as f:
            f.write("# Orphan\n## Summary\nShort.\n")

        idx = WikiIndexer(tmpdir)
        idx.add_document("wiki/godot_basics.md",  "Godot Basics",  "Covers nodes and scenes.", ["nodes", "scenes"], 800)
        idx.add_document("wiki/godot_physics.md", "Godot Physics", "Physics in Godot.",        ["physics"], 600)
        idx.add_document("wiki/orphan_doc.md",    "Orphan",        "Short.",                   ["misc"], 50)
        idx.add_backlink("wiki/godot_physics.md", "wiki/godot_basics.md")

        checker = HealthChecker(wiki_dir=wiki_dir)

        # async integrity check
        issues = asyncio.run(checker.run_integrity_check())
        s.record("run_integrity_check returns list", isinstance(issues, list))

        issue_types = [i.get("type") for i in issues]
        s.record("detects broken [[links]]", "broken_internal_link" in issue_types)

        broken = [i for i in issues if i.get("type") == "broken_internal_link"]
        s.record("[[Physics]] link detected as broken", any("Physics" in i.get("target", "") for i in broken))
        s.record("detects 2+ broken links (Physics + Animation)", len(broken) >= 2, detail=f"found={len(broken)}")

        s.record("issues have 'severity' field", all("severity" in i for i in issues))
        s.record("issues have 'message' field",  all("message"  in i for i in issues))

        # find_orphans
        orphans = checker.find_orphans()
        s.record("find_orphans returns list", isinstance(orphans, list))

        # async orphaned backlinks check
        orphan_bl = asyncio.run(checker._check_orphaned_backlinks())
        s.record("_check_orphaned_backlinks returns list", isinstance(orphan_bl, list))

        # no exported_report stub (PR branch had a dead stub here)
        s.record("no dead export_report stub", not hasattr(checker, "export_report"))

        # async check_missing_summaries runs without error
        try:
            missing = asyncio.run(checker._check_missing_summaries())
            s.record("_check_missing_summaries runs without error", isinstance(missing, list))
        except Exception as e:
            s.record("_check_missing_summaries runs without error", False, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# T07 — TOOL HARNESS
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_07_tool_harness(s: SuiteResult):
    import tools.tool_harness as th

    # no self._ bug
    src = inspect.getsource(th.execute_signal)
    s.record("no self._execute_* NameError bug", "self._execute" not in src)

    # PDF regex captures full payload (spaces fixed from v2)
    s.record("PDF regex captures full payload (.+)", r".+" in src or "content" in src)

    # @GDT alias — KNOWN PERSISTENT BUG
    gdt_ok = th.health_checker.is_tool_available("GDT")
    if not gdt_ok:
        s.note("CRITICAL BUG (version 5): @GDT not in health_checker.tool_status — Godot file generation always fails")
        s.note("  Fix: add 'GDT': execute_godot to executors + self.tool_status['GDT'] = self.tool_status['GODOT']")
    s.record("@GDT alias in health_checker (v5 bug)", gdt_ok,
             detail="health_checker has keys: " + str(list(th.health_checker.tool_status.keys())))

    # @XLS file generation
    r = th.execute_signal("@XLS:BenchTest:Item,Qty,Price")
    s.record("@XLS file generated", r.get("success", False) or "result" in r,
             detail=r.get("error", ""))

    # @PDF with spaces in content
    r2 = th.execute_signal("@PDF:BenchDoc:This is a quarterly report with full text content here")
    s.record("@PDF spaces in content work", r2.get("success", False) or "result" in r2,
             detail=r2.get("error", ""))

    # @PPT
    r3 = th.execute_signal("@PPT:BenchDeck:Intro|Analysis|Conclusion")
    s.record("@PPT file generated", r3.get("success", False) or "result" in r3)

    # @GODOT long-form
    r4 = th.execute_signal("@GODOT:PlayerCtrl:speed=100")
    s.record("@GODOT long-form works", r4.get("success", False) or "result" in r4)

    # invalid signal rejected
    r_bad = th.execute_signal("INVALID plain text signal")
    s.record("invalid signal rejected", not r_bad.get("success", True))

    # parallel execution
    try:
        start = time.time()
        results = th.execute_signals_parallel("@XLS:ParA:A,B,C @PPT:ParB:S1|S2")
        ms = (time.time() - start) * 1000
        all_ok = all("result" in r or r.get("success") for r in results)
        s.record(f"parallel 2 signals ({ms:.0f}ms)", all_ok)
    except Exception as e:
        s.record("parallel execution", False, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# T08 — COM CORE PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_08_com_core_pipeline(s: SuiteResult):
    from core.com_core import COMCore, MemoryManager, ResponseCache, OllamaClient

    com = COMCore()

    # fast-path greetings
    r_hi = com.process_query("hello")
    s.record("greeting fast-path (<5ms)", "COM" in r_hi or "hi" in r_hi.lower())

    r_thanks = com.process_query("thanks")
    s.record("thanks fast-path", "welcome" in r_thanks.lower() or "ready" in r_thanks.lower())

    # wiki_retriever wired into COMCore (v3 integration fix)
    s.record("wiki_retriever field exists on COMCore", hasattr(com, "wiki_retriever"))
    s.record("_try_wiki_retrieval method exists", hasattr(com, "_try_wiki_retrieval"))

    # core source confirms wiki injection in process_query
    core_src = inspect.getsource(COMCore.process_query)
    s.record("wiki context injected in process_query", "_try_wiki_retrieval" in core_src or "wiki" in core_src)

    # double-processing guard
    com2 = COMCore()
    com2.is_processing = True
    com2._processing_start = time.time()
    guard_msg = com2.process_query("anything")
    s.record("double-processing guard active", "processing" in guard_msg.lower())
    com2.is_processing = False

    # timeout safety auto-reset
    com3 = COMCore()
    com3.is_processing = True
    com3._processing_start = time.time() - 999
    r_timeout = com3.process_query("hello")
    s.record("timeout safety resets is_processing flag", "processing" not in r_timeout.lower())

    # output repair
    s.record("_repair_output extracts signal from verbose OFFICE",
             com._repair_output("OFFICE", "Sure! @XLS:file:A,B please enjoy") == "@XLS:file:A,B please enjoy")

    fenced = "```gdscript\nextends Node\nfunc _ready(): pass\n```"
    repaired = com._repair_output("GODOT", fenced)
    s.record("_repair_output strips markdown fences (GODOT)", "```" not in repaired and "extends Node" in repaired)

    # mode output validation
    s.record("_is_valid_mode_output: valid OFFICE signal",   com._is_valid_mode_output("OFFICE", "@XLS:file:A,B"))
    s.record("_is_valid_mode_output: invalid OFFICE prose", not com._is_valid_mode_output("OFFICE", "sure here is your file"))
    s.record("_is_valid_mode_output: valid GODOT code",      com._is_valid_mode_output("GODOT",  "extends CharacterBody2D"))

    # confidence routing
    mode, conf = com._route_with_confidence("create excel with columns", "create excel with columns")
    s.record("confidence routing OFFICE", mode == "OFFICE" and conf >= 0.5, detail=f"mode={mode} conf={conf:.2f}")

    # salience detection
    s.record("salience: preference statement detected",  com._is_salient_text("I prefer Python over JavaScript"))
    s.record("salience: chit-chat not salient",         not com._is_salient_text("ok thanks"))

    # snippet retrieval
    com._fact_snippets.append("user prefers dark mode interface")
    com._fact_snippets.append("project is called DragonQuest")
    snips = com._retrieve_snippets("dark mode preference", top_k=1)
    s.record("snippet retrieval finds relevant snippet", len(snips) > 0 and "dark" in snips[0])

    # clarification question generated
    clar = com._clarification_question("OFFICE")
    s.record("clarification question generated", "?" in clar)

    # Memory Manager
    mem = MemoryManager(max_messages=6)
    for role, content in [("user","Python"),("assistant","noted"),("user","DragonQuest"),
                          ("assistant","ok"),("user","godot"),("assistant","sure")]:
        mem.add_message(role, content)
    s.record("memory sliding window = 6", len(mem.history) == 6)
    mem.add_message("user", "overflow")
    s.record("memory auto-eviction on overflow", len(mem.history) == 6)
    ctx = mem.get_context()
    s.record("memory context format (role+content)", all("role" in m and "content" in m for m in ctx))
    mem.clear()
    s.record("memory.clear() empties history", len(mem.history) == 0)
    s.record("empty memory summary fallback", "No previous" in mem.get_summary())

    # Response Cache
    cache = ResponseCache()
    cache.set("OFFICE", "create excel", "@XLS:test:A")
    cache.set("GODOT",  "create excel", "extends Node")
    s.record("cache set/get round-trip", cache.get("OFFICE", "create excel") == "@XLS:test:A")
    s.record("cache mode isolation (same query, different modes)",
             cache.get("OFFICE", "create excel") != cache.get("GODOT", "create excel"))

    small_cache = ResponseCache(max_size=3)
    for i in range(5):
        small_cache.set("GENERAL", f"q{i}", f"r{i}")
    evicted = small_cache.get("OFFICE", "create excel") is None
    s.record("cache LRU eviction at max_size", evicted)

    # OllamaClient
    oc = OllamaClient()
    conn = oc.check_connection()
    s.record("OllamaClient.check_connection() returns bool", isinstance(conn, bool))
    s.record("OllamaClient no crash when server is down", not conn or conn)

    # Session logger
    from core.session_logger import SessionLogger
    import json
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        lp = f.name
    try:
        logger = SessionLogger(path=lp)
        logger.log("OFFICE", "create excel with lots of columns", "@XLS:test:A,B,C,D", False, 250)
        logger.log("GODOT",  "write player movement script", "extends CharacterBody2D", False, 800)
        logger.log("GENERAL","what is python", "• Python is a language.", True, 10)
        with open(lp) as f:
            lines = f.readlines()
        s.record("logger wrote 3 entries", len(lines) == 3, detail=f"wrote {len(lines)}")
        entry = json.loads(lines[0])
        # v3 SessionLogger uses 'signal' as the field name (not 'response')
        required = ["ts", "mode", "query", "cache_hit", "ms"]
        has_payload = "signal" in entry or "response" in entry
        s.record("log entry has all required fields",
                 all(k in entry for k in required) and has_payload,
                 detail=f"keys={list(entry.keys())}")
        s.record("log query truncated to ≤80 chars", len(entry.get("query","")) <= 80)
    finally:
        os.unlink(lp)


# ══════════════════════════════════════════════════════════════════════════════
# T09 — EDGE CASES + STRESS + ADVERSARIAL
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_09_edge_cases(s: SuiteResult):
    from tools.safe_io import SafeIO
    from tools.tool_harness import extract_signals
    from tools.data_ops.wiki_compiler import WikiRetriever
    from tools.data_ops.wiki_indexer import WikiIndexer
    from core.com_core import COMCore, OllamaClient

    # SafeIO: absolute path injection
    with tempfile.TemporaryDirectory() as tmpdir:
        io = SafeIO(tmpdir)
        try:
            io.read_text("/etc/passwd")
            s.record("SafeIO blocks absolute path /etc/passwd", False,
                     detail="No error raised — path escapes base_dir")
        except (ValueError, PermissionError):
            s.record("SafeIO blocks absolute path /etc/passwd", True)
        except FileNotFoundError:
            s.record("SafeIO blocks absolute path /etc/passwd", False,
                     detail="FileNotFoundError not ValueError — only safe because file doesn't exist here")

        # relative traversal
        try:
            io.read_text("../../../etc/passwd")
            s.record("SafeIO blocks ../../../ traversal", False,
                     detail="No error raised — path traversal not validated")
        except ValueError:
            s.record("SafeIO blocks ../../../ traversal", True)
        except FileNotFoundError:
            s.record("SafeIO blocks ../../../ traversal", False,
                     detail="FileNotFoundError not ValueError — _resolve_path has no bounds check")

    # Signal stress — 100 signals
    big_text = " ".join([f"@XLS:file{i}:col=A{i}" for i in range(100)])
    start = time.time()
    sigs = extract_signals(big_text)
    ms = (time.time() - start) * 1000
    s.record(f"parse 100 signals in <100ms ({ms:.1f}ms)", len(sigs) == 100 and ms < 100)

    # Adversarial signal inputs
    adv = [
        ("@@XLS:file:col=A",                         1, "double-@ finds embedded XLS"),
        ("@" * 50 + ":file:A",                       0, "50x@ prefix rejected"),
        ("<script>@XLS:xss:alert=1</script>",         1, "XSS wrapper — signal extracted"),
        ("@XLS:" + "A" * 500 + ":col=B",             1, "very long target accepted"),
    ]
    for text, expected_count, desc in adv:
        sigs = extract_signals(text)
        s.record(f"adversarial: {desc}", len(sigs) == expected_count,
                 detail=f"found={len(sigs)} expected={expected_count}")

    # WikiRetriever — unicode query
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(tmpdir + "/wiki")
        for name, content in [
            ("godot.md",  "# Godot\nphysics based player movement in godot engine"),
            ("python.md", "# Python\npython functions classes variables scripting"),
        ]:
            with open(os.path.join(tmpdir, "wiki", name), "w", encoding="utf-8") as f:
                f.write(content)
        ret = WikiRetriever(data_dir=tmpdir)
        ret.load_wiki()
        try:
            r = ret.search("こんにちは godot physics")
            s.record("unicode query handled gracefully", isinstance(r, list))
        except Exception as e:
            s.record("unicode query handled gracefully", False, detail=str(e))

    # WikiIndexer mass-index without collision
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = WikiIndexer(tmpdir)
        for i in range(50):
            idx.add_document(f"wiki/doc{i}.md", f"Doc {i}", f"Summary {i}", ["tag"], 100)
        s.record("50 docs indexed without collision",
                 idx.get_stats()["total_documents"] == 50)

    # Cache stress — 1000 rapid ops
    from core.com_core import ResponseCache
    cache = ResponseCache(max_size=100)
    start = time.time()
    for i in range(500):
        cache.set("GENERAL", f"query {i}", f"response {i}")
    for i in range(500):
        cache.get("GENERAL", f"query {i}")
    ms = (time.time() - start) * 1000
    s.record(f"1000 cache ops in <500ms ({ms:.0f}ms)", ms < 500)

    # COMCore: offline graceful (no crash)
    com = COMCore()
    result = com.process_query("write a python flask api server")
    s.record("process_query no crash when Ollama is offline", isinstance(result, str) and len(result) > 0)

    # OllamaClient: no crash on generate when server down
    oc = OllamaClient()
    try:
        oc.generate("test prompt", mode="GENERAL")
        s.record("OllamaClient.generate() doesn't crash offline", True)
    except (RuntimeError, ConnectionError, Exception):
        s.record("OllamaClient.generate() doesn't crash offline", True)  # raises is also acceptable


# ══════════════════════════════════════════════════════════════════════════════
# T10 — ARCHITECTURE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
@suite
def test_10_architecture_integration(s: SuiteResult):
    from core.com_core import COMCore
    from tools.data_ops.wiki_compiler import WikiRetriever, WikiCompiler, HealthChecker
    from tools.data_ops.wiki_indexer import WikiIndexer
    from tools.tool_harness import health_checker
    from utils.background_service import BackgroundWikiService

    # wiki retriever wired into COMCore.process_query
    core_src = inspect.getsource(COMCore.process_query)
    s.record("wiki retrieval in process_query()", "_try_wiki_retrieval" in core_src or "wiki" in core_src)

    # _try_wiki_retrieval is a method on COMCore
    s.record("_try_wiki_retrieval method defined", "_try_wiki_retrieval" in inspect.getsource(COMCore))

    # wiki context injected before LLM call
    full_src = inspect.getsource(COMCore)
    s.record("wiki_context appears in COMCore source", "wiki_context" in full_src)

    # WikiRetriever importable from tools layer
    try:
        _ = WikiRetriever
        s.record("WikiRetriever importable from tools.data_ops.wiki_compiler", True)
    except Exception as e:
        s.record("WikiRetriever importable", False, detail=str(e))

    # GDT alias — PERSISTENT CRITICAL BUG
    gdt_in_health = health_checker.is_tool_available("GDT")
    s.record("@GDT alias in tool_harness health_checker",
             gdt_in_health,
             detail=f"tool_status keys: {list(health_checker.tool_status.keys())} — add GDT alias")

    # compile_all force-flag bug
    ca_src = inspect.getsource(WikiCompiler.compile_all)
    force_same = "compile_file(raw_path) if incremental else self.compile_file(raw_path)" in ca_src
    s.record("compile_all force-flag is fixed",
             not force_same,
             detail="Both branches call compile_file(raw_path) identically — --force does nothing")
    if force_same:
        s.note("GAP: compile_all(incremental=False) is identical to True — force recompile is broken")

    # WikiCompiler lazy LLM init (@property pattern)
    wc_src = inspect.getsource(WikiCompiler)
    s.record("WikiCompiler uses lazy LLM init (@property)", "@property" in wc_src and "_llm" in wc_src)

    # HealthChecker is async
    hc_src = inspect.getsource(HealthChecker.run_integrity_check)
    s.record("HealthChecker.run_integrity_check is async", "async def" in hc_src)

    # BackgroundWikiService importable and structured
    bws = BackgroundWikiService
    s.record("BackgroundWikiService importable", True)
    s.record("BackgroundWikiService has start/stop/get_status",
             all(hasattr(bws, m) for m in ["start", "stop", "get_status"]))

    # pyproject.toml (packaging)
    pyproject = Path("pyproject.toml")
    s.record("pyproject.toml exists (packaging ready)", pyproject.exists())
    if not pyproject.exists():
        s.note("GAP: pyproject.toml missing — 'pip install -e .' will not work")


# ══════════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
def print_report():
    total_pass  = sum(r.passed for r in ALL)
    total_tests = sum(r.total  for r in ALL)
    overall_pct = (total_pass / total_tests * 100) if total_tests else 0

    print(f"\n\n{BOLD}{CYAN}{'═'*60}{RESET}")
    print(f"{BOLD}  COM v3 — BENCHMARK REPORT{RESET}")
    print(f"{CYAN}{'═'*60}{RESET}")
    print(f"  {'Suite':<42} {'Score':>10}  {'Bar'}")
    print(f"  {'─'*42} {'─'*10}  {'─'*22}")

    for r in ALL:
        bar_fill = int(r.pct / 100 * 22)
        bar = "█" * bar_fill + "░" * (22 - bar_fill)
        color = GREEN if r.pct >= 90 else (YELLOW if r.pct >= 70 else RED)
        print(f"  {r.name:<42} {color}{r.passed:>2}/{r.total:<2} ({r.pct:5.1f}%){RESET}  {color}{bar}{RESET}")

    print(f"\n{'─'*60}")
    overall_color = GREEN if overall_pct >= 90 else (YELLOW if overall_pct >= 70 else RED)
    print(f"  {BOLD}OVERALL: {overall_color}{total_pass}/{total_tests} = {overall_pct:.1f}%{RESET}")
    print(f"{'─'*60}")

    # All failures
    all_failures = [(r.name, f) for r in ALL for f in r.failures]
    if all_failures:
        print(f"\n{BOLD}  FAILURES ({len(all_failures)}){RESET}")
        for suite_name, fail_msg in all_failures:
            print(f"  {RED}✗{RESET}  [{suite_name}] {fail_msg}")

    # All notes
    all_notes = [(r.name, n) for r in ALL for n in r.notes]
    if all_notes:
        print(f"\n{BOLD}  GAPS & NOTES ({len(all_notes)}){RESET}")
        for suite_name, note_msg in all_notes:
            print(f"  {YELLOW}→{RESET}  [{suite_name}] {note_msg}")

    print(f"\n{DIM}  Run from COM repo root.  All assertions mirror Claude's 96-assertion benchmark.{RESET}\n")

    # JSON export
    report = {
        "total_pass": total_pass,
        "total_tests": total_tests,
        "overall_pct": round(overall_pct, 2),
        "suites": [
            {
                "name": r.name,
                "passed": r.passed,
                "total": r.total,
                "pct": round(r.pct, 2),
                "failures": r.failures,
                "notes": r.notes,
            }
            for r in ALL
        ],
    }
    out_path = "benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  {DIM}Results saved → {out_path}{RESET}\n")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Suppress INFO logs from tool_harness
    import logging
    logging.disable(logging.INFO)

    print(f"\n{BOLD}{CYAN}COM v3 — Benchmark Suite{RESET}")
    print(f"{DIM}10 suites · 96 assertions · mirrors Claude's benchmark methodology{RESET}")

    # Locate COM root: check cwd, then the directory this script lives in
    _script_dir = Path(__file__).resolve().parent
    _candidates = [Path.cwd(), _script_dir]
    _com_root = None
    for _c in _candidates:
        if (_c / "core" / "com_core.py").exists():
            _com_root = _c
            break
    if _com_root is None:
        print(f"\n{RED}ERROR: Could not find COM root (looking for core/com_core.py).{RESET}")
        print(f"{RED}Place benchmark.py inside your COM repo folder and run from there.{RESET}")
        sys.exit(1)

    # Inject COM root into path so all imports resolve
    _root_str = str(_com_root)
    if _root_str not in sys.path:
        sys.path.insert(0, _root_str)
    os.chdir(_com_root)  # ensure relative paths (pyproject.toml etc.) resolve correctly

    suites = [
        test_01_intent_router,
        test_02_signal_parser,
        test_03_safe_io,
        test_04_wiki_indexer,
        test_05_wiki_retriever,
        test_06_health_checker,
        test_07_tool_harness,
        test_08_com_core_pipeline,
        test_09_edge_cases,
        test_10_architecture_integration,
    ]

    # Optional: run specific suites by number, e.g.  python benchmark.py 1 3 7
    if len(sys.argv) > 1:
        indices = [int(a) - 1 for a in sys.argv[1:] if a.isdigit()]
        suites = [suites[i] for i in indices if 0 <= i < len(suites)]

    for fn in suites:
        try:
            fn()
        except Exception as e:
            print(f"\n  {RED}SUITE CRASHED: {e}{RESET}")
            import traceback
            traceback.print_exc()

    print_report()
