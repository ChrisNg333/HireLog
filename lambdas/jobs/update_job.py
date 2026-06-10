"""
PURPOSE: updates a job application OWNED by the AUTH user.
 
- Called by API Gateway on PATCH /jobs/{job_id}
- Requires a valid JWT (via @require_auth decorator)
- Only allows whitelisted fields to be updated (enforced in db.update_job)
- The ConditionExpression in db.update_job prevents editing another user's job
 
FLOWS:
  1. Authenticate the request via JWT (@require_auth injects `user`)
  2. Extract job_id from path parameters
  3. Validate that at least one updatable field was sent
  4. Call db.update_job() which builds the DynamoDB expression and enforces ownership
  5. Return the updated job record
"""
import json
from shared.db import update_job
from shared.auth_helper import require_auth, success, error
from botocore.exceptions import ClientError
 
@require_auth
def handler(event, context, user):
    #=========== Get job_id from URL path ============#
    path_params = event.get("pathParameters") or {}
    job_id = path_params.get("job_id", "").strip()

    if not job_id:
        return error("job_id is required in the path.", 400)
    
    #=========== Parse Body ============#
    try:
        body = json.loads(event.get("body") or "{}")

    except json.JSONDecodeError:
        return error("Invalid JSON in request",400)
    
    if not body:
        return error("Request body is empty", 400)

    #=========== Attempt to Update ============#

    try:
        updated_job = update_job(
            job_id = job_id,
            user_id = user["user_id"],
            updates = body
        )

    except ValueError as e:
        return error(str(e), 400)
    
    except ClientError as e:
        code = e.response["Error"]["Code"]

        if code == "ConditionalCheckFailedException":
            #job_id not found or belongs to diff users

            return error("Job not found or access denied.",404)
        raise

    return success(updated_job)