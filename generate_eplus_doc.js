const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageOrientation
} = require('docx');
const fs = require('fs');

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "C8C8C8" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const CELL_MARGIN = { top: 100, bottom: 100, left: 140, right: 140 };

const C = {
  ACCENT:    "1A3A5C",
  ACCENT2:   "2563A8",
  SYMBOL_BG: "EBF2FA",
  HEAD_BG:   "1A3A5C",
  ALT_ROW:   "F3F7FD",
  WHITE:     "FFFFFF",
  TEXT:      "1A1A2E",
  MUTED:     "5A6070",
  GREEN_BG:  "E8F5E9",
  PURPLE_BG: "F3E8FF",
  ORANGE_BG: "FFF3E0",
};

function h(text, level, color = C.ACCENT, size = 32) {
  return new Paragraph({
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, bold: true, color, size, font: "Segoe UI" })]
  });
}

function p(text, color = C.TEXT, size = 22) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, color, size, font: "Segoe UI" })]
  });
}

function mono(text, color = C.ACCENT2) {
  return new TextRun({ text, font: "Consolas", size: 20, color, bold: true });
}

function space(n = 1) {
  return new Paragraph({ children: [new TextRun("")], spacing: { before: n * 80, after: 0 } });
}

function hr() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.ACCENT, space: 1 } },
    spacing: { before: 160, after: 160 },
    children: [new TextRun("")]
  });
}

function cell(children, bg = C.WHITE, width = 1170, bold = false, center = false) {
  const cellChildren = Array.isArray(children) ? children : [
    new Paragraph({
      alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: Array.isArray(children) ? children : [
        new TextRun({ text: String(children), size: 19, font: "Segoe UI", bold, color: C.TEXT })
      ]
    })
  ];
  return new TableCell({
    borders: BORDERS,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: bg, type: ShadingType.CLEAR },
    margins: CELL_MARGIN,
    children: cellChildren
  });
}

function monoCell(text, bg = C.SYMBOL_BG, width = 900) {
  return new TableCell({
    borders: BORDERS,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: bg, type: ShadingType.CLEAR },
    margins: CELL_MARGIN,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, font: "Consolas", size: 22, bold: true, color: C.ACCENT2 })]
    })]
  });
}

function headerRow(labels, widths, bg = C.HEAD_BG) {
  return new TableRow({
    tableHeader: true,
    children: labels.map((l, i) => new TableCell({
      borders: BORDERS,
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: bg, type: ShadingType.CLEAR },
      margins: CELL_MARGIN,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: l, bold: true, size: 20, color: C.WHITE, font: "Segoe UI" })]
      })]
    }))
  });
}

