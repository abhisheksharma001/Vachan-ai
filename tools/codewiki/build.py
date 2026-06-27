#!/usr/bin/env python3
"""
codewiki/build.py — generate an AI-readable map of the whole codebase.

WHAT THIS IS (plain English)
----------------------------
A "DeepWiki" for our own repo. It reads every Python file, pulls out each
module's purpose, its classes/functions (with signatures), and what imports
what — then writes one structured Markdown file, `docs/wiki/CODEMAP.md`.

Why: so an AI (Claude Code, etc.) — or a new teammate — can understand the
ENTIRE codebase from a single compact, always-current document, instead of
re-reading 20 files. It's deterministic (pure Python standard library, no API
key, no network), so you regenerate it any time the code changes:

    python3 tools/codewiki/build.py

n8n analogy: it's an auto-generated "map of all your nodes and how they're
wired", refreshed on demand.
"""
from __future__ import annotations

import ast
import datetime as _dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root
SCAN_DIRS = [ROOT / "backend" / "app"]              # source we map
OUT = ROOT / "docs" / "wiki" / "CODEMAP.md"
INTERNAL_PREFIX = "app."                            # our own package root


# ── helpers ──────────────────────────────────────────────────────────────
def _module_name(path: Path) -> str:
    """backend/app/core/llm.py → app.core.llm"""
    rel = path.relative_to(ROOT / "backend").with_suffix("")
    return ".".join(rel.parts)


def _first_line(doc: str | None) -> str:
    if not doc:
        return ""
    for line in doc.strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


def _sig(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = ast.unparse(node.args)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    kw = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{kw} {node.name}({args}){ret}"


def _internal_imports(tree: ast.Module) -> set[str]:
    """Other app.* modules this file imports (for the dependency graph)."""
    deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(INTERNAL_PREFIX):
            deps.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(INTERNAL_PREFIX):
                    deps.add(alias.name)
    return deps


def _parse(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    classes, functions = [], []
    for node in tree.body:  # top-level only
        if isinstance(node, ast.ClassDef):
            methods = [
                _sig(b)
                for b in node.body
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))
                and (not b.name.startswith("_") or b.name == "__init__")
            ]
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            classes.append(
                {"name": node.name, "bases": bases, "doc": _first_line(ast.get_docstring(node)), "methods": methods}
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            functions.append({"sig": _sig(node), "doc": _first_line(ast.get_docstring(node))})
    return {
        "module": _module_name(path),
        "path": str(path.relative_to(ROOT)),
        "doc": _first_line(ast.get_docstring(tree)),
        "classes": classes,
        "functions": functions,
        "deps": sorted(_internal_imports(tree)),
        "loc": src.count("\n") + 1,
    }


def _collect() -> list[dict]:
    files: list[Path] = []
    for base in SCAN_DIRS:
        files += sorted(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    out = []
    for f in files:
        try:
            out.append(_parse(f))
        except Exception as exc:  # never let one bad file kill the map
            out.append({"module": _module_name(f), "path": str(f.relative_to(ROOT)),
                        "doc": f"(parse error: {exc})", "classes": [], "functions": [], "deps": [], "loc": 0})
    return out


def _docs_index() -> list[tuple[str, str]]:
    out = []
    for md in sorted((ROOT / "docs").glob("*.md")):
        title = ""
        for line in md.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        out.append((md.name, title))
    return out


# ── rendering ────────────────────────────────────────────────────────────
def _render(mods: list[dict]) -> str:
    known = {m["module"] for m in mods}
    L: list[str] = []
    a = L.append

    a("# Vachan.ai — CODEMAP (auto-generated)")
    a("")
    a("> **Do not edit by hand.** Regenerate with `python3 tools/codewiki/build.py`.")
    a("> An AI-readable map of the whole backend: every module's purpose, its")
    a("> public classes/functions, and how modules depend on each other.")
    a("> Ask questions against it with `tools/codewiki/ask.py` (see that file).")
    a("")
    a(f"_Generated {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')} • "
      f"{len(mods)} modules • {sum(m['loc'] for m in mods)} lines._")
    a("")

    # Dependency graph (internal imports only).
    a("## Module dependency graph")
    a("")
    a("```mermaid")
    a("graph LR")
    edges = 0
    for m in mods:
        src = m["module"].replace(".", "_")
        for dep in m["deps"]:
            if dep in known and dep != m["module"]:
                a(f"  {src}[{m['module']}] --> {dep.replace('.', '_')}[{dep}]")
                edges += 1
    if edges == 0:
        a("  note[no internal imports yet]")
    a("```")
    a("")

    # Per-module detail.
    a("## Modules")
    a("")
    for m in sorted(mods, key=lambda x: x["module"]):
        a(f"### `{m['module']}`")
        a(f"_{m['path']} · {m['loc']} lines_")
        if m["doc"]:
            a("")
            a(m["doc"])
        if m["deps"]:
            a("")
            a("**Depends on:** " + ", ".join(f"`{d}`" for d in m["deps"] if d in known))
        for c in m["classes"]:
            base = f"({c['bases']})" if c["bases"] else ""
            a("")
            a(f"- **class `{c['name']}`{base}** — {c['doc']}")
            for meth in c["methods"]:
                a(f"  - `{meth}`")
        for fn in m["functions"]:
            a("")
            a(f"- `{fn['sig']}` — {fn['doc']}")
        a("")

    # Conceptual docs index.
    a("## Conceptual docs (the 'why')")
    a("")
    a("The `/docs` wiki explains intent; this CODEMAP explains the code. Pair them.")
    a("")
    for name, title in _docs_index():
        a(f"- [`{name}`](../{name}) — {title}")
    a("")
    return "\n".join(L)


def main() -> None:
    mods = _collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(_render(mods), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}  ({len(mods)} modules)")


if __name__ == "__main__":
    main()
