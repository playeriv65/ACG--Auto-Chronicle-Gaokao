import random
from enum import Enum

class State(Enum):
    NORMAL = "游历"
    HUNTED = "被追杀"
    DUNGEON = "秘境探险"
    RETREAT = "闭关修炼"
    TOURNAMENT = "宗门大比"
    RECOVERY = "重伤疗愈"

class ArcType(Enum):
    REVENGE = "复仇" # 杀了小的来老的
    TREASURE = "怀璧其罪" # 拿到宝物被盯上
    RIVAL = "宿敌" # 长期竞争对手

class PlotEngine:
    def __init__(self, world):
        self.world = world
        self.state = State.NORMAL
        self.active_arcs = [] # 存储待处理的剧情线 [{"type": ArcType.REVENGE, "enemy": "赵长老", "countdown": 3}]
        self.tension = 0 # 0-100, 越高越容易触发高潮
        
    def update(self):
        """每章开始前调用，决定本章的剧情走向"""
        mc = self.world.protagonist
        
        # 1. 强制状态检查
        if mc.current_hp < mc.max_hp * 0.3:
            self.state = State.RECOVERY
            return self._generate_recovery_plot()
            
        # 2. 处理剧情线 (Tick down)
        triggered_arc = None
        for arc in self.active_arcs:
            arc["countdown"] -= 1
            if arc["countdown"] <= 0:
                triggered_arc = arc
                self.active_arcs.remove(arc)
                break
        
        if triggered_arc:
            return self._trigger_arc(triggered_arc)

        # 3. 基于当前状态的状态转移
        if self.state == State.NORMAL:
            # 游历状态下，根据张力决定
            if self.tension > 80:
                # 强制触发大事件释放张力
                self.tension = 0
                return self._trigger_climax()
            else:
                roll = random.random()
                if roll < 0.3: return self._trigger_combat()
                elif roll < 0.5: return self._enter_dungeon()
                elif roll < 0.7: return self._enter_tournament()
                else: return self._trigger_adventure() # 捡漏/拍卖

        elif self.state == State.HUNTED:
            # 被追杀状态，要么反杀（解除状态），要么继续逃
            if random.random() < 0.4:
                return self._resolve_hunt() # 反杀
            else:
                return self._continue_escape()

        elif self.state == State.DUNGEON:
            # 副本连载中
            if random.random() < 0.3:
                self.state = State.NORMAL # 副本结束
                return self._finish_dungeon()
            else:
                return self._continue_dungeon()
                
        # Fallback
        self.state = State.NORMAL
        return self._trigger_adventure()

    # --- Plot Generators ---

    def _trigger_combat(self):
        from novel_engine.core.world import Character
        enemy = Character()
        enemy.level_idx = self.world.protagonist.level_idx
        
        # 埋下伏笔：杀了这个，产生仇恨链
        self.active_arcs.append({
            "type": ArcType.REVENGE,
            "enemy": f"{enemy.sect}的长老",
            "countdown": random.randint(2, 5) # 2-5章后找上门
        })
        self.tension += 20
        return f"主角偶遇{enemy.name}（{enemy.sect}），对方见财起意。战斗爆发。主角将其斩杀，但发现对方身上有宗门令牌，暗道不妙。"

    def _trigger_arc(self, arc):
        self.state = State.HUNTED
        self.tension += 50
        return f"【剧情爆发】之前的因果报应来了！{arc['enemy']}根据气息追踪到了主角。主角陷入绝境，被迫开启逃亡模式。"

    def _trigger_climax(self):
        self.state = State.NORMAL
        return f"【高潮】多方势力汇聚，争夺即将出世的仙帝遗迹。主角在混乱中火中取栗，坑杀了所有对手，震惊天下！"

    def _enter_dungeon(self):
        self.state = State.DUNGEON
        self.tension += 10
        return f"主角发现了一处上古秘境的入口。为了变强，毅然进入。秘境内部危机四伏，机关重重。"

    def _continue_dungeon(self):
        self.tension += 15
        return f"（秘境中）主角深入秘境核心，遇到了一头守护神兽。经过一番苦战，主角利用地形优势获胜。"

    def _finish_dungeon(self):
        self.tension -= 30
        rewards = "上古丹方"
        self.world.protagonist.inventory.append(rewards)
        return f"（秘境终章）主角终于抵达终点，获得了{rewards}。随着秘境崩塌，主角利用传送阵惊险逃脱。"

    def _generate_recovery_plot(self):
        heal = int(self.world.protagonist.max_hp * 0.5)
        self.world.protagonist.current_hp += heal
        self.state = State.NORMAL # 恢复后回归正常
        self.tension -= 20
        return f"主角身受重伤，躲入一个隐蔽的山洞疗伤。回顾之前的战斗，总结得失。服下丹药，伤势恢复了五成。"

    def _continue_escape(self):
        self.tension += 10
        self.world.protagonist.current_hp -= 10 # 逃跑消耗
        return f"追兵越来越近。主角利用阵法设置陷阱，暂时阻挡了敌人，继续向万兽山脉深处逃窜。"

    def _resolve_hunt(self):
        self.state = State.NORMAL
        self.tension = 0
        self.active_arcs.append({"type": ArcType.TREASURE, "enemy": "路过的元婴老怪", "countdown": 10})
        return f"主角逃无可逃，决定背水一战。利用地形反杀了追兵首领。虽然胜利，但因为动静太大，引来了更强者的窥探（伏笔）。"

    def _enter_tournament(self):
        self.state = State.TOURNAMENT
        return f"恰逢{self.world.protagonist.sect}举办大比。主角决定参赛，检验自己的修行成果，并打脸那些曾经看不起他的人。"

    def _trigger_adventure(self):
        self.tension += 5
        return f"主角在坊间闲逛，捡漏买到了一个看起来破旧但内蕴灵气的神秘铁片。系统提示这是神器碎片。"

