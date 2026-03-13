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

CHUNKS_FILE = Path("events_extraction/chunks_for_llm.jsonl")
OUTPUT_FILE = Path("events_extraction/agent_events.jsonl")
PROCESSED_CHUNKS_FILE = Path("events_extraction/.agent_events_done_chunks.txt")
CHECKPOINT_FILE = Path("events_extraction/.agent_events_checkpoint.json")
DB_FILE = Path("novel_engine/data/storage/world_data.db")

SYSTEM_PROMPT = (
    "你是校园互动事件抽取器。"
    "目标是一次性输出可直接用于agent模拟的最终事件模板。"
)

USER_TEMPLATE = """从下述文本提取 2-6 条“关键互动事件模板”。

仅输出 JSON，格式严格为：
{{
  "events": [
    "【课间·教室】{{p1}}向{{p2}}借笔记，{{p2}}拒绝后双方发生争执。",
    "【课间·办公室】老师提醒{{p1}}下课后去办公室。"
  ]
}}

要求：
1) 每条必须是“有人对他人做了什么，并产生推进/后果”的完整互动事件。
2) 输出必须以“【时间·地点】”前缀开头。
3) 人名必须匿名成格式化占位符：{{p1}}/{{p2}}/{{p3}}/{{p4}}（按该条事件首次出现顺序）。
4) 禁止输出真实人名、A/B、某人/某同学/某老师/某家长。
5) 只保留关键节点：冲突、求助、邀请、传话、问答、纪律、合作、关系变化。
6) 不要输出解释，不要输出 markdown。

文本：
{text}
"""

PREFIX_PATTERN = re.compile(r"^【[^【】]{1,8}·[^【】]{1,12}】")
PLACEHOLDER_PATTERN = re.compile(r"\{p([1-4])\}")
ANY_PLACEHOLDER_PATTERN = re.compile(r"\{p(\d+)\}")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        rows.append(json.loads(s))
    return rows


