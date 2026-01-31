import random
from novel_engine.data.database import SkillTree, EventLibrary, NPCData

class Subject:
    MATH = "数学"
    PHYS = "物理"
    CHEM = "化学"
    BIO = "生物"
    ENG = "英语"
    CHN = "语文"
    INFO = "信奥"
    ALL = [MATH, PHYS, CHEM, BIO, ENG, CHN, INFO]

class Person:
    def __init__(self, name, role, tags):
        self.name = name
        self.role = role # 主角/同学/老师
        self.tags = tags # ["卷王", "数学课代表"]
        self.stats = {s: 1000 for s in Subject.ALL}
        self.skills = [] # [(name, level, desc)]
        self.mood = 50
        self.stress = 50
        self.relation_with_mc = 0
        
    def get_power(self, subject):
        base = self.stats[subject]
        # 技能加成
        skill_bonus = len(self.skills) * 200 # 简化：拥有的技能越多越强
        # 状态修正
        mood_fix = (self.mood - 50) / 100
        return int((base + skill_bonus) * (1 + mood_fix))

class BeingEngine:
    def __init__(self):
        self.students = []
        self.teachers = []
        self.protagonist = None
        self.init_world()
        self.event_pool = EventLibrary.COMMON + EventLibrary.RARE + EventLibrary.EPIC

    def init_world(self):
        # 1. 主角
        self.protagonist = Person("叶凌天", "主角", ["做题家", "信奥党"])
        self.students.append(self.protagonist)
        
        # 2. 生成29个同学
        used_names = set()
        for i in range(29):
            is_male = random.random() < 0.6 # 理科班男生多
            name_pool = NPCData.NAMES_MALE if is_male else NPCData.NAMES_FEMALE
            name = random.choice(name_pool)
            while name in used_names: name = random.choice(name_pool) + str(i) # 避免重名
            used_names.add(name)
            
            arch_name, arch_desc, modifiers = random.choice(NPCData.ARCHETYPES)
            p = Person(name, "同学", [arch_name])
            
            # Apply modifiers
            for s in Subject.ALL:
                p.stats[s] *= modifiers.get("mastery", 1.0)
                p.stats[s] += random.randint(-200, 200)
            
            self.students.append(p)
            
        # 3. 生成老师
        for t_name, t_subj, t_desc in NPCData.TEACHERS:
            t = Person(t_name, "老师", [t_subj])
            t.stats[t_subj] = 10000 # 老师是满级大佬
            self.teachers.append(t)

    def tick_week(self):
        logs = []
        
        # 1. 众生演化
        for s in self.students:
            # 随机成长
            growth_subj = random.choice(Subject.ALL)
            growth = random.randint(10, 50)
            if "卷王" in s.tags: growth *= 1.5
            if "天赋怪" in s.tags and random.random() < 0.5: growth *= 2
            s.stats[growth_subj] += growth
            
            # 随机领悟技能
            if random.random() < 0.1:
                # Pick a random subject and level based on stats
                target_subj = random.choice(Subject.ALL)
                mastery = s.stats[target_subj]
                skill_data = SkillTree.get_skill_by_subject(target_subj, mastery)
                # skill_data is (name, level, desc)
                if skill_data and skill_data not in s.skills:
                    s.skills.append(skill_data)
                    if s == self.protagonist:
                        logs.append(f"【顿悟】{s.name}在{target_subj}课上领悟了「{skill_data[0]}」：{skill_data[2]}")

        # 2. 突发事件 (抽卡)
        for _ in range(3): # 每周发生3件大事
            evt = random.choice(self.event_pool)
            _, desc, effect = evt
            
            # 随机分配给某人
            target = random.choice(self.students)
            logs.append(f"【突发】{target.name}{desc}") # 简化日志，具体效果在内部应用
            
            if target == self.protagonist:
                self._apply_effect(self.protagonist, effect)

        return logs

    def _apply_effect(self, p, effect_str):
        # 解析 "mood+10, stress-5"
        parts = effect_str.split(",")
        for part in parts:
            part = part.strip()
            if "mood" in part:
                val = int(part.replace("mood", ""))
                p.mood += val
            elif "stress" in part:
                val = int(part.replace("stress", ""))
                p.stress += val
            elif "all_mastery" in part:
                val = int(part.replace("all_mastery", ""))
                for s in Subject.ALL: p.stats[s] += val
            # ... 其他属性解析

    def get_rankings(self):
        # 计算总分排名
        scores = [(s.name, sum([s.get_power(sub) for sub in Subject.ALL if sub != Subject.INFO])) for s in self.students]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def get_mc_report(self):
        p = self.protagonist
        ranks = self.get_rankings()
        my_rank = -1
        for i, (n, s) in enumerate(ranks):
            if n == p.name: my_rank = i + 1
        
        # 获取最近学会的技能
        recent_skill = p.skills[-1][0] if p.skills else "无"
        return f"叶凌天 | 排名:{my_rank}/{len(self.students)} | 最近技能:{recent_skill} | 标签:{','.join(p.tags)}"