import sqlite3
import json
import os

DB_PATH = "novel_engine/data/storage/world_data.db"

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Archetypes
    cursor.execute("DROP TABLE IF EXISTS archetypes")
    cursor.execute("""
        CREATE TABLE archetypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            title TEXT,
            base_stats TEXT
        )
    """)
    archetypes = [
        ("卷王", "肝帝", json.dumps({"stress": 80})),
        ("天赋怪", "妖孽", json.dumps({"stress": 10})),
        ("恋爱脑", "情种", json.dumps({"mood": 90})),
        ("透明人", "凡人", json.dumps({"stress": 40})),
        ("刺头", "叛逆", json.dumps({"reputation": 20}))
    ]
    cursor.executemany("INSERT INTO archetypes (name, title, base_stats) VALUES (?, ?, ?)", archetypes)

    # 2. Teacher Profiles
    cursor.execute("DROP TABLE IF EXISTS teacher_profiles")
    cursor.execute("""
        CREATE TABLE teacher_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            catchphrase TEXT
        )
    """)
    teacher_profiles = [
        ("数学", "口头禅：送分题"),
        ("英语", "口头禅：最差一届"),
        ("语文", "口头禅：作者想表达什么"),
        ("物理", "口头禅：假设无摩擦"),
        ("化学", "口头禅：实验有微毒"),
        ("信奥", "口头禅：重启试试")
    ]
    cursor.executemany("INSERT INTO teacher_profiles (subject, catchphrase) VALUES (?, ?)", teacher_profiles)

    # 3. Families
    cursor.execute("DROP TABLE IF EXISTS families")
    cursor.execute("CREATE TABLE families (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    families = [("书香门第",), ("暴发户",), ("单亲",), ("普通工薪",), ("农村",), ("高知",)]
    cursor.executemany("INSERT INTO families (name) VALUES (?)", families)

    # 4. Quirks
    cursor.execute("DROP TABLE IF EXISTS quirks")
    cursor.execute("CREATE TABLE quirks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    quirks = [("抖腿",), ("转笔",), ("咬指甲",), ("说话结巴",), ("爱照镜子",), ("二次元",), ("收集橡皮",), ("强迫症",)]
    cursor.executemany("INSERT INTO quirks (name) VALUES (?)", quirks)

    # 5. Flaws
    cursor.execute("DROP TABLE IF EXISTS flaws")
    cursor.execute("CREATE TABLE flaws (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    flaws = [("自卑",), ("傲慢",), ("社恐",), ("暴躁",), ("拖延症",), ("敏感",), ("虚荣",)]
    cursor.executemany("INSERT INTO flaws (name) VALUES (?)", flaws)

    conn.commit()
    conn.close()
    print("✅ NPC metadata seeded successfully into world_data.db")

if __name__ == "__main__":
    seed()