def _load_processed_chunks(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data


def _save_checkpoint(path: Path, *, chunk_id: str, processed_chunks: int, event_counter: int) -> None:
    payload = {
        "last_chunk_id": chunk_id,
        "processed_chunks": processed_chunks,
        "next_event_counter": event_counter,
        "updated_at": int(time.time()),
    }
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_payload(text: str) -> dict[str, Any]:
    cleaned = _strip_fence(text)
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
    raise ValueError("Model output is not valid JSON object")


def _normalize_event_text(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    text = " ".join(raw.strip().split())
    if len(text) < 18:
        return None
    if not PREFIX_PATTERN.match(text):
        return None
    if "A向B" in text or "A和B" in text or "A/B" in text:
        return None
    if any(bad in text for bad in ("某人", "某同学", "某老师", "某家长", "{actor}", "{target}")):
        return None
    any_placeholders = ANY_PLACEHOLDER_PATTERN.findall(text)
    if len(any_placeholders) < 2:
        return None
    if any(int(p) < 1 or int(p) > 4 for p in any_placeholders):
        return None
    unique_indices = sorted({int(p) for p in any_placeholders})
    max_idx = unique_indices[-1]
    if unique_indices != list(range(1, max_idx + 1)):
        return None
    placeholders = PLACEHOLDER_PATTERN.findall(text)
    if len(placeholders) < 2:
        return None
    return text


def _normalize_events(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        raise ValueError("events must be a list")

    result: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            item = item.get("interaction")
        event_text = _normalize_event_text(item)
        if event_text is None:
            continue
        if event_text in seen:
            continue
        seen.add(event_text)
        result.append(event_text)

    if not result:
        raise ValueError("empty events after normalization")
    return result


def _next_event_counter(path: Path) -> int:
    if not path.exists():
        return 1
    counter = 1
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        eid = obj.get("id")
        if isinstance(eid, str) and eid.startswith("e_"):
            try:
                counter = max(counter, int(eid.split("_", 1)[1]) + 1)
            except ValueError:
                continue
    return counter


def _sync_events_to_db(output_file: Path, db_file: Path) -> None:
    if not output_file.exists():
        print("[sync-db] skip: output file not found", flush=True)
        return
    if not db_file.exists():
        raise FileNotFoundError(f"DB not found: {db_file}")

    templates: list[str] = []
    for line in output_file.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        content = obj.get("content")
        if isinstance(content, str) and content:
            templates.append(content)

    if not templates:
        print("[sync-db] skip: no templates", flush=True)
        return

    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.cursor()
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
        before_changes = conn.total_changes
        rows = [("merged", "ANY", t, "", 4, 3, 1) for t in templates]
        cursor.executemany(
            "INSERT OR IGNORE INTO event_pool (source, season, template, effect, relation_delta, mood_delta, enabled) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        inserted = conn.total_changes - before_changes
        cursor.execute("SELECT COUNT(*) FROM event_pool WHERE source='merged'")
        merged_total = int(cursor.fetchone()[0])
        print(f"[sync-db] inserted={inserted} merged_total={merged_total}", flush=True)
    finally:
        conn.close()


def run(
    limit: int | None,
    sleep_sec: float,
    model: str | None,
    reset_progress: bool,
    reset_output: bool,
    sync_db: bool,
    request_timeout_sec: float,
) -> None:
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = model or os.getenv("MODEL_NAME")
    if not api_key or not base_url or not model_name:
        raise RuntimeError("Missing API_KEY / BASE_URL / MODEL_NAME in environment")

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=request_timeout_sec)
    chunks = _load_jsonl(CHUNKS_FILE)
    if reset_progress:
        PROCESSED_CHUNKS_FILE.write_text("", encoding="utf-8")
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
    if reset_output and OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()
    done_chunks = _load_processed_chunks(PROCESSED_CHUNKS_FILE)
    checkpoint = _load_checkpoint(CHECKPOINT_FILE)
    pending = [row for row in chunks if row["id"] not in done_chunks]
    if limit is not None:
        pending = pending[:limit]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    event_counter = _next_event_counter(OUTPUT_FILE)

    if checkpoint:
        last_chunk_id = checkpoint.get("last_chunk_id")
        processed_chunks = checkpoint.get("processed_chunks")
        print(
            f"[resume] last_chunk={last_chunk_id} processed_chunks={processed_chunks} pending={len(pending)}",
            flush=True,
        )

    with OUTPUT_FILE.open("a", encoding="utf-8") as out_f:
        with PROCESSED_CHUNKS_FILE.open("a", encoding="utf-8") as done_f:
            for idx, row in enumerate(pending, start=1):
                chunk_id = row["id"]
                user_prompt = USER_TEMPLATE.format(text=row["text"])

                content: str | None = None
                last_error: Exception | None = None
                for _attempt in range(2):
                    try:
                        completion = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt},
                            ],
                            temperature=0.2,
                            max_tokens=1200,
                            extra_body={"chat_template_kwargs": {"enable_thinking": False, "clear_thinking": True}},
                            timeout=request_timeout_sec,
                            stream=False,
                        )
                        message = completion.choices[0].message
                        content = message.content or getattr(message, "reasoning_content", None)
                        if content:
                            break
                    except Exception as exc:  # noqa: BLE001
                        last_error = exc
                        time.sleep(0.4)

                if not content:
                    if last_error:
                        print(f"[{idx}/{len(pending)}] {chunk_id} -> request_failed: {last_error}", flush=True)
                        done_f.write(chunk_id + "\n")
                        done_f.flush()
                        done_chunks.add(chunk_id)
                        _save_checkpoint(
                            CHECKPOINT_FILE,
                            chunk_id=chunk_id,
                            processed_chunks=len(done_chunks),
                            event_counter=event_counter,
                        )
                        continue
                    print(f"[{idx}/{len(pending)}] {chunk_id} -> empty_response", flush=True)
                    done_f.write(chunk_id + "\n")
                    done_f.flush()
                    done_chunks.add(chunk_id)
                    _save_checkpoint(
                        CHECKPOINT_FILE,
                        chunk_id=chunk_id,
                        processed_chunks=len(done_chunks),
                        event_counter=event_counter,
                    )
                    continue

                try:
                    payload = _extract_json_payload(content)
                except Exception as exc:  # noqa: BLE001
                    print(f"[{idx}/{len(pending)}] {chunk_id} -> invalid_json: {exc}", flush=True)
                    done_f.write(chunk_id + "\n")
                    done_f.flush()
                    done_chunks.add(chunk_id)
                    _save_checkpoint(
                        CHECKPOINT_FILE,
                        chunk_id=chunk_id,
                        processed_chunks=len(done_chunks),
                        event_counter=event_counter,
                    )
                    continue
                try:
                    events = _normalize_events(payload.get("events"))
                except ValueError as exc:
                    if str(exc) == "empty events after normalization":
                        done_f.write(chunk_id + "\n")
                        done_f.flush()
                        done_chunks.add(chunk_id)
                        _save_checkpoint(
                            CHECKPOINT_FILE,
                            chunk_id=chunk_id,
                            processed_chunks=len(done_chunks),
                            event_counter=event_counter,
                        )
                        print(f"[{idx}/{len(pending)}] {chunk_id} -> 0 events (filtered)", flush=True)
                        continue
                    raise

                for event_text in events:
                    out = {"id": f"e_{event_counter:07d}", "content": event_text}
                    out_f.write(json.dumps(out, ensure_ascii=False) + "\n")
                    event_counter += 1
                out_f.flush()

                done_f.write(chunk_id + "\n")
                done_f.flush()
                done_chunks.add(chunk_id)
                _save_checkpoint(
                    CHECKPOINT_FILE,
                    chunk_id=chunk_id,
                    processed_chunks=len(done_chunks),
                    event_counter=event_counter,
                )
                print(f"[{idx}/{len(pending)}] {chunk_id} -> {len(events)} events", flush=True)
                if sleep_sec > 0:
                    time.sleep(sleep_sec)

    if sync_db:
        _sync_events_to_db(OUTPUT_FILE, DB_FILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract agent-interaction events from chunked fiction.")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N pending chunks.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep seconds between API calls.")
    parser.add_argument("--timeout", type=float, default=90.0, help="Per-request timeout in seconds.")
    parser.add_argument("--model", type=str, default=None, help="Override MODEL_NAME from env.")
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Clear progress files (.agent_events_done_chunks.txt/.agent_events_checkpoint.json).",
    )
    parser.add_argument(
        "--reset-output",
        action="store_true",
        help="Delete output file events_extraction/agent_events.jsonl before running.",
    )
    parser.add_argument(
        "--no-sync-db",
        action="store_true",
        help="Do not sync extracted events into world_data.db event_pool.",
    )
    args = parser.parse_args()
    run(
        limit=args.limit,
        sleep_sec=args.sleep,
        model=args.model,
        reset_progress=args.reset_progress,
        reset_output=args.reset_output,
        sync_db=not args.no_sync_db,
        request_timeout_sec=args.timeout,
    )
