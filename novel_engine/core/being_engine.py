import random
import math
import sqlite3
import re
import os
from novel_engine.data.database import SkillTree, get_random_event, NPCData, Subject
from novel_engine.data.curriculum_data import Curriculum
from novel_engine.data.quiz_data import QuizDatabase

import ast

class Person:
    def __init__(self, name, role, tags, gender="男"):
        self.name, self.role, self.tags, self.gender = name, role, tags, gender
        self.family = random.choice(NPCData.FAMILIES)
        self.quirk = random.choice(NPCData.QUIRKS)
        self.flaw = random.choice(NPCData.FLAWS)
        if role == "主角":
            self.talent = {s: 100 for s in Subject.ALL}; self.talent[Subject.INFO] = 300
            self.mastery = {s: random.randint(100, 400) for s in Subject.ALL}; self.mastery[Subject.INFO] = 0
        else:
            is_elite = any(t in ["天赋怪", "卷王"] for t in tags)
            self.talent = {s: random.randint(120, 180) if is_elite else random.randint(90, 130) for s in Subject.ALL}
            self.mastery = {s: random.randint(2500, 4000) if is_elite else random.randint(800, 1500) for s in Subject.ALL}
        self.last_mastery = self.mastery.copy(); self.skills = []
        self.mood, self.stress, self.fatigue = 50, 0, 0
        self.focus_subjects, self.last_week_rank = [], 0

    def to_dict(self):
        d = self.__dict__.copy()
        d['mastery'] = {str(k): v for k, v in self.mastery.items()}
        d['talent'] = {str(k): v for k, v in self.talent.items()}
        d['last_mastery'] = {str(k): v for k, v in self.last_mastery.items()}
        d['focus_subjects'] = [str(s) for s in self.focus_subjects]
        return d

    @staticmethod
    def from_dict(data):
        p = Person(data["name"], data["role"], data["tags"], data["gender"])
        for k, v in data.items(): setattr(p, k, v)
        return p

    def get_exam_score(self, subject):
        m_key = subject if subject in self.mastery else str(subject)
        base = self.mastery.get(m_key, 0)
        penalty = (self.stress + self.fatigue) / 500
        t_key = subject if subject in self.talent else str(subject)
        talent_mod = self.talent.get(t_key, 100) / 100
        skill_bonus = sum([100 for n, lvl, d in self.skills if subject in n])
        score = (base + skill_bonus) * talent_mod * (1 - penalty)
        return int(min(150, score / 50))

    def plan_week(self, is_exam_week, current_week, battle_subjects):
        if battle_subjects and battle_subjects != "全科":
            self.focus_subjects = battle_subjects
        else:
            def get_m(s): return self.mastery.get(s, self.mastery.get(str(s), 0))
            scores = {s: get_m(s) for s in Subject.ALL if s != Subject.INFO}
            self.focus_subjects = [min(scores, key=scores.get)]
        if is_exam_week: self.stress += 15
        if current_week > 10 and "信奥党" in self.tags and not is_exam_week:
            if random.random() < 0.5: self.focus_subjects = [Subject.INFO]

    def execute_week(self):
        self.last_mastery = self.mastery.copy()
        def calc_growth(subj):
            m_key = subj if subj in self.mastery else str(subj)
            current = self.mastery.get(m_key, 0)
            inhibition = 1.0 / (math.log10(current + 10) / 2.0)
            t_key = subj if subj in self.talent else str(subj)
            growth = self.talent.get(t_key, 100) * 5 * inhibition
            if "卷王" in self.tags: growth *= 1.3
            if self.role == "主角" and subj == Subject.INFO: growth *= 2.5
            return growth
        for s in self.focus_subjects:
            m_key = s if s in self.mastery else str(s)
            self.mastery[m_key] = self.mastery.get(m_key, 0) + calc_growth(s)
            self.fatigue += 5
        for s in Subject.ALL:
            if s not in self.focus_subjects:
                m_key = s if s in self.mastery else str(s)
                self.mastery[m_key] = self.mastery.get(m_key, 0) + calc_growth(s) * 0.2
        if self.fatigue > 90:
            self.fatigue = 40
            for k in self.mastery: self.mastery[k] *= 0.95
            return "病倒"
        return "苦修"

    def get_soul_desc(self):
        return f"[{self.family}, {self.flaw}, 喜欢{self.quirk}]"

