# ACG Agents Guide

## Code Standards

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

## Test Workflow

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
- `test_20_generate_plan.py` (plan generation)
- `test_30_run_one_chapter.py` (single chapter generation)
- `test_40+` semantic/contract fail-fast and boundary model tests

### C) Recommended execution order for diagnosis
1. `test_10_static_checks.py`
2. `test_20_generate_plan.py`
3. `test_30_run_one_chapter.py`
4. Full suite (`tests/`) for final verification

## Commit Checklist
- Prompt changes are in `text_for_gen/prompts.yaml` + `config.py` keys only.
- No new fallback/default-silencing behavior introduced.
- Pydantic contract changes are reflected in tests.
- `uv run pytest -q tests` passes.
