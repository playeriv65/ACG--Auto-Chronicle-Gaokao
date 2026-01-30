import random

# 硬性配置
TARGET_CHARS = 1000000 
OUTPUT_FILE = "generated_novel.txt"

# 爽文核心要素库
PROTAGONIST = "叶凌天"
LOCATIONS = ["青云镇", "天星城", "大夏皇都", "上界仙域", "混沌神界", "虚空战场"]
ENEMIES = ["赵强", "林枫", "苏辰", "王腾", "幽冥老祖", "血煞魔尊", "九天神皇"]
SYSTEM_MSGS = ["叮！经验+999", "叮！恭喜宿主获得神级功法", "叮！检测到敌人产生恐惧，装逼值+1000"]
REACTIONS = ["全场死寂！", "众人倒吸一口凉气！", "此子竟然恐怖如斯！", "长老们惊得站了起来！", "这绝对不可能！"]
MOVES = ["碎星掌", "九龙拉棺", "万剑归宗", "寂灭指", "混沌拳"]

class NovelEngine:
    def __init__(self):
        self.chars_count = 0
        self.chapter_idx = 1
        self.current_loc = LOCATIONS[0]

    def build_scene(self):
        enemy = random.choice(ENEMIES)
        move = random.choice(MOVES)
        reaction = random.choice(REACTIONS)
        msg = random.choice(SYSTEM_MSGS)
        
        scene = [
            f"那{enemy}踏前一步，神色狰狞：“{PROTAGONIST}，今日便是你的死期！”",
            f"{PROTAGONIST}淡然一笑，眼底尽是冷漠，“蝼蚁，也敢撼天？”",
            f"话音未落，他猛然挥手，口中轻喝：“{move}！”",
            f"刹那间，风云变色，大地颤抖，一股毁灭性的气息席卷全场。",
            f"{reaction}",
            f"“不！”{enemy}发出一声惨叫，在众目睽睽之下直接化作了飞灰。",
            f"【{msg}】",
            f"周围的人群颤抖着，看向{PROTAGONIST}的眼神中充满了敬畏与恐惧。"
        ]
        return "\n".join(scene)

    def generate(self):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"《无敌从系统开始》\n作者：AI文豪\n\n")
            
            while self.chars_count < TARGET_CHARS:
                title = f"第{self.chapter_idx}章 {random.choice(MOVES)}，震惊全场！\n"
                chapter_content = [title]
                
                # 地图切换
                if self.chapter_idx % 100 == 0:
                    self.current_loc = random.choice(LOCATIONS)
                    chapter_content.append(f"转眼间，{PROTAGONIST}已经来到了{self.current_loc}。这里的规则更加残酷，但他丝毫不惧。\n")

                # 重复构建战斗与对话（爽文精髓：水字数）
                for _ in range(5):
                    chapter_content.append(self.build_scene())
                
                # 典型的凑字数段落
                filler = (f"修行的世界就是这样，弱肉强食。{PROTAGONIST}深知这一点，所以他必须变强，变得比任何人都要强。系统是他的底气，也是他的骄傲。 " * 3)
                chapter_content.append("\n" + filler + "\n")

                full_chapter = "\n".join(chapter_content) + "\n\n"
                f.write(full_chapter)
                
                self.chars_count += len(full_chapter)
                self.chapter_idx += 1
                
                if self.chapter_idx % 500 == 0:
                    print(f"进度：已生成 {self.chars_count} 字...")

if __name__ == "__main__":
    engine = NovelEngine()
    engine.generate()
    print(f"生成完毕！总字数：{engine.chars_count}，文件名：{OUTPUT_FILE}")
