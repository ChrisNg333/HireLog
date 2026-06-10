"""
PURPOSE: creates a new user account.
 
- Called by API Gateway on POST /auth/register
- Writes one record to the USERS table in DynamoDB
- Returns a JWT so the user is immediately logged in after registering
 
FLOWS:
  1.Validate request body (email + password required)
  2.Check the email isn't already taken
  3.Hash the password with bcrypt (never store plain text)
  4.Save the new user to DynamoDB
  5.Return a signed JWT token
"""
import json
import uuid
import bcrypt
from shared.db import get_user_by_email, put_user
from shared.auth_helper import create_token, success, error

def handler(event, context):
    #=========== Parse and Validate Body ============#
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error("Invalid JSON in request", 400)

    email = (body.get("email") or "").strip().lower()       #to handle None type -> lead to crash 
    password = body.get("password") or ""

    if not email or not password:
        return error("email and password is required.", 400)
    
    if len(password) < 8:
        return error("password must be 8 character long.", 400)
    
    if '@' not in email:
        return error("invalid email address.", 400)


    #=========== Check For Existing Acc ============#
    existed = get_user_by_email(email)
    if existed:
        return error("Email already registered.", 409)
    

    #=========== Password Hashing ============#
    hashed_pass = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


    #=========== Create And Save New User Record ============#
    user_id = str(uuid.uuid4())
    user = {
        "user_id" : user_id,
        "email" : email,
        "password" : hashed_pass        #since hashed so good to store 

    }

    put_user(user)      #save user into db

    #=========== Return the JWT For User Instant Login ============#
    token = create_token(user_id=user_id,email=email)
    
    return success(
        {
            "token" : token,
            "user_id": user_id,
            "email": email
        },
        status=201
    )