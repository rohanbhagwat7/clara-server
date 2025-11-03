"""
Quick script to set a job to past due for testing
"""
import psycopg
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://clara:clara_dev_password@localhost:5432/clara"

# Set JOB-2024-1022-003 to yesterday at 2 PM (past due)
yesterday = datetime.now() - timedelta(days=1)
past_due_time = yesterday.replace(hour=14, minute=0, second=0)

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        # Update the job to be past due
        cur.execute(
            """
            UPDATE jobs
            SET scheduled_time = %s, status = 'scheduled'
            WHERE job_id = 'JOB-2024-1022-003'
            """,
            (past_due_time,)
        )
        conn.commit()
        print(f"Updated JOB-2024-1022-003 to past due (scheduled for {past_due_time})")

        # Verify
        cur.execute(
            "SELECT job_id, scheduled_time, status FROM jobs WHERE job_id = 'JOB-2024-1022-003'"
        )
        result = cur.fetchone()
        print(f"  Job: {result[0]}")
        print(f"  Scheduled: {result[1]}")
        print(f"  Status: {result[2]}")
        print(f"  Is past due: {result[1] < datetime.now()}")
