"""LLM interaction layer for scene writing, quiz generation and summaries."""

import json
import sys
from typing import List, Sequence

from config import Config
from novel_engine.core.contracts import ChatMessage, ChatRequest, ChatResponse
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

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
        print(json.dumps([message.model_dump(mode="json") for message in messages], ensure_ascii=False, indent=2), flush=True)
        print("=" * 50 + "\n", flush=True)

    def _build_extra_body(self) -> dict[str, dict[str, bool]]:
        return {"chat_template_kwargs": {"enable_thinking": False, "clear_thinking": True}}

    def _to_openai_messages(self, messages: Sequence[ChatMessage]) -> list[ChatCompletionMessageParam]:
        openai_messages: list[ChatCompletionMessageParam] = []
        for message in messages:
            if message.role == "system":
                system_msg: ChatCompletionSystemMessageParam = {"role": "system", "content": message.content}
                openai_messages.append(system_msg)
            elif message.role == "user":
                user_msg: ChatCompletionUserMessageParam = {"role": "user", "content": message.content}
                openai_messages.append(user_msg)
            else:
                assistant_msg: ChatCompletionAssistantMessageParam = {"role": "assistant", "content": message.content}
                openai_messages.append(assistant_msg)
        return openai_messages

    def _call_api(self, request: ChatRequest) -> str:
        if self.debug:
            self._debug_dump_prompt(request.messages)

        completion = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=self._to_openai_messages(request.messages),
            temperature=Config.TEMPERATURE,
            max_tokens=request.max_tokens,
            extra_body=self._build_extra_body(),
            stream=False,
        )
        message = completion.choices[0].message
        full_response = message.content or getattr(message, "reasoning_content", None)
        if full_response is None:
            raise RuntimeError("Empty response from API")
        return ChatResponse(content=full_response).content

    def generate_quiz(self, subject: str, topic: str) -> str:
        prompt = f"请针对高中{subject}知识点【{topic}】设计1道选择题。输出格式：【题目】、答案和解析。总字数控制在150字以内，不要任何废话。"
        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content="你是一名精准的命题机器。"),
                ChatMessage(role="user", content=prompt),
            ],
            max_tokens=QUIZ_MAX_TOKENS,
        )
        return self._call_api(request)

    def generate_scene(
        self,
        prompt: str,
        stats_context: str,
        system_instruction: str | None = None,
        min_length: int = 4000,
        max_length: int = 20000,
    ) -> str:
        messages: List[ChatMessage] = [
            ChatMessage(role="system", content=system_instruction or Config.SYSTEM_PROMPT),
            ChatMessage(role="user", content=f"【数据包】\n{stats_context}\n\n【大纲】\n{prompt}\n\n请开笔："),
        ]

        full_content = ""
        while True:
            sys.stdout.write(f"\n [AI Writing... {len(full_content)} chars] ")
            sys.stdout.flush()

            request = ChatRequest(messages=messages, max_tokens=Config.MAX_TOKENS)
            new_text = self._call_api(request)
            full_content += new_text + "\n"
            messages.append(ChatMessage(role="assistant", content=new_text))

            if CHAPTER_END_MARKER in full_content and len(full_content) >= min_length:
                full_content = full_content.replace(CHAPTER_END_MARKER, "").strip()
                break
            if len(full_content) >= max_length:
                full_content = full_content[:max_length].strip() + TRUNCATION_NOTICE
                break

            messages.append(ChatMessage(role="user", content=CONTINUE_EXPAND_PROMPT))

        if not full_content.strip():
            raise RuntimeError("Generated scene is empty")

        self.last_chapter_content = full_content
        return full_content

    def summarize_chapter(self, chapter_num: int, content: str) -> str:
        prompt = f"请简要总结第{chapter_num}章的核心剧情发展、人物变动和关键信息。字数控制在200字以内。"
        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content="你是一个严谨的剧情记录员。"),
                ChatMessage(role="user", content=f"【章节内容】\n{content}\n\n【指令】\n{prompt}"),
            ],
            max_tokens=SUMMARY_MAX_TOKENS,
        )

        summary = self._call_api(request)
        with open(self.summary_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- 第{chapter_num}章 摘要 ---\n{summary}\n")
        return summary


writer = AIWriter()
