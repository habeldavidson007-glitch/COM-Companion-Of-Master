const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, LevelFormat, PageBreak } = require('docx');
const fs = require('fs');

const P = { black:'111111', accent:'1E6B4A', accent2:'2D9970', accent3:'E8F5EF', gold:'B8860B', gold_bg:'FFF8E8', red:'C0392B', red_bg:'FDF0EE', blue:'1A4A8A', blue_bg:'EEF3FB', grey:'6C6C6C', lgrey:'F2F4F2', border:'C8D8CC', white:'FFFFFF' };
const bdr = (c='CCCCCC') => ({ style: BorderStyle.SINGLE, size: 1, color: c });
const bdr4 = (c='CCCCCC') => ({ top: bdr(c), bottom: bdr(c), left: bdr(c), right: bdr(c) });
const noBdr = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBdr4 = { top: noBdr, bottom: noBdr, left: noBdr, right: noBdr };
const cellMg = { top: 100, bottom: 100, left: 160, right: 160 };

function sp(n=1) { return Array.from({length:n}, ()=>new Paragraph({children:[new TextRun('')]})); }
function h1(txt) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 400, after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: P.accent, space: 6 } }, children: [new TextRun({ text: txt, font:'Arial', size: 40, bold: true, color: P.black })] }); }
function h2(txt, color=P.accent) { return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 320, after: 120 }, children: [new TextRun({ text: txt, font:'Arial', size: 30, bold: true, color })] }); }
function h3(txt, color=P.black) { return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 220, after: 80 }, children: [new TextRun({ text: txt, font:'Arial', size: 24, bold: true, color })] }); }
function body(txt, spacing={ before:60, after:80 }) { return new Paragraph({ spacing, children: [new TextRun({ text: txt, font:'Arial', size: 21 })] }); }
function run(txt, opts={}) { return new TextRun({ text: txt, font:'Arial', size: 21, ...opts }); }
function bold(txt, color=P.black) { return new TextRun({ text: txt, font:'Arial', size: 21, bold: true, color }); }
function mono(txt, color='1E6B4A') { return new TextRun({ text: txt, font:'Courier New', size: 20, color }); }
function bul(txt, ref='bul1', opts={}) { return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { before: 40, after: 60 }, children: typeof txt === 'string' ? [new TextRun({ text: txt, font:'Arial', size: 21, ...opts })] : txt }); }
function numbered(txt, ref='num1') { return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { before: 60, after: 80 }, children: typeof txt === 'string' ? [new TextRun({ text: txt, font:'Arial', size: 21 })] : txt }); }
function rule(color=P.border) { return new Paragraph({ spacing: { before: 160, after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 2, color, space: 1 } }, children: [new TextRun('')] }); }
function pgBreak() { return new Paragraph({ children: [new PageBreak()] }); }

function callout(title, lines, bg=P.accent3, titleColor=P.accent) {
  const rows = [
    new TableRow({ children: [new TableCell({ borders: bdr4(titleColor), shading: { fill: titleColor, type: ShadingType.CLEAR }, margins: { top:80, bottom:80, left:200, right:200 }, children: [new Paragraph({ children: [new TextRun({ text: title, font:'Arial', size:21, bold:true, color:P.white })] })] })] }),
    new TableRow({ children: [new TableCell({ borders: bdr4(titleColor), shading: { fill: bg, type: ShadingType.CLEAR }, margins: { top:100, bottom:100, left:200, right:200 }, children: lines.map(l => new Paragraph({ spacing:{ before:40, after:40 }, children: typeof l === 'string' ? [new TextRun({ text:l, font:'Arial', size:21 })] : l })) })] })
  ];
  return new Table({ width:{ size:9360, type:WidthType.DXA }, columnWidths:[9360], rows, spacing:{ before:120, after:120 } });
}

function twoCol(left, right, lw=4600, rw=4760) {
  return new Table({ width:{ size:9360, type:WidthType.DXA }, columnWidths:[lw, rw], borders: { insideH: noBdr, insideV: noBdr, top:noBdr, bottom:noBdr, left:noBdr, right:noBdr }, rows:[new TableRow({ children:[ new TableCell({ borders:noBdr4, margins:{ top:0, bottom:0, left:0, right:160 }, width:{ size:lw, type:WidthType.DXA }, children:left }), new TableCell({ borders:noBdr4, margins:{ top:0, bottom:0, left:160, right:0 }, width:{ size:rw, type:WidthType.DXA }, children:right }) ]})] });
}

