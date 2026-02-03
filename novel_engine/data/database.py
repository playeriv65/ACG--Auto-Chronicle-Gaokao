import sqlite3
import random
import os

DB_PATH = "novel_engine/data/storage/world_data.db"

class Subject:
    MATH, PHYS, CHEM, BIO, ENG, CHN, INFO, HIST, GEO, POLI = "数学", "物理", "化学", "生物", "英语", "语文", "信奥", "历史", "地理", "政治"
    ALL = [MATH, PHYS, CHEM, BIO, ENG, CHN, INFO, HIST, GEO, POLI]

class DBConnector:
    @staticmethod
    def get_connection():
        return sqlite3.connect(DB_PATH)

class SkillTree:
    @staticmethod
    def get_skill_by_subject(subject, mastery_val):
        conn = DBConnector.get_connection()
        cursor = conn.cursor()
        
        # Map subject names if necessary, or ensure DB matches
        # The DB was seeded with full Chinese names, so we can query directly
        query_subject = subject
        
        cursor.execute("SELECT name, level, description FROM skills WHERE subject = ? ORDER BY level", (query_subject,))
        skills = cursor.fetchall()
        conn.close()
        
        if not skills:
            return ("基础知识", 1, "平平无奇")
            
        # Mock logic: mastery 1000 = level 1, 2000 = level 2...
        idx = min(len(skills)-1, max(0, int(mastery_val // 1000) - 1))
        # Randomly choose a skill up to the current unlocked level
        # To make it more interesting, we can weight it towards higher level skills
        unlocked = skills[:idx+1]
        
        if not unlocked: return ("基础知识", 1, "平平无奇")
        
        choice = random.choice(unlocked)
        return choice # (name, level, desc)


def get_random_event(season="ANY"):
    conn = DBConnector.get_connection()
    cursor = conn.cursor()
    
    # Get ANY + Current Season
    cursor.execute("SELECT description, effect FROM events WHERE season = 'ANY' OR season = ?", (season,))
    events = cursor.fetchall()
    conn.close()
    
    if not events:
        return ("发呆", "")
        
    return random.choice(events) # (desc, effect)

class NPCData:
    # These are now dynamic
    
    # Cache for weighted names
    _SURNAMES_CACHE = None
    _SURNAMES_WEIGHTS = None

    @staticmethod
    def get_name(gender="M", era="00s"):
        conn = DBConnector.get_connection()
        cursor = conn.cursor()
        
        # 1. Get a Surname (Weighted)
        if NPCData._SURNAMES_CACHE is None:
            try:
                cursor.execute("SELECT name, frequency FROM surnames")
                rows = cursor.fetchall()
                if rows:
                    NPCData._SURNAMES_CACHE = [r[0] for r in rows]
                    NPCData._SURNAMES_WEIGHTS = [r[1] for r in rows]
                else:
                    # Fallback
                    NPCData._SURNAMES_CACHE = ["李", "王", "张"]
                    NPCData._SURNAMES_WEIGHTS = [1, 1, 1]
            except:
                 NPCData._SURNAMES_CACHE = ["李", "王", "张"]
                 NPCData._SURNAMES_WEIGHTS = [1, 1, 1]
        
        surname = random.choices(NPCData._SURNAMES_CACHE, weights=NPCData._SURNAMES_WEIGHTS, k=1)[0]
        
        # 2. Get a Given Name
        # Try to match era and gender
        cursor.execute("SELECT name FROM given_names WHERE gender = ? AND era = ? ORDER BY RANDOM() LIMIT 1", (gender, era))
        res = cursor.fetchone()
        
        if not res:
            # Fallback to any name of that gender
            cursor.execute("SELECT name FROM given_names WHERE gender = ? ORDER BY RANDOM() LIMIT 1", (gender,))
            res = cursor.fetchone()
            
        given_name = res[0] if res else ("强" if gender=="M" else "珍")
        
        conn.close()
        return surname + given_name

    # Static data that doesn't need DB yet (Archetypes, Teacher Profiles)
    ARCHETYPES = [("卷王", "肝帝", {"stress": 80}), ("天赋怪", "妖孽", {"stress": 10}), ("恋爱脑", "情种", {"mood": 90}), ("透明人", "凡人", {"stress": 40}), ("刺头", "叛逆", {"reputation": 20})]
    TEACHER_PROFILES = [("数学", "口头禅：送分题"), ("英语", "口头禅：最差一届"), ("语文", "口头禅：作者想表达什么"), ("物理", "口头禅：假设无摩擦"), ("化学", "口头禅：实验有微毒"), ("信奥", "口头禅：重启试试")]
    FAMILIES = ["书香门第", "暴发户", "单亲", "普通工薪", "农村", "高知"]
    QUIRKS = ["抖腿", "转笔", "咬指甲", "说话结巴", "爱照镜子", "二次元", "收集橡皮", "强迫症"]
    FLAWS = ["自卑", "傲慢", "社恐", "暴躁", "拖延症", "敏感", "虚荣"]