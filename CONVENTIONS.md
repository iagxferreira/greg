# Conventions

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), kept atomic (one logical change per
commit): `type(scope): summary`.

Types used in this repo: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `build`.

## Branches & PRs

- Branch naming: `type/short-slug`, branched from `master` (matches the commit type driving the
  branch, e.g. `feat/nominatim-fallback`).
- One PR per [ROADMAP.md](ROADMAP.md) step. Each PR is opened and left for review/merge — the next
  step branches from `master` only after the previous PR has merged, so roadmap steps land in order.

## Tradeoffs log

Decisions worth remembering, in the order they were made:

- **uv over pip/poetry** — single lockfile (`uv.lock`), fast installs, drop-in pip-compatible,
  no separate venv tooling to manage.
- **ruff over black + flake8 + isort** — one fast tool instead of three separately configured ones.
- **Nominatim over Google Maps Geocoding** for the RAG fallback — free, no API key or billing setup.
  Tradeoff: the public instance is rate-limited to ~1 req/sec and less accurate on ambiguous queries.
  Treated as an explicit stopgap — revisit if fallback volume grows enough to need a paid provider.
- **Feedback logging before bandit reranking** — a bandit reranker has nothing to learn from without
  logged outcomes, so logging (Phase 3) has to land and accumulate real data before the reranker
  (Phase 4) is buildable. Phase 4 stays a documented backlog item until then.
- **CLAUDE.md had gone stale** — it described an earlier Gemini + FAISS design after the code had
  moved to Ollama + pgvector, which would have misled future work on this repo. Lesson: update
  CLAUDE.md in the same PR as any architecture change, not as a separate cleanup later.
- **`FALLBACK_CONFIDENCE_THRESHOLD = 0.7`** — the RAG prompt (`src/prompt.py`) itself defines
  0.50–0.69 as a "weak/ambiguous match," so anything below the "strong match" floor of 0.70 also
  triggers the Nominatim fallback, not just `matched=False`. A successful fallback is assigned a
  fixed `FALLBACK_CONFIDENCE = 0.6` (`src/fallback.py`) since Nominatim doesn't produce a score on
  our 0–1 scale and a single unverified geocoder hit shouldn't be reported as more certain than a
  weak RAG match. On fallback failure the original RAG result is kept rather than surfacing the
  failure to the caller — degrade gracefully, don't turn a weak match into no match.
