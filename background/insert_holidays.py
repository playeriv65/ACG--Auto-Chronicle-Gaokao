import sqlite3
from datetime import datetime, timedelta

def get_week_dates(start_date_str, week_index):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    week_start = start_date + timedelta(weeks=week_index)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end

def main():
    db_path = 'curriculum.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM curriculum ORDER BY week")
    original_rows = [dict(row) for row in cursor.fetchall()]
    cursor.execute("DELETE FROM curriculum")

    sem_starts = ["2020-08-31", "2021-03-01", "2021-08-30", "2022-02-28", "2022-08-29", "2023-01-23"]
    # Specific week numbers to be holidays (1-based)
    holiday_weeks = {5: "国庆假期", 29: "五一假期", 45: "国庆假期", 70: "五一假期", 85: "国庆假期", 115: "五一假期"}

    new_curriculum = []
    for sem_idx in range(6):
        start_date = sem_starts[sem_idx]
        sem_original_content = original_rows[sem_idx*20 : (sem_idx+1)*20]
        content_ptr = 0
        for w_idx in range(20):
            week_num = sem_idx * 20 + w_idx + 1
            w_start, w_end = get_week_dates(start_date, w_idx)
            dr_str = f"{w_start.strftime('%Y-%m-%d')} ~ {w_end.strftime('%Y-%m-%d')}"
            
            if week_num in holiday_weeks:
                h_name = holiday_weeks[week_num]
                row_data = {k: h_name for k in ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics']}
                row_data['week'] = week_num
                row_data['date_range'] = dr_str
            else:
                src = sem_original_content[content_ptr]
                row_data = {k: src[k] for k in src.keys()}
                row_data['week'] = week_num
                row_data['date_range'] = dr_str
                content_ptr += 1
            new_curriculum.append(row_data)

    for r in new_curriculum:
        cols = ', '.join(r.keys())
        placeholders = ':' + ', :'.join(r.keys())
        cursor.execute(f"INSERT INTO curriculum ({cols}) VALUES ({placeholders})", r)

    conn.commit()
    conn.close()
    print("Holidays inserted successfully.")

if __name__ == "__main__":
    main()