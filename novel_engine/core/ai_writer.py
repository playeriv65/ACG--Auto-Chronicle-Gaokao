import time
import json
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
        self.last_request_time = 0
        self.request_interval = 2.0 
        
    def _is_complete(self, text):
        """检查文本是否以标点结尾，判断是否被截断"""
        if not text: return False
        return text.strip()[-1] in ["。", "！", "”", "？", "…", ".", "!", "\"", "?"]

    def generate_scene(self, prompt, context=""):
        full_content = ""
        retry_count = 0
        
        while True: # 死磕循环
            try:
                # 速率限制保护
                elapsed = time.time() - self.last_request_time
                if elapsed < self.request_interval:
                    time.sleep(self.request_interval - elapsed)
                
                system_prompt = self.config["system_prompt"]
                user_prompt = f"【剧情大纲】：\n{prompt}\n\n【设定】：\n{context}\n\n请扩写："
                
                # 如果是续写模式
                if full_content:
                    user_prompt += f"\n\n（上文已生成内容）：\n{full_content[-500:]}\n\n（请紧接上文继续写，不要重复）："

                print(f" [API请求中...]", end="", flush=True)
                
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.config["api"]["temperature"],
                    top_p=0.9,
                    max_tokens=self.config["api"]["max_tokens"]
                )
                
                self.last_request_time = time.time()
                new_text = completion.choices[0].message.content
                
                if not new_text:
                    print(" [返回为空，重试]", end="", flush=True)
                    continue
                    
                full_content += new_text
                
                # 检查完整性
                if self._is_complete(full_content):
                    return full_content
                else:
                    print(" [检测到截断，正在续写...]", end="", flush=True)
                    # 不退出循环，继续下一轮请求，带着 full_content 作为上下文
                    # 但GLM API通常不支持直接传一大段让它补全，这里简化为再次请求让它"继续写完"
                    # 这里为了防止无限循环，简单判断：如果生成了很长但还是没完，可能需要强制截断或结束
                    if len(full_content) > 3000: # 这一章太长了，强制结束
                        full_content += "......"
                        return full_content
                    continue 

            except Exception as e:
                print(f" [错误: {e}，5秒后重试...]", end="", flush=True)
                time.sleep(5)
                retry_count += 1

# Singleton initialization
writer = AIWriter()
