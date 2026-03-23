# ACG Agents Guide

## Code Standards

### 0) Quality Improvements (2026-03-14)

#### 2026-03-15: Social Network and Daily Life System
- **Social network module** (`novel_engine/core/social_network.py`): 
  - Relationship types: 陌生人，朋友，死党，竞争对手，暗恋，暧昧，崇拜，嫉妒，师生关系，敌对，小团体成员，室友，同桌
  - Relationship metrics: score (-100~100), trust (0~100), intimacy (0~100), conflicts, positive_interactions, memories
  - Social circles: 核心圈 (strength>=120), 熟人圈 (60-119), 泛泛之交 (<60)
  - Auto-evolution of relationship types based on interaction history
  - Interest affinity calculation for relationship building
- **Daily events generator** (`novel_engine/core/daily_events.py`):
  - 6 scenes: 教室，食堂，操场，宿舍，走廊，图书馆
  - 30+ daily life event templates with realistic high school interactions
  - Context-aware event generation based on relationships and intimacy levels
  - Events include relation_delta, mood_delta, trust_delta, intimacy_delta
- **Enhanced Person model**:
  - Added `interests` (List[str]) - hobbies and interests
  - Added `values` (List[str]) - personal values and beliefs
  - Expanded archetypes to 20 types (学霸型，社交型，特长型，性格型)
  - Expanded background data: 15 families, 20 quirks, 15 flaws
  - Expanded database: 20 interests, 10 specialties, 8 values
- **Config simplification**: Removed complex metaclass lazy loading; prompts now load at module import time for reliability
- **Type annotations**: Added complete type hints to Config class (e.g., `tuple[str, ...]` for `ELITE_TAGS`)
- **Cache mechanism**: NPCData uses ClassVar caches with manual memoization (not `lru_cache`) for testability
- **Error handling**: All DB methods raise `ValueError` with clear messages when data is missing
- **Code organization**: 
  - Imports cleaned up (removed unused `ClassVar`, `TypedDict`)
  - Line formatting standardized (max 88 chars)
  - Docstrings removed where code is self-explanatory

#### Previous Improvements
- **API resilience**: Timeout (90s) + retry (3 attempts, exponential backoff) in `ai_writer.py`
- **Performance**: Social graph validation runs only in debug mode (skip O(n²) in production)
- **Input validation**: Event records validated before DB sync in `events_extraction/`

### 1) Runtime and tooling
- Use `uv` as the only Python workflow tool (`uv run ...`).
- Do not reintroduce ad-hoc `requirements`-first flows.

### 2) Type and contract rules
- Boundary I/O must be validated with Pydantic models in `novel_engine/core/contracts.py`.
- Core logic consumes typed models/objects, not loose `dict[str, Any]`.
- Keep `extra="forbid"` for contract models to prevent schema drift.
- Use fail-fast semantics: invalid input/config/data should raise immediately.

### 3) Domain modeling rules
- Keep role semantics unified in English literals (`protagonist/classmate/teacher`) in core state.
- Keep person-related mapping centralized in `person.py` (`from_profile`, `to_profile`, `from_state`, `to_state`).
- Avoid string-protocol parsing in core logic (no hidden parsing fallback paths).

### 4) Prompt management rules
- All AI prompt texts/templates live in `text_for_gen/prompts.yaml`.
- Access prompts only through `Config` typed keys in `config.py`.
- Do not hardcode prompt text in `ai_writer.py` / `main.py` business flow.
- Keep technical controls (timeouts, token caps, retry policy) in code, not YAML prose sections.

### 5) Readability rules
- Prefer explicit flow orchestration over thin wrapper/helper chains.
- Remove low-value passthrough helpers and duplicated mapping layers.
- Keep comments short and only for non-obvious logic blocks.

## Structure Standards

### 1) Layering and dependency direction
- `novel_engine/core/*`: domain logic only (engine/person/plan orchestration), no loose JSON parsing.
- `novel_engine/data/*`: storage/query layer only (sqlite/data loading), no chapter prompt orchestration.
- Entry files (`main.py`, `generate_full_plan.py`) are the only top-level process orchestrators.
- Dependency direction must be one-way: `entry -> core -> data`; avoid reverse imports.

### 2) Contract boundaries
- All persisted or loaded boundary data must use models in `novel_engine/core/contracts.py`.
- Core modules exchange typed objects/models, not `dict[str, Any]` payload protocols.
- Any schema change must be reflected in tests under `tests/test_40+`.

### 3) Module ownership
- `being_engine.py`: weekly simulation flow and state transitions only.
- `person.py`: person lifecycle/state mapping (`from_profile/to_profile/from_state/to_state`).
- `plan_builder.py`: weekly script/world settings build pipeline only.
- `presenters.py` + `view_models.py`: text rendering and display DTOs only.
- `ai_writer.py`: LLM call + generation control only; no business state mutation.

### 4) Naming and conventions
- Keep role semantics in English literals: `protagonist/classmate/teacher`.
- Keep placeholders unified: `{p1}/{p2}/{p3}/{p4}`.
- Do not introduce synonym constants for same semantic value.
- Prefer descriptive function names by behavior; avoid thin wrappers that only forward params.

## Test Workflow

### 0) Rerun hygiene (default, required)
- Any logic/config/prompt/event-pool change that affects generation must start from a clean runtime output state.
- Default behavior is **archive-then-rerun** (do not continue from stale `save_state.json`).

