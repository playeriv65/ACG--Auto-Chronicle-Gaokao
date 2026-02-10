from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def run_compare_spirit(mode_name: str, enable_thinking: bool) -> None:
    """单次灵力感应法仪"""
    use_color = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
    reasoning_color = "\033[90m" if use_color else ""
    content_color = "\033[96m" if use_color else ""
    reset_color = "\033[0m" if use_color else ""
    title_color = "\033[93m" if use_color else ""

    print(f"\n{title_color}{'=' * 20} 开启阵法: {mode_name} {'=' * 20}{reset_color}")

    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")
    client = OpenAI(base_url=base_url, api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model="z-ai/glm4.7",
            messages=[{"role": "user", "content": "给我出一道超难的化学推断题。"}],
            temperature=1,
            top_p=1,
            max_tokens=128,
            extra_body={"chat_template_kwargs": {"enable_thinking": enable_thinking, "clear_thinking": True}},
            stream=True,
        )

        full_response = ""
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            if len(chunk.choices) == 0:
                continue

            delta = chunk.choices[0].delta

            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                sys.stdout.write(f"{reasoning_color}{reasoning}{reset_color}")
                sys.stdout.flush()

            content = getattr(delta, "content", None)
            if content:
                sys.stdout.write(f"{content_color}{content}{reset_color}")
                sys.stdout.flush()
                full_response += content

        print(f"\n{title_color}{'-' * 50}{reset_color}")
        print(f"[验证] 正文总字数: {len(full_response)}")

    except Exception as e:
        print(f"\n[失败] 阵法受损: {str(e)}")


def main() -> None:
    print("🚀 [天库对比大阵] 启动...")
    run_compare_spirit("【思维全开】(Thinking Enabled)", True)

    print("\n\n" + "*" * 60 + "\n\n")

    run_compare_spirit("【归元斩思】(Thinking Disabled)", False)

    print("\n✅ [对比大阵] 功德圆满。")


if __name__ == "__main__":
    main()