const DICT = [
  ["@",    "Entity",    "Entitas",    "Declare a variable",               "Deklarasi variabel",             "@Name",                          "name = None"],
  ["@",    "Entity",    "Entitas",    "Assign a value",                   "Menetapkan nilai",               "@Age = (25)",                    "age = 25"],
  ["<<",   "Pull",      "Ambil",      "Get input from user",              "Ambil input dari pengguna",      '<< ("Enter name")',            'input("Enter name")'],
  [">>",   "Push",      "Kirim",      "Display/print output",             "Tampilkan output ke layar",      '>> ("Hello World")',           'print("Hello World")'],
  ["[ ]",  "Blueprint", "Cetak Biru", "Define a function/order",          "Mendefinisikan fungsi",          '[Greet] { >> ("Hi") }',        'def greet():\n    print("Hi")'],
  ["^",    "Invoke",    "Panggil",    "Call / invoke a function",         "Memanggil fungsi",               "^[Greet]",                       "greet()"],
  ["^",    "Invoke",    "Panggil",    "Call function with parameters",    "Panggil fungsi dengan parameter","^[Add](3, 5)",                   "add(3, 5)"],
  ["=>",   "Return",    "Kembalikan", "Return a value from function",     "Mengembalikan nilai dari fungsi","=> (@result)",                   "return result"],
  ["( )",  "Data",      "Data",       "Hold data, string, or parameters","Menyimpan data atau parameter",  '("Hello")',                    '"Hello"'],
  ["( )",  "Data",      "Data",       "Multiple parameters",             "Parameter berganda",             "(10, 20)",                       "(10, 20)"],
  ["?",    "Check",     "Cek",        "If condition",                     "Kondisi jika / if",              '? (@age > 17) { >> ("OK") }',  'if age > 17:\n    print("OK")'],
  ["??",   "Or Check",  "Atau Cek",   "Else-if / elif condition",        "Kondisi lain / elif",            '?? (@age > 13) { >> ("Teen") }','elif age > 13:\n    print("Teen")'],
  ["::",   "Otherwise", "Lainnya",    "Else / default branch",           "Cabang else / lainnya",          ':: { >> ("No") }',             'else:\n    print("No")'],
  ["@@",   "Repeat",    "Ulang",      "Loop n times (for range)",        "Ulangi n kali",                  '@@ (@i, 10) { >> (@i) }',        'for i in range(10):\n    print(i)'],
  ["@@",   "Repeat",    "Ulang",      "Loop over a list (for-each)",     "Iterasi daftar",                 '@@ (@item, @list) { >> (@item) }','for item in list:\n    print(item)'],
  ["@@?",  "While",     "Selama",     "While loop (repeat while true)",  "Ulangi selama kondisi benar",    '@@? (@x > 0) { - @x (1) }',     'while x > 0:\n    x -= 1'],
  ["{ }",  "Block",     "Blok",       "Open/close a code block",        "Membuka/menutup blok kode",      '? (@x) { >> (@x) }',            'if x:\n    print(x)'],
  [">",    "Greater",   "Lebih Dari", "Greater than comparison",         "Perbandingan lebih besar",       "@x > (10)",                      "x > 10"],
  ["<",    "Less",      "Kurang Dari","Less than comparison",            "Perbandingan lebih kecil",       "@x < (10)",                      "x < 10"],
  ["==",   "Same",      "Sama",       "Equality check",                  "Pengecekan kesamaan",            "@x == (10)",                     "x == 10"],
  ["!=",   "Different", "Berbeda",    "Not-equal check",                 "Pengecekan ketidaksamaan",       "@x != (0)",                      "x != 0"],
  [">=",   "At Least",  "Min",        "Greater than or equal",           "Lebih besar atau sama",          "@x >= (18)",                     "x >= 18"],
  ["<=",   "At Most",   "Maks",       "Less than or equal",              "Lebih kecil atau sama",          "@x <= (100)",                    "x <= 100"],
  ["&&",   "And",       "Dan",        "Logical AND",                     "Logika DAN",                     "? (@a > 0 && @b > 0) { }",       "if a > 0 and b > 0:"],
  ["||",   "Or",        "Atau",       "Logical OR",                      "Logika ATAU",                    "? (@a == 0 || @b == 0) { }",     "if a == 0 or b == 0:"],
  ["+",    "Add",       "Tambah",     "Addition / increment",            "Penjumlahan / tambah",           "+ @score (10)",                   "score += 10"],
  ["-",    "Subtract",  "Kurang",     "Subtraction / decrement",        "Pengurangan / kurang",           "- @hp (5)",                      "hp -= 5"],
  ["*",    "Multiply",  "Kali",       "Multiplication",                  "Perkalian",                      "* @price (2)",                    "price *= 2"],
  ["/",    "Divide",    "Bagi",       "Division",                        "Pembagian",                      "/ @total (4)",                    "total /= 4"],
  ["%",    "Property",  "Sifat",      "Access attribute or property",    "Mengakses atribut/properti",     "@Car % (color)",                  "car.color"],
  ["!",    "Stop",      "Berhenti",   "Break out of loop",               "Hentikan perulangan",            '@@ (@i, 10) { ? (@i == 5) { ! } }','for i in range(10):\n    if i == 5:\n        break'],
  ["!!",   "Exit",      "Keluar",     "Exit program entirely",           "Keluar dari program",            "!!",                             "exit()"],
  ["~~",   "Erase",     "Hapus",      "Delete a variable",               "Menghapus variabel",             "~~ @TempData",                    "del temp_data"],
  ["##",   "Note",      "Catatan",    "Single-line comment",             "Komentar satu baris",            "## This is a note",               "# This is a note"],
  ["[ ]@", "List",      "Daftar",     "Declare an empty list",           "Deklarasi daftar kosong",        "@Items = [ ]",                   "items = []"],
  ["+@",   "Append",    "Tambah ke",  "Append item to list",             "Tambah item ke daftar",          '+@ @Items ("Apple")',           'items.append("Apple")'],
];

