import random
from novel_engine.data.database import SkillTree, EventLibrary, NPCData, Subject

class Person:
    def __init__(self, name, role, tags):
        self.name = name
        self.role = role 
        self.tags = tags 
        # 基础属性 (天赋)
        self.talent = {s: random.randint(80, 150) for s in Subject.ALL}
        if "卷王" in tags: self.talent = {k:v*0.9 for k,v in self.talent.items()} # 卷王靠努力
        if "天赋怪" in tags: self.talent = {k:v*1.5 for k,v in self.talent.items()}
        
        # 当前能力值 (技能熟练度) - 初始值
        self.mastery = {s: random.randint(500, 2000) for s in Subject.ALL}
        
        self.skills = [] 
        self.mood = 50
        self.stress = 0
        self.fatigue = 0
        
        # 记忆/历史
        self.last_week_rank = 0
        self.current_rank = 0
        self.focus_subject = Subject.MATH # 当前主攻科目

    def get_exam_score(self, subject):
        # 考试分 = 熟练度 * (1 + 天赋修正) * 状态修正 - 随机波动
        base = self.mastery[subject]
        talent_mod = self.talent[subject] / 100
        
        # 状态影响：压力过大(>80)或疲劳过大(>80)会导致发挥失常
        state_mod = 1.0
        if self.stress > 80: state_mod -= 0.2
        if self.fatigue > 80: state_mod -= 0.2
        if self.mood > 80: state_mod += 0.1
        
        # 技能加成
        skill_bonus = sum([lvl * 50 for n, lvl, d in self.skills if subject in n])
        
        score = (base + skill_bonus) * talent_mod * state_mod
        # 归一化到 0-150 (假设 5000 熟练度对应 150 分)
        final_score = int(score / 50)
        return max(0, min(150, final_score))

    def plan_week(self, is_exam_coming):
        # AI 决策本周干什么
        if is_exam_coming:
            # 备考模式：补弱科
            scores = {s: self.mastery[s] for s in Subject.ALL}
            self.focus_subject = min(scores, key=scores.get)
            self.stress += 10
        else:
            # 日常模式：随机或按性格
            if "偏科狂" in self.tags or "信奥党" in self.tags:
                self.focus_subject = Subject.INFO if "信奥党" in self.tags else Subject.MATH
            else:
                self.focus_subject = random.choice(Subject.ALL)
                
    def execute_week(self):
        # 执行成长
        growth = self.talent[self.focus_subject] * 2 # 基础成长
        
        if "卷王" in self.tags:
            growth *= 1.5
            self.fatigue += 20
        elif "天赋怪" in self.tags:
            if random.random() < 0.5: # 经常偷懒
                growth = 0
                self.mood += 20
                self.stress -= 10
            else:
                growth *= 2.0 # 稍微学一下就很快
        
        self.mastery[self.focus_subject] += growth
        self.fatigue += 5
        
        # 疲劳恢复机制
        if self.fatigue > 90:
            self.fatigue = 0 # 强制休息一周
            self.mastery = {k:v*0.98 for k,v in self.mastery.items()} # 逆水行舟
            return f"{self.name}因疲劳过度病倒了，本周在宿舍躺平。"
            
        return f"{self.name}主攻{self.focus_subject}，熟练度+{int(growth)}。"

class BeingEngine:
    def __init__(self):
        self.students = []
        self.teachers = []
        self.protagonist = None
        self.init_world()
        self.event_pool = EventLibrary.COMMON + EventLibrary.RARE + EventLibrary.EPIC
        
        self.week_cycle = 0 # 0:Normal, 1:Prep, 2:Exam, 3:Result

    def init_world(self):
        # 初始化 30 人 (逻辑保持不变，复用之前的代码结构，但实例化新的 Person)
        # 1. 主角
        self.protagonist = Person("叶凌天", "主角", ["做题家", "信奥党"])
        self.protagonist.talent = {s: 100 for s in Subject.ALL} # 平庸开局
        self.protagonist.talent[Subject.INFO] = 200 # 金手指
        self.students.append(self.protagonist)
        
        # 2. 生成29个同学
        used_names = set()
        for i in range(29):
            is_male = random.random() < 0.6 
            name_pool = NPCData.NAMES_MALE if is_male else NPCData.NAMES_FEMALE
            name = random.choice(name_pool)
            while name in used_names: name = random.choice(name_pool) + str(i)
            used_names.add(name)
            
            arch_name, arch_desc, modifiers = random.choice(NPCData.ARCHETYPES)
            p = Person(name, "同学", [arch_name])
            self.students.append(p)

    def tick(self, week_idx):
        logs = []
        
        # 确定本周状态
        is_exam_week = (week_idx % 4 == 0)
        is_prep_week = (week_idx % 4 == 3)
        is_result_week = (week_idx % 4 == 1) and week_idx > 1
        
        phase_name = "日常周"
        if is_prep_week: phase_name = "备考周"
        if is_exam_week: phase_name = "考试周"
        if is_result_week: phase_name = "出分周"
        
        logs.append(f"【本周阶段】{phase_name}")

        # 1. 全员规划与执行
        for s in self.students:
            s.plan_week(is_exam_week or is_prep_week)
            action_log = s.execute_week()
            # 只有主角或特殊事件才记录详细日志，否则日志太长
            # 这里我们不记录每个人的流水账，只记录突发事件
        
        # 2. 突发事件 (Focus Events)
        # 挑选 3 个焦点人物
        focus_students = random.sample(self.students, 3)
        if self.protagonist not in focus_students: focus_students[0] = self.protagonist
        
        for s in focus_students:
            evt = random.choice(self.event_pool)
            _, desc, effect = evt
            logs.append(f"【焦点人物】{s.name}({','.join(s.tags)}): {desc}")
            self._apply_effect(s, effect)

        # 3. 考试结算逻辑
        if is_exam_week:
            self.calculate_rankings()
            top3 = self.rankings[:3]
            logs.append(f"【月考榜单】状元:{top3[0].name} 榜眼:{top3[1].name} 探花:{top3[2].name}")
            
            # 主角成绩
            mc_rank = self.students.index(self.protagonist) + 1
            logs.append(f"【主角战绩】全班第{mc_rank}名。")
            
            # 记录排名变化
            for s in self.students:
                s.last_week_rank = self.students.index(s) + 1

        return logs, phase_name

    def _apply_effect(self, p, effect_str):
        # 简化版效果应用
        if "mood+" in effect_str: p.mood += 10
        if "mood-" in effect_str: p.mood -= 10
        if "stress+" in effect_str: p.stress += 10
        if "stress-" in effect_str: p.stress -= 10
        if "mastery+" in effect_str: 
            for s in Subject.ALL: p.mastery[s] += 50

    def calculate_rankings(self):
        # 按总分排序
        self.students.sort(key=lambda s: sum([s.get_exam_score(sub) for sub in Subject.ALL if sub != Subject.INFO]), reverse=True)
        self.rankings = self.students # update cached list

    def get_student_detail(self, name):
        s = next((x for x in self.students if x.name == name), None)
        if not s: return ""
        scores = [f"{sub.value}:{s.get_exam_score(sub)}" for sub in Subject.ALL if sub != Subject.INFO]
        return f"{s.name} | 状态:心情{s.mood}/压力{s.stress} | 强科:{s.focus_subject.value} | 成绩单: {', '.join(scores)}"
