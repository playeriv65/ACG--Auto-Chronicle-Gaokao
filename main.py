import sys
import os
import json
import random
sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer
from novel_engine.data.database import Subject

# Load Config
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

OUTPUT_FILE = "generated_novel.txt"
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
1. 必须基于提供的【班级日志】进行扩写。
2. 严格遵守时间周期逻辑：
   - 备考周：写气氛压抑、临阵磨枪、抢占资源。
   - 考试周：写考场如战场、题目如魔兽、笔尖如刀剑。
   - 出分周：写榜单发布后的众生相、排名的剧烈变动。
   - 日常周：写积累、顿悟、同学间的摩擦。
3. 重点描写【焦点人物】的互动。引用他们的数据变化（如“王强虽然数学考了140，但因为偏科总分依然垫底”）。"""
        
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

    def generate_prompt(self, logs, phase_name, date_str):
        # 获取主角详情
        mc_detail = self.engine.get_student_detail("叶凌天")
        
        # 随机抽取一个配角的详情，作为对比
        rival_name = logs[-1].split(":")[1].split()[0] if "月考榜单" in logs[-1] else "林峰" # 简单抓取
        rival_detail = self.engine.get_student_detail(rival_name)
        if not rival_detail: rival_detail = self.engine.get_student_detail(self.engine.students[1].name)

        lines = []
        lines.append(f"【时间】{date_str}（{phase_name}）")
        lines.append(f"【主角面板】{mc_detail}")
        lines.append(f"【对照组面板】{rival_detail}")
        lines.append("【本周大事件】")
        for log in logs:
            lines.append(f"- {log}")
            
        lines.append("\n要求：")
        if phase_name == "考试周":
            lines.append("本章重点描写考试过程。描写数学最后一道大题的恐怖，以及主角如何利用‘信奥思维’去解物理题。")
        elif phase_name == "出分周":
            lines.append("本章重点描写排名公布时的心理战。主角看着自己的排名，是惊喜还是不甘？对比卷王和天赋怪的不同反应。")
        else:
            lines.append("本章重点描写日常积累。突发事件如何打乱了主角的学习计划？")
            
        return "\n".join(lines)

    def run(self):
        print(f"🏫 拮抗中学：众生相版v2 | 目标：{CONFIG['novel']['target_chars']}字")
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write("《拮抗中学：众生相》\n\n")

            while self.year <= 3:
                date_str = f"高{self.year}{'上' if self.semester==1 else '下'} 第{self.week}周"
                
                # 1. 引擎推演
                logs, phase_name = self.engine.tick(self.week)
                
                # 2. 生成 Prompt
                prompt = self.generate_prompt(logs, phase_name, date_str)
                context = f"当前章节：第{self.chapter_count}章"
                
                print(f"正在撰写：{date_str} [{phase_name}]...", end="")
                
                # 3. AI 写作
                content = writer.generate_scene(prompt, context)
                
                # 4. 存盘
                header = f"\n\n第{self.chapter_count}章 {date_str} {phase_name}\n"
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
