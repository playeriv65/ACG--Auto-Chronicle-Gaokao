from __future__ import annotations

import json
import sqlite3

DB_PATH = "novel_engine/data/storage/world_data.db"


def seed() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS archetypes")
    cursor.execute(
        """
        CREATE TABLE archetypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            title TEXT,
            base_stats TEXT
        )
    """
    )
    archetypes = [
        # 学霸型
        ("卷王", "肝帝", json.dumps({"stress": 80})),
        ("天赋怪", "妖孽", json.dumps({"stress": 10})),
        ("学神", "大神", json.dumps({"reputation": 90})),
        ("学渣", "废物", json.dumps({"reputation": 20})),
        ("偏科怪才", "偏才", json.dumps({"reputation": 50, "mood": 60})),
        # 社交型
        ("现充", "开心果", json.dumps({"mood": 80})),
        ("社牛", "话痨", json.dumps({"mood": 70, "reputation": 70})),
        ("小透明", "凡人", json.dumps({"stress": 40})),
        ("八卦王", "包打听", json.dumps({"mood": 60, "reputation": 60})),
        ("和事佬", "和平者", json.dumps({"stress": 50, "reputation": 75})),
        # 特长型
        ("体育生", "运动健将", json.dumps({"mood": 80, "stress": 20})),
        ("艺术生", "文艺范", json.dumps({"mood": 75, "reputation": 85})),
        ("技术宅", "极客", json.dumps({"mood": 40, "reputation": 30})),
        ("文艺青年", "文青", json.dumps({"mood": 85, "reputation": 70})),
        # 性格型
        ("中二病", "中二期", json.dumps({"mood": 90, "reputation": 30})),
        ("毒舌", "嘴炮", json.dumps({"stress": 10, "reputation": 40})),
        ("温柔学姐", "姐姐", json.dumps({"mood": 80, "reputation": 85})),
        ("傲娇", "别扭", json.dumps({"stress": 60, "mood": 70})),
        ("腹黑", "笑面虎", json.dumps({"stress": 40, "reputation": 60})),
    ]
    cursor.executemany(
        "INSERT INTO archetypes (name, title, base_stats) VALUES (?, ?, ?)", archetypes
    )

    cursor.execute("DROP TABLE IF EXISTS teacher_profiles")
    cursor.execute(
        """
        CREATE TABLE teacher_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            catchphrase TEXT
        )
    """
    )
    teacher_profiles = [
        ("数学", "口头禅：送分题"),
        ("英语", "口头禅：最差一届"),
        ("语文", "口头禅：作者想表达什么"),
        ("物理", "口头禅：假设无摩擦"),
        ("化学", "口头禅：实验有微毒"),
        ("信奥", "口头禅：重启试试"),
    ]
    cursor.executemany(
        "INSERT INTO teacher_profiles (subject, catchphrase) VALUES (?, ?)",
        teacher_profiles,
    )

    cursor.execute("DROP TABLE IF EXISTS families")
    cursor.execute(
        "CREATE TABLE families (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    families = [
        ("书香门第",),
        ("暴发户",),
        ("单亲",),
        ("普通工薪",),
        ("农村",),
        ("高知",),
        ("军官",),
        ("医生",),
        ("商人",),
        ("离异",),
        ("低保",),
        ("华侨",),
        ("个体户",),
        ("工人",),
        ("公务员",),
    ]
    cursor.executemany("INSERT INTO families (name) VALUES (?)", families)

    cursor.execute("DROP TABLE IF EXISTS quirks")
    cursor.execute(
        "CREATE TABLE quirks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    quirks = [
        ("抖腿",),
        ("转笔",),
        ("咬指甲",),
        ("爱照镜子",),
        ("二次元",),
        ("收集橡皮",),
        ("强迫症",),
        ("洁癖",),
        ("路痴",),
        ("脸盲",),
        ("话痨",),
        ("结巴",),
        ("口头禅",),
        ("哼歌",),
        ("转头发",),
        ("抠手",),
        ("自言自语",),
        ("记仇",),
        ("社恐",),
        ("拖延症",),
    ]
    cursor.executemany("INSERT INTO quirks (name) VALUES (?)", quirks)

    cursor.execute("DROP TABLE IF EXISTS flaws")
    cursor.execute(
        "CREATE TABLE flaws (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    flaws = [
        ("自卑",),
        ("傲慢",),
        ("社恐",),
        ("暴躁",),
        ("敏感",),
        ("虚荣",),
        ("玻璃心",),
        ("控制欲",),
        ("依赖症",),
        ("完美主义",),
        ("优柔寡断",),
        ("冲动",),
        ("嫉妒",),
        ("消极",),
        ("固执",),
    ]
    cursor.executemany("INSERT INTO flaws (name) VALUES (?)", flaws)

    cursor.execute("DROP TABLE IF EXISTS interests")
    cursor.execute(
        "CREATE TABLE interests (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    interests = [
        ("篮球",),
        ("足球",),
        ("跑步",),
        ("健身",),
        ("音乐",),
        ("绘画",),
        ("书法",),
        ("阅读",),
        ("写作",),
        ("编程",),
        ("游戏",),
        ("动漫",),
        ("手工",),
        ("摄影",),
        ("烹饪",),
        ("旅行",),
        ("唱歌",),
        ("跳舞",),
        ("乐器",),
        ("电影",),
    ]
    cursor.executemany("INSERT INTO interests (name) VALUES (?)", interests)

    cursor.execute("DROP TABLE IF EXISTS specialties")
    cursor.execute(
        "CREATE TABLE specialties (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    specialties = [
        ("数学竞赛",),
        ("物理竞赛",),
        ("信息学奥赛",),
        ("作文比赛",),
        ("英语演讲",),
        ("科技创新",),
        ("体育特长",),
        ("艺术特长",),
        ("组织能力",),
        ("领导力",),
    ]
    cursor.executemany("INSERT INTO specialties (name) VALUES (?)", specialties)

    cursor.execute("DROP TABLE IF EXISTS values_system")
    cursor.execute(
        "CREATE TABLE values_system (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    values_system = [
        ("成绩至上",),
        ("友情第一",),
        ("享受当下",),
        ("追求卓越",),
        ("平淡是真",),
        ("叛逆自由",),
        ("家庭责任",),
        ("理想主义",),
    ]
    cursor.executemany("INSERT INTO values_system (name) VALUES (?)", values_system)

    conn.commit()
    conn.close()
    print("✅ NPC metadata seeded successfully into world_data.db")


if __name__ == "__main__":
    seed()
