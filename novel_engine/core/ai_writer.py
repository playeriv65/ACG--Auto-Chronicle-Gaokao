import time
import json
import os
import sys
import traceback
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv() # 加载 .env 灵力

class AIWriter:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.client = OpenAI(
            base_url=os.getenv("BASE_URL") or self.config["api"]["base_url"], 
            api_key=os.getenv("API_KEY") or self.config["api"]["api_key"]
        )
        self.model = self.config["api"]["model"]
        self.last_request_time, self.request_interval = 0, 2.0 
        self.summary_file, self.last_chapter_content = "plot_summary.txt", ""
        self.messages = []

    def _call_api(self, messages, max_tokens=16384):
        """核心：归元斩思模式，带指数退避重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_interval: time.sleep(self.request_interval - elapsed)
            
            try:
                # 强化封条：按照官方标准语法显式禁止推演
                extra_body={"chat_template_kwargs":{"enable_thinking":False,"clear_thinking":True}}
                
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=max_tokens,
                    extra_body=extra_body,
                    stream=False
                )
                full_response = completion.choices[0].message.content

                if not full_response:
                    raise ValueError("Empty response from API")

                self.last_request_time = time.time()
                return full_response

            except Exception as e:
                wait_time = 2 ** (attempt + 1)
                print(f" [API ERROR] 尝试 {attempt+1}/{max_retries} 失败: {str(e)}。{wait_time}秒后重试...")
                time.sleep(wait_time)
                self.last_request_time = time.time()
        
        return None

    def generate_quiz(self, subject, topic):
        """让 AI 针对知识点快速出题 (归元模式：极简提示词)"""
        prompt = f"请针对高中{subject}知识点【{topic}】设计1道选择题。输出格式：【题目】、答案和解析。总字数控制在150字以内，不要任何废话。"

        messages = [
            {"role": "system", "content": "你是一名精准的命题机器。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api(messages, max_tokens=500)

    def generate_scene(self, prompt, stats_context, min_length=4000):
        # ... (逻辑同前，但内部调用 _call_api_stream) ...
        messages = [
            {"role": "system", "content": "你是一个硬核校园爽文作家。完结后输出 [CHAPTER_END]。"},
            {"role": "user", "content": f"【数据包】\n{stats_context}\n\n【大纲】\n{prompt}\n\n请开笔（4000字+）："}
        ]
        
        full_content = ""
        while True:
            sys.stdout.write(f"\n [AI Writing... {len(full_content)} chars] "); sys.stdout.flush()
            new_text = self._call_api(messages, max_tokens=16384)
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