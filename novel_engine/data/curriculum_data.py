from novel_engine.data.database import Subject

class Curriculum:
    # 结构：Year -> Semester -> Week -> {Subject: Topic}
    
    SCHEDULE = {
        1: { # Year 1
            1: { # Semester 1
                1: {
                    Subject.MATH: "集合的概念与表示",
                    Subject.PHYS: "质点、参考系与时间",
                    Subject.CHEM: "物质的分类与转化",
                    Subject.BIO: "走近细胞",
                    Subject.CHN: "沁园春·长沙 (现代诗歌)",
                    Subject.ENG: "Welcome Unit: 词汇与自我介绍"
                },
                2: {
                    Subject.MATH: "集合的基本关系与运算",
                    Subject.PHYS: "位置变化与位移",
                    Subject.CHEM: "物质的量(摩尔质量)",
                    Subject.BIO: "细胞中的元素和化合物",
                    Subject.CHN: "红烛 / 立在地球边上放号",
                    Subject.ENG: "Unit 1: Teenage Life (Listening)"
                },
                3: {
                    Subject.MATH: "充分条件与必要条件",
                    Subject.PHYS: "速度与速率",
                    Subject.CHEM: "气体摩尔体积",
                    Subject.BIO: "生命活动的主要承担者——蛋白质",
                    Subject.CHN: "百合花 / 哦，香雪",
                    Subject.ENG: "Unit 1: Grammar (Noun Phrases)"
                },
                4: {
                    Subject.MATH: "一元二次函数与不等式",
                    Subject.PHYS: "速度变化快慢——加速度",
                    Subject.CHEM: "物质的量浓度及其配制",
                    Subject.BIO: "遗传信息的携带者——核酸",
                    Subject.CHN: "喜看稻菽千重浪",
                    Subject.ENG: "Unit 1: Reading & Writing"
                },
                5: {
                    Subject.MATH: "函数的概念与表示",
                    Subject.PHYS: "匀变速直线运动的规律",
                    Subject.CHEM: "电解质与离子反应",
                    Subject.BIO: "细胞中的糖类和脂质",
                    Subject.CHN: "芣苢 / 插秧歌 (诗经)",
                    Subject.ENG: "Unit 2: Travelling Around (Reading)"
                },
                6: {
                    Subject.MATH: "函数的单调性",
                    Subject.PHYS: "自由落体运动",
                    Subject.CHEM: "离子方程式的书写与正误判断",
                    Subject.BIO: "细胞膜的结构与功能",
                    Subject.CHN: "短歌行 / 归园田居",
                    Subject.ENG: "Unit 2: Grammar (Present Continuous)"
                },
                7: {
                    Subject.MATH: "函数的奇偶性",
                    Subject.PHYS: "伽利略对自由落体的研究",
                    Subject.CHEM: "氧化还原反应(电子转移)",
                    Subject.BIO: "细胞器——系统内的分工",
                    Subject.CHN: "梦游天姥吟留别 (李白)",
                    Subject.ENG: "Unit 2: Video & Writing"
                },
                8: {
                    Subject.MATH: "幂函数",
                    Subject.PHYS: "重力与弹力",
                    Subject.CHEM: "氧化剂与还原剂",
                    Subject.BIO: "细胞核——系统的控制中心",
                    Subject.CHN: "琵琶行 (白居易)",
                    Subject.ENG: "Unit 3: Sports and Fitness"
                },
                9: {
                    Subject.MATH: "指数与指数函数",
                    Subject.PHYS: "摩擦力(静摩擦/滑动摩擦)",
                    Subject.CHEM: "钠及其化合物",
                    Subject.BIO: "物质跨膜运输的实例",
                    Subject.CHN: "念奴娇·赤壁怀古 (苏轼)",
                    Subject.ENG: "Unit 3: Grammar (Adjectives)"
                },
                10: { 
                    "ALL": "期中综合大考",
                    "DESC": "检测前半学期函数与氧化还原的掌握情况"
                },
                11: {
                    Subject.MATH: "对数与对数函数",
                    Subject.PHYS: "力的合成",
                    Subject.CHEM: "氯气及其化合物",
                    Subject.BIO: "生物膜的流动镶嵌模型",
                    Subject.CHN: "永遇乐·京口北固亭怀古",
                    Subject.ENG: "Unit 4: Natural Disasters"
                },
                12: {
                    Subject.MATH: "函数的应用(零点/模型)",
                    Subject.PHYS: "力的分解",
                    Subject.CHEM: "铁及其化合物",
                    Subject.BIO: "物质跨膜运输的方式(主动/被动)",
                    Subject.CHN: "声声慢 (李清照)",
                    Subject.ENG: "Unit 4: Reading for Writing"
                },
                13: {
                    Subject.MATH: "任意角与弧度制",
                    Subject.PHYS: "共点力的平衡",
                    Subject.CHEM: "金属材料与合金",
                    Subject.BIO: "酶的作用与本质",
                    Subject.CHN: "劝学 (荀子)",
                    Subject.ENG: "Unit 5: Languages Around the World"
                },
                14: {
                    Subject.MATH: "三角函数的概念",
                    Subject.PHYS: "牛顿第一定律(惯性)",
                    Subject.CHEM: "物质的量在化学方程式计算中的应用",
                    Subject.BIO: "ATP的主要来源——细胞呼吸",
                    Subject.CHN: "师说 (韩愈)",
                    Subject.ENG: "Unit 5: Grammar (Relative Clauses)"
                },
                15: {
                    Subject.MATH: "诱导公式",
                    Subject.PHYS: "牛顿第二定律(实验探究)",
                    Subject.CHEM: "元素周期表初步",
                    Subject.BIO: "能量之源——光与光合作用",
                    Subject.CHN: "反对党八股 (毛泽东)",
                    Subject.ENG: "Workbook Exercise"
                },
                16: {
                    Subject.MATH: "正弦函数与余弦函数的图像",
                    Subject.PHYS: "牛顿第二定律的应用",
                    Subject.CHEM: "原子结构与核外电子排布",
                    Subject.BIO: "细胞的增殖(有丝分裂)",
                    Subject.CHN: "拿来主义 (鲁迅)",
                    Subject.ENG: "Review Unit 1-5"
                },
                17: {
                    Subject.MATH: "三角函数的性质(周期/振幅)",
                    Subject.PHYS: "力学单位制",
                    Subject.CHEM: "元素周期律",
                    Subject.BIO: "细胞的分化",
                    Subject.CHN: "故都的秋 (郁达夫)",
                    Subject.ENG: "Listening Comprehension Practice"
                },
                18: {
                    Subject.MATH: "三角恒等变换(两角和差)",
                    Subject.PHYS: "超重与失重",
                    Subject.CHEM: "化学键(离子键/共价键)",
                    Subject.BIO: "细胞的衰老和凋亡",
                    Subject.CHN: "荷塘月色 (朱自清)",
                    Subject.ENG: "Reading Comprehension Practice"
                },
                19: {
                    Subject.MATH: "三角函数综合应用",
                    Subject.PHYS: "牛顿运动定律综合应用",
                    Subject.CHEM: "必修一总复习",
                    Subject.BIO: "细胞的癌变",
                    Subject.CHN: "必修上册古诗文默写",
                    Subject.ENG: "Writing Practice (Essays)"
                },
                20: { 
                    "ALL": "期末终极审判",
                    "DESC": "决定寒假是否好过的战役"
                }
            },
            2: { # 高一下
                1: {Subject.MATH: "平面向量的概念", Subject.PHYS: "曲线运动", Subject.CHEM: "硫及其化合物", Subject.BIO: "遗传因子的发现", Subject.ENG: "Unit 1: Cultural Heritage"},
                20: {"ALL": "【期末分班考试】文理分科", "DESC": "命运的十字路口"}
            }
        }
    }

    @staticmethod
    def get_weekly_content(year, semester, week):
        term_schedule = Curriculum.SCHEDULE.get(year, {}).get(semester, {})
        week_content = term_schedule.get(week)
        
        if not week_content:
            return {"ALL": "自主复习", "DESC": "查漏补缺"}
            
        return week_content
