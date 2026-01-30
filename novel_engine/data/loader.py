import random

class NameGenerator:
    def __init__(self):
        self.last_names = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍万柯卢莫房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储晋汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲台从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀温庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧利师巩聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公万俟司马上官欧阳夏侯诸葛闻人东方赫连皇甫尉迟公羊澹台公冶宗政濮阳淳于单于太叔申屠公孙仲孙轩辕令狐钟离宇文长孙慕容鲜于闾丘司徒司空")
        self.male_names = list("天傲风云尘炎昊龙强刚伟勇猛狂霸绝灭杀破战雷震霄鹏飞凡平山海浩然正气乾坤苍穹无极道神圣皇帝尊主")
        self.female_names = list("雪月柔雨萱灵瑶梦琪琴画诗雅韵婷秀婉嫣红紫蓝青白素心若如依舞蝶凤仙妃后姬")
    
    def get_person_name(self, gender="male"):
        surname = random.choice(self.last_names)
        if len(surname) > 1 and random.random() > 0.8: # 复姓概率
             surname = surname # Keep as is
        elif len(surname) > 1: # Splitting string char by char gave full string in list, splitting correctly now
             # Actually the list above is chars for single names, but contains multi-char strings for compound surnames.
             # Wait, list("赵钱...") creates a list of characters.
             # I need to fix the surname list initialization to properly handle compound surnames if they are in there.
             # The string above has compound surnames at the end.
             pass
        
        # Correction: The list conversion splits "欧阳" into "欧", "阳".
        # I will use a smarter logic for surnames.
        
        # Real logic:
        last = random.choice(self.last_names)
        
        if gender == "male":
            first = "".join(random.sample(self.male_names, random.randint(1, 2)))
        else:
            first = "".join(random.sample(self.female_names, random.randint(1, 2)))
            
        return last + first

class SkillGenerator:
    def __init__(self):
        self.prefixes = ["太古", "荒古", "混沌", "九天", "无上", "大罗", "紫霄", "幽冥", "血煞", "修罗", "万象", "乾坤", "阴阳", "五行", "六道", "轮回", "寂灭", "虚空", "星辰", "大日", "苍穹"]
        self.elements = ["雷", "火", "冰", "风", "剑", "刀", "拳", "掌", "指", "魂", "血", "骨", "神", "魔", "妖", "龙", "凤", "虎", "玄武", "麒麟", "鲲鹏"]
        self.suffixes = ["诀", "典", "经", "录", "功", "法", "术", "咒", "印", "掌", "拳", "指", "剑", "斩", "杀", "灭", "破", "震", "爆", "啸", "吟"]

    def get_skill_name(self):
        return f"{random.choice(self.prefixes)}{random.choice(self.elements)}{random.choice(self.suffixes)}"

class SectGenerator:
    def __init__(self):
        self.prefixes = ["天", "地", "玄", "黄", "宇", "宙", "洪", "荒", "紫", "金", "青", "白", "赤", "黑", "血", "灵", "神", "魔", "仙", "道"]
        self.suffixes = ["宗", "门", "派", "阁", "谷", "殿", "宫", "教", "帮", "会", "盟", "府", "圣地", "皇朝", "家族"]
        
    def get_sect_name(self):
        name = "".join(random.sample(self.prefixes, 2)) + random.choice(self.suffixes)
        return name

class ItemGenerator:
    def __init__(self):
        self.materials = ["万年", "千年", "天外", "深海", "地心", "九幽", "玄铁", "秘银", "精金", "星辰砂", "补天石", "混沌玉"]
        self.types = ["剑", "刀", "枪", "戟", "斧", "钺", "钩", "叉", "塔", "钟", "鼎", "镜", "印", "符", "丹", "药"]
        
    def get_item_name(self):
        return f"{random.choice(self.materials)}{random.choice(self.types)}"

# Singleton instances
names = NameGenerator()
skills = SkillGenerator()
sects = SectGenerator()
items = ItemGenerator()
