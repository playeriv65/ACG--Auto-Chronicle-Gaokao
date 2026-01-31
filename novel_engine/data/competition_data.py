class CompSect:
    MATH = "数仙门"
    PHYS = "物炼宗"
    CHEM = "化毒教"
    BIO = "生灵谷"
    INFO = "寒克武(信奥魔教)"

class CompSkills:
    skills = {
        CompSect.MATH: ["欧拉通路", "群论结界", "拓扑折叠", "数论皇冠"],
        CompSect.PHYS: ["相对论力场", "量子隧穿", "光学迷彩", "超导爆发"],
        CompSect.CHEM: ["晶胞构建", "有机合成阵", "平衡常数逆转"],
        CompSect.BIO: ["PCR扩增", "基因测序眼", "生态位这一击"],
        CompSect.INFO: ["AC自动机", "线段树封锁", "动态规划(DP)预判", "网络流最大割", "暴力枚举破万法"]
    }
    
    stages = [
        "初赛(海选)", 
        "复赛(NOIP/分赛区)", 
        "省选(省队争夺战)", 
        "国决(NOI/CMO/CPhO)", 
        "集训队(国家队)", 
        "国际金牌(IOI/IMO - 飞升)"
    ]

    @staticmethod
    def get_skill(sect):
        import random
        return random.choice(CompSkills.skills.get(sect, ["基础内功"]))
