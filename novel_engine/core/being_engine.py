import random
import math
from novel_engine.data.database import SkillTree, EventLibrary, NPCData, Subject
from novel_engine.data.curriculum_data import Curriculum
from novel_engine.data.quiz_data import QuizDatabase

class Person:
    def __init__(self, name, role, tags, gender="男"):
        self.name, self.role, self.tags, self.gender = name, role, tags, gender
        self.family = random.choice(NPCData.FAMILIES)
        self.quirk = random.choice(NPCData.QUIRKS)
        self.flaw = random.choice(NPCData.FLAWS)
        
        if role == "主角":
            self.talent = {s: 100 for s in Subject.ALL}; self.talent[Subject.INFO] = 250
            self.mastery = {s: random.randint(100, 400) for s in Subject.ALL}; self.mastery[Subject.INFO] = 0
        else:
            if "天赋怪" in tags or "卷王" in tags:
                self.talent = {s: random.randint(120, 180) for s in Subject.ALL}
                self.mastery = {s: random.randint(2000, 3500) for s in Subject.ALL}
            else:
                self.talent = {s: random.randint(90, 130) for s in Subject.ALL}
                self.mastery = {s: random.randint(800, 1500) for s in Subject.ALL}
        
        self.last_mastery = self.mastery.copy()
        self.skills = []
        self.mood, self.stress, self.fatigue = 50, 0, 0
        self.focus_subject, self.last_week_rank = Subject.MATH, 0

    def to_dict(self):
        # 排除掉 Subject 这种非 JSON 序列化的对象，或者将其转换为字符串
        data = self.__dict__.copy()
        data['mastery'] = {str(k): v for k, v in self.mastery.items()}
        data['talent'] = {str(k): v for k, v in self.talent.items()}
        data['focus_subject'] = str(self.focus_subject)
        # last_mastery 也可以同样处理
        data['last_mastery'] = {str(k): v for k, v in self.last_mastery.items()}
        return data

    @staticmethod
    def from_dict(data):
        p = Person(data["name"], data["role"], data["tags"], data["gender"])
        # 这里需要将字符串形式的 key 还原为 Subject 枚举，或者直接用原始数据（如果逻辑兼容）
        # 为了稳定，我们直接覆盖属性
        for k, v in data.items():
            setattr(p, k, v)
        return p

    def get_exam_score(self, subject):
        base = self.mastery.get(subject, self.mastery.get(str(subject), 0))
        penalty = (self.stress + self.fatigue) / 400 
        talent_mod = self.talent.get(subject, self.talent.get(str(subject), 100)) / 100
        skill_bonus = sum([100 for n, lvl, d in self.skills if subject in n])
        score = (base + skill_bonus) * talent_mod * (1 - penalty)
        return int(min(150, score / 50))

    def plan_week(self, is_exam_coming, current_week=1, schedule_content=None):
        # (保持 Turn 25 的逻辑)
        if is_exam_coming:
            scores = {s: self.mastery.get(s, self.mastery.get(str(s), 0)) for s in Subject.ALL if s != Subject.INFO}
            self.focus_subject = min(scores, key=scores.get)
            self.stress += 15
        elif schedule_content:
            priority = [Subject.MATH, Subject.PHYS, Subject.CHEM, Subject.BIO, Subject.ENG, Subject.CHN]
            for s in priority:
                if s in schedule_content: self.focus_subject = s; break
        else:
            if current_week > 10 and "信奥党" in self.tags: self.focus_subject = Subject.INFO
            else: self.focus_subject = random.choice([s for s in Subject.ALL if s != Subject.INFO])

    def execute_week(self, current_week=1, schedule_content=None):
        self.last_mastery = self.mastery.copy()
        def calc_growth(subj):
            current = self.mastery.get(subj, self.mastery.get(str(subj), 0))
            base_growth = self.talent.get(subj, self.talent.get(str(subj), 100)) * 4
            inhibition = 1.0 / (math.log10(current + 10) / 2.0)
            growth = base_growth * inhibition
            if "卷王" in self.tags: growth *= 1.3
            if self.role == "主角" and subj == Subject.INFO: growth *= 2.0
            return growth
        g = calc_growth(self.focus_subject)
        self.mastery[self.focus_subject] = self.mastery.get(self.focus_subject, self.mastery.get(str(self.focus_subject), 0)) + g
        self.fatigue += 10
        for s in Subject.ALL:
            if s != self.focus_subject:
                self.mastery[s] = self.mastery.get(s, self.mastery.get(str(s), 0)) + calc_growth(s) * 0.2
        if self.fatigue > 90:
            self.fatigue = 40; self.mastery = {k:v*0.95 for k,v in self.mastery.items()}
            return f"{self.name}病倒了。"
        return f"{self.name}主修{self.focus_subject}。"

    def get_growth_report(self):
        return "Values Updated" # 简化版

    def get_soul_desc(self):
        return f"[{self.family}, {self.flaw}, 喜欢{self.quirk}]"

