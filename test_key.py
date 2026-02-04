import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 灵力
load_dotenv()

def run_compare_spirit(mode_name, enable_thinking):
    """单次灵力感应法仪"""
    _USE_COLOR = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
    _REASONING_COLOR = "\033[90m" if _USE_COLOR else ""
    _CONTENT_COLOR = "\033[96m" if _USE_COLOR else ""
    _RESET_COLOR = "\033[0m" if _USE_COLOR else ""
    _TITLE_COLOR = "\033[93m" if _USE_COLOR else ""

    print(f"\n{_TITLE_COLOR}{'='*20} 开启阵法: {mode_name} {'='*20}{_RESET_COLOR}")
    
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    try:
        completion = client.chat.completions.create(
            model="z-ai/glm4.7",
            messages=[{"role": "user", "content": "给我出一道超难的化学推断题。"}],
            temperature=1,
            top_p=1,
            max_tokens=128,
            extra_body={"chat_template_kwargs": {"enable_thinking": enable_thinking, "clear_thinking": True}},
            stream=True
        )

        full_response = ""
        for chunk in completion:
            if not getattr(chunk, "choices", None): continue
            if len(chunk.choices) == 0: continue
            
            delta = chunk.choices[0].delta
            
            # 捕获并显示思考过程 (如果有)
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                sys.stdout.write(f"{_REASONING_COLOR}{reasoning}{_RESET_COLOR}")
                sys.stdout.flush()
            
            # 捕获并显示正文
            content = getattr(delta, "content", None)
            if content:
                sys.stdout.write(f"{_CONTENT_COLOR}{content}{_RESET_COLOR}")
                sys.stdout.flush()
                full_response += content

        print(f"\n{_TITLE_COLOR}{'-'*50}{_RESET_COLOR}")
        print(f"[验证] 正文总字数: {len(full_response)}")

    except Exception as e:
        print(f"\n[失败] 阵法受损: {str(e)}")

def main():
    print("🚀 [天库对比大阵] 启动...")
    # 第一场：开启思考
    run_compare_spirit("【思维全开】(Thinking Enabled)", True)
    
    print("\n\n" + "*"*60 + "\n\n")
    
    # 第二场：斩断思维
    run_compare_spirit("【归元斩思】(Thinking Disabled)", False)
    
    print("\n✅ [对比大阵] 功德圆满。")

if __name__ == "__main__":
    main()
