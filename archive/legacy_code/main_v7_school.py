import sys
import os
import json
import random
sys.path.append(os.getcwd())

from novel_engine.core.school_logic import SchoolCalendar, EventType, StudentStatus
from novel_engine.data.jiekang_loader import vocab
from novel_engine.core.ai_writer import writer

# Load Config (We will inject a new system prompt dynamically)
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TARGET_CHARS = CONFIG["novel"]["target_chars"]
OUTPUT_FILE = "generated_novel_v7_school.txt"
SAVE_FILE = "save_state_v7.json"

# Override system prompt for School setting
SCHOOL_SYSTEM_PROMPT = """你是一个中国校园风格的‘爽文’作家。
背景：拮抗中学（虽然是高中，但内部竞争如同修仙宗门一样残酷）。
核心设定：
1. 将‘考试’描写成‘比武决斗’。
2. 将‘解题’描写成‘施展功法’（如：他使出了一招‘洛必达法则’，强行化解了这道极限题的杀气）。
3. 老师是‘长老’，教导主任是‘执法者’，参考书是‘秘籍’。
4. 风格要中二、热血、夸张，但逻辑必须基于真实的高中生活（刷题、排名、早自习）。
5. 主角叶凌天拥有‘题霸系统’，可以解析万物。
"""

class SchoolEngine:
    def __init__(self):
        self.calendar = SchoolCalendar()
        self.status = StudentStatus()
        self.total_chars = 0
        self.chapter_count = 1
        
        # Patch the writer's system prompt (Runtime injection)
        writer.config["system_prompt"] = SCHOOL_SYSTEM_PROMPT
        
        self.load_state()

    def load_state(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_chars = data.get('total_chars', 0)
                    self.chapter_count = data.get('chapter_count', 1)
                    self.calendar.year = data.get('year', 1)
                    self.calendar.semester = data.get('semester', 1)
                    self.calendar.week = data.get('week', 1)
                    self.status.rank_score = data.get('score', 100)
                    print(f"【系统】读取教务处档案：{self.calendar._get_date_string()}")
            except: pass

    def save_state(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({
                'total_chars': self.total_chars, 
                'chapter_count': self.chapter_count,
                'year': self.calendar.year,
                'semester': self.calendar.semester,
                'week': self.calendar.week,
                'score': self.status.rank_score
            }, f)

    def generate_prompt(self, event_type, date_str):
        title = self.status.get_title()
        skill = vocab.get_skill()
        item = random.choice(vocab.items)
        enemy = random.choice(vocab.enemies)
        
        lines = []
        lines.append(f"时间：{date_str}。 সন")
        lines.append(f"主角当前境界：【{title}】。")
        
        if event_type == EventType.NORMAL_STUDY:
            lines.append(f"事件：日常修炼（晚自习）。")
            lines.append(f"主角正在攻克一本{item}。 সন")
            lines.append(f"突然领悟了【{skill}】，解题速度提升100%。")
            lines.append(f"周围的学渣们感受到了来自智商的压制，纷纷颤抖。 সন")
            
        elif event_type == EventType.WEEKLY_TEST:
            lines.append(f"事件：周测切磋。 সন")
            lines.append(f"对手是{enemy}。 সন")
            lines.append(f"题目异常刁钻，充满了陷阱。 সন")
            lines.append(f"主角冷笑一声，祭出本命法宝‘错题本’，瞬间看破破绽。 সন")
            
        elif event_type in [EventType.MONTHLY_EXAM, EventType.MID_TERM, EventType.FINAL_EXAM]:
            lines.append(f"事件：{event_type.value}（大型战役）。 সন")
            lines.append(f"全校排名大洗牌。气氛肃杀。 সন")
            lines.append(f"考场上，监考老师（长老）释放出强大的威压。 সন")
            lines.append(f"压轴题是一头‘太古魔兽’（奥赛难度）。 সন")
            lines.append(f"主角火力全开，笔尖擦出火花，提前30分钟交卷，震惊全场。 সন")
            
        elif event_type == EventType.SPECIAL:
            lines.append(f"事件：突发状况（家长会/运动会）。 সন")
            lines.append(f"主角在不擅长的领域（如体育或面对家长）遭遇危机。 সন")
            lines.append(f"但系统开启了临时Buff，让主角再次装逼成功。 সন")
        
        elif event_type == EventType.GAOKAO:
            lines.append(f"事件：高考（飞升大劫）。 সন")
            lines.append(f"三年磨一剑。 সন")
            lines.append(f"这是最终的战场，数百万考生同台竞技。 সন")
            lines.append(f"主角回顾三年历程，心境圆满，下笔如有神。 সন")
            
        return "\n".join(lines)

    def run(self):
        print(f"🏫 拮抗中学开学啦！目标：{TARGET_CHARS}字")
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if os.path.getsize(OUTPUT_FILE) == 0:
                f.write("《学霸修仙：拮抗中学篇》\n\n")

            while self.total_chars < TARGET_CHARS and not self.calendar.is_graduated:
                # 1. Get Schedule
                event_type, date_str = self.calendar.advance_week()
                
                # 2. Simulate Status
                status_log = self.status.update(event_type)
                
                # 3. Generate Prompt
                prompt = self.generate_prompt(event_type, date_str)
                context = f"状态：{status_log} | 疲劳度：{self.status.fatigue}"
                
                print(f"正在书写 [{date_str}] {event_type.value}...", end="")
                
                # 4. AI Write
                content = writer.generate_scene(prompt, context)
                
                # 5. Save
                header = f"\n\n第{self.chapter_count}章 {date_str}：{event_type.value}\n"
                f.write(header + content + "\n")
                f.flush()
                
                self.total_chars += len(content)
                self.chapter_count += 1
                self.save_state()
                print(f" 完成 ({len(content)}字)")
            
            if self.calendar.is_graduated:
                print("🎓 恭喜毕业！全书完。 সন")

if __name__ == "__main__":
    SchoolEngine().run()
