import sqlite3
from datetime import datetime, timedelta

def get_week_range(start_date_str, week_num_in_semester):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    week_start = start_date + timedelta(weeks=(week_num_in_semester - 1))
    week_end = week_start + timedelta(days=6)
    return f"{week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}"

def main():
    db_path = 'curriculum.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add date_range column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE curriculum ADD COLUMN date_range TEXT")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Semester start dates
    semesters = [
        (1, 20, "2020-08-31"),   # Grade 1 Autumn
        (21, 40, "2021-03-01"),  # Grade 1 Spring
        (41, 60, "2021-08-30"),  # Grade 2 Autumn
        (61, 80, "2022-02-28"),  # Grade 2 Spring
        (81, 100, "2022-08-29"), # Grade 3 Autumn
        (101, 120, "2023-01-23") # Grade 3 Spring
    ]

    for start, end, start_date in semesters:
        for w in range(start, end + 1):
            week_in_sem = w - start + 1
            dr = get_week_range(start_date, week_in_sem)
            cursor.execute("UPDATE curriculum SET date_range = ? WHERE week = ?", (dr, w))

    conn.commit()
    conn.close()
    print("Successfully added date markers to curriculum.db")

if __name__ == "__main__":
    main()
