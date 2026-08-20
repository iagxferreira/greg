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
- **Feedback logging is best-effort and stores compact candidate summaries** — `log_resolution`
  (`src/feedback.py`) catches and swallows its own DB errors (warns to stderr) so a broken feedback
  pipeline never breaks resolution itself. Logged `candidates` keep only `id`/`name`/`iso2`/
  `similarity` per candidate, not the full enriched `content` text — that text is reconstructible
  from `id` via the `countries` table, and repeating it per feedback row would bloat storage for no
  training benefit.
- **Second fallback provider (e.g. geocode.xyz) deferred** — considered and explicitly declined for
  now (2026-08-20): no data yet on how often Nominatim actually fails, and provider-chaining adds
  real complexity (precedence, config, error handling) for an unvalidated need. Revisit once
  `resolution_feedback` has enough `nominatim_fallback` rows to show the real failure rate.
- **`ollama-init`'s command must go in `entrypoint` as one list item, not a separate `command`
  string** — `docker compose config` was used to validate `docker-compose.yml` (no Docker daemon was
  available to actually run it) and caught that `entrypoint: ["/bin/sh", "-c"]` paired with
  `command: "ollama pull mistral:latest && ollama pull nomic-embed-text"` got silently truncated to
  just `ollama pull mistral:latest` — Compose's string-command normalization doesn't preserve `&&`
  chaining. Folding the full shell command into `entrypoint` itself as a third list element
  (`entrypoint: ["/bin/sh", "-c", "cmd1 && cmd2"]`) round-trips through `docker compose config`
  intact. Always run `docker compose config` after editing multi-command entrypoints — the bug is
  silent otherwise (the container still starts, it just doesn't do what you wrote).
- **`CountryResult` used directly as FastAPI's `response_model`, no separate Pydantic model** —
  FastAPI serializes stdlib dataclasses natively, so `src/api.py` reuses `src/models.py`'s
  `CountryResult` as-is rather than hand-maintaining a parallel Pydantic schema that could drift
  from it. Revisit only if the API response shape ever needs to diverge from the internal one
  (e.g. hiding an internal-only field).
- **`GET /v1/countries/resolve` despite writing to `resolution_feedback`** — the write is an
  internal logging side-effect the caller doesn't control or see, not a resource mutation from the
  API's point of view; `resolve_country` (called by both the CLI and this endpoint) always logs
  regardless of transport. Kept as `GET` since the endpoint semantically is a lookup and that's
  what a client of this API expects to call it as.
