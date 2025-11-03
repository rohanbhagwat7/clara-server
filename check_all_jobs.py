"""
Check all jobs in database
"""
import psycopg
from datetime import datetime

DATABASE_URL = "postgresql://clara:clara_dev_password@localhost:5432/clara"

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        # Get all jobs
        cur.execute(
            """
            SELECT job_id, title, status, scheduled_time
            FROM jobs
            ORDER BY scheduled_time
            """
        )
        results = cur.fetchall()

        print(f"Total jobs in database: {len(results)}")
        print("\nAll jobs:")
        print("-" * 80)
        for row in results:
            now = datetime.now()
            is_past = row[3] < now if row[3] else False
            past_str = "[PAST DUE]" if is_past and row[2] == 'scheduled' else ""
            print(f"{row[0]}: {row[1]}")
            print(f"  Status: {row[2]}")
            print(f"  Scheduled: {row[3]} {past_str}")
            print()
