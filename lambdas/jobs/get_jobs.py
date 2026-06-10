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