function buildDictTable() {
  const widths = [700, 900, 900, 1500, 1500, 1800, 1626];
  const total  = widths.reduce((a,b)=>a+b,0);

  const rows = [
    headerRow(["Symbol","EN Name","ID Name","EN Meaning","ID Meaning","E+ Example","Python Output"], widths),
    ...DICT.map((row, idx) => {
      const bg = idx % 2 === 0 ? C.WHITE : C.ALT_ROW;
      return new TableRow({ children: [
        monoCell(row[0], C.SYMBOL_BG, widths[0]),
        cell(row[1], bg, widths[1], true),
        cell(row[2], bg, widths[2], true),
        cell(row[3], bg, widths[3]),
        cell(row[4], bg, widths[4]),
        new TableCell({
          borders: BORDERS, width: { size: widths[5], type: WidthType.DXA },
          shading: { fill: C.GREEN_BG, type: ShadingType.CLEAR }, margins: CELL_MARGIN,
          children: [new Paragraph({ children: [mono(row[5], "#1B5E20")] })]
        }),
        new TableCell({
          borders: BORDERS, width: { size: widths[6], type: WidthType.DXA },
          shading: { fill: C.PURPLE_BG, type: ShadingType.CLEAR }, margins: CELL_MARGIN,
          children: [new Paragraph({ children: [mono(row[6], "#4A148C")] })]
        }),
      ]});
    })
  ];

  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows });
}

