# Events Extraction Directory

## Core Files
- `extract_agent_events.py`: 单次提取并直接输出最终模板事件（`【时间·地点】` + `{p1...}`）。
- `clean_agent_events_with_llm.py`: 可选的 legacy 二次清洗脚本。
- `agent_events.jsonl`: 事件库（默认即最终格式）。
- `agent_events_cleaned_preview.jsonl`: 清洗预览文件（可选）。
- `chunks_for_llm.jsonl`: 分块后的小说文本输入。

## Data Sources
- `fictions/`: 原始小说文本文件。

## Resume State
- `.agent_events_done_chunks.txt`: 提取脚本已处理 chunk 列表。
- `.agent_events_checkpoint.json`: 提取脚本断点信息。
- `.agent_events_clean_checkpoint.json`: 清洗脚本断点信息。

## Common Commands
```bash
set -a; . ./.env; set +a
uv run python events_extraction/extract_agent_events.py --reset-progress --reset-output --sleep 0
```