class BeingEngine:
    def __init__(self):
        self.students, self.teachers, self.protagonist = [], [], None
        self.rankings, self.global_cooldowns = [], {}
        self.year, self.semester = 1, 1
        self.init_world()
        self.event_pool = EventLibrary.EVENTS

    def to_dict(self):
        return {"students": [s.to_dict() for s in self.students], "teachers": [t.to_dict() for t in self.teachers], "global_cooldowns": self.global_cooldowns, "year": self.year, "semester": self.semester}

    def from_dict(self, data):
        self.students = [Person.from_dict(s) for s in data["students"]]
        self.teachers = [Person.from_dict(t) for t in data["teachers"]]
        self.protagonist = next((s for s in self.students if s.role == "主角"), self.students[0])
        self.global_cooldowns, self.year, self.semester = data["global_cooldowns"], data["year"], data["semester"]

    def init_world(self):
        self.protagonist = Person("叶凌天", "主角", ["做题家"], gender="男")
        self.students.append(self.protagonist)
        nemesis = Person("顾辞远", "同学", ["天赋怪", "卷王"], gender="男")
        nemesis.mastery = {s: 4000 for s in Subject.ALL}
        self.students.append(nemesis)
        used = {"叶凌天", "顾辞远"}
        for i in range(28):
            is_male = random.random() < 0.5
            name = random.choice(NPCData.SURNAMES) + random.choice(NPCData.STUDENT_NAMES_MALE if is_male else NPCData.STUDENT_NAMES_FEMALE)
            while name in used: name = random.choice(NPCData.SURNAMES) + random.choice(NPCData.STUDENT_NAMES_MALE if is_male else NPCData.STUDENT_NAMES_FEMALE)
            used.add(name)
            self.students.append(Person(name, "同学", [random.choice(NPCData.ARCHETYPES)[0]], gender=("男" if is_male else "女")))
        for subj, desc in NPCData.TEACHER_PROFILES:
            name = random.choice(NPCData.SURNAMES) + random.choice(NPCData.TEACHER_NAMES_MALE)
            self.teachers.append(Person(name + "老师", "老师", [subj]))

    def tick(self, week_idx):
        logs = []
        is_exam_week = (week_idx % 4 == 0)
        season = "SUMMER" if (week_idx % 20) < 10 else "WINTER"
        week_content = Curriculum.get_weekly_content(self.year, self.semester, week_idx)
        quiz_data = None
        if "ALL" in week_content:
            battle_type, battle_target = f"【{week_content['ALL']}】", "全科"
        else:
            boss_subj = next((s for s in [Subject.MATH, Subject.PHYS, Subject.CHEM] if s in week_content), Subject.MATH)
            topic = week_content.get(boss_subj, "自习")
            battle_type, battle_target = f"【周考·{boss_subj}：{topic}】", boss_subj
            quiz_data = QuizDatabase.get_quiz(boss_subj, topic)
        
        if week_idx == 11 and self.year == 1 and self.semester == 1:
            self.protagonist.tags.append("信奥党"); logs.append("开启信奥之路。")

        for s in self.students:
            s.plan_week(is_exam_week, current_week=week_idx, schedule_content=week_content)
            s.execute_week(current_week=week_idx, schedule_content=week_content)
            
        focus = random.sample(self.students, 3)
        if self.protagonist not in focus: focus[0] = self.protagonist
        for s in focus:
            desc, effect = self._select_valid_event(s, week_idx, season)
            self.global_cooldowns[desc] = week_idx
            self._apply_effect(s, effect)
            logs.append(f"【突发】{s.name}: {desc}")
            if random.random() < (0.4 if s.role == "主角" else 0.1):
                target_subj = random.choice(Subject.ALL)
                skill_data = SkillTree.get_skill_by_subject(target_subj, s.mastery.get(target_subj, 0))
                if skill_data and skill_data[0] not in [sk[0] for sk in s.skills]:
                    s.skills.append(skill_data); logs.append(f"【突破】{s.name}领悟绝学「{skill_data[0]}」")

        self.calculate_rankings()
        mc = self.protagonist
        mc_score = sum([mc.get_exam_score(s) for s in Subject.ALL if s != Subject.INFO]) if battle_target == "全科" else mc.get_exam_score(battle_target)
        rival = self.students[0] if self.students[0] != mc else self.students[1]
        rival_score = sum([rival.get_exam_score(s) for s in Subject.ALL if s != Subject.INFO]) if battle_target == "全科" else rival.get_exam_score(battle_target)
        logs.append(f"【战报】主角 {mc_score} vs 榜首({rival.name}) {rival_score}")
        for s in self.students: s.last_week_rank = self.students.index(s) + 1
        return logs, battle_type, quiz_data

    def _select_valid_event(self, person, week, season):
        candidates = [(d,e) for t,d,e in self.event_pool if (week - self.global_cooldowns.get(d,-99) >= 20) and (t in ["ANY", season])]
        return random.choice(candidates) if candidates else ("发呆", "")

    def calculate_rankings(self):
        self.students.sort(key=lambda s: sum([s.get_exam_score(sub) for sub in Subject.ALL if sub != Subject.INFO]), reverse=True)
        self.rankings = self.students

    def _apply_effect(self, p, effect):
        if not effect: return
        for part in effect.split(","):
            if "mood+" in part: p.mood += 10
            if "stress+" in part: p.stress += 10
            if "all_mastery+" in part: 
                for s in Subject.ALL: p.mastery[s] = p.mastery.get(s, 0) + 100

    def get_rankings(self):
        if not self.rankings: self.calculate_rankings()
        return self.rankings

    def get_student_detail(self, name):
        s = next((x for x in self.students if x.name == name), None)
        if not s: return ""
        skill_list = " | ".join([sk[0] for sk in s.skills]) if s.skills else "无"
        return f"{s.name}({s.gender}) | {s.get_soul_desc()} | 排名:{s.last_week_rank} | 修为:{int(sum([v for k,v in s.mastery.items() if isinstance(v, (int,float))]))} | 掌握技能:{skill_list}"