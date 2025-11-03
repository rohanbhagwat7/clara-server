"""
Set HVAC job to future time today
"""
import psycopg
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://clara:clara_dev_password@localhost:5432/clara"

# Set job to 2 hours from now
future_time = datetime.now() + timedelta(hours=2)

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        # Update the HVAC job to scheduled for future
        cur.execute(
            """
            UPDATE jobs
            SET scheduled_time = %s, status = 'scheduled'
            WHERE job_id = 'JOB-2024-1022-001'
            """,
            (future_time,)
        )
        conn.commit()
        print(f"Updated JOB-2024-1022-001 (HVAC) to scheduled for {future_time}")
        print(f"Current time: {datetime.now()}")
        print(f"Job will NOT be past due")
