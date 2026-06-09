import boto3
import os
from botocore.exceptions import ClientError

"""
This file contain the methods used to interact with databases
"""


# DynamoDB, reused across all lambda
dynamodb = boto3.resource(
    "dynamodb",
    region_name = os.environ.get("AWS_REGION", "us-east-1")
)
#Table references — names pulled from .env, never hardcoded
USERS_TABLE = dynamodb.Table(os.environ["USERS_TABLE_NAME"])
JOBS_TABLE  = dynamodb.Table(os.environ["JOBS_TABLE_NAME"])

def get_user_by_email(email:str) -> dict | None:
    """get user by email, return None if not found"""

    try:
        response = USERS_TABLE.get_item(Key={"email": email})
        return response.get("Item")
    except ClientError as e:
        print(f"[db] get_user_by_email error: {e.response['Error']['Message']}")
        raise

#save user into db
def put_user(user:dict):
    try:
        USERS_TABLE.put_item(Item=user)
    except ClientError as e:
        print(f"[db] put_user error: {e.response['Error']['Message']}")
        raise


def put_job(job:dict):
    """insert or overwrite job"""
    try:
        JOBS_TABLE.put_item(Item=job)
    except ClientError as e:
        print(f"[db] put_job error: {e.response['Error']['Message']}")
        raise


def get_job_by_user(user_id:str) -> list[dict]:
    """get all job applications belonging to a user."""
    try:
        response = JOBS_TABLE.query(
            IndexName = "user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid":user_id}
        )
        return response.get("Items", [])
    except ClientError as e:
        print(f"[db] get_jobs_by_user error: {e.response['Error']['Message']}")
        raise


def update_job(job_id:str, user_id:str, updates:dict) -> dict:
    """
    Partially update a job record.
    Only allows whitelisted fields to be changed.
    Returns the updated item.
    """

    ALLOWED_FIELDS = {"status", "notes", "next_step", "follow_up_date"}
    safe_updates = {k: v for k, v in updates.items() if k in ALLOWED_FIELDS}

    if not safe_updates:
        raise ValueError("No valid field to update!")
    
    # Build DynamoDB update expression dynamically
    expression_parts = []
    expression_names  = {}
    exprression_values = {}

    for i, (field,value) in enumerate(safe_updates.items()):
        placeholder_name  = f"#f{i}"
        placeholder_value = f":v{i}"
        expression_parts.append(f"{placeholder_name} = {placeholder_value}")
        expression_names[placeholder_name] = field
        exprression_values[placeholder_value] = value

    update_expression = "SET "+ ", ".join(expression_parts)

    try:
        response=JOBS_TABLE.update_item(
            Key={"job_id": job_id, "user_id":user_id},
            UpdateExpression = update_expression,
            ExpressionAttributeNames = expression_names,
            ExpressionAttributeValues = exprression_values,
            ConditionExpression = "user_id = :uid",      #users can only edit their own jobs
            ExpressionAttributeValues = {**exprression_values, ":uid" : user_id},
            ReturnValues = "ALL_NEW"
        )
        return response.get("Attributes", {})
    except ClientError as e:
        print(f"[db] update_job error: {e.response['Error']['Message']}")
        raise


def scan_all_jobs() -> list[dict]:
    """
    Full table scan — used to check ghost jobs.
    Handles DynamoDB pagination automatically.
    """

    items = []
    try:
        response = JOBS_TABLE.scan()
        items.extend(response.get("Items", []))

        #DynamoDB paginates at 1MB, keep fetching if there's more
        while "LastEvaluatedKey" in response:
            response = JOBS_TABLE.scan(
                ExclusiveStartKey = response["LastEvaluatedKey"]
            )

            items.extend(response.get("Items", []))

        return items
    except ClientError as e:    
        print(f"[db] scan_all_jobs error: {e.response['Error']['Message']}")
        raise














