from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

DB_PATH = Path("novel_engine/data/storage/world_data.db")
AGENT_EVENTS_PATH = Path("events_extraction/agent_events.jsonl")
OUTPUT_PATH = Path("events_extraction/event_pool_rebuilt.jsonl")
DONE_PATH = Path("events_extraction/.event_pool_rebuild_done.txt")
CHECKPOINT_PATH = Path("events_extraction/.event_pool_rebuild_checkpoint.json")

PREFIX_PATTERN = re.compile(r"^【[^【】]{1,12}·[^【】]{1,16}】")
PLACEHOLDER_PATTERN = re.compile(r"\{p([1-4])\}")
ANY_PLACEHOLDER_PATTERN = re.compile(r"\{p(\d+)\}")

SYSTEM_PROMPT = (
    "你是校园事件标准化与社交标注器。"
    "把输入事件改写成可直接用于状态机的模板，并给出社交关系和心情变化数值。"
)

USER_TEMPLATE = """请处理这批事件，返回严格 JSON：
{{
  "items": [
    {{
      "uid": "x",
      "season": "ANY|SUMMER|WINTER",
      "template": "【课间·教室】{{p1}}向{{p2}}借笔记，{{p2}}拒绝后双方争执。",
      "effect": "stress+",
      "relation_delta": -4,
      "mood_delta": -3
    }}
  ]
}}

硬性要求：
1) template 必须以【时间·地点】开头，且至少包含 {{p1}} 和 {{p2}}，禁止真实人名。
2) relation_delta 取值范围 [-8,8] 且不能为 0。
3) mood_delta 取值范围 [-6,6] 且不能为 0。
4) season 只能是 ANY/SUMMER/WINTER。
5) effect 保留简短效果标签字符串；没有就给空字符串。
6) 每条输入都必须返回一条输出（uid 一一对应）。

输入：
{payload}
"""


