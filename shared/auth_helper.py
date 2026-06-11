import os
import json
import jwt
from functools import wraps
 
JWT_SECRET    = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"


# ------------ CREATE TOKEN -----------------#

def create_token(user_id: str, email:str) -> str:
    import time 
    payload = {
        "user_id": user_id,
        "email" : email,
        "exp" : int(time.time()) + (3*24*60*60)  #3 days
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# ------------ VALIDATE TOKEN -----------------#

def decode_token(token:str) -> dict:
    """decode and verify JWT"""    
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

def get_user_from_event(event:dict) -> dict | None:
    """
    Extract and decode the JWT from an API Gateway event's Authorization header.
    Expected header format:  Authorization: Bearer <token>
    """
    headers = event.get("headers") or {}     

    auth_header = headers.get("authorization") or headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[len("Bearer "):]

    try:
        return decode_token(token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
        


#------------- Lambda decorator -------------------#

"""
    Decorator for Lambda handlers that require authentication.
 
    Usage:
        @require_auth
        def handler(event, context, user):
            # user = decoded JWT payload with user_id and email
            ...
 
    Returns 401 automatically if token is missing or invalid.
"""
def require_auth(handler):
    @wraps(handler)
    def wrapper(event, context):
        user = get_user_from_event(event)
        if not user:
            return {
                "statusCode" : 401,
                "headers" :  _cors_headers(),
                "body" : json.dumps({"error": "Unauthorized. Invalid token."})
            }
        return handler(event, context, user)
    return wrapper


#------------- Shared response helper func ----------------#

def success(data:dict | list, status: int = 200) -> dict:
    return {
        "statusCode": status,
        "headers": _cors_headers(),
        "body": json.dumps(data, default=str)       # str due to handling decimal and datetime

    }


def error(message: str, status: int = 400) -> dict:
    return {
        "statusCode": status,
        "headers": _cors_headers(),
        "body": json.dumps({"error": message})
    }

def _cors_headers() -> dict:
    """
    CORS headers so a browser frontend can call the API.
    Tighten ALLOWED_ORIGIN in production to your actual domain.
    """
    allowed_origin = os.environ.get("ALLOWED_ORIGIN","*")
    return {
        "Content-Type" : "application/json",
        "Access-Control-Allow-Origin":  allowed_origin,
        "Access-Control-Allow-Headers": "ContentType,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS"
    }
