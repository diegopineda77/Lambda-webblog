
import os
import json
import base64
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr


TABLE_NAME = os.environ["TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

EDITABLE_FIELDS = {
    "title",
    "content",
    "publication_date",
    "author_id",
    "author_name",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=str)
    }


def parse_body(event):
    body = event.get("body")

    if body is None:
        return {}

    if isinstance(body, dict):
        return body

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    return json.loads(body)


def validate_publication_date(value):
    if not isinstance(value, str):
        return False

    try:
        # Accepts YYYY-MM-DD or an ISO date with a time component.
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_post_data(data, require_all=False):
    if not isinstance(data, dict):
        return "The request body must be a JSON object."

    allowed = EDITABLE_FIELDS
    unknown = set(data) - allowed

    if unknown:
        return f"Disallowed fields: {', '.join(sorted(unknown))}"

    required = {"title", "content", "publication_date"}

    if require_all:
        missing = required - set(data)
        if missing:
            return f"Missing required fields: {', '.join(sorted(missing))}"

        if not data.get("author_id") and not data.get("author_name"):
            return "You must provide author_id or author_name."

    for field in ("title", "content"):
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return f"{field} must be a non-empty string."

    if "publication_date" in data:
        if not validate_publication_date(data["publication_date"]):
            return "publication_date must be a valid ISO date."

    for field in ("author_id", "author_name"):
        if field in data and data[field] is not None:
            if not isinstance(data[field], str) or not data[field].strip():
                return f"{field} must be a non-empty string."

    return None


