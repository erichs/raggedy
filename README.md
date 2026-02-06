# raggedy

Fix ragged right edges in LLM-generated ASCII/Unicode box diagrams.

LLMs consistently generate ASCII box diagrams with inconsistent right borders — missing corners, short rules, content lines without closing borders. `raggedy` autodetects these diagrams inside markdown fenced code blocks and fixes them.

## Install & Run

```bash
# Run directly with uvx (no install needed)
uvx raggedy file.md

# Or install with pip/uv
pip install raggedy
raggedy file.md
```

## Usage

```
raggedy [OPTIONS] FILE [FILE...]

Options:
  -b, --backup      Create .bak backup before editing
  --mdtable         Also fix markdown tables
  --check           Exit 1 if changes needed (no modification; for CI)
  --diff            Show diff without modifying
  -h, --help        Show help
```

## What It Fixes

Given a markdown file containing:

````
```
┌──────────────────┐
│ Header           │
├──────────────────┤
│ Row 1
│ Row 2 is longer content
│ Short
└──────────────────┘
```
````

Running `raggedy file.md` produces:

````
```
┌────────────────────────┐
│ Header                 │
├────────────────────────┤
│ Row 1                  │
│ Row 2 is longer content│
│ Short                  │
└────────────────────────┘
```
````

Supports both Unicode (`┌│├└`) and ASCII (`+|-`) box-drawing styles.

## CI Usage

Use `--check` in CI to enforce clean diagrams:

```bash
raggedy --check docs/**/*.md
```