class BeingEngine:
    def __init__(self):
        self.db_path = "background/curriculum.db"
        self.students, self.teachers, self.protagonist, self.rankings = [], [], None, []
        self.global_cooldowns, self.year, self.semester = {}, 1, 1
        self.last_battle_subjects = []
        self.init_world()

    def to_dict(self):
        return {"students": [s.to_dict() for s in self.students], "teachers": [t.to_dict() for t in self.teachers], "global_cooldowns": self.global_cooldowns, "year": self.year, "semester": self.semester, "last_battle_subjects": [str(s) for s in self.last_battle_subjects]}

    def from_dict(self, data):
        self.students = [Person.from_dict(s) for s in data["students"]]
        self.teachers = [Person.from_dict(t) for t in data["teachers"]]
        self.protagonist = next((s for s in self.students if s.role == "主角"), self.students[0])
        self.global_cooldowns, self.year, self.semester = data["global_cooldowns"], data["year"], data["semester"]
        self.last_battle_subjects = data.get("last_battle_subjects", [])

    def init_from_settings(self, settings_data):
        self.students = []
        self.teachers = []
        
        char_list = settings_data.get("characters", [])
        if not char_list:
            self.init_world()
            return
            
        print(f" [Engine] Initializing from settings ({len(char_list)} students)...")
        
        # Recreate students from settings
        for c in char_list:
            name = c["name"]
            gender = c["gender"]
            tags = ast.literal_eval(c["tags"])
            
            # Determine role/archetype from name or tags
            # In generate_full_plan, we saved protagonist as "叶凌天"
            role = "主角" if name == "叶凌天" else "同学" # Hardcoded for now, or could inferred
            
            p = Person(name, role, tags, gender=gender)
            
            # Parse background string to restore quirks/flaws if possible
            # Format: "[Family, Flaw, 喜欢Quirk]"
            bg = c["background"]
            if bg.startswith("[") and bg.endswith("]"):
                parts = [x.strip() for x in bg[1:-1].split(",")]
                if len(parts) >= 3:
                    p.family = parts[0]
                    p.flaw = parts[1]
                    # "喜欢Quirk" -> "Quirk"
                    p.quirk = parts[2].replace("喜欢", "")
            
            self.students.append(p)
            
        self.protagonist = next((s for s in self.students if s.role == "主角"), self.students[0])
        
        # Init teachers (standard)
        for subj, desc in NPCData.TEACHER_PROFILES:
             is_male_teacher = random.random() < 0.5
             t_name = NPCData.get_name("M" if is_male_teacher else "F", "70s")
             self.teachers.append(Person(t_name + "老师", "老师", [subj]))

    def init_world(self):
        self.protagonist = Person("叶凌天", "主角", ["做题家"], gender="男"); self.students.append(self.protagonist)
        nemesis = Person("顾辞远", "同学", ["天赋怪", "卷王"], gender="男"); nemesis.mastery = {s: 4000 for s in Subject.ALL}; self.students.append(nemesis)
        used = {"叶凌天", "顾辞远"}
        for i in range(28):
            is_male = random.random() < 0.5; gender = "男" if is_male else "女"
            # 使用新接口生成 00后 学生名字
            name = NPCData.get_name("M" if is_male else "F", "00s")
            while name in used: 
                name = NPCData.get_name("M" if is_male else "F", "00s")
            used.add(name); self.students.append(Person(name, "同学", [random.choice(NPCData.ARCHETYPES)[0]], gender=gender))
        for subj, desc in NPCData.TEACHER_PROFILES:
            # 使用新接口生成 70后 老师名字
            # 简单假设老师性别根据科目随机，或者这里可以随机
            is_male_teacher = random.random() < 0.5
            name = NPCData.get_name("M" if is_male_teacher else "F", "70s")
            self.teachers.append(Person(name + "老师", "老师", [subj]))

    def tick(self, week_idx):
        abs_week = (self.year - 1) * 40 + (self.semester - 1) * 20 + week_idx
        curriculum = self._get_curriculum_from_db(abs_week)
        logs = []; is_exam_week = (week_idx % 4 == 0); season = "SUMMER" if (week_idx % 20) < 10 else "WINTER"
        
        if is_exam_week: battle_type, battle_subjects = "【全科月考】", "全科"
        else:
            if self.year == 1:
                candidates = [Subject.MATH, Subject.PHYS, Subject.CHEM, Subject.BIO, Subject.ENG, Subject.CHN]
                candidates = [c for c in candidates if str(c) not in self.last_battle_subjects]
                battle_subjects = [random.choice(candidates)]
            elif self.year == 2: battle_subjects = [Subject.PHYS, Subject.CHEM, Subject.BIO]
            else: battle_subjects = [Subject.MATH, Subject.PHYS, Subject.CHEM, Subject.BIO, Subject.ENG, Subject.CHN]
            self.last_battle_subjects = [str(s) for s in battle_subjects]
            battle_type = f"【周考·{'/'.join([str(s) for s in battle_subjects])}】"

        if abs_week == 11 and self.year == 1: self.protagonist.tags.append("信奥党"); logs.append("开启信奥。")

        # 冲突判定 (道心抉择)
        if "信奥党" in self.protagonist.tags and random.random() < 0.15:
            conflict_log = self._resolve_conflict(battle_type, "信奥集训")
            logs.append(conflict_log)

        for s in self.students: s.plan_week(is_exam_week, abs_week, battle_subjects); s.execute_week()
            
        focus = random.sample(self.students, 3)
        if self.protagonist not in focus: focus[0] = self.protagonist
        for s in focus:
            desc, effect = get_random_event(season)
            self.global_cooldowns[desc] = abs_week; self._apply_effect(s, effect); logs.append(f"【突发】{s.name}: {desc}")
            if random.random() < (0.4 if s.role == "主角" else 0.1):
                target_subj = random.choice(Subject.ALL); mastery_val = s.mastery.get(target_subj, s.mastery.get(str(target_subj), 0))
                skill_data = SkillTree.get_skill_by_subject(target_subj, mastery_val)
                if skill_data and skill_data[0] not in [sk[0] for sk in s.skills]:
                    s.skills.append(skill_data); logs.append(f"【突破】{s.name}领悟绝学「{skill_data[0]}」")

        self.calculate_rankings(); mc = self.protagonist
        if battle_subjects == "全科":
            subs = [Subject.MATH, Subject.PHYS, Subject.CHEM, Subject.BIO, Subject.ENG, Subject.CHN]
            mc_score = sum([mc.get_exam_score(s) for s in subs])
            rival_score = sum([self.students[0].get_exam_score(s) for s in subs])
        else:
            mc_score = sum([mc.get_exam_score(s) for s in battle_subjects])
            rival_score = sum([self.students[0].get_exam_score(s) for s in battle_subjects])
        
        # 战斗描述生成 (考场厮杀)
        battle_log = self._battle_narrative(mc, self.rankings[0], battle_type, mc_score, rival_score)
        logs.append(battle_log)

        for s in self.students: s.last_week_rank = self.students.index(s) + 1
        
        quiz_data = None
        if not is_exam_week and self.year == 1:
            quiz_data = QuizDatabase.get_quiz(battle_subjects[0], curriculum.get(battle_subjects[0], "复习") if curriculum else "复习")
            
        return logs, battle_type, quiz_data

    def _resolve_conflict(self, main, sub):
        choices = [
            f"放弃{main}复习，潜入机房备战{sub}。林清北嘲笑主角是逃兵。",
            f"一边应付{main}，一边在草稿纸上推导{sub}算法。双线操作，神魂枯竭。",
            f"在{main}的考场上，把作文写成了代码，震惊阅卷长老。"
        ]
        return f"【道心抉择】{random.choice(choices)}"
    
    def _battle_narrative(self, mc, rival, event, mc_score, rival_score):
        diff = mc_score - rival_score
        scenes = [
            "监考老师祭出‘信号屏蔽仪’，全场灵气被封印。",
            "压轴导数题化作一条恶龙，盘踞在卷面上。",
            "听力广播里传来了魔音贯耳的英语听力，试图扰乱道心。",
            "隔壁班学霸开启了‘抖腿光环’，引发地震波攻击。",
            f"{rival.name}眼神冰冷，随手丢出一招‘洛必达法则’。"
        ]
        
        if diff > 10: 
            res = f"{mc.name}使用了‘{(mc.skills[-1][0] if mc.skills else '基础解题法')}’，提前交卷，留下一个孤傲的背影。"
        elif diff > -20:
            res = f"{mc.name}与{rival.name}在分数线上反复拉锯，最终险胜/惜败。"
        else:
            res = f"{mc.name}被压轴题镇压，道心破碎，看着{rival.name}绝尘而去。"
            
        return f"【战报】{random.choice(scenes)} {res} (我方战力:{mc_score} vs 榜首:{rival_score})"

    def calculate_rankings(self):
        def total_score(s): return sum([s.get_exam_score(sub) for sub in [Subject.MATH, Subject.PHYS, Subject.CHEM, Subject.BIO, Subject.ENG, Subject.CHN]])
        self.students.sort(key=total_score, reverse=True); self.rankings = self.students

    def get_rankings(self):
        if not self.rankings: self.calculate_rankings()
        return self.rankings

    def get_mc_report(self):
        p = self.protagonist; ranks = self.get_rankings(); my_rank = -1
        for i, s in enumerate(ranks):
            if s.name == p.name: my_rank = i + 1
        skill = p.skills[-1][0] if p.skills else '无'
        return f"排名:{my_rank} | 技能:{skill} | 压力:{p.stress}"

    def get_student_detail(self, name):
        s = next((x for x in self.students if x.name == name), None)
        if not s: return ""
        skill_list = " | ".join([sk[0] for sk in s.skills]) if s.skills else "无"
        sum_val = sum([v for v in s.mastery.values() if isinstance(v, (int,float))])
        return f"{s.name}({s.gender}) | {s.get_soul_desc()} | 排名:{s.last_week_rank} | 修为:{int(sum_val)} | 技能:{skill_list}"

    def _get_curriculum_from_db(self, abs_week):
        if not os.path.exists(self.db_path): return None
        try:
            conn = sqlite3.connect(self.db_path); cursor = conn.cursor()
            cursor.execute("SELECT * FROM curriculum WHERE week = ?", (abs_week,))
            row = cursor.fetchone(); conn.close()
            if row:
                res = {Subject.CHN: row[1], Subject.MATH: row[2], Subject.ENG: row[3], Subject.PHYS: row[4], Subject.CHEM: row[5], Subject.BIO: row[6], Subject.HIST: row[7], Subject.GEO: row[8], Subject.POLI: row[9]}
                for k, v in res.items(): res[k] = re.sub(r'!\[.*?\]\(.*?\)', '', str(v))
                return res
        except: return None

    def _apply_effect(self, p, effect):
        if not effect: return
        for part in effect.split(","):
            if "mood+" in part: p.mood += 10
            if "stress+" in part: p.stress += 10
            if "all_mastery+" in part: 
                for s in Subject.ALL:
                    key = str(s); p.mastery[key] = p.mastery.get(key, 0) + 100