def create_post(event):
    data = parse_body(event)

    error = validate_post_data(data, require_all=True)
    if error:
        return response(400, {"error": error})

    timestamp = now_iso()

    post = {
        "post_id": str(uuid.uuid4()),
        "title": data["title"].strip(),
        "content": data["content"].strip(),
        "publication_date": data["publication_date"],
        "status": "Published",
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    if data.get("author_id"):
        post["author_id"] = data["author_id"].strip()

    if data.get("author_name"):
        post["author_name"] = data["author_name"].strip()

    table.put_item(
        Item=post,
        ConditionExpression=Attr("post_id").not_exists()
    )

    return response(201, post)


def get_posts(event):
    params = event.get("queryStringParameters") or {}

    status = params.get("status")
    code = params.get("code")
    author_id = params.get("authorId")
    author_name = params.get("authorName")
    exact_date = params.get("date")
    start_date = params.get("startDate")
    end_date = params.get("endDate")

    if status and status not in {"Published", "Deleted"}:
        return response(400, {
            "error": "status must be Published or Deleted."
        })

    if exact_date and (start_date or end_date):
        return response(400, {
            "error": "Use date or the startDate/endDate range, not both."
        })

    if exact_date and not validate_publication_date(exact_date):
        return response(400, {"error": "date is invalid."})

    if start_date and not validate_publication_date(start_date):
        return response(400, {"error": "startDate is invalid."})

    if end_date and not validate_publication_date(end_date):
        return response(400, {"error": "endDate is invalid."})

    if start_date and end_date and start_date > end_date:
        return response(400, {
            "error": "startDate cannot be later than endDate."
        })

    try:
        limit = int(params.get("limit", "50"))
        if not 1 <= limit <= 100:
            raise ValueError()
    except ValueError:
        return response(400, {
            "error": "limit must be between 1 and 100."
        })

    filters = []

    if status:
        filters.append(Attr("status").eq(status))

    if code:
        filters.append(Attr("post_id").eq(code))

    if author_id:
        filters.append(Attr("author_id").eq(author_id))

    if author_name:
        filters.append(Attr("author_name").eq(author_name))

    if exact_date:
        filters.append(Attr("publication_date").eq(exact_date))

    if start_date:
        filters.append(Attr("publication_date").gte(start_date))

    if end_date:
        filters.append(Attr("publication_date").lte(end_date))

    filter_expression = None
    for condition in filters:
        filter_expression = (
            condition if filter_expression is None
            else filter_expression & condition
        )

    scan_args = {"Limit": limit}

    if filter_expression is not None:
        scan_args["FilterExpression"] = filter_expression

    next_token = params.get("nextToken")

    if next_token:
        try:
            raw = base64.urlsafe_b64decode(
                next_token.encode("utf-8")
            )
            scan_args["ExclusiveStartKey"] = json.loads(raw)
        except Exception:
            return response(400, {
                "error": "nextToken is invalid."
            })

    result = table.scan(**scan_args)

    next_key = result.get("LastEvaluatedKey")
    encoded_next_token = None

    if next_key:
        encoded_next_token = base64.urlsafe_b64encode(
            json.dumps(next_key).encode("utf-8")
        ).decode("utf-8")

    return response(200, {
        "items": result.get("Items", []),
        "count": len(result.get("Items", [])),
        "nextToken": encoded_next_token
    })


def update_post(event, post_id):
    data = parse_body(event)

    if not data:
        return response(400, {
            "error": "You must provide fields to update."
        })

    error = validate_post_data(data)
    if error:
        return response(400, {"error": error})

    # Editing a deleted post is not allowed.
    existing = table.get_item(
        Key={"post_id": post_id},
        ConsistentRead=True
    ).get("Item")

    if not existing:
        return response(404, {"error": "Post not found."})

    if existing.get("status", "Published") == "Deleted":
        return response(409, {
            "error": "A deleted post cannot be edited."
        })

    update_parts = []
    names = {}
    values = {}

    for index, (field, value) in enumerate(data.items()):
        name_key = f"#f{index}"
        value_key = f":v{index}"

        update_parts.append(f"{name_key} = {value_key}")
        names[name_key] = field
        values[value_key] = (
            value.strip()
            if isinstance(value, str) else value
        )

    update_parts.append("#updated = :updated")
    names["#updated"] = "updated_at"
    values[":updated"] = now_iso()

    try:
        result = table.update_item(
            Key={"post_id": post_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ConditionExpression=(
                Attr("post_id").exists()
                & Attr("status").eq("Published")
            ),
            ReturnValues="ALL_NEW"
        )

        return response(200, result["Attributes"])

    except Exception as exc:
        # A concurrent modification may have deleted
        # the record or changed its status.
        current = table.get_item(
            Key={"post_id": post_id},
            ConsistentRead=True
        ).get("Item")

        if not current:
            return response(404, {
                "error": "Post not found."
            })

        if current.get("status", "Published") == "Deleted":
            return response(409, {
                "error": "The post has been deleted."
            })

        raise exc


def delete_post(post_id):
    try:
        result = table.update_item(
            Key={"post_id": post_id},
            UpdateExpression="SET #s = :deleted, #u = :updated",
            ExpressionAttributeNames={
                "#s": "status",
                "#u": "updated_at"
            },
            ExpressionAttributeValues={
                ":deleted": "Deleted",
                ":updated": now_iso()
            },
            ConditionExpression=(
                Attr("post_id").exists()
                & Attr("status").eq("Published")
            ),
            ReturnValues="ALL_NEW"
        )

        return response(200, {
            "message": "Post logically deleted.",
            "post": result["Attributes"]
        })

    except Exception:
        existing = table.get_item(
            Key={"post_id": post_id},
            ConsistentRead=True
        ).get("Item")

        if not existing:
            return response(404, {
                "error": "Post not found."
            })

        if existing.get("status") == "Deleted":
            return response(409, {
                "error": "The post has already been deleted."
            })

        raise


def lambda_handler(event, context):
    try:
        method = (
            event.get("httpMethod")
            or event.get("requestContext", {})
                 .get("http", {})
                 .get("method", "")
        ).upper()

        path = event.get("rawPath") or event.get("path", "")
        path = path.rstrip("/") or "/"

        path_params = event.get("pathParameters") or {}
        post_id = path_params.get("id")

        if not post_id and path.startswith("/posts/"):
            post_id = path.split("/")[2] if len(path.split("/")) > 2 else None

        if method == "POST" and path == "/posts":
            return create_post(event)

        if method == "GET" and path == "/posts":
            return get_posts(event)

        if method == "PUT" and post_id:
            return update_post(event, post_id)

        if method == "PATCH" and post_id:
            return update_post(event, post_id)

        if method == "DELETE" and post_id:
            return delete_post(post_id)

        return response(404, {"error": "Endpoint not found."})

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON."})

    except Exception:
        logger.exception("PUT request failed")
        return response(500, {
            "error": "Internal server error."
        })
