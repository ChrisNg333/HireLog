"""
PURPOSE: Authenticates user then returns a JWT.
 
- Called by API Gateway on POST /auth/login
- Reads from the USERS table to verify the password
- Returns a JWT the client stores and sends on every future request
 
FLOWS:
  1. Validate request body (email + password required)
  2. Look up the user by email in DynamoDB
  3. Verify the submitted password against the stored bcrypt hash
  4. Return a signed JWT token on success
"""
import json
import bcrypt
from shared.db import get_user_by_email
from shared.auth_helper import create_token, success, error

def handler(event, context):
    #=========== Parse and Validate Body ============#
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error("Invalid JSON in request",400)
    
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return error("Email and Password are required", 400)
    

    #=========== Lookup User ============#
    user = get_user_by_email(email)

    if not user:
        return error("Invalid email or password.", 401)

    #=========== Verify Password With Hashed ============#
    password_match = bcrypt.checkpw(
        password.encode("utf-8"),
        user["password"].encode("utf-8")
    )

    if not password_match:
        #being vague so hacker cant guess which one is wrong LOL
        return error("Invalid email or password.",401)      

    #=========== Give out JWT ============#
    token = create_token(user_id=user["user_id"], email=user["email"])

    return success({
        "token": token,
        "user_id": user["user_id"],
        "email": user["email"]
    })

