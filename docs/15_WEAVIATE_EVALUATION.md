# Weaviate Evaluation — Viability & Build Assessment (VBA)

> Status: **HOLD / NOT SELECTED FOR PHASE 1**  
> Owner: Vachan.ai architecture council  
> Last reviewed: 2026-07-01

---

## 1. What was evaluated

Weaviate as the vector / memory backend for Vachan's per-persona knowledge base, correction learning, and MCP/voice-agent integration.

Research sources:
- Weaviate docs: https://docs.weaviate.io
- Weaviate MCP server: https://docs.weaviate.io/weaviate/configuration/mcp-server
- Verba (archived RAG UI): https://github.com/weaviate/Verba
- Quivr: https://github.com/QuivrHQ/quivr
- Onyx (ex-Danswer): https://github.com/onyx-dot-app/onyx
- Mem0: https://github.com/mem0ai/mem0
- LangMem: https://github.com/langchain-ai/langmem
- Letta: https://github.com/letta-ai/letta
- memary: https://github.com/kingjulio8238/memary

---

## 2. Why it is attractive

| Capability | Why it matters for Vachan |
|---|---|
| Native hybrid search (BM25 + vector fusion) | Better recall for mixed Hinglish/English queries and named entities. |
| Multi-tenancy | One tenant per persona gives clean isolation and lifecycle control. |
| Built-in MCP server (`/v1/mcp`) | Voice agents could query memory directly without a custom MCP bridge. |
| HNSW + quantization | Handles larger memory corpora than pgvector comfortably. |
| RBAC + tenant-scoped permissions | Safer external agent access. |

---

## 3. Why we are NOT using it now

1. **Operational complexity.** Vachan Phase 1 targets an open-source, easy-to-run project. Adding a second production service conflicts with that goal.
2. **Current scale is small.** pgvector is sufficient for the first few personas and correction-learning experiments.
3. **MCP server is preview.** API may change; pinning to a preview feature before V1 is risky.
4. **Postgres is already in the stack.** RLS, migrations, backups, and team fluency are already solved there.
5. **Persona isolation can be modeled in SQL.** `persona_id` + Row-Level Security gives us acceptable isolation for the MVP.

---

## 4. Current decision

**Use Postgres + pgvector for Phase 1 / MVP / open-source release.**

Weaviate stays on the roadmap as the likely Phase 2 backend if any of the following become true:
- Memory per persona exceeds ~5–10M vectors.
- Hybrid recall quality with pgvector is visibly worse than Weaviate in user tests.
- Voice agents need direct memory access via MCP and maintaining our own MCP bridge becomes painful.
- Multi-modal memory (images, audio) becomes a requirement.

---

## 5. Production / deployment checklist — **NEED TO BE CHECKED** before revisiting

> The items below are intentionally left unresolved. Revisit this file when deployment or production scale is near.

- [ ] **Deployment model:** self-hosted Docker/K8s vs Weaviate Cloud (WCD) vs embedded mode. **Need to be checked** at deployment phase.
- [ ] **Cost projection at target scale.** **Need to be checked** before production budget lock.
- [ ] **Backup / disaster recovery:** incremental backups, tenant restore, point-in-time recovery. **Need to be checked** at deployment phase.
- [ ] **AuthZ audit:** confirm RBAC roles map to Vachan org/user/persona model. **Need to be checked** before production.
- [ ] **MCP server stability:** verify Weaviate MCP is GA and tool surface covers delete/aggregate/reference traversal. **Need to be checked** before relying on it.
- [ ] **Multi-node behavior:** test hybrid recall and tenant activation latency in a clustered setup. **Need to be checked** at scale phase.
- [ ] **Migration path:** dual-write + backfill script from `persona_kb_entries` to Weaviate. **Need to be checked** before cutover.
- [ ] **Operational runbook:** on-call alerts, upgrades, indexing load, memory usage. **Need to be checked** before production.
- [ ] **DPDP / data residency:** where tenant data lives and how erasure works. **Need to be checked** before production.
- [ ] **Embedding hosting:** self-hosted (Ollama) vs API modules; latency and key management. **Need to be checked** at deployment phase.

---

## 6. POC recipe (kept for future reference)

If we revisit Weaviate, run this first:

```bash
docker run -p 8080:8080 -p 50051:50051 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -e MCP_SERVER_ENABLED=true \
  -e MCP_SERVER_WRITE_ACCESS_ENABLED=true \
  semitechnologies/weaviate:1.37.1
```

Then model one `Memory` collection with multi-tenancy enabled and one tenant per persona. Test hybrid recall and MCP tool calls against a held-out query set before any migration.

---

## 7. Bottom line

Weaviate is the stronger long-term backend for Vachan's memory vision, but it is **not the right choice for the first open-source release**. Postgres + pgvector keeps the project simple, self-contained, and production-ready enough for the initial phase. Re-open this VBA when scale, recall quality, or MCP ergonomics force the conversation.
