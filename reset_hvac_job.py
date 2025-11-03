"""
Reset HVAC job to scheduled status for today
"""
import psycopg
from datetime import datetime

DATABASE_URL = "postgresql://clara:clara_dev_password@localhost:5432/clara"

# Set job to today at 9 AM
today = datetime.now()
scheduled_time = today.replace(hour=9, minute=0, second=0)

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        # Update the HVAC job to scheduled for today
        cur.execute(
            """
            UPDATE jobs
            SET scheduled_time = %s, status = 'scheduled'
            WHERE job_id = 'JOB-2024-1022-001'
            """,
            (scheduled_time,)
        )
        conn.commit()
        print(f"Updated JOB-2024-1022-001 (HVAC) to scheduled for {scheduled_time}")

        # Verify
        cur.execute(
            "SELECT job_id, title, scheduled_time, status FROM jobs ORDER BY scheduled_time"
        )
        results = cur.fetchall()
        print("\nAll jobs:")
        for row in results:
            print(f"  {row[0]}: {row[1][:30]}... - {row[2]} [{row[3]}]")