def _ensure_event_pool_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS event_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            season TEXT NOT NULL DEFAULT 'ANY',
            template TEXT NOT NULL,
            effect TEXT NOT NULL DEFAULT '',
            relation_delta INTEGER NOT NULL DEFAULT 0,
            mood_delta INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            UNIQUE(source, template)
        )
        """
    )
    cursor.execute("PRAGMA table_info(event_pool)")
    cols = {row[1] for row in cursor.fetchall()}
    if "relation_delta" not in cols:
        cursor.execute("ALTER TABLE event_pool ADD COLUMN relation_delta INTEGER NOT NULL DEFAULT 0")
    if "mood_delta" not in cols:
        cursor.execute("ALTER TABLE event_pool ADD COLUMN mood_delta INTEGER NOT NULL DEFAULT 0")


def _load_legacy_events() -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT season, description, effect FROM events").fetchall()
    finally:
        conn.close()

    result: list[dict[str, Any]] = []
    for idx, (season, description, effect) in enumerate(rows, start=1):
        if not description:
            continue
        result.append(
            {
                "uid": f"legacy_{idx}",
                "source": "legacy",
                "season": str(season or "ANY"),
                "text": str(description).strip(),
                "effect": str(effect or "").strip(),
            }
        )
    return result


def _load_agent_events() -> list[dict[str, Any]]:
    if not AGENT_EVENTS_PATH.exists():
        return []
    result: list[dict[str, Any]] = []
    for idx, line in enumerate(AGENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        content = obj.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        result.append(
            {
                "uid": f"agent_{idx}",
                "source": "agent",
                "season": "ANY",
                "text": content.strip(),
                "effect": "",
            }
        )
    return result


def _load_done_uids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj if isinstance(obj, dict) else {}


def _save_checkpoint(path: Path, *, done_count: int, last_uid: str) -> None:
    payload = {
        "done_count": done_count,
        "last_uid": last_uid,
        "updated_at": int(time.time()),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_template(text: str) -> str:
    return " ".join(text.strip().split())


def _validate_template(template: str) -> None:
    if not PREFIX_PATTERN.match(template):
        raise ValueError(f"template missing prefix: {template}")
    if "{p1}" not in template or "{p2}" not in template:
        raise ValueError(f"template must include {{p1}} and {{p2}}: {template}")
    all_placeholders = [int(x) for x in ANY_PLACEHOLDER_PATTERN.findall(template)]
    if not all_placeholders:
        raise ValueError(f"template has no placeholders: {template}")
    unique_sorted = sorted(set(all_placeholders))
    if unique_sorted != list(range(1, unique_sorted[-1] + 1)):
        raise ValueError(f"template placeholders not compact: {template}")
    if unique_sorted[-1] > 4:
        raise ValueError(f"template placeholders exceed p4: {template}")
    if len(PLACEHOLDER_PATTERN.findall(template)) < 2:
        raise ValueError(f"template must have >=2 placeholder occurrences: {template}")


def _validate_item(item: dict[str, Any], expected_uid: str) -> dict[str, Any]:
    uid = item.get("uid")
    if uid != expected_uid:
        raise ValueError(f"uid mismatch: got={uid} expected={expected_uid}")

    season = str(item.get("season", "ANY")).upper().strip()
    if season not in {"ANY", "SUMMER", "WINTER"}:
        raise ValueError(f"invalid season: {season}")

    template = _normalize_template(str(item.get("template", "")))
    _validate_template(template)

    raw_relation_delta = item.get("relation_delta")
    raw_mood_delta = item.get("mood_delta")
    if raw_relation_delta is None or raw_mood_delta is None:
        raise ValueError(f"missing social deltas for uid={expected_uid}")
    relation_delta = int(raw_relation_delta)
    mood_delta = int(raw_mood_delta)
    if relation_delta == 0 or relation_delta < -8 or relation_delta > 8:
        raise ValueError(f"invalid relation_delta: {relation_delta}")
    if mood_delta == 0 or mood_delta < -6 or mood_delta > 6:
        raise ValueError(f"invalid mood_delta: {mood_delta}")

    effect = str(item.get("effect", "")).strip()
    return {
        "uid": uid,
        "season": season,
        "template": template,
        "effect": effect,
        "relation_delta": relation_delta,
        "mood_delta": mood_delta,
    }


def _estimate_social_deltas(effect: str, text: str) -> tuple[int, int]:
    negative_keywords = ("拒绝", "嘲笑", "争执", "冲突", "警告", "尴尬", "失望", "心虚", "冷战", "羞辱", "责备")
    positive_keywords = ("帮助", "鼓励", "安慰", "合作", "支持", "道谢", "邀请", "请教", "和解", "分享")

    if any(k in effect for k in ("mood-", "stress+", "fatigue+")):
        return -4, -3
    if any(k in effect for k in ("mood+", "stress-", "fatigue-")):
        return 4, 3
    if any(k in text for k in negative_keywords):
        return -4, -3
    if any(k in text for k in positive_keywords):
        return 4, 3
    return 2, 1


def _heuristic_tag_row(row: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(str(row["text"]).strip().split())
    season = str(row.get("season", "ANY")).upper().strip()
    if season not in {"ANY", "SUMMER", "WINTER"}:
        season = "ANY"

    if "{p1}" in text and "{p2}" in text:
        template = text
        if not PREFIX_PATTERN.match(template):
            template = f"【日常时段·校园】{template}"
    else:
        core = text
        if core.startswith("【") and "】" in core:
            core = core.split("】", 1)[1].strip()
        template = f"【日常时段·校园】{{p1}}与{{p2}}发生互动：{core}"

    effect = str(row.get("effect", "")).strip()
    relation_delta, mood_delta = _estimate_social_deltas(effect, template)
    return _validate_item(
        {
            "uid": row["uid"],
            "season": season,
            "template": template,
            "effect": effect,
            "relation_delta": relation_delta,
            "mood_delta": mood_delta,
        },
        str(row["uid"]),
    )


def _chunked(items: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        obj = json.loads(cleaned[start : end + 1])
        if isinstance(obj, dict):
            return obj
    raise ValueError("LLM output is not a valid JSON object")


def _llm_tag_batch(client: OpenAI, model_name: str, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload = [
        {
            "uid": item["uid"],
            "season": item["season"],
            "text": item["text"],
            "effect": item["effect"],
        }
        for item in batch
    ]
    prompt = USER_TEMPLATE.format(payload=json.dumps(payload, ensure_ascii=False, indent=2))
    raw: dict[str, Any] | None = None
    last_exc: Exception | None = None
    for _ in range(3):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=3000,
                extra_body={"chat_template_kwargs": {"enable_thinking": False, "clear_thinking": True}},
                stream=False,
                timeout=90,
            )
            message = completion.choices[0].message
            content = message.content or getattr(message, "reasoning_content", None)
            if not content:
                raise RuntimeError("LLM returned empty content")
            raw = _extract_json_object(content)
            break
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(0.6)
    if raw is None:
        raise RuntimeError(f"LLM batch parse failed: {last_exc}") from last_exc
    items = raw.get("items")
    if not isinstance(items, list):
        raise ValueError("LLM output missing items list")
    by_uid = {item["uid"]: item for item in items if isinstance(item, dict) and "uid" in item}
    validated: list[dict[str, Any]] = []
    for row in batch:
        uid = row["uid"]
        if uid not in by_uid:
            raise ValueError(f"LLM output missing uid: {uid}")
        validated.append(_validate_item(by_uid[uid], uid))
    return validated


def _write_rebuilt_file(rows: list[dict[str, Any]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sync_to_db(rows: list[dict[str, Any]]) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        _ensure_event_pool_schema(cursor)
        cursor.execute("DELETE FROM event_pool")
        inserts = [
            (
                "rebuilt",
                row["season"],
                row["template"],
                row["effect"],
                int(row["relation_delta"]),
                int(row["mood_delta"]),
                1,
            )
            for row in rows
        ]
        cursor.executemany(
            """
            INSERT INTO event_pool (source, season, template, effect, relation_delta, mood_delta, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            inserts,
        )
        conn.commit()
    finally:
        conn.close()


