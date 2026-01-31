import sys
import os
import random
import time
sys.path.append(os.getcwd())

from novel_engine.core.world import World
from novel_engine.core.ai_writer import writer

# Configuration
TARGET_CHARS = 1000000 
OUTPUT_FILE = "generated_novel_v3_ai.txt"

class AIStoryEngine:
    def __init__(self):
        self.world = World()
        self.total_chars = 0
        self.chapter_count = 1
        self.scene_buffer = [] # Accumulate logic events to form a prompt
        
    def log_event(self, text):
        # Accumulate simulation events into a buffer
        self.scene_buffer.append(text)

    def flush_scene_to_ai(self, f):
        if not self.scene_buffer:
            return

        # Construct Prompt from simulation events
        plot_outline = "\n".join(self.scene_buffer)
        
        # Context info
        mc = self.world.protagonist
        context = f"主角：{mc.name}，境界：{mc.level_idx}阶，所在地图：{self.world.get_current_map().name}。性格：杀伐果断。"
        
        print(f" -> 正在调用 AI 生成第 {self.chapter_count} 章片段...", end="", flush=True)
        
        # Call AI
        content = writer.generate_scene(plot_outline, context)
        
        # Write to file
        header = f"\n\n第{self.chapter_count}章\n"
        full_text = header + content + "\n"
        f.write(full_text)
        f.flush()
        
        # Update stats
        added_len = len(full_text)
        self.total_chars += added_len
        self.chapter_count += 1
        print(f" 完成 (本章{len(content)}字, 总计{self.total_chars}字)")
        
        # Clear buffer
        self.scene_buffer = []

    def run(self):
        print(f"启动 v3.0 AI 豪华版... 接入 NVIDIA GLM-4 模型")
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f: # Append mode
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write("《AI 修仙：无尽传说》\nPowered by GLM-4\n\n")
            
            while self.total_chars < TARGET_CHARS:
                # --- Simulation Phase (Same logic as v2, but simplified loop) ---
                curr_map = self.world.get_current_map()
                
                # 1. Opening
                self.log_event(f"主角{self.world.protagonist.name}来到了{curr_map.name}。这里气氛压抑。")
                
                # 2. Encounter
                from novel_engine.core.world import Character
                enemy = Character() # New random enemy
                enemy.level_idx = self.world.protagonist.level_idx + random.randint(0, 2)
                
                self.log_event(f"遭遇敌人：{enemy.name}（{enemy.sect}，{enemy.level_idx}阶）。")
                self.log_event(f"敌人挑衅：{enemy.get_dialogue('provoke')}")
                
                # 3. Combat Summary
                rounds = 0
                combat_log = []
                while self.world.protagonist.current_hp > 0 and enemy.current_hp > 0 and rounds < 5:
                    rounds += 1
                    # MC attack
                    skill = random.choice(self.world.protagonist.skills)
                    combat_log.append(f"主角使用{skill}攻击。")
                    enemy.current_hp -= self.world.protagonist.attack
                    
                    if enemy.current_hp <= 0:
                        combat_log.append(f"敌人被击杀。遗言：{enemy.get_dialogue('dying')}")
                        break
                        
                    # Enemy attack
                    if random.random() > 0.3:
                        e_skill = random.choice(enemy.skills)
                        combat_log.append(f"敌人反击，使用{e_skill}。")
                        self.world.protagonist.current_hp -= max(0, enemy.attack - self.world.protagonist.defense)
                
                self.log_event("战斗过程：" + ";".join(combat_log))
                
                if self.world.protagonist.current_hp <= 0:
                     self.log_event("主角重伤倒地，但系统的力量修复了他的身体。")
                     self.world.protagonist.current_hp = self.world.protagonist.max_hp
                else:
                     self.log_event("主角获胜，搜刮了战利品。")
                     loot = enemy.inventory
                     if loot: self.log_event(f"获得物品：{', '.join(loot)}")

                # 4. Level Up Check
                if random.random() < 0.3:
                    new_skill = self.world.protagonist.level_up()
                    self.log_event(f"主角突破境界！当前为{self.world.protagonist.level_idx}阶。领悟新招式：{new_skill}。")

                # --- Generation Phase ---
                # We have enough "plot" for one chapter/scene now.
                self.flush_scene_to_ai(f)
                
                # Check target
                if self.total_chars >= TARGET_CHARS:
                    break

if __name__ == "__main__":
    eng = AIStoryEngine()
    eng.run()
