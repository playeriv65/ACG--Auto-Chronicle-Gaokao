
import sqlite3
import os

DB_PATH = "novel_engine/data/storage/world_data.db"

def seed_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Existing database removed.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 姓氏表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS surnames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        frequency INTEGER DEFAULT 1
    )
    """)
    
    # 2. 名字表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS given_names (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        gender TEXT, -- 'M' or 'F'
        era TEXT,    -- '70s' (Teacher), '00s' (Student)
        UNIQUE(name, gender, era)
    )
    """)
    
    # 3. 技能表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        name TEXT,
        level INTEGER,
        description TEXT,
        UNIQUE(subject, name)
    )
    """)

    # 4. 事件表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season TEXT,
        description TEXT UNIQUE,
        effect TEXT
    )
    """)
    
    # --- Data Injection ---
    
    # Surnames (Common Surnames + Common Compound Surnames)
    # Removing obscure cultivation surnames to keep it realistic
    surnames = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍万柯卢莫房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储晋汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲台从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀温庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧利师巩聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公") + ["欧阳", "上官", "司马", "诸葛", "夏侯", "皇甫", "尉迟", "端木", "公孙", "慕容", "宇文", "长孙"]
    
    print(f"Injecting {len(surnames)} surnames...")
    for s in surnames:
        if s.strip():
            cursor.execute("INSERT OR IGNORE INTO surnames (name) VALUES (?)", (s.strip(),))
            
    # Given Names (70s vs 00s)
    names_70s_m = ["建国", "建军", "志强", "志刚", "志伟", "国庆", "军", "勇", "强", "亮", "伟", "刚", "平", "兵", "雷"]
    names_70s_f = ["秀英", "玉兰", "丽华", "艳华", "敏华", "桂芬", "红霞", "秀芬", "玉珍", "招娣", "英", "丽", "梅", "燕", "红"]
    
    names_00s_m = ["浩宇", "宇轩", "浩然", "子轩", "皓轩", "宇航", "梓豪", "子豪", "亦辰", "奕辰", "俊杰", "鑫", "杰", "涛", "磊", "帅"]
    names_00s_f = ["欣怡", "梓涵", "诗涵", "梓宣", "子涵", "紫涵", "佳怡", "雨涵", "雨欣", "一诺", "梦琪", "婷", "静", "悦", "雪", "颖"]
    
    all_names = []
    for n in names_70s_m: all_names.append((n, 'M', '70s'))
    for n in names_70s_f: all_names.append((n, 'F', '70s'))
    for n in names_00s_m: all_names.append((n, 'M', '00s'))
    for n in names_00s_f: all_names.append((n, 'F', '00s'))
    
    print(f"Injecting {len(all_names)} given names...")
    cursor.executemany("INSERT OR IGNORE INTO given_names (name, gender, era) VALUES (?, ?, ?)", all_names)

    # Skills from old database.py (Manual Extraction)
    skill_data = [
        ("数学", "集合的概念与表示", 1, "展开‘全集领域’..."), ("数学", "函数的概念与性质", 2, "解析敌人漏洞..."), ("数学", "指数与对数函数", 3, "战力瞬间翻倍..."), ("数学", "三角恒等变换", 4, "诱导公式迷宫..."), ("数学", "平面向量", 5, "线性打击..."), ("数学", "数列与数学归纳法", 6, "等比数列陷阱..."), ("数学", "立体几何", 7, "降维打击..."), ("数学", "解析几何", 8, "离心率锁定..."), ("数学", "导数及其应用", 9, "切线风暴..."), ("数学", "概率与统计", 10, "大数定律锁定..."),
        ("物理", "运动的描述", 1, "参考系预判..."), ("物理", "牛顿运动定律", 2, "反伤甲..."), ("物理", "圆周运动", 3, "向心力牵引..."), ("物理", "万有引力与航天", 4, "第一宇宙速度..."), ("物理", "机械能守恒", 5, "势能转动能..."), ("物理", "动量守恒", 6, "碰撞冲击..."), ("物理", "静电场", 7, "库仑力场..."), ("物理", "磁场与洛伦兹力", 8, "回旋加速器..."), ("物理", "电磁感应", 9, "楞次定律..."), ("物理", "波粒二象性", 10, "薛定谔的猫..."),
        ("化学", "物质的量", 1, "摩尔诅咒..."), ("化学", "氧化还原反应", 2, "强氧化剂..."), ("化学", "元素周期律", 3, "位构性统一..."), ("化学", "化学反应速率", 4, "催化剂爆发..."), ("化学", "化学平衡", 5, "勒夏特列原理..."), ("化学", "电解质溶液", 6, "盐类水解..."), ("化学", "有机烃类", 7, "苯环结界..."), ("化学", "烃的衍生物", 8, "银镜反应..."), ("化学", "合成高分子", 9, "聚合反应..."), ("化学", "物质结构与性质", 10, "杂化轨道..."),
        ("生物", "细胞的结构", 1, "细胞膜过滤..."), ("生物", "细胞呼吸", 2, "线粒体过载..."), ("生物", "光合作用", 3, "灵感制造..."), ("生物", "有丝分裂", 4, "分身答题..."), ("生物", "遗传规律", 5, "孟德尔神算..."), ("生物", "基因的表达", 6, "中心法则..."), ("生物", "变异与进化", 7, "抗题性进化..."), ("生物", "内环境稳态", 8, "激素调节..."), ("生物", "神经调节", 9, "反射弧归零..."), ("生物", "生态系统", 10, "食物链顶端..."),
        ("信奥", "C++语言基础", 1, "编译永不报错..."), ("信奥", "基础算法", 2, "二分查找..."), ("信奥", "数据结构", 3, "单调队列..."), ("信奥", "搜索", 4, "剪枝神术..."), ("信奥", "动态规划", 5, "状态转移..."), ("信奥", "图论", 6, "Dijkstra寻路..."), ("信奥", "树形结构", 7, "Lazy标记..."), ("信奥", "数论", 8, "扩展欧几里得..."), ("信奥", "字符串", 9, "AC自动机..."), ("信奥", "计算几何", 10, "最大流最小割..."),
        ("语文", "现代文阅读", 2, "共情能力..."), ("语文", "文言文实词", 4, "通假字识破..."), ("语文", "古诗词默写", 6, "意象具象化..."), ("语文", "作文立意", 8, "凤头猪肚豹尾..."),
        ("英语", "3500词汇", 2, "词根分析眼..."), ("英语", "语法从句", 4, "从句套娃..."), ("英语", "完形填空", 6, "语感预判..."), ("英语", "书面表达", 8, "衡水体书法...")
    ]
    print(f"Injecting {len(skill_data)} skills...")
    cursor.executemany("INSERT OR IGNORE INTO skills (subject, name, level, description) VALUES (?, ?, ?, ?)", skill_data)

    # Events from old database.py
    events_data = [
        ("ANY", "宿舍夜聊聊到了未来，大家都沉默了。", "mood-5"), ("ANY", "舍友打呼噜像电钻，你盯着天花板到天亮。", "fatigue+20, stress+10"),
        ("ANY", "偷偷在宿舍煮火锅，香味引来了宿管阿姨。", "stress+20"), ("ANY", "发现晾在阳台的内裤被风吹到了楼下树上。", "mood-10"),
        ("ANY", "全宿舍合资买了个二手小冰箱，快乐似神仙。", "mood+10"), ("ANY", "因为谁去倒垃圾的问题，和室友爆发冷战。", "mood-10"),
        ("ANY", "半夜有人说梦话，大喊‘这题选C！’。", "mood+5"), ("WINTER", "宿舍暖气坏了，大家裹着棉被瑟瑟发抖。", "fatigue+10"),
        ("SUMMER", "宿舍不仅没空调连风扇都坏了，热成狗。", "fatigue+15"), ("ANY", "隔壁宿舍传来吉他声，唱着跑调的《成都》。", "mood+5"),
        ("ANY", "在床板下发现了上一届学长留下的刻字：‘快逃！’。", "stress+5"), ("ANY", "熄灯后偷偷玩手机，屏幕光亮瞎了眼。", "fatigue+10"),
        ("ANY", "早上起床抢厕所，上演生死时速。", "stress+5"), ("ANY", "周末赖床直到下午两点，早饭午饭一起吃。", "fatigue-20"),
        ("ANY", "突击检查违禁电器，你的热得快藏在了鞋盒里。", "stress+15"), ("ANY", "食堂推出新品‘辣椒炒月饼’，勇士们跃跃欲试。", "mood+5"),
        ("ANY", "在免费汤里捞出了一整只完整的鸡头，吓尿。", "stress+10"), ("ANY", "排了半天队，轮到你时阿姨刚好把红烧肉抖没了。", "mood-20"),
        ("ANY", "食堂电视正在放NBA总决赛，男生们围得水泄不通。", "mood+10"), ("ANY", "米饭里吃出了一颗钢丝球，阿姨赔了你个鸡腿。", "mood+5"),
        ("ANY", "因为插队问题，高三学长和高一新生打起来了。", "stress+5"), ("ANY", "食堂涨价了，肉包子从1块涨到了1块5。", "mood-5"),
        ("ANY", "发现食堂角落坐着校花，这顿饭吃得格外香。", "mood+10"), ("ANY", "带了老干妈去食堂，成为了全桌的救世主。", "reputation+5"),
        ("ANY", "暴饮暴食庆祝考试结束，结果拉肚子。", "fatigue+10"), ("ANY", "粉笔头精准命中了你的额头，全班哄堂大笑。", "reputation-5"),
        ("ANY", "晚自习停电！全班欢呼3秒后被班主任镇压。", "mood+5"), ("ANY", "后座的同学一直抖腿，连带着你的桌子都在共振。", "stress+10"),
        ("ANY", "黑板还没擦干就写字，反光完全看不清。", "stress+5"), ("ANY", "体育课被数学老师占了，理由是体育老师‘落枕’。", "mood-20, math+5"),
        ("ANY", "英语听力全是杂音，像是在听外星语。", "stress+10"), ("ANY", "同桌借你的笔记去复印，结果把你夹在里面的情书弄丢了。", "mood-30"),
        ("ANY", "被老师点名回答问题，全班死寂，你尴尬站立。", "stress+10"), ("ANY", "换了座位，新同桌是个超级学霸，压力山大。", "stress+15, all_mastery+10"),
        ("ANY", "换了座位，新同桌是个话痨，你的学习效率直线下降。", "all_mastery-10"), ("ANY", "在课桌抽屉深处摸到一块干硬的口香糖。", "mood-5"),
        ("ANY", "做课间操时转体运动，看到暗恋的人也在看你。", "mood+20"), ("ANY", "眼保健操时间，大家都在偷偷睁眼比谁的白眼翻得大。", "mood+5"),
        ("ANY", "班主任站在后门窗户口，死亡凝视长达5分钟。", "stress+30"), ("ANY", "发下来的试卷印反了，做题节奏大乱。", "stress+10"),
        ("ANY", "自动铅笔芯断在了一道几何题的辅助线上，弄脏了卷面。", "stress+5"), ("ANY", "为了解一道压轴题，不知不觉用完了一整本草稿纸。", "all_mastery+20"),
        ("ANY", "早读声音太小，被罚站到走廊去读。", "reputation-5"), ("ANY", "历史老师讲野史讲得太精彩，全班没人想下课。", "mood+10"),
        ("ANY", "物理实验课，把电路接短路了，冒出一股黑烟。", "reputation+5"), ("ANY", "化学实验课，不小心把试管摔碎了，赔了5块钱。", "mood-5"),
        ("HIGH_STRESS", "看着窗外的飞鸟，突然很想变成一只鸟飞走。", "mood-10"), ("HIGH_STRESS", "因为一道题算不出来，趴在桌子上无声地哭了。", "stress-10"),
        ("LOW_SCORE", "被叫去办公室喝茶，班主任进行了长达1小时的心理按摩。", "stress+20"), ("LOW_SCORE", "父母承诺考进前十名就奖励最新款手机。", "stress+10"),
        ("ANY", "收到了匿名的小纸条，上面写着‘加油’。", "mood+20"), ("ANY", "目睹了楼道里的情侣吵架，觉得单身真好。", "mood+5"),
        ("ANY", "好朋友突然不理你了，你完全不知道做错了什么。", "stress+10"), ("ANY", "帮别人递情书被老师截获，成了背锅侠。", "reputation-10"),
        ("ANY", "全班起哄撮合某两个人，当事人满脸通红。", "mood+5"), ("ANY", "在操场散步，听到有人在背单词，顿时感到内卷的恐怖。", "stress+5"),
        ("ANY", "愚人节，班长骗大家说今天放假，差点被打死。", "mood+10"), ("ANY", "元旦晚会，平时沉默寡言的同学上去跳了段街舞，炸场。", "mood+10"),
        ("ANY", "运动会，班级接力赛掉棒了，大家都很沮丧。", "mood-10"), ("ANY", "运动会，本来没希望的项目拿了第一，全班沸腾。", "mood+20"),
        ("ANY", "隔壁班女生来借书，全班男生行注目礼。", "mood+5"), ("ANY", "有人在厕所抽烟被抓，全校通报批评。", "stress+5"),
        ("HIGH_RELATION", "生病请假，同桌帮你记了满满几页的笔记。", "mood+30"), ("HIGH_RELATION", "周末约了同学去书店，结果最后变成了去网吧。", "fatigue+10"),
        ("ANY", "毕业班在喊楼，漫天飞舞的试卷像雪花一样。", "stress+10"), ("WINTER", "第一场雪，大家疯了一样冲出教室打雪仗。", "mood+20"),
        ("WINTER", "流感肆虐，班里空了一半座位，你也觉得喉咙痛。", "fatigue+15"), ("WINTER", "手冻僵了，写字像鸡爪，完全不在状态。", "all_mastery-5"),
        ("SUMMER", "知了叫得人心烦意乱，完全看不进书。", "stress+5"), ("SUMMER", "教室里弥漫着汗味和风油精混合的味道。", "stress+5"),
        ("SUMMER", "一场暴雨，操场变成了‘拮抗海’，大家都在看海。", "mood+10"), ("SUMMER", "蚊子在耳边嗡嗡作响，打死一只带血的。", "mood-2"),
        ("ANY", "高考倒计时牌变成了两位数，气氛骤然紧张。", "stress+20"), ("ANY", "体检，大家都在比谁的身高又长了。", "mood+5"),
        ("ANY", "拍证件照，摄影师把你拍成了通缉犯。", "mood-5"), ("ANY", "学校修路，挖掘机一整天都在‘突突突’。", "stress+10"),
        ("ANY", "小卖部倒闭了，全校陷入恐慌。", "mood-10"), ("ANY", "由于台风过境，学校宣布停课半天！", "mood+50"),
        ("ANY", "消防演习，大家慢悠悠地散步到操场。", "fatigue-5"), ("ANY", "全校停水，厕所的味道令人窒息。", "stress+10")
    ]
    print(f"Injecting {len(events_data)} events...")
    cursor.executemany("INSERT OR IGNORE INTO events (season, description, effect) VALUES (?, ?, ?)", events_data)

    conn.commit()
    conn.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed_db()