def run(
    limit: int | None,
    batch_size: int,
    sleep_sec: float,
    model: str | None,
    reset: bool,
    heuristic_only: bool,
) -> None:
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = model or os.getenv("MODEL_NAME")
    if not api_key or not base_url or not model_name:
        raise RuntimeError("Missing API_KEY / BASE_URL / MODEL_NAME")

    if reset:
        DONE_PATH.write_text("", encoding="utf-8")
        if CHECKPOINT_PATH.exists():
            CHECKPOINT_PATH.unlink()
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=90)
    src_rows = _load_legacy_events() + _load_agent_events()
    if not src_rows:
        raise RuntimeError("No source events found")

    # de-dup by raw text to reduce repeated labeling
    dedup_map: dict[str, dict[str, Any]] = {}
    for row in src_rows:
        key = row["text"]
        if key not in dedup_map:
            dedup_map[key] = row
    rows = list(dedup_map.values())
    rows.sort(key=lambda x: x["uid"])

    done_uids = _load_done_uids(DONE_PATH)
    checkpoint = _load_checkpoint(CHECKPOINT_PATH)
    if checkpoint:
        print(
            f"[resume] done={checkpoint.get('done_count')} last_uid={checkpoint.get('last_uid')}",
            flush=True,
        )

    pending = [row for row in rows if row["uid"] not in done_uids]
    if limit is not None:
        pending = pending[:limit]
    print(f"[rebuild] total={len(rows)} done={len(done_uids)} pending={len(pending)}", flush=True)

    rebuilt_rows: dict[str, dict[str, Any]] = {}
    if OUTPUT_PATH.exists():
        for line in OUTPUT_PATH.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s:
                continue
            obj = json.loads(s)
            uid = obj.get("uid")
            if isinstance(uid, str):
                rebuilt_rows[uid] = obj

    batches = _chunked(pending, max(1, batch_size))
    with DONE_PATH.open("a", encoding="utf-8") as done_f:
        for idx, batch in enumerate(batches, start=1):
            if heuristic_only:
                processed = [_heuristic_tag_row(row) for row in batch]
            else:
                try:
                    processed = _llm_tag_batch(client, model_name, batch)
                except Exception:
                    processed = []
                    for row in batch:
                        try:
                            processed.extend(_llm_tag_batch(client, model_name, [row]))
                        except Exception:
                            processed.append(_heuristic_tag_row(row))
            for item in processed:
                rebuilt_rows[item["uid"]] = item
                done_f.write(item["uid"] + "\n")
                done_uids.add(item["uid"])
            done_f.flush()
            _save_checkpoint(
                CHECKPOINT_PATH,
                done_count=len(done_uids),
                last_uid=batch[-1]["uid"],
            )
            print(f"[rebuild] batch={idx}/{len(batches)} done={len(done_uids)}", flush=True)
            if sleep_sec > 0:
                time.sleep(sleep_sec)

    target_rows = rows if limit is None else rows[:len(done_uids)]
    final_rows = [rebuilt_rows[row["uid"]] for row in target_rows if row["uid"] in rebuilt_rows]
    if len(final_rows) != len(target_rows):
        raise RuntimeError(f"Rebuild incomplete: got={len(final_rows)} expected={len(target_rows)}")

    _write_rebuilt_file(final_rows)
    _sync_to_db(final_rows)
    print(f"[rebuild] completed rows={len(final_rows)} output={OUTPUT_PATH}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild event_pool with social deltas by LLM")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--heuristic-only", action="store_true")
    args = parser.parse_args()
    run(
        limit=args.limit,
        batch_size=args.batch_size,
        sleep_sec=args.sleep,
        model=args.model,
        reset=args.reset,
        heuristic_only=args.heuristic_only,
    )


if __name__ == "__main__":
    main()
