"""
PURPOSE: creates a new job record for the AUTHENTICATED user.
 
- Called by API Gateway on POST /jobs
- Requires a valid JWT (via @require_auth decorator)
- Writes one record to the JOBS table in DynamoDB
- Returns the full job object that was saved
 
FLOWS:
  1. Authenticate the request via JWT (@require_auth injects `user`)
  2. Validate required fields (company, role)
  3. Build a job record with default status "applied"
  4. Save to DynamoDB via put_job()
  5. Return the saved job
"""
import json
import uuid
from datetime import datetime, timezone
from shared.db import put_job
from shared.auth_helper import require_auth, success, error

@require_auth
def handler(event, context, user):
    #=========== Parse and Validate Body ============#
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error("Invalid JSON request.",400)
    
    company = (body.get("company") or "").strip()
    role = (body.get("role") or "").strip()


    if not company or not role:
        return error("Company or Role is required.",400)
    
    #extra fields
    status = body.get("status", "applied")
    notes = body.get("notes", "")
    next_step    = body.get("next_step", "")
    follow_up_date = body.get("follow_up_date", "")     # expected: ISO date string e.g. "2025-06-15"

    VALID_STATUS = {"applied", "interviewing", "offer", "rejected", "ghosted"}      #possible status 
    if status not in VALID_STATUS:
        return error(f"Invalid status, allowed statuses: {', '.join(VALID_STATUS)}")
       
    
    #=========== Build Job Record ============#
    job_id = str(uuid.uuid4())
    curr_time = datetime.now(timezone.utc).isoformat()

    job = {
        "job_id"        : job_id,
        "user_id"       : user["user_id"],      #injected by @require_auth from JWT
        "company"       : company,
        "role"          : role,
        "status"        : status,
        "notes"         : notes,
        "next_step"     : next_step,
        "follow_up_date": follow_up_date,
        "created_at"    : curr_time,
        "updated_at"    : curr_time,
    }
    
    
    #=========== Save and Return ============#
    put_job(job)
    return success(job, status=201)