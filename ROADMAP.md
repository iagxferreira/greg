# Roadmap

Tracks the phased plan for turning geo-resolution-rag into a production-ready system. Each numbered
step lands as its own PR — see [CONVENTIONS.md](CONVENTIONS.md) for the workflow.

## Phase 0 — Foundations

- [x] 1. `chore/uv-migration` — replace `requirements.txt` with `pyproject.toml` + `uv.lock`; update
      install/run commands in README and CLAUDE.md.
- [x] 2. `chore/ruff-lint` — add ruff lint + format config, fix violations.
- [x] 3. `docs/architecture-and-conventions` — rewrite CLAUDE.md's Architecture/Commands sections to
      match the real Ollama + pgvector, country-only-so-far system.
- [x] 4. `test/pytest-scaffold` — pytest config + unit tests for `models.CountryResult`,
      `prompt.format_country_candidates`, and a resolver test with mocked `llm`/`vector_store`.

## Phase 1 — Known gap (backlog, not scheduled)

`src/loaders/cities.py` and `src/loaders/states.py` populate the `cities` and `states` tables and
`vector_store.py` can search them, but there is no `resolve_city`/`resolve_state`, no prompt, and no
CLI wiring for either — unlike what the README's feature list implies. City/state resolution is a
backlog item, not part of the current pass.

## Phase 2 — Resilience

- [x] 5. `feat/nominatim-fallback` — when `resolve_country` returns `matched=False` or low confidence,
      fall back to Nominatim (OpenStreetMap) geocoding. Scoped to country resolution since that's the
      only resolver that exists today.

## Phase 3 — Feedback loop groundwork

- [x] 6. `feat/feedback-logging` — new `resolution_feedback` Postgres table (migration
      `004_create_resolution_feedback_table.sql`) logging each resolution's query, source (`rag` vs
      `nominatim_fallback`), matched result, confidence, and candidate set. This is the data a future
      reranker needs to train on.

## Phase 4 — Bandit-style reranking (future, blocked on Phase 3 data)

Use logged outcomes from Phase 3 to train a lightweight contextual bandit / learned reranker that
reorders pgvector candidates before they hit the LLM. Not implemented yet — there's no reward signal
to learn from until Phase 3 has been running and accumulating data.

## Phase 5 — Developer experience

- [ ] 7. `docs/readme-accuracy` — rewrite README's Usage/Example Resolutions/Architecture sections,
      which still describe the aspirational city-resolution + FAISS design, to match the real
      country-only CLI with the Nominatim fallback and feedback logging.
- [ ] 8. `feat/docker-dev-stack` — add an `ollama` service (+ a one-shot init service that pulls
      `mistral:latest`/`nomic-embed-text`) to `docker-compose.yml` alongside the existing `postgres`
      service, and auto-run `migrations/*.sql` on first Postgres start, so `docker compose up -d` is
      enough to get both dependencies running without a native Ollama install.
