import sqlite3
import re
import os

def parse_md_tables(file_path, subject_cols):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all tables in the markdown
    # Tables are roughly lines starting with | and containing |
    # We look for rows like | **1** | ... |
    data = {}
    
    # Subject columns mapping
    # subject_cols is a list of subject names in the order they appear in the table after the week column
    
    rows = re.findall(r'^\|\s*\*\*?(\d+)\*\*?\s*\|(.*)', content, re.MULTILINE)
    for week_str, remaining in rows:
        week = int(week_str)
        # Split by | and strip whitespace/markdown bolding
        # The remaining string might end with a |
        cells = [c.strip().replace('**', '') for c in remaining.split('|')]
        # Filter out empty strings from trailing |
        cells = [c for c in cells if c or cells.index(c) < len(subject_cols)]
        
        week_data = {}
        for i, subject in enumerate(subject_cols):
            if i < len(cells):
                week_data[subject] = cells[i]
            else:
                week_data[subject] = ""
        data[week] = week_data
    
    return data

def main():
    db_path = 'curriculum.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE curriculum (
            week INTEGER PRIMARY KEY,
            chinese TEXT,
            math TEXT,
            english TEXT,
            physics TEXT,
            chemistry TEXT,
            biology TEXT,
            history TEXT,
            geography TEXT,
            politics TEXT
        )
    ''')
    
    # Initialize 120 weeks
    all_data = {w: {s: "" for s in ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics']} for w in range(1, 121)}
    
    # Parse 语数英
    ysy_data = parse_md_tables('高中理科班语数英三年120周教学日程表.md', ['chinese', 'math', 'english'])
    for w, d in ysy_data.items():
        all_data[w].update(d)
        
    # Parse 理化生
    lhs_data = parse_md_tables('高中理科班理化生三年120周教学日程表.md', ['physics', 'chemistry', 'biology'])
    for w, d in lhs_data.items():
        all_data[w].update(d)
        
    # Parse 政史地
    zsd_data = parse_md_tables('高中理科班政史地会考科目日程表.md', ['history', 'geography', 'politics'])
    for w, d in zsd_data.items():
        all_data[w].update(d)
        
    # Special handling for 政史地 gaps based on the file content
    for w in range(41, 77):
        all_data[w]['history'] = "暂停 (理科选修强化)"
        all_data[w]['geography'] = "暂停 (理科选修强化)"
        all_data[w]['politics'] = "暂停 (理科选修强化)"
    
    for w in range(81, 121):
        all_data[w]['history'] = "结课"
        all_data[w]['geography'] = "结课"
        all_data[w]['politics'] = "结课"
        
    # Insert into database
    for w in range(1, 121):
        d = all_data[w]
        cursor.execute('''
            INSERT INTO curriculum (week, chinese, math, english, physics, chemistry, biology, history, geography, politics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (w, d['chinese'], d['math'], d['english'], d['physics'], d['chemistry'], d['biology'], d['history'], d['geography'], d['politics']))
    
    conn.commit()
    conn.close()
    print(f"Successfully imported 120 weeks into {db_path}")

if __name__ == "__main__":
    main()
