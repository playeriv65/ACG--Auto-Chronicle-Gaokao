import sys
import os
import time
import json
import random
sys.path.append(os.getcwd())

from novel_engine.core.world import World, Character
from novel_engine.core.ai_writer import writer
from novel_engine.data import loader

# Load Config
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TARGET_CHARS = CONFIG["novel"]["target_chars"]
OUTPUT_FILE = CONFIG["novel"]["output_file"]
SAVE_FILE = CONFIG["novel"]["save_state_file"]

class ProEngine:
    def __init__(self):
        self.world = World()
        self.total_chars = 0
        self.chapter_count = 1
        self.buffer = []
        self.load_state()

    def load_state(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_chars = data.get('total_chars', 0)
                    self.chapter_count = data.get('chapter_count', 1)
            except: pass

    def save_state(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({
                'total_chars': self.total_chars, 
                'chapter_count': self.chapter_count
            }, f)

    def generate_prompt(self):
        # 简化版事件选择器，保证必然发生点什么
        mc = self.world.protagonist
        event_type = random.choice(["combat", "adventure", "breakthrough"])
        
        lines = []
        if event_type == "combat":
            enemy = Character()
            enemy.level_idx = mc.level_idx
            lines.append(f"主角在{self.world.get_current_map().name}遭遇强敌{enemy.name}。")
            lines.append(f"敌人使用了{random.choice(enemy.skills)}，威力巨大。")
            lines.append(f"主角陷入苦战，最终使用底牌反杀。")
        elif event_type == "adventure":
            lines.append(f"主角进入了一个上古遗迹。 ")
            lines.append(f"发现了一本残缺的{loader.items.get_item_name()}。")
            lines.append(f"但是有守护兽看守，主角智取宝物。")
        else:
            lines.append(f"主角感悟天地法则，准备突破{mc.level_idx + 1}阶。")
            lines.append(f"天劫降临，九死一生。")
            lines.append(f"最终成功突破，全属性大幅提升。")
            
        return "\n".join(lines)

    def run(self, max_chapters=None):
        print(f"🔥 v5.0 宗门大阵启动 | 目标：{TARGET_CHARS}字 | 模式：{'无限' if max_chapters is None else f'演示({max_chapters}章)'}")
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write(f"{CONFIG['novel']['title']}\n\n")

            while self.total_chars < TARGET_CHARS:
                # 演示模式检查
                if max_chapters and self.chapter_count > max_chapters:
                    print("\n✅ 演示完成，阵法暂停。")
                    break

                # 1. 生成大纲
                prompt = self.generate_prompt()
                mc = self.world.protagonist
                context = f"主角：{mc.name}，{mc.level_idx}阶。当前状态：{random.choice(['杀气腾腾', '心如止水', '重伤初愈'])}。"
                
                print(f"正在炼制第 {self.chapter_count} 章...", end="")
                
                # 2. AI 扩写 (死磕模式)
                content = writer.generate_scene(prompt, context)
                
                # 3. 写入
                header = f"\n\n第{self.chapter_count}章 赛博飞升\n"
                f.write(header + content + "\n")
                f.flush()
                
                # 4. 统计与保存
                self.total_chars += len(content)
                self.chapter_count += 1
                self.save_state()
                print(f" 完成 (本章 {len(content)} 字)")

if __name__ == "__main__":
    # 这里设置为5章，为了向你展示结果
    ProEngine().run(max_chapters=5)
