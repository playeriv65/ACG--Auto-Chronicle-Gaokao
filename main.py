import sys
import os
import json
import random
sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer

# Load Config
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

OUTPUT_FILE = "novel.txt"
SAVE_FILE = "save_state.json"

class NovelGenerator:
    def __init__(self):
        self.engine = BeingEngine()
        self.total_chars = 0
        self.chapter_count = 1
        self.year = 1
        self.semester = 1
        self.week = 1
        
        # Inject System Prompt
        writer.config["system_prompt"] = """你是一个硬核‘数据流’校园修仙小说家。
背景：拮抗中学（全员恶人，分数至上）。
核心：
1. 必须基于提供的【班级日志】进行扩写，所有NPC的名字、技能、事件都要用上。
2. 技能描述必须硬核：使用‘牛顿第三定律’反弹伤害，使用‘化学平衡’抵抗压力。
3. 风格：群像剧，不要只写主角，要体现班级里其他人的勾心斗角。
4. 每一章结尾要总结一下主角的排名变化。"""
        
        self.load_state()

    def load_state(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_chars = data.get('total_chars', 0)
                    self.chapter_count = data.get('chapter_count', 1)
                    self.year = data.get('year', 1)
                    self.semester = data.get('semester', 1)
                    self.week = data.get('week', 1)
                    print(f"【系统】读取存档：高{self.year} 第{self.week}周")
            except: pass

    def save_state(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({
                'total_chars': self.total_chars, 
                'chapter_count': self.chapter_count,
                'year': self.year,
                'semester': self.semester,
                'week': self.week
            }, f)

    def generate_prompt(self, logs, date_str):
        report = self.engine.get_mc_report()
        rankings = self.engine.get_rankings()[:5] # Top 5
        
        lines = []
        lines.append(f"【时间】{date_str}")
        lines.append(f"【主角状态】{report}")
        lines.append(f"【班级前五】{', '.join([f'{n}({s})' for n,s in rankings])}")
        lines.append("【本周大事件】")
        for log in logs:
            lines.append(f"- {log}")
            
        lines.append("\n要求：")
        lines.append("1. 将上述‘突发事件’扩写为具体的冲突或趣事。")
        lines.append("2. 如果有‘领悟技能’，请详细描写领悟过程（如看到落叶领悟了万有引力）。")
        lines.append("3. 描写主角与其他同学（特别是卷王、天赋怪）的互动。")
        
        return "\n".join(lines)

    def run(self):
        print(f"🏫 拮抗中学：众生相版 | 目标：{CONFIG['novel']['target_chars']}字")
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write("《拮抗中学：众生相》\n\n")

            while self.year <= 3:
                date_str = f"高{self.year}{'上' if self.semester==1 else '下'} 第{self.week}周"
                
                # 1. 引擎推演
                logs = self.engine.tick_week()
                
                # 月考特殊处理
                if self.week % 4 == 0:
                    logs.append(f"【月考】本周进行了月考。全班气氛肃杀。")
                
                # 2. 生成 Prompt
                prompt = self.generate_prompt(logs, date_str)
                context = f"当前章节：第{self.chapter_count}章"
                
                print(f"正在撰写：{date_str}...", end="")
                
                # 3. AI 写作
                content = writer.generate_scene(prompt, context)
                
                # 4. 存盘
                header = f"\n\n第{self.chapter_count}章 {date_str}\n"
                f.write(header + content + "\n")
                f.flush()
                
                self.total_chars += len(content)
                self.chapter_count += 1
                self.save_state()
                print(f" 完成 ({len(content)}字)")
                
                # 时间流逝
                self.week += 1
                if self.week > 20:
                    self.week = 1
                    if self.semester == 1:
                        self.semester = 2
                    else:
                        self.semester = 1
                        self.year += 1

if __name__ == "__main__":
    NovelGenerator().run()