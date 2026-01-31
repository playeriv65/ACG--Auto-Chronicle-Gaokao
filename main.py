import sys
import os
import json
import random
sys.path.append(os.getcwd())

from novel_engine.core.complex_fsm import DualFSM, GameState
from novel_engine.core.ai_writer import writer
from novel_engine.data.jiekang_loader import vocab # 复用之前的词库
from novel_engine.data.competition_data import CompSect

# Load Config
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

OUTPUT_FILE = "generated_novel.txt"
SAVE_FILE = "save_state.json"

class NovelGenerator:
    def __init__(self):
        self.fsm = DualFSM()
        self.total_chars = 0
        self.chapter_count = 1
        
        # Inject System Prompt
        writer.config["system_prompt"] = """你是一个中国校园风格的‘大纲流’网文作家。
背景：拮抗中学（竞争残酷如修仙宗门）。
核心：
1. ‘双修’设定：高考是正道，竞赛是旁门。
2. 风格：中二、热血、玩梗（把做题写成战斗）。
3. 必须严格按照用户提供的【大纲】和【状态】进行扩写，不要偏离剧情。"""
        
        self.load_state()

    def load_state(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_chars = data.get('total_chars', 0)
                    self.chapter_count = data.get('chapter_count', 1)
                    # Restore FSM State (Simplified)
                    self.fsm.year = data.get('year', 1)
                    self.fsm.semester = data.get('semester', 1)
                    self.fsm.week = data.get('week', 1)
                    self.fsm.profile.gaokao_score = data.get('gaokao', 450)
                    self.fsm.profile.comp_score = data.get('comp', 0)
                    print(f"【系统】读取存档：高{self.fsm.year} 第{self.fsm.week}周")
            except Exception as e:
                print(f"【警告】存档读取失败: {e}")

    def save_state(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({
                'total_chars': self.total_chars, 
                'chapter_count': self.chapter_count,
                'year': self.fsm.year,
                'semester': self.fsm.semester,
                'week': self.fsm.week,
                'gaokao': self.fsm.profile.gaokao_score,
                'comp': self.fsm.profile.comp_score
            }, f)

    def generate_prompt_from_fsm(self, log_entry):
        """将状态机生成的简短日志转换为详细的AI提示词"""
        state = log_entry['state']
        event = log_entry['event']
        stats = log_entry['stats']
        
        prompt = []
        prompt.append(f"【时间】：{log_entry['date']}")
        prompt.append(f"【当前状态】：{state}")
        prompt.append(f"【主角属性】：{stats}")
        prompt.append(f"【核心剧情】：{event}")
        
        # 增加细节描写指令
        if state == GameState.EXAM_COMBAT.value:
            prompt.append("要求：重点描写考场上的压抑气氛，以及主角解题时的特效（如笔尖生莲、逻辑链条锁死题目）。")
        elif state == GameState.COMP_BATTLE.value:
            prompt.append("要求：重点描写竞赛题目的变态难度，以及主角如何用‘旁门左道’（算法）破解。")
        elif state == GameState.COMP_TRAINING.value:
            prompt.append("要求：描写机房里阴暗、潮湿但充满极客精神的氛围。代码在屏幕上流动的视觉感。")
        elif "冲突" in event:
            prompt.append("要求：着重描写主角内心的挣扎，以及老师/教导主任的压迫感。")
            
        return "\n".join(prompt)

    def run(self):
        print(f"🏫 拮抗中学正式开学 | 版本：Git Managed | 目标：{CONFIG['novel']['target_chars']}字")
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write("《拮抗中学：双修编年史》\n\n")

            while self.fsm.year <= 3:
                # 1. 状态机推演一周
                self.fsm.tick()
                # 获取刚刚生成的那条日志
                latest_log = self.fsm.history_log[-1]
                
                # 如果是寒暑假或者普通周，稍微跳过一些，避免太流水账
                # 但为了百万字，我们尽量都要写
                
                # 2. 生成提示词
                prompt = self.generate_prompt_from_fsm(latest_log)
                context = f"当前章节：第{self.chapter_count}章"
                
                print(f"正在撰写：{latest_log['date']} [{latest_log['state']}]...", end="")
                
                # 3. AI 写作
                content = writer.generate_scene(prompt, context)
                
                # 4. 存盘
                header = f"\n\n第{self.chapter_count}章 {latest_log['date']}：{latest_log['state']}\n"
                f.write(header + content + "\n")
                f.flush()
                
                self.total_chars += len(content)
                self.chapter_count += 1
                self.save_state()
                print(f" 完成 ({len(content)}字)")
                
                # 高考结束检查
                if "高考飞升" in latest_log['event']:
                    print("🎓 高考结束，全书完！")
                    break

if __name__ == "__main__":
    NovelGenerator().run()
