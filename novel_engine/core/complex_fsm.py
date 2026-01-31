import random
from enum import Enum
from novel_engine.data.competition_data import CompSect, CompSkills

class GameState(Enum):
    NORMAL = "日常修行"
    EXAM_PREP = "闭关备考"
    EXAM_COMBAT = "月考大战"
    COMP_TRAINING = "竞赛特训"
    COMP_BATTLE = "竞赛决战"
    SLUMP = "走火入魔" # 成绩下滑/心态崩了
    HOLIDAY = "云游修整"

class StudentProfile:
    def __init__(self):
        self.gaokao_score = 450 # 基础分
        self.comp_score = 0 # 竞赛积分
        self.sanity = 100
        self.energy = 100
        self.reputation = 50 # 老师好感度
        self.comp_sect = CompSect.INFO # 默认加入寒克武（最惨的）
        self.comp_rank = 0 # 0:无, 1:省一, 2:国决, 3:集训队, 4:金牌
        self.buffs = []

class DualFSM:
    def __init__(self):
        self.year = 1
        self.semester = 1
        self.week = 1
        self.max_weeks = 20
        self.state = GameState.NORMAL
        self.profile = StudentProfile()
        self.history_log = []
        
        # Timeline Triggers
        self.comp_start_week = (1, 1, 11) # Y1 S1 W11 (Mid-term after)
        self.comp_end_week = (3, 1, 15)   # Y3 S1 W15 (End of road)

    def is_comp_active(self):
        # 简单的周数转换逻辑
        current_abs_week = (self.year - 1) * 40 + (self.semester - 1) * 20 + self.week
        start_abs = (self.comp_start_week[0] - 1) * 40 + (self.comp_start_week[1] - 1) * 20 + self.comp_start_week[2]
        end_abs = (self.comp_end_week[0] - 1) * 40 + (self.comp_end_week[1] - 1) * 20 + self.comp_end_week[2]
        
        # 只有在 active 期间，且没有保送/退役才算
        return start_abs <= current_abs_week <= end_abs and self.profile.comp_rank < 4

    def tick(self):
        # 1. 状态重置
        self.profile.energy = 100
        event_desc = ""
        conflict = False
        
        # 2. 时间推进逻辑
        date_str = f"高{self.year}{'上' if self.semester==1 else '下'} 第{self.week}周"
        
        # 3. 强制事件检测 (Main Thread)
        main_event = self._check_main_events()
        
        # 4. 竞赛事件检测 (Sub Thread)
        sub_event = None
        if self.is_comp_active():
            sub_event = self._check_comp_events()

        # 5. 状态机决策 (Decision Making)
        if main_event and sub_event:
            # 冲突！修罗场！
            self.state = GameState.COMP_BATTLE
            conflict = True
            event_desc = self._resolve_conflict(main_event, sub_event)
        elif main_event:
            self.state = GameState.EXAM_COMBAT if "考" in main_event else GameState.NORMAL
            event_desc = self._handle_main(main_event)
        elif sub_event:
            self.state = GameState.COMP_BATTLE if "赛" in sub_event else GameState.COMP_TRAINING
            event_desc = self._handle_sub(sub_event)
        else:
            # 无特殊事件，根据策略日常挂机
            event_desc = self._daily_grind()

        # 6. 结算属性
        self._update_stats()
        
        # 7. 记录
        log_entry = {
            "date": date_str,
            "state": self.state.value,
            "event": event_desc,
            "stats": f"高考力:{self.profile.gaokao_score} | 竞赛力:{self.profile.comp_score} | 理智:{self.profile.sanity} | 老师好感:{self.profile.reputation}"
        }
        self.history_log.append(log_entry)
        
        # 8. 推进时间
        self.week += 1
        if self.week > self.max_weeks:
            self._end_semester()

    def _end_semester(self):
        self.week = 1
        if self.semester == 1:
            self.semester = 2
            self.history_log.append({"date": "寒假", "state": "HOLIDAY", "event": "寒假闭关，在被窝里偷偷刷题。", "stats": "-"})
        else:
            self.semester = 1
            self.year += 1
            self.history_log.append({"date": "暑假", "state": "HOLIDAY", "event": "暑假特训营，前往省城受虐。", "stats": "-"})

    # --- Event Checkers ---

    def _check_main_events(self):
        if self.week == 10: return "期中大劫"
        if self.week == 20: return "期末天罚"
        if self.week in [4, 8, 12, 16]: return "月考切磋"
        if self.year == 3 and self.semester == 2 and self.week == 18: return "高考飞升"
        return None

    def _check_comp_events(self):
        # 设定每年的赛季节奏
        if self.semester == 1:
            if self.week == 12: return "NOIP初赛(海选)"
            if self.week == 18: return "NOIP复赛(分赛区)"
        if self.semester == 2:
            if self.week == 8: return "省选(省队战)"
            if self.week == 15 and self.profile.comp_rank >= 1: return "NOI国决(决赛)"
        
        # 随机集训
        if random.random() < 0.15: return "机房集训"
        return None

    # --- Handlers ---

    def _resolve_conflict(self, main, sub):
        # 经典剧情：为了竞赛放弃月考，被老师骂
        self.profile.reputation -= 20
        self.profile.gaokao_score -= 10
        self.profile.comp_score += 50
        return f"【冲突爆发】{main}与{sub}撞车！主角毅然选择了‘寒克武’，逃掉晚自习去机房参赛。教导主任暴怒，在窗外死亡凝视。"

    def _handle_main(self, event):
        if "考" in event:
            outcome = "发挥稳定"
            if self.profile.sanity < 50:
                outcome = "心态炸裂，发挥失常"
                self.profile.gaokao_score -= 20
            else:
                self.profile.gaokao_score += 10
            return f"【正道试炼】{event}降临。主角{outcome}。全校排名波动。"
        return "ERROR"

    def _handle_sub(self, event):
        skill = CompSkills.get_skill(self.profile.comp_sect)
        if "赛" in event:
            # 比赛逻辑
            success_prob = 0.1 + (self.profile.comp_score / 1000)
            if random.random() < success_prob:
                self.profile.comp_rank += 1
                self.profile.reputation += 30 # 拿到奖老师就高兴了
                return f"【旁门左道】{event}。主角祭出绝学‘{skill}’，AC了压轴题，成功晋级！全校通报表扬！"
            else:
                self.profile.sanity -= 20
                self.profile.reputation -= 10
                return f"【旁门左道】{event}。主角在‘{skill}’上失误（爆零），惨遭淘汰。被正道老师嘲讽：‘早说了搞竞赛没前途’。"
        else:
            # 训练逻辑
            self.profile.comp_score += 20
            self.profile.gaokao_score -= 5 # 偏科
            return f"【魔教潜修】{event}。主角在机房通宵刷题，领悟了‘{skill}’。文化课作业没写完，被罚站。"

    def _daily_grind(self):
        # 只有在非特殊事件时，根据理智决定策略
        if self.is_comp_active():
            # 偷偷搞竞赛
            self.profile.comp_score += 5
            self.profile.energy -= 40
            return "日常：表面复习文化课，书底下压着一本《算法导论》。"
        else:
            self.profile.gaokao_score += 5
            return "日常：枯燥的刷题岁月。五三，王后雄，天利38套。"

    def _update_stats(self):
        # 自然恢复与消耗
        if self.profile.reputation < 20:
            self.state = GameState.SLUMP
            self.profile.sanity -= 5
        
        # 随着年级升高，难度增加
        self.profile.sanity += 5 # 周末回血
        if self.profile.sanity > 100: self.profile.sanity = 100
