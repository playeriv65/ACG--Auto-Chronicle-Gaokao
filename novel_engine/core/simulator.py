import random
from novel_engine.core.sim_model import CharacterProfile, Subject, Trait, NPC, GAME_ITEMS

class SimulationEngine:
    def __init__(self):
        self.mc = CharacterProfile("叶凌天")
        self.mc.traits.append(Trait.GRINDER) # 初始性格：做题家
        
        # 初始化 NPC
        self.npcs = [
            NPC("林清北", "学神"),
            NPC("苏小狸", "偏科狂"),
            NPC("陈二狗", "女神") # 误，校花
        ]
        self.npcs[2].name = "沈幼楚"
        
        self.year = 1
        self.week = 1
        self.history = []
        
    def get_week_strategy(self):
        """AI根据当前状态决定本周策略"""
        # 简单AI：哪里不行补哪里
        scores = {s: self.mc.get_score(s) for s in Subject if s != Subject.INFO}
        min_subj = min(scores, key=scores.get)
        
        if self.mc.stress > 80: return "摆烂休息"
        if self.mc.mastery[Subject.INFO] > 2000 and self.year < 3: return "竞赛冲刺"
        if scores[min_subj] < 90: return f"恶补{min_subj.value}"
        return "均衡发展"

    def tick_week(self):
        strategy = self.get_week_strategy()
        log = []
        log.append(f"【周一】本周策略：{strategy}")
        
        # 模拟一周的效果
        if "摆烂" in strategy:
            self.mc.stress -= 30
            self.mc.mood += 20
            self.mc.fatigue -= 30
            log.append("这一周，主角彻底放飞自我，上课看小说，晚自习睡觉。")
            
        elif "竞赛" in strategy:
            self.mc.mastery[Subject.INFO] += self.mc.stats["LOG"] * 2
            self.mc.fatigue += 20
            # 偏科代价
            for s in Subject:
                if s != Subject.INFO: self.mc.mastery[s] -= 10
            log.append("主角把自己关在机房里，对着黑底白字的屏幕敲击着未来的音符。")
            
        elif "恶补" in strategy:
            target_subj_name = strategy.replace("恶补", "")
            target_s = next(s for s in Subject if s.value == target_subj_name)
            
            gain = self.mc.stats["IQ"] * 1.5
            if Trait.GENIUS in self.mc.traits: gain *= 1.5
            
            self.mc.mastery[target_s] += gain
            self.mc.stress += 15
            self.mc.fatigue += 15
            log.append(f"主角像疯了一样刷{target_subj_name}题，连上厕所都在背公式。")
            
        else: # 均衡
            for s in Subject:
                if s != Subject.INFO: self.mc.mastery[s] += self.mc.stats["IQ"] * 0.3
            self.mc.stress += 5
            log.append("按部就班的一周。刷题，听课，考试。")

        # 随机事件处理
        event_log = self._trigger_random_event()
        if event_log: log.append(event_log)
        
        # 属性边界检查
        self.mc.stress = max(0, min(100, self.mc.stress))
        self.mc.fatigue = max(0, min(100, self.mc.fatigue))
        self.mc.mood = max(0, min(100, self.mc.mood))
        
        # NPC 发展
        for npc in self.npcs:
            # 简单模拟 NPC 成长
            for s in Subject: npc.mastery[s] += npc.stats["IQ"] * 0.4
            
        return log

    def _trigger_random_event(self):
        roll = random.random()
        if roll < 0.1:
            self.mc.stress += 20
            return "【突发】被班主任叫去办公室喝茶，批评最近状态下滑。"
        elif roll < 0.2:
            self.mc.relations["沈幼楚"] = self.mc.relations.get("沈幼楚", {})
            self.mc.relations["沈幼楚"]["love"] = self.mc.relations["沈幼楚"].get("love", 0) + 10
            self.mc.mood += 30
            return "【桃花】做间操的时候，沈幼楚回头看了主角一眼，主角觉得整个世界都亮了。"
        elif roll < 0.3:
            self.mc.mastery[Subject.MATH] += 100
            return "【顿悟】在发呆时突然想通了困扰已久的解析几何压轴题。"
        return None

    def get_status_report(self):
        """生成详细的数值报告"""
        scores = {s.value: self.mc.get_score(s) for s in Subject if s != Subject.INFO}
        total = sum(scores.values())
        rank = 1
        # 简单排名模拟
        for npc in self.npcs:
            if npc.total_score() > total: rank += 1
            
        return f"总分:{int(total)} (班级第{rank}) | 心情:{int(self.mc.mood)} 压力:{int(self.mc.stress)} | 强科:{max(scores, key=scores.get)} 弱科:{min(scores, key=scores.get)}"

    def run_year(self):
        # 运行一年的模拟
        logs = []
        for w in range(1, 21): # 20 weeks per semester
            self.week = w
            week_logs = self.tick_week()
            
            # Month Exam
            if w % 4 == 0:
                report = self.get_status_report()
                week_logs.append(f"【月考总结】{report}")
                
            logs.append({
                "week": f"第{w}周",
                "events": week_logs,
                "status": self.get_status_report()
            })
        return logs
