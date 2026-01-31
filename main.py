import sys
import os
import json
import random
import time
import io
import threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer

CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CHAPTER_DIR = "novel_chapters"
SAVE_FILE = "save_state.json"

class NovelGenerator:
    def __init__(self):
        self.engine = BeingEngine()
        self.total_chars, self.chapter_count = 0, 1
        self.year, self.semester, self.week = 1, 1, 1
        
        # 终极文风锁定
        writer.system_prompt = """你是一个顶级爽文作家，擅长【校园修仙/数据流】。
背景：拮抗中学（分数即等级，题目即魔兽）。
核心画风：
1. **武侠化描写**：解出一道几何题叫‘斩落魔首’，写错一个符号叫‘走火入魔’。多用夸张的动词（震碎、咆哮、贯穿、撕裂）。
2. **拒绝列表**：严禁输出表格、严禁输出时间戳列表、严禁像说明书一样列数据。
3. **数据融合**：数值要写在对话或描写里（例：“这一笔落下，他感到自己数学修为又精进了几分”）。
4. **群像生动**：配角要有戏！那个喜欢转笔的同学本章必须转断一支笔，那个社恐的学霸必须在角落里瑟瑟发抖。
5. **高潮迭起**：每章末尾必须有一个‘震惊全场’或‘留下悬念’的钩子。"""
        
        self.load_state()

    def log(self, msg):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sys.stdout.write(f"[{timestamp}] {msg}\n"); sys.stdout.flush()

    def load_state(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_chars, self.chapter_count = data.get('total_chars', 0), data.get('chapter_count', 1)
                    self.year, self.semester, self.week = data.get('year', 1), data.get('semester', 1), data.get('week', 1)
                    if "engine_state" in data: self.engine.from_dict(data["engine_state"])
                    self.log(f"Karma Reconnected: Ch.{self.chapter_count}")
            except: self.engine.init_world()
        else: self.engine.init_world()

    def save_state(self):
        state_data = {'total_chars': self.total_chars, 'chapter_count': self.chapter_count, 'year': self.year, 'semester': self.semester, 'week': self.week, 'engine_state': self.engine.to_dict()}
        with open(SAVE_FILE, 'w', encoding='utf-8') as f: json.dump(state_data, f, ensure_ascii=False, indent=2)

    def generate_prompt(self, logs, battle_type, date_str, quiz_data=None):
        mc = self.engine.protagonist
        mc_detail = self.engine.get_student_detail(mc.name)
        
        # 挑选本周的“焦点受害者”
        focus_names = [log.split("【突发】")[1].split("(")[0] for log in logs if "【突发】" in log]
        rival_name = focus_names[0] if focus_names else self.engine.students[1].name
        rival_detail = self.engine.get_student_detail(rival_name)

        # 构造极具煽动性的指令
        prompt = f"""
【天命时刻】：{date_str} {battle_type}
【主角绝密档案】：{mc_detail}
【宿敌/配角档案】：{rival_detail}
【因果律事件】：
{chr(10).join(['- ' + l for l in logs])}

【真题降临】：
{quiz_data if quiz_data else "暂无"}

【主编寄语】：
1. 别写成日记！我们要的是小说！
2. 重点描写主角如何用他的‘信奥怪才’思维去虐杀那些传统的‘正道题海’。
3. 结尾必须让全班‘倒吸一口凉气’。
"""
        return prompt

    def run(self):
        self.log("Igniting Blood & Ink Engine...")
        while self.year <= 3:
            date_str = f"G{self.year}S{self.semester}_W{self.week:02d}"
            logs, battle_type, quiz_content = self.engine.tick(self.week)
            prompt = self.generate_prompt(logs, battle_type, date_str, quiz_data=quiz_content)
            context = f"接续第{self.chapter_count-1}章，延续热血节奏。"
            self.log(f"Forging: {date_str}")
            
            stop_heartbeat = threading.Event()
            def heartbeat():
                while not stop_heartbeat.is_set():
                    sys.stdout.write("."); sys.stdout.flush(); time.sleep(15)
            h_thread = threading.Thread(target=heartbeat); h_thread.start()
            
            try:
                content = writer.generate_scene(prompt, context, min_length=4000)
            except KeyboardInterrupt:
                self.save_state(); sys.exit(0)
            except Exception as e:
                self.log(f"Critical Error: {e}"); time.sleep(10); stop_heartbeat.set(); h_thread.join(); continue
            finally:
                stop_heartbeat.set(); h_thread.join(); sys.stdout.write("\n")
            
            if content:
                writer.summarize_chapter(self.chapter_count, content)
                file_name = f"Chapter_{self.chapter_count:03d}_{date_str}.txt"
                with open(os.path.join(CHAPTER_DIR, file_name), "w", encoding="utf-8") as f:
                    f.write(f"第{self.chapter_count}章 {date_str} {battle_type}\n" + "="*50 + "\n\n" + content)
                self.total_chars += len(content)
                self.chapter_count += 1
                self.week += 1
                if self.week > 20: 
                    self.week, self.semester = 1, (2 if self.semester==1 else 1)
                    if self.semester == 1: self.year += 1
                    self.engine.year, self.engine.semester = self.year, self.semester
                self.save_state()
                self.log(f"Finished: {file_name} ({len(content)} chars)")

if __name__ == "__main__":
    NovelGenerator().run()