import random
from enum import Enum

class Subject(Enum):
    CHINESE = "语文"
    MATH = "数学"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEM = "化学"
    BIO = "生物"
    INFO = "信奥" # 隐藏学科

class Trait(Enum):
    GENIUS = "天赋异禀" # 学习效率+50%
    PROCRASTINATOR = "拖延症" # 心情高时效率高，低时摆烂
    NIGHT_OWL = "夜猫子" # 晚上效率高，白天犯困
    LOVER = "恋爱脑" # 容易受异性影响
    GRINDER = "做题家" # 只要练不死，就往死里练

class CharacterProfile:
    def __init__(self, name):
        self.name = name
        # 六维属性
        self.stats = {
            "IQ": random.randint(80, 130), # 智商
            "EQ": random.randint(80, 120), # 情商
            "PHY": random.randint(60, 100), # 体魄
            "MEM": random.randint(70, 120), # 记忆力
            "LOG": random.randint(70, 120), # 逻辑
            "IMG": random.randint(60, 110)  # 想象力
        }
        
        # 学科熟练度 (Max 10000)
        self.mastery = {s: random.randint(1000, 3000) for s in Subject}
        # 学科上限 (由天赋决定)
        self.potential = {s: self.stats["IQ"] * 50 + random.randint(0, 2000) for s in Subject}
        self.potential[Subject.INFO] = self.stats["LOG"] * 80 # 特殊计算
        
        # 实时状态
        self.stress = 0 # 压力 (0-100)
        self.fatigue = 0 # 疲劳 (0-100)
        self.mood = 50 # 心情 (0-100)
        
        self.traits = []
        self.inventory = []
        self.buffs = {} # "Coffee": 3 turns
        
        # 人际关系 {NPC_NAME: {friend: 0, rival: 0, love: 0}}
        self.relations = {}

    def get_score(self, subject):
        """根据熟练度、状态、随机波动计算卷面分"""
        base = min(150, self.mastery[subject] / 50) # 假设5000熟练度=100分
        if subject in [Subject.PHYSICS, Subject.CHEM, Subject.BIO]:
            base = min(100, self.mastery[subject] / 50)
            
        # 状态修正
        mood_factor = 1 + (self.mood - 50) / 500 # +/- 10%
        fatigue_penalty = max(0, (self.fatigue - 70) / 100) # 疲劳>70开始扣分
        
        final = base * mood_factor * (1 - fatigue_penalty)
        return int(final)

    def total_score(self):
        return sum([self.get_score(s) for s in Subject if s != Subject.INFO])

class NPC(CharacterProfile):
    def __init__(self, name, archetype):
        super().__init__(name)
        self.archetype = archetype
        if archetype == "学神":
            self.stats["IQ"] = 145
            self.mastery = {s: 6000 for s in Subject}
            self.traits.append(Trait.GENIUS)
        elif archetype == "女神":
            self.stats["EQ"] = 140
            self.traits.append(Trait.LOVER)
        elif archetype == "偏科狂":
            self.stats["LOG"] = 140
            self.mastery[Subject.MATH] = 7000
            self.mastery[Subject.ENGLISH] = 1000

class Item:
    def __init__(self, name, effect_desc, cost):
        self.name = name
        self.effect = effect_desc
        self.cost = cost # 精力消耗或金钱

GAME_ITEMS = [
    Item("红牛", "疲劳-20, 压力+5", 0),
    Item("五三题库", "全科熟练度+50, 压力+10", 10),
    Item("某人纸条", "心情+30, 熟练度-10", 0),
    Item("手机", "心情+50, 疲劳+20, 熟练度-50", 0)
]
