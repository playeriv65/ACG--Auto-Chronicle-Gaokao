import random

class Subject:
    MATH = "数学"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    ENGLISH = "英语"
    CHINESE = "语文"
    BIOLOGY = "生物"

class SchoolVocabulary:
    def __init__(self):
        self.ranks = ["吊车尾", "学渣", "学民", "学霸", "学神", "考帝", "圣人"]
        
        self.skills = {
            Subject.MATH: ["洛必达法则", "泰勒展开式", "拉格朗日中值定理", "辅助线风暴", "导数大招", "立体几何降维打击"],
            Subject.PHYSICS: ["牛顿第三定律反冲", "洛伦兹力回旋", "动量守恒冲击", "薛定谔的猫视界", "热力学熵增诅咒"],
            Subject.CHEMISTRY: ["王水腐蚀", "氧化还原反应", "电子跃迁闪光", "苯环结界", "元素周期表镇压"],
            Subject.ENGLISH: ["从句嵌套迷宫", "完形填空预判", "听力透视", "3500词汇海", "语法分析眼"],
            Subject.CHINESE: ["古诗词具象化", "阅读理解读心术", "作文排比气场", "文言文时光回溯"],
            Subject.BIOLOGY: ["有丝分裂分身", "基因编辑重组", "光合作用充能", "神经递质加速"]
        }
        
        self.items = [
            "《五年高考三年模拟》(帝兵)", "《天利38套》(圣器)", "晨光孔庙祈福笔", "红牛(爆发药水)", 
            "风油精(清心丹)", "错题本(本命法宝)", "满分作文选(秘籍)", "计算器(外挂)"
        ]
        
        self.enemies = [
            "隔壁班班长", "年级主任(地中海强者)", "转校生(隐藏世家)", "早恋的校花", "监考老师(执法者)", 
            "最后的压轴题(魔兽)", "听力故障的录音机", "没涂完的答题卡"
        ]

    def get_skill(self, subject=None):
        if not subject:
            subject = random.choice(list(self.skills.keys()))
        return random.choice(self.skills[subject])

vocab = SchoolVocabulary()
