"""
PURPOSE: Automatically marks job applications as "ghosted" if there's been no update
         in over 21 days and status is still "applied" or "interviewing".
 
- Triggered by EventBridge Scheduler (runs once daily, not via API Gateway)
- Scans the entire JOBS table (full scan is acceptable — this is a background job)
- Calls update_job() for each stale record to flip status to "ghosted"
- Returns a summary of how many jobs were updated

 
FLOWS:
  1. Scan all jobs from DynamoDB
  2. Filter for jobs in "applied" or "interviewing" with updated_at older than 21 days
  3. Update each stale job's status to "ghosted"
  4. Return a count summary (EventBridge doesn't use the response but it's good for logs)
"""

from datetime import datetime, timezone, timedelta
from shared.db import scan_all_jobs, update_job
from botocore.exceptions import ClientError

STALE_STATUSES       = {"applied", "interviewing"}
GHOST_THRESHOLD_DAYS = 10

def handler(event, context):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=GHOST_THRESHOLD_DAYS)

    all_job = scan_all_jobs()
    ghosted = []
    error = []

    for job in all_job:
        if job.get("status") not in STALE_STATUSES:
            continue

        # parse updated_at
        updated_at_str = job.get("updated_at","")
        try :
            updated_at = datetime.fromisoformat(updated_at_str)

        except (ValueError, TypeError):
            print(f"[ghost_checker] Skipping job {job.get('job_id')} — bad updated_at: {updated_at_str!r}")
            continue

        # Make timezone-aware if stored without timezone info    
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)    

        if updated_at < cutoff:
            try:
                update_job(
                    job_id = job["job_id"],
                    user_id = job["user_id"],
                    update = {"status": "ghosted"}
                )
                ghosted.append(job["job_id"])
                print(f"[ghost_checker] Marked as ghosted: {job['job_id']} (company: {job.get('company')})")
            except ClientError as e:
                error.append(job["job_id"])
                print(f"[ghost_checker] Failed to update {job['job_id']}: {e.response['Error']['Message']}")
 
    
    summary = {
        "checked" : len(all_job),
        "ghosted" : len(ghosted),
        "errors": len(error),
        "ghosted_ids": ghosted
    }

    print(f"[ghost_checker] Done. Summary: {summary}")
    return summary
