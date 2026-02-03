import time
import json
import os
import sys
import traceback
from openai import OpenAI
from config import Config

class AIWriter:
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.OPENAI_API_BASE,
            api_key=Config.OPENAI_API_KEY
        )
        self.summary_file, self.last_chapter_content = "plot_summary.txt", ""
        self.messages = []
        self.debug = False

    def _call_api(self, messages, max_tokens=Config.MAX_TOKENS):
        """核心：归元斩思模式，带指数退避重试机制"""
        if self.debug:
            print("\n" + "="*50, flush=True)
            print(" [DEBUG] AI PROMPT:", flush=True)
            print(json.dumps(messages, ensure_ascii=False, indent=2), flush=True)
            print("="*50 + "\n", flush=True)
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 强化封条：按照官方标准语法显式禁止推演
                extra_body={"chat_template_kwargs":{"enable_thinking":False,"clear_thinking":True}}
                
                completion = self.client.chat.completions.create(
                    model=Config.MODEL_NAME,
                    messages=messages,
                    temperature=Config.TEMPERATURE,
                    max_tokens=max_tokens,
                    extra_body=extra_body,
                    stream=False
                )
                full_response = completion.choices[0].message.content

                if not full_response:
                    raise ValueError("Empty response from API")

                return full_response

            except Exception as e:
                wait_time = 2 ** (attempt + 1)
                print(f" [API ERROR] 尝试 {attempt+1}/{max_retries} 失败: {str(e)}。{wait_time}秒后重试...")
                time.sleep(wait_time)
        return None

    def generate_quiz(self, subject, topic):
        """让 AI 针对知识点快速出题 (归元模式：极简提示词)"""
        prompt = f"请针对高中{subject}知识点【{topic}】设计1道选择题。输出格式：【题目】、答案和解析。总字数控制在150字以内，不要任何废话。"

        messages = [
            {"role": "system", "content": "你是一名精准的命题机器。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api(messages, max_tokens=500)

    def generate_scene(self, prompt, stats_context, system_instruction=None, min_length=4000, max_length=20000):
        messages = [
            {"role": "system", "content": Config.SYSTEM_PROMPT},
            {"role": "user", "content": f"【数据包】\n{stats_context}\n\n【大纲】\n{prompt}\n\n请开笔："}
        ]
        
        full_content = ""
        while True:
            sys.stdout.write(f"\n [AI Writing... {len(full_content)} chars] "); sys.stdout.flush()
            new_text = self._call_api(messages)
            if not new_text:
                print(" [ERROR] AI 未返回任何内容，写作中断。")
                break
            
            full_content += new_text + "\n"
            messages.append({"role": "assistant", "content": new_text})
            
            if "[CHAPTER_END]" in full_content and len(full_content) >= min_length:
                full_content = full_content.replace("[CHAPTER_END]", "").strip()
                break
            elif len(full_content) >= max_length:
                full_content = full_content[:max_length].strip()
                full_content += "\n\n（此处因篇幅过长，天道强行截断...）"
                break
            else:
                messages.append({"role": "user", "content": "（字数不足，请继续深度扩写剧情细节，严禁收尾！）"})
        
        self.last_chapter_content = full_content
        return full_content

    def summarize_chapter(self, chapter_num, content):
        """让 AI 总结本章核心剧情，用于维持因果连续性"""
        prompt = f"请简要总结第{chapter_num}章的核心剧情发展、人物变动和关键信息。字数控制在200字以内。"
        
        messages = [
            {"role": "system", "content": "你是一个严谨的剧情记录员。"},
            {"role": "user", "content": f"【章节内容】\n{content}\n\n【指令】\n{prompt}"}
        ]
        
        summary = self._call_api(messages, max_tokens=2000)
        if summary:
            with open(self.summary_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- 第{chapter_num}章 摘要 ---\n{summary}\n")
        return summary

writer = AIWriter()