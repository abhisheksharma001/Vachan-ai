<!--
GATED: do not send/run this pitch until CAPSULE_SPEC_v0.md has a public URL
(pushed to the repo, repo public or a design partner has read access). The
merge-gate story below is a claim without something a compliance buyer can
click through to. Sequence: items 1-3 (code fixes) -> item 4 (MCP tools) ->
item 5 (spec public) -> this brief goes out. Not before.
-->

# Vachan.ai — AI Tone Governance, Not Another Chatbot

## The problem (in their language)

Your AI agents generate customer-facing output with no audit trail, no
version history, and no human approval step before the agent's memory of
"how we sound" updates itself. If a bad data batch shifts your support
agent's tone, you find out from a customer complaint, not from a system that
caught it.

## What Vachan gives you that nothing else does

1. **A fidelity score on every reply (PFS)** — not a vibe check, a number,
   computed against your brand's actual measured writing style, gating
   whether a reply ships.
2. **A versioned, append-only voice history** — every change to your agent's
   tone is a numbered version with a timestamp and a consent record, never
   silently overwritten.
3. **A human approval gate before drift ships** — when new data would shift
   your agent's voice significantly, it's quarantined and flagged for a
   one-tap human review, not auto-merged into production.

## The merge gate, concretely

A noisy capture batch — a support agent's chat log with a different person's
replies mixed in — gets fed into the system. The tone shifts measurably
toward casual. Vachan's merge gate catches the shift before it goes live: the
new version is stored (nothing is lost) but does not become the version your
agent actually uses until a human approves it. The audit log shows exactly
what changed, when, and who signed off.

## The ask

A 30-minute call with whoever owns AI governance or agent quality on your
team.