function phaseCard(num, title, duration, status, bullets, color=P.accent) {
  const headerRow = new TableRow({ children:[ new TableCell({ borders: bdr4(color), shading:{ fill:color, type:ShadingType.CLEAR }, margins:{ top:100, bottom:100, left:200, right:200 }, columnSpan: 2, children:[new Paragraph({ children:[ new TextRun({ text:'Phase '+num+'  ', font:'Arial', size:24, bold:true, color:P.white }), new TextRun({ text:title, font:'Arial', size:24, bold:true, color:P.white }), new TextRun({ text:'  -  '+duration, font:'Arial', size:20, color:'CCFFDD' }), new TextRun({ text:'  ['+status+']', font:'Arial', size:18, color:'CCFFDD' }), ]})] })] });
  const bodyRow = new TableRow({ children:[ new TableCell({ borders: bdr4(color), shading:{ fill:'F8FBF9', type:ShadingType.CLEAR }, margins:{ top:100, bottom:120, left:200, right:200 }, children: bullets.map(b => new Paragraph({ numbering:{ reference:'bul1', level:0 }, spacing:{ before:40, after:50 }, children: typeof b === 'string' ? [new TextRun({ text:b, font:'Arial', size:20 })] : b })) })] });
  return new Table({ width:{ size:9360, type:WidthType.DXA }, columnWidths:[9360], rows:[headerRow, bodyRow], spacing:{ before:160, after:60 } });
}

const numbering = { config: [
  { reference:'bul1', levels:[{ level:0, format:LevelFormat.BULLET, text:'*', alignment:AlignmentType.LEFT, style:{ paragraph:{ indent:{ left:480, hanging:280 } } } }] },
  { reference:'num1', levels:[{ level:0, format:LevelFormat.DECIMAL, text:'%1.', alignment:AlignmentType.LEFT, style:{ paragraph:{ indent:{ left:540, hanging:300 } } } }] },
  { reference:'num2', levels:[{ level:0, format:LevelFormat.DECIMAL, text:'%1.', alignment:AlignmentType.LEFT, style:{ paragraph:{ indent:{ left:540, hanging:300 } } } }] },
  { reference:'num3', levels:[{ level:0, format:LevelFormat.DECIMAL, text:'%1.', alignment:AlignmentType.LEFT, style:{ paragraph:{ indent:{ left:540, hanging:300 } } } }] },
]};

const children = [
  ...sp(2),
  new Paragraph({ spacing:{ before:0, after:60 }, children:[ new TextRun({ text:'COM IDE', font:'Arial', size:72, bold:true, color:P.accent }) ]}),
  new Paragraph({ spacing:{ before:0, after:80 }, children:[ new TextRun({ text:'Godot AI Companion - Full Roadmap to IDE', font:'Arial', size:32, color:P.grey }) ]}),
  new Paragraph({ spacing:{ before:0, after:40 }, children:[ new TextRun({ text:'From zero infrastructure to a shipping product', font:'Arial', size:22, color:P.grey, italics:true }) ]}),
  new Paragraph({ spacing:{ before:0, after:320 }, children:[ new TextRun({ text:'Compiled: May 2026 - Status: Active Development', font:'Arial', size:20, color:'AAAAAA' }) ]}),
  ...sp(1),
  callout('Why this pivot is correct', [
    'The #1 Godot developer pain point is not missing features - it is silent failures: crashes without reasons, node binding errors discovered at runtime, RAM exhaustion mid-session, and the constant back-and-forth with external LLMs that have no knowledge of the project.',
    'No existing Godot plugin addresses this holistically. All existing tools are either syntax helpers or external chatbots. None sit inside the development loop and watch the project state in real time.',
    'COM already has the signal architecture, intent routing, and wiki knowledge layer to do this. The pivot is not starting over - it is pointing what already exists at the right target.',
  ], P.accent3, P.accent),
  ...sp(1), pgBreak(),

  h1('01  The Real Problem - What Godot Developers Actually Suffer'),
  body('Understanding the pain precisely determines everything built. These are the failure modes reported consistently by indie Godot developers across forums, Discord, and direct observation.'),
  ...sp(1),
  h2('1.1  Silent Crashes With No Actionable Reason'),
  body('Godot crashes or freezes without surfacing a line number the developer can act on. The output log exists but it reports engine internals, not the users code. The developer knows something broke but not what, not why, and not where to start.'),
  bul('RAM exhaustion happens mid-playtest with no warning - the engine simply stops or throws a generic OS-level error'),
  bul('Corrupted scene state from a bad node removal leaves the project in an invalid state that survives saves and reopens'),
  bul('Signal connections that were valid in one Godot version silently fail in the next without any migration warning'),
  bul('Physics engine instability produces different results on different machines, making bugs non-reproducible'),
  ...sp(1),
  h2('1.2  Node Binding Errors Found Too Late'),
  body('Scripts reference nodes by path. Those paths are strings. Strings cannot be validated at write time in the default Godot editor - only at runtime when the scene runs. By the time the error surfaces, the developer may have written hundreds of lines against a node that no longer exists or moved.'),
  bul([bold('$NodePath validation happens at runtime, not at write time'), run(' - the developer writes @onready var player = $Player and does not discover the node was renamed to PlayerCharacter until five minutes into a playtest')]),
  bul('Export variables pointing to resources that were deleted from the filesystem produce errors that point to the wrong place'),
  bul('Inheritance chains where a child scene overrides a parent node path break silently'),
  ...sp(1),
  h2('1.3  The External LLM Loop Tax'),
  body('The current workflow for most developers: encounter error, copy error + context, paste into ChatGPT/Claude, read answer, switch back to Godot, try fix, encounter next error, repeat. Every context switch is a cognitive reset. The LLM has no knowledge of the project structure, the scene tree, or which nodes are actually connected. Answers are generic.'),
  bul('Average 4-8 context switches per debugging session based on developer self-reports'),
  bul('Each switch requires re-explaining project structure the LLM has never seen'),
  bul('Generic answers suggest fixes that break other parts of the project the LLM is not aware of'),
  bul('No memory between sessions - the LLM forgets everything and the developer re-explains the same codebase repeatedly'),
  ...sp(1),
  h2('1.4  Plugin Ecosystem Gap'),
  body('Godots plugin ecosystem is thin compared to Unity or Unreal. Existing plugins focus on adding features (more node types, visual shaders, asset importers) rather than on the development experience itself. The gap is not capability - it is intelligence about the developers own project.'),
  callout('The gap in one sentence', [ 'No tool currently sits inside the Godot development loop, knows your project structure, watches your code as you write it, catches node binding errors before runtime, and answers questions about your specific codebase without you having to explain it every time.' ], P.blue_bg, P.blue),
  ...sp(1), pgBreak(),

  h1('02  The Product - COM IDE for Godot'),
  body('COM IDE is not a replacement for the Godot editor. It is an AI companion layer that runs alongside Godot, understands your project, and closes the gap between writing code and knowing it works.'),
  ...sp(1),
  h2('2.1  Core Value Proposition'),
  callout('What COM IDE does that nothing else does', [
    '1.  Reads your scene tree and script files locally - no upload, no API cost, no privacy concern',
    '2.  Catches node path errors before you run the scene',
    '3.  Explains crashes in plain language using your actual project context',
    '4.  Answers GDScript questions with knowledge of your specific codebase, not generic examples',
    '5.  Runs inference locally on Ollama - works without internet, works on 16GB RAM',
  ], P.accent3, P.accent),
  ...sp(1),
  h2('2.2  What It Is NOT'),
  bul('Not a replacement for the Godot editor - opens alongside it, not instead of it'),
  bul('Not a cloud service - everything runs on the developers machine'),
  bul('Not a full IDE with its own text editor in Phase 1 - that comes in Phase 3'),
  bul('Not a general-purpose coding assistant - specialized for Godot and GDScript'),
  bul('Not a subscription - local inference means no per-query cost'),
  ...sp(1),
  h2('2.3  The E+ Language Layer (Long Game)'),
  body('The symbolic language concept (E+) fits naturally as COM IDEs scripting layer above GDScript. Rather than trying to replace Python or C++ universally, E+ becomes the language for describing Godot game logic in near-English terms that translate to GDScript in real time. This is achievable because the translation domain is constrained - you are not translating to all of programming, only to one engines scripting language.'),
  bul([mono('@new player -> physics scene'), run('   translates to:   '), mono('var player = CharacterBody2D.new(); add_child(player)')]),
  bul([mono('@connect signal "hit" -> player.take_damage'), run('   wires a signal connection correctly')]),
  bul([mono('@when player enters area -> play "damage" sound'), run('   generates Area2D body_entered handler')]),
  body('This is not Phase 1. It is the destination the architecture is being built toward.'),
  ...sp(1), pgBreak(),

  h1('03  Build Phases - From Nothing to Shipping'),
  body('Each phase produces something usable and demonstrable before the next begins. No phase requires completing the full vision before delivering value. Revenue potential begins at Phase 2.'),
  ...sp(1),
  phaseCard('1', 'Project Scanner + Error Explainer', '6-8 weeks', 'START HERE', [
    'Build a Python script that reads a Godot project directory and builds a scene tree map in memory',
    'Parse all .gd files and extract @onready var declarations, $NodePath references, and signal connections',
    'Cross-reference node paths against the actual scene tree - flag any path that does not resolve',
    'Pipe errors from Godots output log through local Ollama with project context injected - return plain-English explanation',
    'Simple terminal UI or basic Tkinter window showing: current errors, node path warnings, recent log analysis',
    'Uses COMs existing OllamaClient and wiki layer - most infrastructure already exists',
    [bold('Deliverable: '), run('A developer opens their Godot project, opens COM IDE alongside it, and sees "Node $Player not found in MainScene.tscn - the node was renamed to PlayerCharacter at line 47" instead of a crash.')],
  ], P.accent),
  ...sp(1),
  phaseCard('2', 'Context-Aware Q&A + Memory', '6-8 weeks', 'FIRST DEMO', [
    'Index the projects GDScript files into COMs wiki knowledge layer (already built)',
    'When developer asks a question, search the project index first, then supplement with Godot documentation',
    'Implement project memory: remember which nodes exist, which signals are connected, which scenes are parent/child',
    'Add session persistence - COM remembers the project between restarts, no re-explaining required',
    'Build the COM Chat panel: persistent sidebar showing conversation history with project-aware answers',
    'Add "Suggest Fix" mode: when a runtime error occurs, COM proposes a specific fix to the specific line in the specific file',
    [bold('Deliverable: '), run('Developer asks "why does my player keep falling through the floor" and COM answers using the actual CollisionShape2D configuration in their scene, not a generic physics tutorial.')],
  ], P.accent2),
  ...sp(1),
  phaseCard('3', 'VS Code Extension', '8-10 weeks', 'DISTRIBUTION', [
    'Port the COM IDE interface to a VS Code extension - this is the correct distribution mechanism',
    'GDScript syntax highlighting with inline node path validation (red underline if path does not exist)',
    'Live error explanation panel that updates when Godots output log changes',
    'IntelliSense-style completions that know your scene tree (not just GDScript syntax, but your actual nodes)',
    'One-click "Explain this error" that opens COM Chat with the error already loaded and project context injected',
    'Works with GodotTools extension already in VS Code - complements it, does not replace it',
    [bold('Deliverable: '), run('A VS Code extension on the marketplace. This is the first publicly distributable artifact. Free tier with basic error explanation, paid tier with full project-aware Q&A.')],
  ], P.blue),
  ...sp(1),
  phaseCard('4', 'E+ Language Translator (Live Preview)', '10-14 weeks', 'LANGUAGE LAYER', [
    'Implement the E+ grammar as a formal parser - start with 20 constructs covering 80% of common Godot patterns',
    'Side-by-side editor: left pane is E+, right pane is live-translated GDScript',
    'Translation is rule-based for the core constructs (no LLM needed, deterministic, no latency)',
    'LLM handles ambiguous or complex E+ statements that the rule engine cannot resolve',
    'Two-way translation: paste existing GDScript, get E+ equivalent (for learning)',
    'Integrated with the VS Code extension from Phase 3',
    [bold('Deliverable: '), run('A developer who has never written GDScript writes "@when player jumps -> if on_floor: velocity.y = jump_force" and gets working GDScript that they can copy into their project or run directly through COM.')],
  ], P.gold),
  ...sp(1),
  phaseCard('5', 'Standalone COM IDE', '12-16 weeks', 'FULL PRODUCT', [
    'Build the full standalone IDE using Python + Qt or Electron - own the editor surface',
    'Integrated GDScript editor with E+ layer, live translation, and inline COM assistance',
    'Scene tree visualizer showing node structure without opening Godot',
    'One-click error fix: COM proposes the fix, developer approves, COM writes the change to the file',
    'Project health dashboard: unconnected signals, unreferenced nodes, RAM usage trends, script coupling metrics',
    'Plugin system so the community can add tool integrations (Blender, Aseprite, etc.)',
    [bold('Deliverable: '), run('A complete development environment for Godot that a developer could use as their primary tool, with COM AI assistance built into every layer of the workflow.')],
  ], P.red),
  ...sp(1), pgBreak(),

  h1('04  What COM Already Has - Assets That Transfer Directly'),
  body('This is not starting from zero. The benchmark work and refactoring across six versions has produced real, tested infrastructure that maps directly to the IDE.'),
  ...sp(1),
  twoCol(
    [ h3('Already Built', P.accent),
      bul('Intent router with 6 modes (GODOT, OFFICE, CODE, DESKTOP, WIKI, GENERAL)'),
      bul('Signal-of-Thought protocol - structured token dispatch'),
      bul('OllamaClient with health check, retry, cooldown, and offline fallback'),
      bul('WikiRetriever TF-IDF with multi-doc relevance ranking'),
      bul('WikiIndexer with concept graph and backlink tracking'),
      bul('SafeIO with atomic writes and path traversal protection'),
      bul('ResponseCache with LRU eviction and mode isolation'),
      bul('MemoryManager with sliding window and salience filter'),
      bul('HealthChecker async integrity scanner'),
      bul('BackgroundWikiService daemon'),
      bul('SessionLogger JSONL for debugging'),
      bul('Tool harness: XLS, PPT, PDF, GODOT file generation'),
      bul('Reflective Signal Protocol (parse_reflective_response)'),
      bul('config.py with ModelConfig and SystemConfig'),
      bul('pyproject.toml - packaging ready'),
    ],
    [ h3('Maps Directly To', P.accent),
      bul('Route developer query to correct tool/mode'),
      bul('Dispatch project scan commands to the right handler'),
      bul('Local inference with graceful degradation on weak hardware'),
      bul('Search Godot documentation and project files'),
      bul('Track which scripts reference which nodes and scenes'),
      bul('Read project files without corruption risk'),
      bul('Cache repeated LLM answers for same error/context'),
      bul('Remember project state between conversations'),
      bul('Validate scene tree integrity on project open'),
      bul('Run periodic project health scans in background'),
      bul('Log every COM action for debugging and tuning'),
      bul('Generate scaffold scripts and report files'),
      bul('Parse and validate complex LLM responses'),
      bul('Model switching between smollm2 and qwen-coder'),
      bul('pip install -e . for local development setup'),
    ]
  ),
  ...sp(1),
  callout('The two things still needed for Phase 1', [
    '1.  A Godot project parser - reads .tscn/.tres/.gd files and builds a live in-memory scene tree. This is ~300 lines of Python. Godots scene format is text-based and well-documented.',
    '2.  A log watcher - monitors Godots output.log or stderr in real time and pipes new entries through the error explainer. This is a 50-line asyncio file watcher.',
  ], P.gold_bg, P.gold),
  ...sp(1), pgBreak(),

  h1('05  Hardware Reality - What Works on 16GB RAM'),
  body('16GB RAM is not a limitation that blocks this project. It constrains the model tier, not the product. Here is exactly what runs and what it can do.'),
  ...sp(1),
  new Table({
    width:{ size:9360, type:WidthType.DXA }, columnWidths:[2800, 2200, 2200, 2160],
    rows:[
      new TableRow({ children:['Model', 'RAM Usage', 'Speed (tok/s)', 'Best For'].map((h,i) => new TableCell({ borders: bdr4(P.accent), shading:{ fill:P.accent, type:ShadingType.CLEAR }, width:{ size:[2800,2200,2200,2160][i], type:WidthType.DXA }, margins: cellMg, children:[new Paragraph({ children:[new TextRun({ text:h, font:'Arial', size:20, bold:true, color:P.white })] })] }))}),
      ...[['smollm2:1.7b-q4_K_M', '~1.2 GB', '~45 tok/s', 'Fast replies, signal routing'], ['qwen2.5-coder:7b-q4', '~4.5 GB', '~18 tok/s', 'Code generation, GDScript'], ['deepseek-coder:6.7b-q4', '~4.2 GB', '~20 tok/s', 'Error explanation, debugging'], ['qwen2.5:14b-q4', '~9 GB', '~8 tok/s', 'Complex reasoning (tight on 16GB)'], ['codellama:7b-q4', '~4.5 GB', '~18 tok/s', 'Code completion, E+ translation'],
      ].map((row, ri) => new TableRow({ children: row.map((cell,ci) => new TableCell({ borders: bdr4(P.border), shading:{ fill: ri%2===0 ? P.white : P.lgrey, type:ShadingType.CLEAR }, width:{ size:[2800,2200,2200,2160][ci], type:WidthType.DXA }, margins: cellMg, children:[new Paragraph({ children:[new TextRun({ text:cell, font: ci===0 ? 'Courier New' : 'Arial', size:20 })] })] }))}))
    ]
  }),
  ...sp(1),
  body('The recommended setup for COM IDE development: smollm2:1.7b for intent routing and fast replies (always loaded, 1.2GB), qwen2.5-coder:7b for GDScript generation and error explanation (loaded on demand, released after 10 minutes idle). Total peak RAM for both loaded simultaneously: ~6GB, leaving 10GB for Godot, VS Code, and the OS.'),
  ...sp(1),
  callout('Important: no GPU required for this tier', [
    'CPU inference on modern x86 processors runs the 7B quantized models at 15-20 tokens/second. For a tool that explains errors and answers questions - not a real-time autocomplete - this is fast enough. A 200-token error explanation arrives in about 10 seconds. That is acceptable for a debugging workflow.',
    'GPU acceleration (even a mid-range RTX 3060 with 12GB VRAM) would bring this to 80-120 tok/s. It is a quality-of-life improvement, not a requirement.',
  ], P.blue_bg, P.blue),
  ...sp(1), pgBreak(),

  h1('06  First 30 Days - Concrete Tasks in Order'),
  body('This is the actionable sequence for Phase 1. Each task is scoped to be completable in 1-3 days. No task depends on the next being complete to be testable.'),
  ...sp(1),
  h2('Week 1 - Godot Project Parser'),
  numbered('Create tools/godot/scene_parser.py - reads .tscn files, extracts node names, types, and parent paths into a dict', 'num1'),
  numbered('Create tools/godot/script_parser.py - reads .gd files, extracts @onready vars, $NodePath strings, and signal connections via regex', 'num1'),
  numbered('Create tools/godot/project_map.py - combines scene tree + script refs into a unified ProjectMap object', 'num1'),
  numbered('Write 10 unit tests: one per scene/script parsing edge case (renamed nodes, nested scenes, inherited scripts)', 'num1'),
  ...sp(1),
  h2('Week 2 - Node Path Validator'),
  numbered('Implement ProjectMap.validate_node_paths() - returns list of ValidationError(file, line, path, suggestion)', 'num2'),
  numbered('Add similarity matching for suggestions: if $Player not found but $PlayerCharacter exists, suggest it', 'num2'),
  numbered('Create tools/godot/log_watcher.py - asyncio file watcher on Godots output path, emits new log lines as events', 'num2'),
  numbered('Wire log_watcher output through OllamaClient with ProjectMap as context injection', 'num2'),
  ...sp(1),
  h2('Week 3 - First UI'),
  numbered('Create a minimal Tkinter window (reuse frontend/viewer.py pattern) with three panels: Errors, Warnings, Chat', 'num3'),
  numbered('Errors panel: shows ValidationErrors from the node path validator, updates on file change', 'num3'),
  numbered('Chat panel: accepts developer questions, injects ProjectMap context, returns Ollama response', 'num3'),
  numbered('Add "Explain last error" button: takes most recent Godot log line, sends to Ollama with project context', 'num3'),
  ...sp(1),
  h2('Week 4 - Integration + Polish'),
  numbered('Run COM IDE against three real Godot projects (your own, or open-source projects from GitHub)', 'num1'),
  numbered('Document every false positive and false negative from the node path validator', 'num1'),
  numbered('Fix the top 5 most common false positives before calling Phase 1 complete', 'num1'),
  numbered('Write a 60-second demo: start COM IDE, open a Godot project with a known bug, show COM finding it', 'num1'),
  ...sp(1), pgBreak(),

  h1('07  Two COM Bugs to Fix Before Phase 1 Starts'),
  body('These two bugs exist in the current COM master and will cause silent failures in the IDE. Fix them before writing any new code.'),
  ...sp(1),
  callout('Fix 1 - @GDT alias (30 minutes, 2 lines)', [
    'File: tools/tool_harness.py',
    'Problem: health_checker.tool_status has no "GDT" key. is_tool_available("GDT") returns False. Every Godot file generation call fails silently.',
    'Fix: in _check_all_tools(), add:  self.tool_status["GDT"] = self.tool_status["GODOT"]',
    'Fix: in execute_signal() executors dict, add:  "GDT": execute_godot',
    'This bug has been documented in 6 consecutive benchmarks. It must not enter Phase 1.',
  ], P.red_bg, P.red),
  ...sp(1),
  callout('Fix 2 - WikiRetriever TF-IDF truncation (45 minutes, 5 lines)', [
    'File: tools/data_ops/wiki_compiler.py, WikiRetriever.load_wiki()',
    'Problem: self.documents[path] = content[:2000] - truncates all documents to 2000 chars before indexing.',
    'For a 5000-word GDScript reference document, 60% of content is invisible to TF-IDF search.',
    'Fix: add self.snippets = {}  in __init__. In load_wiki(): self.documents[path] = content (full).  self.snippets[path] = content[:200] (preview only).',
    'In search(): return self.snippets.get(path, content[:200]) as the snippet string, not self.documents[path][:200].',
    'This matters because the wiki is the knowledge backbone of Phase 2 project Q&A.',
  ], P.red_bg, P.red),
  ...sp(1), pgBreak(),

  h1('08  Path to Revenue - Realistic, Not Optimistic'),
  body('The honest answer about money: Phase 1 and Phase 2 are pre-revenue. They are the foundation that makes the product worth paying for. Phase 3 (VS Code extension) is the first realistic revenue opportunity.'),
  ...sp(1),
  twoCol(
    [ h3('Free Tier (Phase 3)', P.accent), bul('Node path validation - unlimited'), bul('Error log plain-English explanation - 10/day'), bul('Basic project health report'), bul('GDScript syntax checking'), ...sp(1),
      h3('Paid Tier - ~$5/month (Phase 3)', P.gold), bul('Unlimited error explanations'), bul('Project-aware Q&A - unlimited'), bul('Session memory across project sessions'), bul('Suggest Fix mode - writes the code change'), bul('Priority feature requests'), ...sp(1),
      h3('E+ Language (Phase 4)', P.blue), bul('Free: 50 E+ to GDScript translations/day'), bul('Paid: unlimited + two-way translation'), bul('Paid: custom E+ vocabulary for team'),
    ],
    [ h3('Why developers will pay', P.accent),
      body('The value proposition is measurable: if COM IDE saves a developer 30 minutes per session catching bugs before runtime, and a developer values their time at $15/hour, the tool pays for itself in 20 minutes of saved debugging per month.'), ...sp(1),
      body('The subscription model works because the value compounds over time: the more the developer uses COM, the more project context it builds, and the more accurate its answers become. Switching away means losing that context - which is healthy retention, not lock-in.'), ...sp(1),
      callout('Revenue milestone target', [ '50 paying users at $5/month = $250/month', 'Enough to fund one month of dedicated development time', 'Enough to buy one month of GPU cloud access for model testing', 'Achievable within 3 months of Phase 3 launch with consistent community presence' ], P.accent3, P.accent),
    ]
  ),
  ...sp(1), pgBreak(),

  h1('09  Risks - Honest Assessment'), ...sp(1),
  h2('9.1  Technical Risks', P.red),
  bul([bold('Godot scene format changes: '), run('Godot 4.x has changed the .tscn format twice. The parser must be version-aware. Mitigation: test against Godot 4.0, 4.1, 4.2, and 4.3 project files from the start.')]),
  bul([bold('LLM response quality on small models: '), run('qwen2.5-coder:7b produces good GDScript but occasionally hallucinates node names. Mitigation: validate all LLM-suggested node paths against the ProjectMap before showing them to the user.')]),
  bul([bold('Log watching on Windows vs Linux: '), run('Godot outputs logs differently on different OS. Mitigation: test on both from Week 1, not Week 8.')]), ...sp(1),
  h2('9.2  Market Risks', P.red),
  bul([bold('Godot releases an official AI plugin: '), run('Unlikely in 2026 - Godot Foundation has consistently deprioritised AI tooling. But if it happens, COMs project-aware context and local inference are still differentiators.')]),
  bul([bold('VS Codes GitHub Copilot already does this: '), run('Copilot does not know your scene tree. It does not validate node paths. It is a generic code assistant. COM is project-specific. This is the moat.')]),
  bul([bold('Developer adoption inertia: '), run('The first 50 users are the hardest. Community presence in the Godot Discord and subreddit is the distribution strategy, not advertising.')]), ...sp(1),
  h2('9.3  Personal Risks', P.red),
  bul([bold('Hardware bottleneck: '), run('16GB RAM is sufficient for development. It becomes a bottleneck if you need to test the 14B models or run inference in parallel. Cloud fallback: use a free-tier Colab notebook for model testing when local RAM is insufficient.')]),
  bul([bold('Scope creep: '), run('The E+ language is exciting. The standalone IDE is exciting. Phase 1 is unglamorous file parsing. The discipline to finish Phase 1 before touching Phase 4 is the single most important non-technical decision in this project.')]), ...sp(1), pgBreak(),

  h1('10  Summary - What to Do Tomorrow'),
  body('Everything above is context. This is the actionable summary.'), ...sp(1),
  callout('The 5 things to do this week, in order', [
    '1.  Fix the @GDT alias bug in tools/tool_harness.py - 30 minutes. Run the benchmark to confirm it passes. Never let this appear in a benchmark again.',
    '2.  Fix the WikiRetriever TF-IDF truncation - 45 minutes. This is the knowledge backbone of Phase 2.',
    '3.  Create tools/godot/ directory. Write scene_parser.py. Test it against one real .tscn file.',
    '4.  Write script_parser.py. Extract every $NodePath reference from one real .gd file. Print them to terminal.',
    '5.  Create a ProjectMap that combines the two. Run validate_node_paths(). See what it finds.', '',
    'At the end of this week you will have the core of Phase 1 working against a real project. Everything else is UI, polish, and distribution.',
  ], P.accent3, P.accent), ...sp(1),
  body('You are not starting from nothing. You have a tested signal architecture, a working inference client, a knowledge retrieval system, and six versions of benchmark evidence about what is solid and what is not. The pivot to Godot IDE is not a restart - it is a focusing of what already exists onto a problem worth solving.'), ...sp(1),
  body('The people who will use this are sitting in Discord right now asking why their player keeps falling through the floor. Build for them.'), ...sp(2),
  rule(P.accent),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing:{ before:120, after:0 }, children:[ new TextRun({ text:'COM IDE - Signal-of-Thought Architecture - Built for Godot developers on real hardware', font:'Arial', size:18, color:P.grey, italics:true }) ]}),
];

const doc = new Document({
  numbering,
  styles: {
    default: { document: { run: { font:'Arial', size:21, color:P.black } } },
    paragraphStyles: [
      { id:'Heading1', name:'Heading 1', basedOn:'Normal', next:'Normal', quickFormat:true, run:{ size:40, bold:true, font:'Arial', color:P.black }, paragraph:{ spacing:{ before:400, after:160 }, outlineLevel:0 } },
      { id:'Heading2', name:'Heading 2', basedOn:'Normal', next:'Normal', quickFormat:true, run:{ size:30, bold:true, font:'Arial', color:P.accent }, paragraph:{ spacing:{ before:320, after:120 }, outlineLevel:1 } },
      { id:'Heading3', name:'Heading 3', basedOn:'Normal', next:'Normal', quickFormat:true, run:{ size:24, bold:true, font:'Arial', color:P.black }, paragraph:{ spacing:{ before:220, after:80 }, outlineLevel:2 } },
    ]
  },
  sections:[{ properties:{ page:{ size:{ width:12240, height:15840 }, margin:{ top:1080, right:1080, bottom:1080, left:1080 } } }, children }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/workspace/COM_IDE_Roadmap.docx', buf);
  console.log('Done - COM_IDE_Roadmap.docx created successfully');
});
