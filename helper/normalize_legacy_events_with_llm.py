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
OUTPUT_PATH = Path("events_extraction/legacy_events_cleaned.jsonl")
CHECKPOINT_PATH = Path("events_extraction/.legacy_events_clean_checkpoint.json")

PREFIX_PATTERN = re.compile(r"^【[^【】]{1,8}·[^【】]{1,12}】")
PLACEHOLDER_PATTERN = re.compile(r"\{p([1-4])\}")

SYSTEM_PROMPT = "你是校园事件清洗器。把旧突发事件改写成统一模板格式，用于事件数据库。"
MAX_RETRIES = 5


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


def _load_events_from_db(db_path: Path) -> list[dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, season, description, effect FROM events ORDER BY id")
        rows = cur.fetchall()
    return [
        {
            "id": int(r[0]),
            "season": str(r[1]),
            "description": str(r[2]),
            "effect": str(r[3] or ""),
        }
        for r in rows
    ]


def _load_checkpoint(path: Path) -> int:
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    next_index = data.get("next_index")
    if not isinstance(next_index, int):
        return 0
    return max(0, next_index)


def _save_checkpoint(path: Path, next_index: int) -> None:
    payload = {"next_index": next_index, "updated_at": int(time.time())}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def _build_prompt(batch: list[dict[str, Any]]) -> str:
    payload = {
        "items": [
            {"id": item["id"], "description": item["description"]} for item in batch
        ]
    }
    return (
        "请把下面旧事件改写为统一模板，仅输出 JSON。\n"
        "输出格式严格为：\n"
        "{\n"
        '  "items": [\n'
        '    {"id": 1, "content": "【日常时段·校园】{p1}与{p2}因排队问题发生争执。"}\n'
        "  ]\n"
        "}\n\n"
        "硬性要求：\n"
        "1) 保留原 id，不增删条目，顺序与输入一致。\n"
        "2) content 必须是单句，并以“【时间·地点】”开头。\n"
        "3) 人物统一使用 {p1}/{p2}/{p3}/{p4} 占位符。\n"
        "   每条至少包含 {p1}；即使原句未点名人物，也要改写成“{p1}遭遇/发现/经历...”的表达。\n"
        "4) 不要出现真实人名，不要出现 A/B 或 某人/某同学/某老师。\n"
        "5) 保留原事件核心，不要编造新剧情。\n\n"
        f"输入：\n{json.dumps(payload, ensure_ascii=False)}"
    )


def _validate_content(text: str) -> None:
    if not PREFIX_PATTERN.match(text):
        raise RuntimeError("missing prefix")
    if "A/B" in text or "A向B" in text or "A和B" in text:
        raise RuntimeError("contains A/B")
    if any(bad in text for bad in ("某人", "某同学", "某老师", "某家长")):
        raise RuntimeError("contains 某X")
    placeholders = PLACEHOLDER_PATTERN.findall(text)
    if not placeholders:
        raise RuntimeError("missing {pN}")
    ids = sorted({int(p) for p in placeholders})
    if ids != list(range(1, ids[-1] + 1)):
        raise RuntimeError("placeholder index gap")


def run(batch_size: int, sleep_sec: float, model: str | None, reset: bool) -> None:
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = model or os.getenv("MODEL_NAME")
    if not api_key or not base_url or not model_name:
        raise RuntimeError("Missing API_KEY / BASE_URL / MODEL_NAME in environment")

    events = _load_events_from_db(DB_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if reset:
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()
        if CHECKPOINT_PATH.exists():
            CHECKPOINT_PATH.unlink()

    start = _load_checkpoint(CHECKPOINT_PATH)
    if start > len(events):
        raise RuntimeError("Checkpoint out of range, run with --reset")

    client = OpenAI(api_key=api_key, base_url=base_url)
    mode = "a" if OUTPUT_PATH.exists() and start > 0 else "w"

    with OUTPUT_PATH.open(mode, encoding="utf-8") as out_f:
        for i in range(start, len(events), batch_size):
            batch = events[i : i + batch_size]
            prompt = _build_prompt(batch)
            last_error: Exception | None = None
            cleaned_items: list[dict[str, Any]] | None = None

            for attempt in range(MAX_RETRIES):
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.1,
                        max_tokens=3200,
                        stream=False,
                    )
                    msg = completion.choices[0].message
                    response_text = msg.content or getattr(
                        msg, "reasoning_content", None
                    )
                    if not response_text:
                        raise RuntimeError("Empty response")
                    payload = _extract_json_payload(response_text)
                    items = payload.get("items")
                    if not isinstance(items, list):
                        raise RuntimeError("Missing items list")

                    in_ids = [row["id"] for row in batch]
                    out_ids: list[int] = []
                    tmp_items: list[dict[str, Any]] = []
                    for obj in items:
                        if not isinstance(obj, dict):
                            raise RuntimeError("Non-object output item")
                        item_id = obj.get("id")
                        content = obj.get("content")
                        if not isinstance(item_id, int) or not isinstance(content, str):
                            raise RuntimeError("Missing id/content")
                        _validate_content(content.strip())
                        out_ids.append(item_id)
                        tmp_items.append({"id": item_id, "content": content.strip()})
                    if out_ids != in_ids:
                        raise RuntimeError("IDs/order mismatch")
                    cleaned_items = tmp_items
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempt == MAX_RETRIES - 1:
                        raise RuntimeError(
                            f"Batch {i // batch_size + 1} failed: {exc}"
                        ) from exc
                    prompt += (
                        "\n\n上轮输出不合规，请严格修正："
                        "每条必须以【时间·地点】开头，必须至少出现{p1}，"
                        "禁止真实人名/某人/A-B 写法，且保持输入 id 顺序不变。"
                    )
                    time.sleep(0.5)

            if cleaned_items is None:
                raise RuntimeError(
                    f"No cleaned items for batch at index {i}: {last_error}"
                )

            meta_map = {row["id"]: row for row in batch}
            for row in cleaned_items:
                src = meta_map[row["id"]]
                out = {
                    "id": row["id"],
                    "season": src["season"],
                    "effect": src["effect"],
                    "content": row["content"],
                }
                out_f.write(json.dumps(out, ensure_ascii=False) + "\n")
            out_f.flush()
            _save_checkpoint(CHECKPOINT_PATH, i + len(batch))
            print(f"[legacy-clean] {i + len(batch)}/{len(events)}", flush=True)
            if sleep_sec > 0:
                time.sleep(sleep_sec)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Normalize legacy DB events to {p1..} templates via LLM."
    )
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    run(
        batch_size=args.batch_size,
        sleep_sec=args.sleep,
        model=args.model,
        reset=args.reset,
    )
