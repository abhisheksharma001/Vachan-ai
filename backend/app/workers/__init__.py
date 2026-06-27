"""
Workers — Layer that drains the ingress queue and runs the engine.

Phase 0 ships ONE worker: the echo worker (no LLM), which proves the whole
pipeline web → ingress → queue → worker → echo back, and lands a sanitized
writing sample in persona_observations. Phase 1 replaces the echo step with the
real supervisor → domain agent → persona renderer chain.
"""