function scenarioBlock(title, eplus, python_code, desc) {
  const widths = [4463, 4463];
  return [
    space(2),
    new Paragraph({
      spacing: { before: 160, after: 80 },
      children: [new TextRun({ text: title, bold: true, size: 24, color: C.ACCENT2, font: "Segoe UI" })]
    }),
    p(desc, C.MUTED, 20),
    space(1),
    new Table({
      width: { size: 8926, type: WidthType.DXA },
      columnWidths: widths,
      rows: [
        new TableRow({ tableHeader: true, children: [
          new TableCell({ borders: BORDERS, width: { size: widths[0], type: WidthType.DXA },
            shading: { fill: "#1B5E20", type: ShadingType.CLEAR }, margins: CELL_MARGIN,
            children: [new Paragraph({ alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: "E+ Code", bold: true, size: 20, color: C.WHITE, font: "Segoe UI" })] })] }),
          new TableCell({ borders: BORDERS, width: { size: widths[1], type: WidthType.DXA },
            shading: { fill: "#4A148C", type: ShadingType.CLEAR }, margins: CELL_MARGIN,
            children: [new Paragraph({ alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: "Python Output", bold: true, size: 20, color: C.WHITE, font: "Segoe UI" })] })] }),
        ]}),
        new TableRow({ children: [
          new TableCell({ borders: BORDERS, width: { size: widths[0], type: WidthType.DXA },
            shading: { fill: C.GREEN_BG, type: ShadingType.CLEAR }, margins: { top: 160, bottom: 160, left: 160, right: 160 },
            children: eplus.split('\n').map(l => new Paragraph({ children: [mono(l, "#1B5E20")] })) }),
          new TableCell({ borders: BORDERS, width: { size: widths[1], type: WidthType.DXA },
            shading: { fill: C.PURPLE_BG, type: ShadingType.CLEAR }, margins: { top: 160, bottom: 160, left: 160, right: 160 },
            children: python_code.split('\n').map(l => new Paragraph({ children: [mono(l, "#4A148C")] })) }),
        ]})
      ]
    })
  ];
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Segoe UI", size: 22 } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 15840, height: 12240, orientation: PageOrientation.LANDSCAPE },
        margin: { top: 1000, bottom: 1000, left: 1080, right: 1080 }
      }
    },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 600, after: 120 },
        children: [new TextRun({ text: "E+", bold: true, size: 120, color: C.ACCENT, font: "Segoe UI" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: "Official Language Dictionary v2.0", bold: true, size: 40, color: C.ACCENT2, font: "Segoe UI" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: "Bilingual Reference — English · Bahasa Indonesia", size: 24, color: C.MUTED, font: "Segoe UI" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 40, after: 40 },
        children: [new TextRun({ text: "Target: Python 3  ·  COM IDE Compiler", size: 22, color: C.MUTED, font: "Segoe UI" })]
      }),
      hr(),
      h("What is E+?", HeadingLevel.HEADING_1, C.ACCENT, 30),
      p("E+ is a symbolic intent language designed to reduce cognitive load for beginner programmers. Instead of memorizing Python syntax like def, if, print, learners use intuitive symbols that map directly to their meaning. E+ is multilingual by design — every symbol has both an English and Bahasa Indonesia name, making it accessible to a global audience while remaining natural to Indonesian learners.", C.TEXT, 21),
      space(1),
      p("The COM IDE compiler reads E+ symbols, parses them using a regex-based scanner, and transpiles them into valid, runnable Python 3 code — automatically handling indentation, colons, and block structure.", C.MUTED, 20),
      space(2),
      h("Complete Symbol Dictionary", HeadingLevel.HEADING_1, C.ACCENT, 30),
      p("Every symbol in E+ v2.0. Symbols are grouped by category. The E+ column shows the symbol in context; the Python column shows the exact output the compiler generates.", C.MUTED, 20),
      space(1),
      buildDictTable(),
      space(2),
      h("Grammar Rules", HeadingLevel.HEADING_1, C.ACCENT, 30),
      h("Rule 1 — Entity Declaration", HeadingLevel.HEADING_2, C.ACCENT2, 26),
      new Paragraph({ spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: "Every variable starts with @. Assignment uses = followed by Data in ( ).", font: "Segoe UI", size: 21 })] }),
      new Paragraph({ spacing: { before: 40, after: 80 },
        children: [mono("@Score = (0)   →   score = 0", C.ACCENT2)] }),
      h("Rule 2 — Function Blueprint + Block", HeadingLevel.HEADING_2, C.ACCENT2, 26),
      new Paragraph({ spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: "Functions are declared with [ ] containing the name. Their body lives inside { }. Call with ^.", font: "Segoe UI", size: 21 })] }),
      new Paragraph({ spacing: { before: 40, after: 80 },
        children: [mono('[Greet](@name) { >> ("Hello " + @name) }   →   def greet(name): print("Hello " + name)', C.ACCENT2)] }),
      h("Rule 3 — Condition Chain", HeadingLevel.HEADING_2, C.ACCENT2, 26),
      new Paragraph({ spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: "Always: ? first, then any number of ??, then :: for the fallback.", font: "Segoe UI", size: 21 })] }),
      new Paragraph({ spacing: { before: 40, after: 80 },
        children: [mono("? (A) { } ?? (B) { } :: { }   →   if A: ... elif B: ... else: ...", C.ACCENT2)] }),
      h("Rule 4 — Loop Forms", HeadingLevel.HEADING_2, C.ACCENT2, 26),
      new Paragraph({ spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: "@@ = counted loop or for-each. @@? = while loop. Loop body always in { }.", font: "Segoe UI", size: 21 })] }),
      new Paragraph({ spacing: { before: 40, after: 80 },
        children: [mono("@@ (@i, 10) { }   →   for i in range(10):    |    @@? (@x > 0) { }   →   while x > 0:", C.ACCENT2)] }),
      h("Rule 5 — Input / Output", HeadingLevel.HEADING_2, C.ACCENT2, 26),
      new Paragraph({ spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: "<< pulls data in from the user. >> pushes data out to the screen. Never swap them.", font: "Segoe UI", size: 21 })] }),
      new Paragraph({ spacing: { before: 40, after: 100 },
        children: [mono('@Name = << ("Enter name: ")   >>   name = input("Enter name: ")', C.ACCENT2)] }),
      hr(),
      h("Worked Examples", HeadingLevel.HEADING_1, C.ACCENT, 30),
      ...scenarioBlock(
        "Scenario 1 — Simple Greeting",
        '@Name = << ("What is your name? ")\n>> ("Hello, " + @Name + "!")',
        'name = input("What is your name? ")\nprint("Hello, " + name + "!")',
        "Declare a variable, get input, print output. The most basic E+ program."
      ),
      ...scenarioBlock(
        "Scenario 2 — Age Gate (Condition)",
        '@Age = << ("How old are you? ")\n? (@Age > 17) {\n    >> ("Welcome in!")\n} ?? (@Age > 12) {\n    >> ("You are a teenager.")\n} :: {\n    >> ("Entry denied.")\n}',
        'age = int(input("How old are you? "))\nif age > 17:\n    print("Welcome in!")\nelif age > 12:\n    print("You are a teenager.")\nelse:\n    print("Entry denied.")',
        "Full condition chain: ? (if) + ?? (elif) + :: (else). Block structure enforces nesting."
      ),
      ...scenarioBlock(
        "Scenario 3 — Counting Loop",
        '@Total = (0)\n@@ (@i, 10) {\n    + @Total (@i)\n}\n>> ("Sum: " + @Total)',
        'total = 0\nfor i in range(10):\n    total += i\nprint("Sum: " + str(total))',
        "Counted loop using @@, incrementing a variable with +, then pushing the result."
      ),
      ...scenarioBlock(
        "Scenario 4 — Function with Return",
        '[Add](@a, @b) {\n    @Result = (@a + @b)\n    => (@Result)\n}\n@Answer = ^[Add](10, 25)\n>> (@Answer)',
        'def add(a, b):\n    result = a + b\n    return result\nanswer = add(10, 25)\nprint(answer)',
        "Blueprint definition with parameters, return with =>, and invocation with ^."
      ),
      ...scenarioBlock(
        "Scenario 5 — List + Loop",
        '@Fruits = [ ]\n+@ @Fruits ("Apple")\n+@ @Fruits ("Mango")\n+@ @Fruits ("Durian")\n@@ (@item, @Fruits) {\n    >> (@item)\n}',
        'fruits = []\nfruits.append("Apple")\nfruits.append("Mango")\nfruits.append("Durian")\nfor item in fruits:\n    print(item)',
        "Declare an empty list, append items with +@, iterate with for-each @@."
      ),
      ...scenarioBlock(
        "Scenario 6 — While Loop with Break",
        '@Count = (10)\n@@? (@Count > 0) {\n    >> (@Count)\n    - @Count (1)\n    ? (@Count == 5) { ! }\n}',
        'count = 10\nwhile count > 0:\n    print(count)\n    count -= 1\n    if count == 5:\n        break',
        "While loop with @@?, decrement with -, and an early exit using ! (break)."
      ),
      hr(),
      h("Quick Reference Card", HeadingLevel.HEADING_1, C.ACCENT, 30),
      new Table({
        width: { size: 8926, type: WidthType.DXA },
        columnWidths: [2231, 2231, 2231, 2233],
        rows: [
          headerRow(["Entity & I/O", "Functions & Flow", "Conditions & Loops", "Operators & Misc"], [2231,2231,2231,2233]),
          new TableRow({ children: [
            new TableCell({ borders: BORDERS, width: { size: 2231, type: WidthType.DXA }, shading: { fill: C.SYMBOL_BG, type: ShadingType.CLEAR }, margins: CELL_MARGIN,
              children: [
                new Paragraph({ children: [mono("@Name", C.ACCENT2)], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Entity/Variable",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono('<< ("prompt")', C.ACCENT2)], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Input",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono('>> ("text")', C.ACCENT2)], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Output",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("~~  @Var", C.ACCENT2)], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Delete var",size:18,font:"Segoe UI",color:C.MUTED})] }),
              ]}),
            new TableCell({ borders: BORDERS, width: { size: 2231, type: WidthType.DXA }, shading: { fill: C.GREEN_BG, type: ShadingType.CLEAR }, margins: CELL_MARGIN,
              children: [
                new Paragraph({ children: [mono("[Name] { }", "#1B5E20")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Define function",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("^[Name]", "#1B5E20")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Call function",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("=> (@x)", "#1B5E20")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Return value",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("## note", "#1B5E20")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Comment",size:18,font:"Segoe UI",color:C.MUTED})] }),
              ]}),
            new TableCell({ borders: BORDERS, width: { size: 2231, type: WidthType.DXA }, shading: { fill: C.ORANGE_BG, type: ShadingType.CLEAR }, margins: CELL_MARGIN,
              children: [
                new Paragraph({ children: [mono("? (cond) { }", "#E65100")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = if",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("?? (cond) { }", "#E65100")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = elif",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono(":: { }", "#E65100")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = else",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("@@ (@i, n) { }", "#E65100")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = for loop",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("@@? (cond) { }", "#E65100")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = while loop",size:18,font:"Segoe UI",color:C.MUTED})] }),
              ]}),
            new TableCell({ borders: BORDERS, width: { size: 2233, type: WidthType.DXA }, shading: { fill: C.PURPLE_BG, type: ShadingType.CLEAR }, margins: CELL_MARGIN,
              children: [
                new Paragraph({ children: [mono("== != > < >= <=", "#4A148C")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Compare",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("&& ||", "#4A148C")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = AND / OR",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("+ - * /", "#4A148C")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [new TextRun({text:" = Arithmetic",size:18,font:"Segoe UI",color:C.MUTED})] }),
                new Paragraph({ children: [mono("! = break   !! = exit", "#4A148C")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [mono("% = property", "#4A148C")], spacing:{before:40,after:20} }),
                new Paragraph({ children: [mono("+@ = append to list", "#4A148C")], spacing:{before:40,after:20} }),
              ]}),
          ]})
        ]
      }),
      space(2),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 200, after: 0 },
        children: [new TextRun({ text: "E+ Language v2.0  ·  COM IDE  ·  Bilingual EN / ID  ·  github.com/your-repo", size: 18, color: C.MUTED, font: "Segoe UI" })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/workspace/com_output/E+_Official_Dictionary_v2.docx", buf);
  console.log("Done: E+_Official_Dictionary_v2.docx");
});
