import random
from enum import Enum

class EventType(Enum):
    NORMAL_STUDY = "日常刷题"
    WEEKLY_TEST = "周测切磋"
    MONTHLY_EXAM = "月考大战"
    MID_TERM = "期中战役"
    FINAL_EXAM = "期末决战"
    GAOKAO = "高考飞升" # The End
    VACATION = "寒暑假闭关"
    SPECIAL = "突发事件" # 家长会、运动会

class SchoolCalendar:
    def __init__(self):
        self.year = 1
        self.semester = 1 # 1 or 2
        self.week = 1
        self.max_weeks = 20
        self.total_chapters = 0
        self.is_graduated = False
        
    def advance_week(self):
        event = self._get_event_type()
        
        # Increment time
        self.week += 1
        if self.week > self.max_weeks:
            self._end_semester()
            
        return event, self._get_date_string()

    def _get_date_string(self):
        grade = ["高一", "高二", "高三"][self.year - 1]
        sem = "上学期" if self.semester == 1 else "下学期"
        return f"{grade}{sem} 第{self.week}周"

    def _end_semester(self):
        self.week = 1
        if self.semester == 1:
            self.semester = 2
        else:
            self.semester = 1
            self.year += 1
            if self.year > 3:
                self.is_graduated = True

    def _get_event_type(self):
        if self.is_graduated:
            return EventType.GAOKAO
            
        if self.year == 3 and self.semester == 2 and self.week >= 18:
            return EventType.GAOKAO # 高三最后时刻

        if self.week in [10]: return EventType.MID_TERM
        if self.week in [20]: return EventType.FINAL_EXAM
        if self.week in [4, 8, 12, 16]: return EventType.MONTHLY_EXAM
        
        # Random special events
        if random.random() < 0.1: return EventType.SPECIAL
        
        # Default flow
        if random.random() < 0.5: return EventType.WEEKLY_TEST
        return EventType.NORMAL_STUDY

class StudentStatus:
    def __init__(self):
        self.rank_score = 100 # Initial combat power
        self.sanity = 100 # HP
        self.fatigue = 0
        self.buffs = []
        
    def update(self, event_type):
        if event_type == EventType.NORMAL_STUDY:
            self.rank_score += random.randint(1, 5)
            self.fatigue += 5
        elif event_type in [EventType.MONTHLY_EXAM, EventType.MID_TERM, EventType.FINAL_EXAM]:
            # Big gains or losses
            change = random.randint(10, 50)
            self.rank_score += change
            self.sanity -= 10
            return f"名次上升{random.randint(1, 20)}名"
        return "平稳度过"

    def get_title(self):
        if self.rank_score < 200: return "吊车尾"
        if self.rank_score < 500: return "学民"
        if self.rank_score < 800: return "学霸"
        if self.rank_score < 1500: return "学神"
        return "考帝"
