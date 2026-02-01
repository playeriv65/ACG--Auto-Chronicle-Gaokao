import sys
import os
import json
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer

CONFIG_FILE = "config.json"
CHAPTER_DIR = "novel_chapters"
SAVE_FILE = "save_state.json"

class NovelGenerator:
    def __init__(self):
        self.engine = BeingEngine()
        self.total_chars, self.chapter_count = 0, 1
        self.year, self.semester, self.week = 1, 1, 1
        self.load_state()

    def load_state(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_chars, self.chapter_count = data.get('total_chars', 0), data.get('chapter_count', 1)
                    self.year, self.semester, self.week = data.get('year', 1), data.get('semester', 1), data.get('week', 1)
                    if "engine_state" in data: self.engine.from_dict(data["engine_state"])
            except: self.engine.init_world()
        else: self.engine.init_world()

    def save_state(self):
        state_data = {'total_chars': self.total_chars, 'chapter_count': self.chapter_count, 'year': self.year, 'semester': self.semester, 'week': self.week, 'engine_state': self.engine.to_dict()}
        with open(SAVE_FILE, 'w', encoding='utf-8') as f: json.dump(state_data, f, ensure_ascii=False, indent=2)

    def run(self):
        while self.year <= 3:
            date_str = f"G{self.year}S{self.semester}_W{self.week:02d}"
            logs, battle_type, quiz_content = self.engine.tick(self.week)
            mc_detail = self.engine.get_student_detail(self.engine.protagonist.name)
            
            prompt = f"【节点】{date_str} {battle_type}\n【主角】{mc_detail}\n【真题】{quiz_content}"
            print(f"[{time.strftime('%H:%M:%S')}] Forging: {date_str}...", end="", flush=True)
            
            try:
                content = writer.generate_scene(prompt, "维持高武侠风格，写满4000字。", min_length=4000)
                if content:
                    writer.summarize_chapter(self.chapter_count, content)
                    file_name = f"Chapter_{self.chapter_count:03d}_{date_str}.txt"
                    with open(os.path.join(CHAPTER_DIR, file_name), "w", encoding="utf-8") as f:
                        f.write(content)
                    self.total_chars += len(content)
                    self.chapter_count += 1
                    self.week += 1
                    if self.week > 20: 
                        self.week, self.semester = 1, (2 if self.semester==1 else 1)
                        if self.semester == 1: self.year += 1
                        self.engine.year, self.engine.semester = self.year, self.semester
                    self.save_state()
                    print(f" Done ({len(content)} chars)")
            except Exception as e:
                print(f" Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    NovelGenerator().run()
