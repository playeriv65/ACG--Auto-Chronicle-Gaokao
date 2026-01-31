import sys
import os
import random
import time
import json
import traceback
sys.path.append(os.getcwd())

from novel_engine.core.world import World, Character
from novel_engine.core.ai_writer import writer
from novel_engine.data import loader

# Configuration
TARGET_CHARS = 1000000 
OUTPUT_FILE = "generated_novel_v4_ultimate.txt"
SAVE_STATE_FILE = "save_state.json"

class UltimateEngine:
    def __init__(self):
        self.world = World()
        self.total_chars = 0
        self.chapter_count = 1
        self.scene_buffer = [] 
        
        # Load state if exists
        self.load_state()

    def load_state(self):
        if os.path.exists(SAVE_STATE_FILE):
            try:
                with open(SAVE_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_chars = data.get('total_chars', 0)
                    self.chapter_count = data.get('chapter_count', 1)
                    # Restore MC stats partially (simplified)
                    self.world.protagonist.level_idx = data.get('level', 0)
                    self.world.protagonist.spirit_stones = data.get('money', 0)
                    print(f"【系统】成功读取存档。当前字数：{self.total_chars}，章节：{self.chapter_count}")
            except Exception as e:
                print(f"【系统】存档读取失败，从头开始。Error: {e}")

    def save_state(self):
        data = {
            'total_chars': self.total_chars,
            'chapter_count': self.chapter_count,
            'level': self.world.protagonist.level_idx,
            'money': self.world.protagonist.spirit_stones
        }
        with open(SAVE_STATE_FILE, 'w') as f:
            json.dump(data, f)

    def log_event(self, text):
        self.scene_buffer.append(text)

    # --- Event Simulators ---
    
    def event_combat(self):
        mc = self.world.protagonist
        enemy = Character()
        enemy.level_idx = mc.level_idx + random.randint(0, 1)
        
        self.log_event(f"【遭遇战】主角在{self.world.get_current_map().name}遇到了{enemy.name}（{enemy.sect}）。")
        self.log_event(f"敌人嘲讽：{enemy.get_dialogue('provoke')}")
        
        rounds = 0
        combat_log = []
        while mc.current_hp > 0 and enemy.current_hp > 0 and rounds < 5:
            rounds += 1
            # MC Attack
            skill = random.choice(mc.skills)
            damage = mc.attack - enemy.defense
            enemy.current_hp -= max(1, damage)
            combat_log.append(f"主角施展{skill}，造成{max(1, damage)}点伤害。")
            
            if enemy.current_hp <= 0:
                combat_log.append(f"敌人陨落。")
                loot_stones = random.randint(10, 100) * (enemy.level_idx + 1)
                mc.add_loot(enemy.inventory, loot_stones)
                self.log_event(f"战斗胜利！搜刮获得：{', '.join(enemy.inventory)} 和 {loot_stones}灵石。")
                break
            
            # Enemy Attack
            if random.random() > 0.4:
                e_skill = random.choice(enemy.skills)
                mc.current_hp -= max(0, enemy.attack - mc.defense)
                combat_log.append(f"敌人反击使用{e_skill}。")

        self.log_event("交手过程：" + ";".join(combat_log))
        if mc.current_hp <= 0:
            self.log_event("主角重伤垂死，但依靠【不灭经】（系统）瞬间复原！")
            mc.current_hp = mc.max_hp

    def event_auction(self):
        mc = self.world.protagonist
        item_name = loader.items.get_item_name()
        price = random.randint(100, 5000) * (mc.level_idx + 1)
        
        self.log_event(f"【拍卖会】主角参加了一场盛大的拍卖会。")
        self.log_event(f"压轴宝物【{item_name}】登场，起拍价 {price // 2} 灵石。")
        
        rival = loader.names.get_person_name()
        self.log_event(f"富二代{rival}不断加价，嘲讽主角是穷鬼。")
        
        if mc.spirit_stones > price:
            mc.spirit_stones -= price
            mc.inventory.append(item_name)
            self.log_event(f"主角直接甩出 {price} 灵石，震惊全场，成功拿下宝物！")
            self.log_event(f"{rival}脸色铁青，灰溜溜地走了。")
        else:
            self.log_event(f"主角囊中羞涩，决定拍卖会结束后... ‘杀人夺宝’。")
            # Trigger immediate combat next time logic could be complex, keeping it simple here
            self.log_event(f"主角暗中记下了{rival}的气息，准备尾随。")

    def event_tournament(self):
        self.log_event(f"【宗门大比】{self.world.protagonist.sect} 开启了十年一度的内门大比。")
        self.log_event(f"主角报名参加，目标是第一名的奖励。")
        self.log_event(f"一路过关斩将，遇到了宿敌。")
        self.log_event(f"最终，主角爆发底牌，夺得魁首，全宗震动！")
        self.world.protagonist.spirit_stones += 1000

    def event_seclusion(self):
        self.log_event(f"【闭关修炼】主角感觉修为遇到了瓶颈，找了一处灵气浓郁的山洞闭关。")
        years = random.randint(1, 10)
        self.log_event(f"山中无甲子，寒尽不知年。转眼{years}年过去。")
        if random.random() < 0.5:
            new_skill = self.world.protagonist.level_up()
            self.log_event(f"出关之时，天地异象！主角成功突破，并领悟{new_skill}！")
        else:
            self.log_event(f"虽然没有突破大境界，但根基更加稳固了。")

    # --- Main Loop ---

    def flush_chapter(self, f):
        if not self.scene_buffer: return

        prompt = "\n".join(self.scene_buffer)
        mc = self.world.protagonist
        context = f"主角：{mc.name}，境界：{mc.level_idx}阶，灵石：{mc.spirit_stones}。性格：杀伐果断。当前持有：{', '.join(mc.inventory[:3])}..."
        
        print(f" -> [AI] 正在生成第 {self.chapter_count} 章 (类型: {prompt[:10]}...)...", end="")
        
        # Retry loop for AI
        content = ""
        retries = 0
        while retries < 3:
            try:
                content = writer.generate_scene(prompt, context)
                if content and "AI未返回内容" not in content:
                    break
            except Exception as e:
                print(f" [API Error: {e}, Retrying...]", end="")
                time.sleep(2)
            retries += 1
        
        if not content:
            content = "（系统：本章数据流丢失，主角正在虚空穿梭...）\n" + prompt

        # Write
        header = f"\n\n第{self.chapter_count}章 逆天改命\n"
        full_text = header + content + "\n"
        f.write(full_text)
        f.flush()
        
        added = len(full_text)
        self.total_chars += added
        self.chapter_count += 1
        print(f" 完成 (+{added}字 | 总计 {self.total_chars})")
        
        self.scene_buffer = []
        self.save_state()

    def run(self):
        print(f"启动 v4.0 永生世界引擎... 目标：{TARGET_CHARS} 字")
        print(f"输出文件：{OUTPUT_FILE}")
        
        # Open in append mode 'a'
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write("《永生传说：AI纪元》\n\n")

            while self.total_chars < TARGET_CHARS:
                try:
                    # Dice roll for event type
                    roll = random.random()
                    if roll < 0.5:
                        self.event_combat()
                    elif roll < 0.7:
                        self.event_auction()
                    elif roll < 0.85:
                        self.event_tournament()
                    else:
                        self.event_seclusion()
                    
                    self.flush_chapter(f)
                    
                except KeyboardInterrupt:
                    print("\n【系统】用户手动停止。进度已保存。")
                    self.save_state()
                    break
                except Exception as e:
                    print(f"\n【严重错误】{e}")
                    traceback.print_exc()
                    print("尝试自动恢复...")
                    time.sleep(5) # Wait and continue

if __name__ == "__main__":
    UltimateEngine().run()
