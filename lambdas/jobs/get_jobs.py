"""
PURPOSE: Returns all job applications belonging to the authenticated user.
 
- Called by API Gateway on GET /jobs
- Requires a valid JWT (via @require_auth decorator)
- Queries the JOBS table using the user_id-index GSI
- Supports optional ?status= query param to filter results client-side
 
FLOWS:
  1. Authenticate the request via JWT (@require_auth injects `user`)
  2. Query DynamoDB for all jobs where user_id matches
  3. Optionally filter by status if ?status= is provided
  4. Return the list (empty list is valid — not a 404)
"""


from shared.db import get_job_by_user
from shared.auth_helper import require_auth, success

@require_auth
def handler(event, context, user):
    #=========== Get All Jobs For This User ============#
    jobs = get_job_by_user(user["user_id"])

    #=========== Optional Status Filter ============#

    query_param = event.get("queryStringParameters") or {}
    status_filter = query_param.get("status", "").strip().lower()


    if status_filter:
        jobs = [j for j in jobs if j.get("status", "").lower() == status_filter]

    #============ Sort by newest ===========#
    def get_created_time(job):
        return job.get("created_at", "")
    
    jobs.sort(key=get_created_time,reverse=True)

    return success({"jobs": jobs, "count": len(jobs)})