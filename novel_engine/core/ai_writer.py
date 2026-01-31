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
        self.client = OpenAI(base_url=self.config["api"]["base_url"], api_key=self.config["api"]["api_key"])
        self.model = self.config["api"]["model"]
        self.last_request_time, self.request_interval = 0, 2.0 
        self.summary_file, self.last_chapter_content = "plot_summary.txt", ""
        self.messages = []
        self.load_history()

    def load_history(self):
        if os.path.exists("chat_history.json"):
            try:
                with open("chat_history.json", "r", encoding="utf-8") as f: self.messages = json.load(f)
            except: self.messages = []
        if not self.messages: 
            self.messages = [{"role": "system", "content": self.config.get("system_prompt", "Initializing...")}]

    def save_history(self):
        if len(self.messages) > 100: self.messages = [self.messages[0]] + self.messages[-80:]
        with open("chat_history.json", "w", encoding="utf-8") as f: json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def _call_api(self, messages, max_tokens=16384):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval: time.sleep(self.request_interval - elapsed)
        
        extra_body = {}
        if "glm" in self.model.lower() and self.config["api"].get("enable_thinking"):
            extra_body = {"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}}

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.config["api"]["temperature"],
                top_p=1.0,
                max_tokens=max_tokens,
                extra_body=extra_body,
                stream=False # main.py 逻辑基于非流式，此处保持一致
            )
            self.last_request_time = time.time()
            return completion.choices[0].message.content
        except Exception as e:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            sys.stderr.write(f"[{timestamp}] [GLM_API_ERROR] {str(e)}\n")
            return None

    def summarize_chapter(self, chapter_num, content):
        prompt = f"请将下面内容浓缩成200字以内摘要，记录核心因果。内容：\n{content[:4000]}"
        summary = self._call_api([{"role": "system", "content": "你是一个冷酷的档案管理员。"}, {"role": "user", "content": prompt}], max_tokens=1000)
        if summary:
            with open(self.summary_file, "a", encoding="utf-8") as f: f.write(f"第{chapter_num}章摘要：{summary}\n")
            return summary
        return "摘要生成失败"

    def get_full_summary(self):
        if os.path.exists(self.summary_file):
            with open(self.summary_file, "r", encoding="utf-8") as f: return f.read()
        return "故事开始。"

    def generate_scene(self, prompt, stats_context, min_length=4000):
        full_summary = self.get_full_summary()
        
        messages = [
            {"role": "system", "content": self.messages[0]["content"] + "\n重要：本章情节全部交待完毕且字数达标后，输出 [CHAPTER_END] 表示完结。"},
            {"role": "user", "content": f"【前情提要】\n{full_summary}"},
            {"role": "user", "content": f"【上一章（衔接）】\n{self.last_chapter_content[-2000:]}"},
            {"role": "user", "content": f"【本章大纲与数据包】\n{prompt}\n\n【实时因果数据】\n{stats_context}\n\n请开始深思熟虑后的撰写（不少于4000字）："}
        ]
        
        full_content = ""
        while True:
            sys.stdout.write(f" [GLM-4.7 Generating... Current: {len(full_content)} chars]\n"); sys.stdout.flush()
            new_text = self._call_api(messages, max_tokens=16384)
            if not new_text: time.sleep(5); continue
            
            full_content += new_text + "\n"
            messages.append({"role": "assistant", "content": new_text})
            
            if "[CHAPTER_END]" in full_content and len(full_content) >= min_length:
                full_content = full_content.replace("[CHAPTER_END]", "").strip()
                break
            else:
                cmd = "（字数尚浅，请继续保持深度思考，展开描写后续情节，严禁直接总结！）" if len(full_content) < min_length else "（请将剩余事件交代完整，输出 [CHAPTER_END]。）"
                messages.append({"role": "user", "content": cmd})
        
        self.last_chapter_content = full_content
        return full_content

    def generate_quiz(self, subject, topic):
        p = f"请针对高中{subject}【{topic}】出一道极高难度的真题，含答案和深层陷阱解析。"
        return self._call_api([{"role": "system", "content": "奥赛命题组组长。"}, {"role": "user", "content": p}], max_tokens=2000)

writer = AIWriter()
