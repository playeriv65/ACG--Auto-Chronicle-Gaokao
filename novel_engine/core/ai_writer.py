import time
import json
import os
import sys
import traceback
from openai import OpenAI

class AIWriter:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.client = OpenAI(
            base_url=self.config["api"]["base_url"], 
            api_key=self.config["api"]["api_key"]
        )
        self.model = self.config["api"]["model"]
        self.last_request_time, self.request_interval = 0, 2.0 
        self.summary_file, self.last_chapter_content = "plot_summary.txt", ""
        self.messages = []

    def _call_api_stream(self, messages, max_tokens=16384):
        """核心：完全复刻宗主提供的流式调用逻辑"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval: time.sleep(self.request_interval - elapsed)
        
        full_response = ""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=1.0,
                top_p=1.0,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}},
                stream=True
            )
            
            for chunk in completion:
                if not getattr(chunk, "choices", None): continue
                if len(chunk.choices) == 0: continue
                delta = chunk.choices[0].delta
                
                # 忽略 reasoning_content (Thinking)，只采集正文 content
                content = getattr(delta, "content", None)
                if content is not None:
                    full_response += content
                    # 为了不让控制台死寂，输出个点
                    sys.stdout.write("·"); sys.stdout.flush()
            
            self.last_request_time = time.time()
            return full_response if full_response else None
        except Exception as e:
            sys.stderr.write(f" [STREAM ERROR] {str(e)}\n")
            return None

    def generate_quiz(self, subject, topic):
        """让 AI 针对特定知识点出 5 道梯度难题"""
        prompt = f"""请针对高中{subject}的知识点【{topic}】，出 5 道高质量题目。
要求：
1. 难度梯度：1道基础陷阱，2道中档综合，2道奥赛压轴。
2. 内容：每道题需包含【题目】、【答案】、【致死陷阱/逻辑核心】。
3. 严禁废话：直接输出题目内容."""

        messages = [
            {"role": "system", "content": "你是一名冷酷无情的全国顶级奥赛命题专家."},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_stream(messages, max_tokens=4000)

    def generate_scene(self, prompt, stats_context, min_length=4000):
        # ... (逻辑同前，但内部调用 _call_api_stream) ...
        messages = [
            {"role": "system", "content": "你是一个硬核校园爽文作家。完结后输出 [CHAPTER_END]。"},
            {"role": "user", "content": f"【数据包】\n{stats_context}\n\n【大纲】\n{prompt}\n\n请开笔（4000字+）："}
        ]
        
        full_content = ""
        while True:
            sys.stdout.write(f"\n [AI Writing... {len(full_content)} chars] "); sys.stdout.flush()
            new_text = self._call_api_stream(messages, max_tokens=16384)
            if not new_text: time.sleep(10); continue
            
            full_content += new_text + "\n"
            messages.append({"role": "assistant", "content": new_text})
            
            if "[CHAPTER_END]" in full_content and len(full_content) >= min_length:
                full_content = full_content.replace("[CHAPTER_END]", "").strip()
                break
            else:
                messages.append({"role": "user", "content": "（字数不足，请继续深度扩写剧情细节，严禁收尾！）"})
        
        self.last_chapter_content = full_content
        return full_content

writer = AIWriter()