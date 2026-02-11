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
        prompt = Config.QUIZ_USER_PROMPT_TEMPLATE.format(subject=subject, topic=topic)
        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content=Config.QUIZ_SYSTEM_PROMPT),
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
            ChatMessage(
                role="user",
                content=Config.SCENE_USER_PROMPT_TEMPLATE.format(stats_context=stats_context, prompt=prompt),
            ),
        ]

        full_content = ""
        while True:
            sys.stdout.write(f"\n [AI Writing... {len(full_content)} chars] ")
            sys.stdout.flush()

            request = ChatRequest(messages=messages, max_tokens=Config.MAX_TOKENS)
            new_text = self._call_api(request)
            full_content += new_text + "\n"
            messages.append(ChatMessage(role="assistant", content=new_text))

            if Config.CHAPTER_END_MARKER in full_content and len(full_content) >= min_length:
                full_content = full_content.replace(Config.CHAPTER_END_MARKER, "").strip()
                break
            if len(full_content) >= max_length:
                full_content = full_content[:max_length].strip() + Config.TRUNCATION_NOTICE
                break

            messages.append(ChatMessage(role="user", content=Config.CONTINUE_EXPAND_PROMPT))

        if not full_content.strip():
            raise RuntimeError("Generated scene is empty")

        self.last_chapter_content = full_content
        return full_content

    def summarize_chapter(self, chapter_num: int, content: str) -> str:
        prompt = Config.SUMMARY_INSTRUCTION_TEMPLATE.format(chapter_num=chapter_num)
        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content=Config.SUMMARY_SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=Config.SUMMARY_USER_PROMPT_TEMPLATE.format(content=content, instruction=prompt),
                ),
            ],
            max_tokens=SUMMARY_MAX_TOKENS,
        )

        summary = self._call_api(request)
        with open(self.summary_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- 第{chapter_num}章 摘要 ---\n{summary}\n")
        return summary


writer = AIWriter()
