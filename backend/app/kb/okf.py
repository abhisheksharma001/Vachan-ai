"""
OKF (Open Knowledge Format) rendering for per-persona knowledge.

Spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

Each PersonaKBEntry is one OKF "concept": a typed, tagged unit of knowledge
with a YAML-frontmatter header and a markdown body. This module only renders
that shape — it deliberately does NO retrieval/search infrastructure (OKF's
own non-goals, spec §1): a single persona's knowledge base is small enough in
Phase 1 to inject the whole bundle into the system prompt, so there is no
vector store / embedding pipeline to build or run.
"""
from __future__ import annotations

import yaml

from app.models.tables import PersonaKBEntry

# Keep the injected KB block small relative to the rest of the system prompt
# (voice description, hard rules, anchors) so it can never crowd those out.
_DEFAULT_MAX_BUNDLE_CHARS = 4000


def concept_id(entry: PersonaKBEntry) -> str:
    """A stable, path-like OKF concept id for this entry (§2 Concept ID)."""
    slug = "-".join((entry.title or entry.type).strip().lower().split())
    return f"{entry.type.lower()}/{slug}-{str(entry.id)[:8]}"


def render_concept(entry: PersonaKBEntry) -> str:
    """Render one entry as a full OKF concept document (frontmatter + body, §4)."""
    front_matter = {
        "type": entry.type,
        "title": entry.title,
        "description": entry.description,
        "tags": entry.tags or [],
        "timestamp": entry.updated_at.isoformat() if entry.updated_at else None,
    }
    front_matter = {k: v for k, v in front_matter.items() if v not in (None, [], "")}
    return f"---\n{yaml.safe_dump(front_matter, sort_keys=False)}---\n\n{entry.body.strip()}\n"


def render_index(entries: list[PersonaKBEntry]) -> str:
    """Render an OKF index.md: entries grouped by `type` (§6)."""
    by_type: dict[str, list[PersonaKBEntry]] = {}
    for e in entries:
        by_type.setdefault(e.type, []).append(e)

    sections: list[str] = []
    for type_name, group in by_type.items():
        lines = [f"# {type_name}"]
        for e in group:
            title = e.title or e.body.strip().splitlines()[0][:60]
            desc = f" - {e.description}" if e.description else ""
            lines.append(f"* [{title}]({concept_id(e)}.md){desc}")
        sections.append("\n".join(lines))
    return ("\n\n".join(sections) + "\n") if sections else ""


def render_bundle_context(
    entries: list[PersonaKBEntry], max_chars: int = _DEFAULT_MAX_BUNDLE_CHARS
) -> str:
    """Render entries as a compact block for chat-time prompt injection.

    Newest first, truncated to `max_chars`. This is the Phase-1 "corpus is
    small, load it all" strategy OKF was chosen for — not semantic search.
    """
    if not entries:
        return ""
    ordered = sorted(entries, key=lambda e: e.created_at, reverse=True)
    blocks: list[str] = []
    used = 0
    for e in ordered:
        header = f"[{e.type}]" + (f" {e.title}" if e.title else "")
        block = f"{header}\n{e.body.strip()}"
        if blocks and used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def entry_to_dict(entry: PersonaKBEntry) -> dict:
    """JSON-friendly view of an entry for the KB CRUD API."""
    return {
        "id": str(entry.id),
        "type": entry.type,
        "title": entry.title,
        "description": entry.description,
        "tags": entry.tags or [],
        "body": entry.body,
        "source": entry.source,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }
