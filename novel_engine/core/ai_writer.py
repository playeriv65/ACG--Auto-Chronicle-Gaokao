import os
import time
from openai import OpenAI

class AIWriter:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key="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"
        )
        self.model = "z-ai/glm4.7"
        self.last_request_time = 0
        self.request_interval = 2.0 # Enforce ~30 requests/min to be safe
        
    def generate_scene(self, prompt, context=""):
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
            
        system_prompt = """你是一个专业的玄幻网文作家。请根据用户提供的剧情大纲，扩写成一段精彩的小说正文。
要求：
1. 风格热血、爽快，多用短句。
2. 重点描写战斗细节、特效夸张（如“空间破碎”、“大道磨灭”）。
3. 增加路人/反派的心理活动，突出主角的强大（侧面烘托）。
4. 字数要求：每次输出至少500字。
5. 不要输出任何解释性文字，直接输出小说内容。"""

        full_prompt = f"【当前剧情梗概】：\n{prompt}\n\n【上下文设定】：\n{context}\n\n请扩写这段剧情："

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.8,
                top_p=0.9,
                max_tokens=2048
            )
            
            self.last_request_time = time.time()
            res_content = completion.choices[0].message.content
            return res_content if res_content else "（AI未返回内容）"
        except Exception as e:
            print(f"\n[AI Error]: {e}")
            return f"（AI生成失败，系统自动填充）\n{prompt}\n"

# Singleton
writer = AIWriter()