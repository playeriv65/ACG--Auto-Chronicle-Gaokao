from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

INPUT_FILE = Path("events_extraction/agent_events.jsonl")
DEFAULT_OUTPUT_FILE = Path("events_extraction/agent_events_cleaned.jsonl")
CHECKPOINT_FILE = Path("events_extraction/.agent_events_clean_checkpoint.json")

SYSTEM_PROMPT = (
    "你是校园事件清洗器。"
    "任务是把原始事件改写成可复用模板：去掉具体人名，保留核心互动，并补时间地点。"
)


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


def _load_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        event_id = obj.get("id")
        content = obj.get("content")
        if isinstance(event_id, str) and isinstance(content, str):
            rows.append({"id": event_id, "content": content})
    return rows


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
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _build_user_prompt(items: list[dict[str, str]]) -> str:
    payload = {"items": items}
    alias_rule = "人物代号必须使用格式化占位符“{p1}/{p2}/{p3}/{p4}”（按事件内首次出现顺序分配）。"
    alias_example = "【课间·教室】{p1}向{p2}借笔记，{p2}拒绝后双方发生争执。"

    return (
        "请清洗下面事件，仅输出 JSON。\n"
        "输入格式：{\"items\":[{\"id\":\"e_xxx\",\"content\":\"...\"}]}\n"
        "输出格式严格为：\n"
        "{\n"
        "  \"items\": [\n"
        f"    {{\"id\":\"e_xxx\",\"content\":\"{alias_example}\"}}\n"
        "  ]\n"
        "}\n\n"
        "硬性要求：\n"
        "1) 保留 id，不增删条目，输出顺序必须与输入一致。\n"
        f"2) 去掉具体人名。{alias_rule}\n"
        "3) 严禁出现“某人/某同学/某老师/某家长”等“某X”写法。\n"
        "4) 每条 content 必须以“【时间·地点】”开头。\n"
        "5) 保留原事件核心动作，不要编造新剧情。\n"
        "6) 单句表达，不要解释，不要 markdown。\n\n"
        f"输入：\n{json.dumps(payload, ensure_ascii=False)}"
    )


def clean_with_llm(
    *,
    input_file: Path,
    output_file: Path,
    batch_size: int,
    sleep_sec: float,
    model: str | None,
    reset: bool,
    max_items: int | None,
) -> None:
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = model or os.getenv("MODEL_NAME")
    if not api_key or not base_url or not model_name:
        raise RuntimeError("Missing API_KEY / BASE_URL / MODEL_NAME in environment")
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")
    if not input_file.exists():
        raise RuntimeError(f"Input file not found: {input_file}")

    rows = _load_rows(input_file)
    if not rows:
        raise RuntimeError("No valid rows in input file")
    if max_items is not None:
        rows = rows[: max(0, max_items)]

    client = OpenAI(api_key=api_key, base_url=base_url)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if reset:
        if output_file.exists():
            output_file.unlink()
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()

    start_index = _load_checkpoint(CHECKPOINT_FILE)
    if start_index > len(rows):
        raise RuntimeError("Checkpoint next_index out of range; run with --reset")

    mode = "a" if output_file.exists() and start_index > 0 else "w"
    with output_file.open(mode, encoding="utf-8") as out_f:
        for i in range(start_index, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            user_prompt = _build_user_prompt(batch)
            input_ids = [item["id"] for item in batch]
            output_items: list[dict[str, str]] | None = None
            last_error: Exception | None = None

            for attempt in range(3):
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=3200,
                        extra_body={"chat_template_kwargs": {"enable_thinking": False, "clear_thinking": True}},
                        stream=False,
                    )
                    message = completion.choices[0].message
                    response_text = message.content or getattr(message, "reasoning_content", None)
                    if not response_text:
                        raise RuntimeError(f"Empty cleaner response at index {i}")

                    payload = _extract_json_payload(response_text)
                    items = payload.get("items")
                    if not isinstance(items, list):
                        raise RuntimeError("Cleaner output missing items list")

                    output_ids: list[str] = []
                    current_output_items: list[dict[str, str]] = []
                    for obj in items:
                        if not isinstance(obj, dict):
                            raise RuntimeError("Cleaner output item is not object")
                        event_id = obj.get("id")
                        content = obj.get("content")
                        if not isinstance(event_id, str) or not isinstance(content, str):
                            raise RuntimeError("Cleaner output missing id/content")
                        output_ids.append(event_id)
                        normalized_content = content.strip()
                        if (
                            "某人" in normalized_content
                            or "某同学" in normalized_content
                            or "某老师" in normalized_content
                            or "某家长" in normalized_content
                        ):
                            raise RuntimeError("Cleaner output contains forbidden 某X pattern")
                        if not re.search(r"\{p[1-4]\}", normalized_content):
                            raise RuntimeError("Cleaner output missing {pN} placeholders")
                        current_output_items.append({"id": event_id, "content": normalized_content})

                    if output_ids != input_ids:
                        raise RuntimeError("Cleaner output ids/order mismatch with input batch")
                    output_items = current_output_items
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempt == 2:
                        raise
                    time.sleep(0.5)
                    user_prompt += "\n\n上轮输出不合规：仍出现“某X”或缺少{pN}。请严格重写并只输出合法JSON。"

            if output_items is None:
                raise RuntimeError(f"Cleaner failed at batch index {i}: {last_error}")

            for obj in output_items:
                out_f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            out_f.flush()

            _save_checkpoint(CHECKPOINT_FILE, i + len(batch))
            print(f"[clean-llm] {i + len(batch)}/{len(rows)}", flush=True)
            if sleep_sec > 0:
                time.sleep(sleep_sec)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean agent_events.jsonl with LLM rewrite.")
    parser.add_argument("--input", type=str, default=str(INPUT_FILE), help="Input JSONL path.")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_FILE), help="Output JSONL path.")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size per API call.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep seconds between API calls.")
    parser.add_argument("--model", type=str, default=None, help="Override MODEL_NAME from env.")
    parser.add_argument("--reset", action="store_true", help="Reset output and checkpoint.")
    parser.add_argument("--max-items", type=int, default=None, help="Only clean first N rows (for trial).")
    args = parser.parse_args()
    clean_with_llm(
        input_file=Path(args.input),
        output_file=Path(args.output),
        batch_size=args.batch_size,
        sleep_sec=args.sleep,
        model=args.model,
        reset=args.reset,
        max_items=args.max_items,
    )
