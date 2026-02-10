"""LLM interaction layer for scene writing, quiz generation and summaries."""

import json
import sys
from typing import Dict, List, Sequence, TypeAlias

from config import Config
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

ChatMessage: TypeAlias = ChatCompletionMessageParam
QUIZ_MAX_TOKENS = 500
SUMMARY_MAX_TOKENS = 2000
CONTINUE_EXPAND_PROMPT = "（字数不足，请继续深度扩写剧情细节，严禁收尾！）"
CHAPTER_END_MARKER = "[CHAPTER_END]"
TRUNCATION_NOTICE = "\n\n（此处因篇幅过长，天道强行截断...）"


class AIWriter:
    """Wraps chat-completions calls with strict fail-fast behavior."""

    def __init__(self) -> None:
        self.client = OpenAI(base_url=Config.OPENAI_API_BASE, api_key=Config.OPENAI_API_KEY)
        self.summary_file: str = "plot_summary.txt"
        self.last_chapter_content: str = ""
        self.debug: bool = False

    def _debug_dump_prompt(self, messages: Sequence[ChatMessage]) -> None:
        print("\n" + "=" * 50, flush=True)
        print(" [DEBUG] AI PROMPT:", flush=True)
        print(json.dumps(list(messages), ensure_ascii=False, indent=2), flush=True)
        print("=" * 50 + "\n", flush=True)

    def _build_extra_body(self) -> Dict[str, Dict[str, bool]]:
        return {"chat_template_kwargs": {"enable_thinking": False, "clear_thinking": True}}

    def _call_api(self, messages: Sequence[ChatMessage], max_tokens: int = Config.MAX_TOKENS) -> str:
        if self.debug:
            self._debug_dump_prompt(messages)

        completion = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=list(messages),
            temperature=Config.TEMPERATURE,
            max_tokens=max_tokens,
            extra_body=self._build_extra_body(),
            stream=False,
        )
        message = completion.choices[0].message
        full_response = message.content or getattr(message, "reasoning_content", None)
        if not full_response:
            raise RuntimeError("Empty response from API")
        return full_response

    def generate_quiz(self, subject: str, topic: str) -> str:
        prompt = f"请针对高中{subject}知识点【{topic}】设计1道选择题。输出格式：【题目】、答案和解析。总字数控制在150字以内，不要任何废话。"
        messages: List[ChatMessage] = [
            {"role": "system", "content": "你是一名精准的命题机器。"},
            {"role": "user", "content": prompt},
        ]
        return self._call_api(messages, max_tokens=QUIZ_MAX_TOKENS)

    def generate_scene(
        self,
        prompt: str,
        stats_context: str,
        system_instruction: str | None = None,
        min_length: int = 4000,
        max_length: int = 20000,
    ) -> str:
        messages: List[ChatMessage] = [
            {"role": "system", "content": system_instruction or Config.SYSTEM_PROMPT},
            {"role": "user", "content": f"【数据包】\n{stats_context}\n\n【大纲】\n{prompt}\n\n请开笔："},
        ]

        full_content = ""
        while True:
            sys.stdout.write(f"\n [AI Writing... {len(full_content)} chars] ")
            sys.stdout.flush()

            new_text = self._call_api(messages)
            full_content += new_text + "\n"
            messages.append({"role": "assistant", "content": new_text})

            if CHAPTER_END_MARKER in full_content and len(full_content) >= min_length:
                full_content = full_content.replace(CHAPTER_END_MARKER, "").strip()
                break
            if len(full_content) >= max_length:
                full_content = full_content[:max_length].strip() + TRUNCATION_NOTICE
                break

            messages.append({"role": "user", "content": CONTINUE_EXPAND_PROMPT})

        if not full_content.strip():
            raise RuntimeError("Generated scene is empty")

        self.last_chapter_content = full_content
        return full_content

    def summarize_chapter(self, chapter_num: int, content: str) -> str:
        prompt = f"请简要总结第{chapter_num}章的核心剧情发展、人物变动和关键信息。字数控制在200字以内。"
        messages: List[ChatMessage] = [
            {"role": "system", "content": "你是一个严谨的剧情记录员。"},
            {"role": "user", "content": f"【章节内容】\n{content}\n\n【指令】\n{prompt}"},
        ]

        summary = self._call_api(messages, max_tokens=SUMMARY_MAX_TOKENS)
        with open(self.summary_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- 第{chapter_num}章 摘要 ---\n{summary}\n")
        return summary


writer = AIWriter()
