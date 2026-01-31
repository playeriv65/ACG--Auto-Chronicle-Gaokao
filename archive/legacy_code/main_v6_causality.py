import sys
import os
import json
import time
sys.path.append(os.getcwd())

from novel_engine.core.world import World
from novel_engine.core.plot import PlotEngine
from novel_engine.core.ai_writer import writer

# Config loading
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)
    
TARGET_CHARS = CONFIG["novel"]["target_chars"]
OUTPUT_FILE = "generated_novel_v6_causality.txt"
SAVE_FILE = "save_state_v6.json"

class CausalityEngine:
    def __init__(self):
        self.world = World()
        self.plot_engine = PlotEngine(self.world)
        self.total_chars = 0
        self.chapter_count = 1
        
        self.load_state()

    def load_state(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_chars = data.get('total_chars', 0)
                    self.chapter_count = data.get('chapter_count', 1)
                    # Simple state restore (In real project, need to pickle PlotEngine)
                    # Here we just reset tension/arcs to default to avoid complexity in JSON serialization for now
                    print(f"【系统】读取进度：第 {self.chapter_count} 章")
            except: pass

    def save_state(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({
                'total_chars': self.total_chars, 
                'chapter_count': self.chapter_count
            }, f)

    def run(self):
        print(f"🔮 v6.0 因果律引擎启动 | 目标：{TARGET_CHARS}字")
        print("逻辑状态机：已加载。仇恨链系统：已就绪。")
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write("《因果修仙》\nPowered by Causality Engine\n\n")

            while self.total_chars < TARGET_CHARS:
                # 1. 询问 PlotEngine 获取逻辑严密的大纲
                # 这是一个"Stateful"的操作，PlotEngine 内部会更新状态
                plot_outline = self.plot_engine.update()
                
                # Context info
                mc = self.world.protagonist
                state_name = self.plot_engine.state.value
                context = f"主角：{mc.name} | 境界：{mc.level_idx}阶 | 当前HP：{mc.current_hp}/{mc.max_hp} | 状态：【{state_name}】"
                
                print(f"正在生成第 {self.chapter_count} 章 [{state_name}]...", end="")
                
                # 2. AI Write
                content = writer.generate_scene(plot_outline, context)
                
                # 3. Output
                header = f"\n\n第{self.chapter_count}章 {state_name}篇\n"
                f.write(header + content + "\n")
                f.flush()
                
                # 4. Stats
                self.total_chars += len(content)
                self.chapter_count += 1
                self.save_state()
                print(f" 完成 ({len(content)}字)")

if __name__ == "__main__":
    CausalityEngine().run()
