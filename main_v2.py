import sys
import os
import random
# Add current dir to path to find packages
sys.path.append(os.getcwd())

from novel_engine.core.world import World
from novel_engine.core.combat import CombatSystem

TARGET_CHARS = 1000000 
OUTPUT_FILE = "generated_novel_v2.txt"

class StoryEngine:
    def __init__(self):
        self.world = World()
        self.buffer = []
        self.total_chars = 0
        self.combat_sys = CombatSystem(self.write_line)
        self.chapter_count = 1
        
    def write_line(self, text):
        self.buffer.append(text)

    def flush_chapter(self, f):
        title = f"\n\n第{self.chapter_count}章 {random.choice(['风云再起', '杀戮降临', '秘境探险', '强者之路', '生死一线'])} (v2.0智能生成)\n"
        content = title + "\n".join(self.buffer) + "\n"
        f.write(content)
        
        char_len = len(content)
        self.total_chars += char_len
        self.buffer = [] # Clear buffer
        self.chapter_count += 1
        return char_len

    def run(self):
        print(f"启动 v2.0 智能修仙模拟器... 目标：{TARGET_CHARS} 字")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("《智能修仙传》\n基于动态世界观与战斗模拟\n\n")
            
            while self.total_chars < TARGET_CHARS:
                # 1. Travel / Encounter
                curr_map = self.world.get_current_map()
                self.write_line(f"此时，{self.world.protagonist.name}正在{curr_map.name}历练。")
                self.write_line(f"这里环境恶劣，但对于拥有【系统】的他来说，正是练级的好地方。")
                
                # 2. Find Enemy
                if not curr_map.npcs:
                     # Refresh map mobs if empty
                     curr_map = self.world.maps[self.world.current_map_idx] # Simple refresh logic re-init or just re-add?
                     # Actually world init created fixed maps. Let's just spawn a new mob dynamically.
                     from novel_engine.core.world import Character
                     enemy = Character()
                     enemy.level_idx = self.world.protagonist.level_idx + random.randint(0, 1) # Scaling
                else:
                    enemy = curr_map.npcs.pop()

                # 3. Combat
                self.combat_sys.battle(self.world.protagonist, enemy)
                
                # 4. Level Up / Rest
                if random.random() < 0.2:
                    new_skill = self.world.protagonist.level_up()
                    self.write_line(f"\n【系统提示】恭喜宿主升级！当前境界：{self.world.protagonist.level_idx}阶！")
                    self.write_line(f"领悟新技能：【{new_skill}】！")
                    
                    # Map transition check
                    if self.world.protagonist.level_idx > curr_map.min_level + 5:
                        if self.world.move_to_next_map():
                             self.write_line(f"这个地图已经没有挑战性了。{self.world.protagonist.name}决定前往下一站。")
                
                # 5. Flush periodically
                if len(self.buffer) > 50: # Write every ~50 lines to form a chapter
                     self.flush_chapter(f)
                     
                if self.chapter_count % 100 == 0 and len(self.buffer) == 0:
                     print(f"进度：{self.total_chars} / {TARGET_CHARS} ({int(self.total_chars/TARGET_CHARS*100)}%)")
            
            # Final flush
            if self.buffer:
                self.flush_chapter(f)

if __name__ == "__main__":
    eng = StoryEngine()
    eng.run()
    print("Done.")
