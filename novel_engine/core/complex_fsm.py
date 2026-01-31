import random
from enum import Enum
from novel_engine.data.competition_data import CompSect, CompSkills
from novel_engine.data.jiekang_loader import vocab

class GameState(Enum):
    NORMAL = "日常修行"
    EXAM_PREP = "闭关备考"
    EXAM_COMBAT = "正道试炼"
    COMP_TRAINING = "旁门潜修"
    COMP_BATTLE = "魔教征伐"
    SLUMP = "走火入魔"
    HOLIDAY = "云游修整"
    CONFLICT = "道心抉择"

class NPC:
    def __init__(self, name, sect, archetype, base_score):
        self.name = name
        self.sect = sect
        self.archetype = archetype
        self.score = base_score
        
    def update(self, year):
        # Diminishing returns for genius
        growth_cap = 750
        if self.score >= growth_cap: return
        
        factor = 1.0 if year == 1 else 0.5
        growth = random.randint(0, 8) * factor
        self.score += growth

class StudentProfile:
    def __init__(self):
        self.gaokao_score = 450 
        self.comp_score = 0 
        self.sanity = 100
        self.energy = 100
        self.reputation = 50 
        self.comp_sect = CompSect.INFO
        self.comp_rank = 0 

class DualFSM:
    def __init__(self):
        self.year = 1
        self.semester = 1
        self.week = 1
        self.max_weeks = 20
        self.state = GameState.NORMAL
        self.profile = StudentProfile()
        self.history_log = []
        
        self.npcs = [
            NPC("林清北", "全能", "天才", 600),
            NPC("苏小狸", "寒克武", "竞赛党", 400), 
        ]
        
        self.comp_start_week = (1, 1, 11) 
        self.comp_end_week = (3, 1, 15)

    def is_comp_active(self):
        current_abs_week = (self.year - 1) * 40 + (self.semester - 1) * 20 + self.week
        start_abs = (self.comp_start_week[0] - 1) * 40 + (self.comp_start_week[1] - 1) * 20 + self.comp_start_week[2]
        end_abs = (self.comp_end_week[0] - 1) * 40 + (self.comp_end_week[1] - 1) * 20 + self.comp_end_week[2]
        return start_abs <= current_abs_week <= end_abs and self.profile.comp_rank < 4

    def tick(self):
        self.profile.energy = 100
        event_desc = ""
        self.state = GameState.NORMAL
        date_str = f"高{self.year}{'上' if self.semester==1 else '下'} 第{self.week}周"
        
        for npc in self.npcs: npc.update(self.year)
        
        main_event = self._check_main_events()
        sub_event = self._check_comp_events() if self.is_comp_active() else None

        if main_event and sub_event:
            self.state = GameState.CONFLICT
            event_desc = self._resolve_conflict(main_event, sub_event)
        elif main_event:
            self.state = GameState.EXAM_COMBAT
            event_desc = self._handle_main(main_event)
        elif sub_event:
            self.state = GameState.COMP_BATTLE if "赛" in sub_event else GameState.COMP_TRAINING
            event_desc = self._handle_sub(sub_event)
        else:
            self.state = GameState.NORMAL
            event_desc = self._daily_grind()

        rival = self.npcs[0]
        log_entry = {
            "date": date_str,
            "state": self.state.value,
            "event": event_desc,
            "stats": f"高考力:{int(self.profile.gaokao_score)} | 竞赛力:{self.profile.comp_score} | 宿敌({rival.name}:{int(rival.score)})"
        }
        self.history_log.append(log_entry)
        
        self.week += 1
        if self.week > self.max_weeks:
            self._end_semester()

    def _end_semester(self):
        self.week = 1
        if self.semester == 1:
            self.semester = 2
            self.history_log.append({"date": "寒假", "state": "HOLIDAY", "event": "寒假：被父母送去‘衡水宗’分舵闭关，每日挥剑一万次（做卷子）。", "stats": "-"})
        else:
            self.semester = 1
            self.year += 1
            self.history_log.append({"date": "暑假", "state": "HOLIDAY", "event": "暑假：参加竞赛集训营，与来自全国的天才切磋。", "stats": "-"})

    def _check_main_events(self):
        if self.week == 10: return "期中大劫"
        if self.week == 20: return "期末天罚"
        if self.week in [4, 8, 12, 16]: return "月考切磋"
        if self.year == 3 and self.semester == 2 and self.week == 18: return "高考飞升"
        return None

    def _check_comp_events(self):
        if self.semester == 1:
            if self.week == 12: return "NOIP初赛"
            if self.week == 18: return "NOIP复赛"
        if self.semester == 2:
            if self.week == 8: return "省选(省队战)"
            if self.week == 15 and self.profile.comp_rank >= 1: return "NOI国决"
        if random.random() < 0.2: return "机房集训"
        return None

    def _resolve_conflict(self, main, sub):
        choices = [
            f"放弃{main}，潜入机房备战{sub}。林清北嘲笑主角是逃兵。",
            f"一边应付{main}，一边在草稿纸上推导{sub}的算法。双线操作，神魂枯竭。",
            f"在{main}的考场上，把作文写成了代码，震惊阅卷长老。"
        ]
        return f"【道心抉择】{random.choice(choices)}"

    def _handle_main(self, event):
        rival = self.npcs[0]
        diff = self.profile.gaokao_score - rival.score
        
        # 动态描述生成
        scenes = [
            "监考老师祭出‘信号屏蔽仪’，全场灵气被封印。",
            "压轴导数题化作一条恶龙，盘踞在卷面上。",
            "听力广播里传来了魔音贯耳的英语听力，试图扰乱道心。",
            "隔壁班学霸开启了‘抖腿光环’，引发地震波攻击。"
        ]
        
        if diff > 30: 
            res = "主角笔走龙蛇，提前交卷，留下一个孤傲的背影。"
        elif diff > -50:
            res = f"主角与{rival.name}在分数线上反复拉锯，最终险胜/惜败。"
        else:
            res = f"主角被题目镇压，道心破碎，看着{rival.name}绝尘而去。"
            
        growth = random.randint(15, 25) # 加快成长速度
        self.profile.gaokao_score += growth
        
        return f"【{event}】{random.choice(scenes)} {res}"

    def _handle_sub(self, event):
        skill = CompSkills.get_skill(self.profile.comp_sect)
        if "赛" in event:
            if random.random() < 0.7: 
                self.profile.comp_rank += 1
                return f"【魔教扬威】{event}。主角使用‘{skill}’暴力破解了第三题。获得金牌！全校通报。"
            else:
                return f"【魔教折戟】{event}。评测机显示‘Runtime Error’。主角掩面而泣，苏小狸递来一张纸巾。"
        else:
            daily = [
                f"机房空调坏了，服务器散热的声音如雷鸣。",
                f"因为在机房吃泡面，被教导主任抓住。",
                f"为了调试一个Bug，主角三天没洗头。"
            ]
            return f"【旁门潜修】{random.choice(daily)} 领悟了‘{skill}’。"

    def _daily_grind(self):
        events = [
            "晚自习停电，全班点蜡烛夜战。",
            f"食堂抢饭，利用‘图论’规划最短路径。",
            f"体育课被占，数学老师笑眯眯地走了进来。",
            "发现一本《五三》残卷，如获至宝。",
            "被没收了手机，只能在脑海中运行代码。",
            "同桌的笔掉在地上，主角帮忙捡起，引发蝴蝶效应。"
        ]
        self.profile.gaokao_score += 8
        return f"【日常】{random.choice(events)}"
