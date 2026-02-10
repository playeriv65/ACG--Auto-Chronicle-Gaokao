"""LLM interaction layer for scene writing, quiz generation and summaries."""

import json
import sys
import time
from typing import Dict, List, Optional, Sequence, TypeAlias

from config import Config
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

ChatMessage: TypeAlias = ChatCompletionMessageParam
DEFAULT_RETRY_TIMES = 3
QUIZ_MAX_TOKENS = 500
SUMMARY_MAX_TOKENS = 2000
CONTINUE_EXPAND_PROMPT = "（字数不足，请继续深度扩写剧情细节，严禁收尾！）"
CHAPTER_END_MARKER = "[CHAPTER_END]"
TRUNCATION_NOTICE = "\n\n（此处因篇幅过长，天道强行截断...）"

class AIWriter:
    """Wraps chat-completions calls with retry and prompt helpers."""

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=Config.OPENAI_API_BASE,
            api_key=Config.OPENAI_API_KEY
        )
        self.summary_file: str = "plot_summary.txt"
        self.last_chapter_content: str = ""
        self.messages: List[ChatMessage] = []
        self.debug: bool = False

    def _debug_dump_prompt(self, messages: Sequence[ChatMessage]) -> None:
        """Print full request payload when debug mode is enabled."""
        print("\n" + "=" * 50, flush=True)
        print(" [DEBUG] AI PROMPT:", flush=True)
        print(json.dumps(list(messages), ensure_ascii=False, indent=2), flush=True)
        print("=" * 50 + "\n", flush=True)

    def _build_extra_body(self) -> Dict[str, Dict[str, bool]]:
        """Return provider-specific options to disable reasoning stream."""
        return {"chat_template_kwargs": {"enable_thinking": False, "clear_thinking": True}}

    def _system_message(self, content: str) -> ChatCompletionSystemMessageParam:
        return {"role": "system", "content": content}

    def _user_message(self, content: str) -> ChatCompletionUserMessageParam:
        return {"role": "user", "content": content}

    def _assistant_message(self, content: str) -> ChatCompletionAssistantMessageParam:
        return {"role": "assistant", "content": content}

    def _call_api(self, messages: Sequence[ChatMessage], max_tokens: int = Config.MAX_TOKENS) -> Optional[str]:
        """核心：归元斩思模式，带指数退避重试机制"""
        # Retry loop intentionally wraps the full request so transient model/network errors can self-heal.
        if self.debug:
            self._debug_dump_prompt(messages)
            
        for attempt in range(DEFAULT_RETRY_TIMES):
            try:
                completion = self.client.chat.completions.create(
                    model=Config.MODEL_NAME,
                    messages=list(messages),
                    temperature=Config.TEMPERATURE,
                    max_tokens=max_tokens,
                    extra_body=self._build_extra_body(),
                    stream=False
                )
                full_response = completion.choices[0].message.content

                if not full_response:
                    raise ValueError("Empty response from API")

                return full_response

            except Exception as e:
                wait_time = 2 ** (attempt + 1)
                print(f" [API ERROR] 尝试 {attempt+1}/{DEFAULT_RETRY_TIMES} 失败: {str(e)}。{wait_time}秒后重试...")
                time.sleep(wait_time)
        return None

    def generate_quiz(self, subject: str, topic: str) -> Optional[str]:
        """让 AI 针对知识点快速出题 (归元模式：极简提示词)"""
        prompt = f"请针对高中{subject}知识点【{topic}】设计1道选择题。输出格式：【题目】、答案和解析。总字数控制在150字以内，不要任何废话。"

        messages = [
            self._system_message("你是一名精准的命题机器。"),
            self._user_message(prompt),
        ]
        return self._call_api(messages, max_tokens=QUIZ_MAX_TOKENS)

    def generate_scene(
        self,
        prompt: str,
        stats_context: str,
        system_instruction: Optional[str] = None,
        min_length: int = 4000,
        max_length: int = 20000,
    ) -> str:
        """Generate one chapter body via iterative continuation calls."""
        # Continue generation until end marker or hard length limit to stabilize chapter completeness.
        messages = [
            self._system_message(system_instruction or Config.SYSTEM_PROMPT),
            self._user_message(f"【数据包】\n{stats_context}\n\n【大纲】\n{prompt}\n\n请开笔："),
        ]
        
        full_content = ""
        while True:
            sys.stdout.write(f"\n [AI Writing... {len(full_content)} chars] "); sys.stdout.flush()
            new_text = self._call_api(messages)
            if not new_text:
                print(" [ERROR] AI 未返回任何内容，写作中断。")
                break
            
            full_content += new_text + "\n"
            messages.append(self._assistant_message(new_text))
            
            if CHAPTER_END_MARKER in full_content and len(full_content) >= min_length:
                full_content = full_content.replace(CHAPTER_END_MARKER, "").strip()
                break
            elif len(full_content) >= max_length:
                full_content = full_content[:max_length].strip()
                full_content += TRUNCATION_NOTICE
                break
            else:
                messages.append(self._user_message(CONTINUE_EXPAND_PROMPT))
        
        self.last_chapter_content = full_content
        return full_content

    def summarize_chapter(self, chapter_num: int, content: str) -> Optional[str]:
        """Generate and append chapter summary for long-term continuity."""
        prompt = f"请简要总结第{chapter_num}章的核心剧情发展、人物变动和关键信息。字数控制在200字以内。"
        
        messages = [
            self._system_message("你是一个严谨的剧情记录员。"),
            self._user_message(f"【章节内容】\n{content}\n\n【指令】\n{prompt}"),
        ]
        
        summary = self._call_api(messages, max_tokens=SUMMARY_MAX_TOKENS)
        if summary:
            with open(self.summary_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- 第{chapter_num}章 摘要 ---\n{summary}\n")
        return summary

writer = AIWriter()