```bash
ts=$(date +%Y%m%d_%H%M%S)
archive_dir="archive/cleanup_${ts}"
mkdir -p "$archive_dir/novel_chapters" "$archive_dir/test_reports" "$archive_dir/events_extraction"

shopt -s nullglob
for f in novel_chapters/Chapter_*.txt; do mv "$f" "$archive_dir/novel_chapters/"; done
for f in save_state.json simulation_trace.jsonl plot_summary.txt world_settings.json weekly_script.json; do
  [ -e "$f" ] && mv "$f" "$archive_dir/"
done
for f in events_extraction/raw_moments.jsonl events_extraction/moments_extracted.jsonl events_extraction/.agent_events_pid; do
  [ -e "$f" ] && mv "$f" "$archive_dir/events_extraction/"
done
for d in __pycache__ events_extraction/__pycache__ .pytest_cache; do
  [ -d "$d" ] && mv "$d" "$archive_dir/"
done
mkdir -p test_reports
```

Then regenerate from scratch:
```bash
uv run python generate_full_plan.py
```
- Optional chapter rerun:
```bash
uv run python main.py --chapter-range 1-5
```

### A) Fast local gate (before commit)
1. Static compile:
```bash
uv run python -m py_compile config.py main.py generate_full_plan.py novel_engine/core/*.py novel_engine/data/*.py tests/*.py
```
2. Type check:
```bash
uv run pyright novel_engine/core novel_engine/data
```
3. Core static test:
```bash
uv run pytest -q tests/test_10_static_checks.py
```

### B) Full regression gate
```bash
uv run pytest -q tests
```

Current canonical suite includes:
- `test_00_api_key.py` (API connectivity and key checks)
- `test_10_static_checks.py` (compile + pyright)
- `test_40_fail_fast_semantics.py` (fail-fast validation)
- `test_41_schema_validation.py` (Pydantic schema enforcement)
- `test_42_engine_state_roundtrip.py` (state serialization)
- `test_43_presenters.py` (view rendering)
- `test_44_data_boundary_models.py` (boundary contracts)
- `test_45_person_unit.py` (Person class unit tests - TDD ready)
- `test_46_person_elite_semantics.py` (elite vs normal semantics)
- `test_47_engine_business.py` (BeingEngine core logic - TDD ready)
- `test_49_database_fail_fast.py` (DB fail-fast)
- `test_50_event_social_mood.py` (event and social graph)
- `test_20_generate_plan.py` (plan generation)
- `test_30_run_one_chapter.py` (single chapter generation)
- `test_40+` semantic/contract fail-fast and boundary model tests

### C) Recommended execution order for diagnosis
1. `test_10_static_checks.py`
2. `test_45_person_unit.py` + `test_47_engine_business.py` (unit tests)
3. Full suite (`tests/`) for final verification

### D) TDD Development Guidelines (2026-03-15)
- **Red-Green-Refactor**: Write failing test first, implement minimal code, then refactor
- **Unit test priority**: `test_45_person_unit.py` and `test_47_engine_business.py` are TDD-ready
- **Test isolation**: Each test should be independent and repeatable
- **Boundary testing**: Include tests for edge cases, null values, and error conditions
- **Business rule coverage**: Tests verify exam scores, growth multipliers, fatigue, breakdown logic
- **Fail-fast semantics**: Invalid input should raise immediately with clear error messages

## Commit Checklist
- Prompt changes are in `text_for_gen/prompts.yaml` + `config.py` keys only.
- No new fallback/default-silencing behavior introduced.
- Pydantic contract changes are reflected in tests.
- `uv run pytest -q tests` passes.

## Events Extraction Ops

### 1) Incremental extraction (resume by default)
```bash
set -a; . ./.env; set +a
uv run python events_extraction/extract_agent_events.py --limit 20 --sleep 0
```
- Resume files:
  - `events_extraction/.agent_events_done_chunks.txt`
  - `events_extraction/.agent_events_checkpoint.json`
- Output file:
  - `events_extraction/agent_events.jsonl`
- DB sync:
  - automatically syncs into `novel_engine/data/storage/world_data.db` table `event_pool` (source=`merged`)
  - use `--no-sync-db` to disable auto sync

### 2) Reset progress (do not delete output)
```bash
uv run python events_extraction/extract_agent_events.py --reset-progress --limit 0
```

### 2.1) Rebuild output from scratch (single-pass final format)
```bash
set -a; . ./.env; set +a
uv run python events_extraction/extract_agent_events.py --reset-progress --reset-output --sleep 0
```
- Output is final format directly:
  - `【时间·地点】` prefix
  - `{p1}/{p2}/{p3}/{p4}` placeholders

### 2.2) Sync events into DB unified pool
```bash
uv run python helper/sync_event_pool.py
```
- Mostly for one-shot rebuild/migration; daily extraction flow already auto-syncs via `extract_agent_events.py`.
- Target table:
  - `event_pool` in `novel_engine/data/storage/world_data.db`
- Sources:
  - `events_extraction/legacy_events_cleaned.jsonl` (preferred if present)
  - legacy `events` table (fallback)
  - `events_extraction/agent_events.jsonl`

### 2.3) AI normalize legacy events to `{p1...}` format
```bash
set -a; . ./.env; set +a
uv run python helper/normalize_legacy_events_with_llm.py --reset --batch-size 20 --sleep 0
```
- Output:
  - `events_extraction/legacy_events_cleaned.jsonl`
- Resume checkpoint:
  - `events_extraction/.legacy_events_clean_checkpoint.json`

### 3) Temp file cleanup
```bash
rm -f events_extraction/raw_moments.jsonl events_extraction/moments_extracted.jsonl
rm -rf events_extraction/__pycache__
```
- Keep only the active extraction script:
  - `events_extraction/extract_agent_events.py`

### 4) Optional legacy cleaner
```bash
set -a; . ./.env; set +a
uv run python events_extraction/clean_agent_events_with_llm.py --reset --batch-size 20 --sleep 0
```
