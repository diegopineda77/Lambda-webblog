## Lambda Function

Create a Lambda function using the `lambda_function.py` file, with `BlogPosts` name. Create a label `project:webpost`.

## Api Call

### Create Post

`POST /posts`

```
{
  "httpMethod": "POST",
  "path": "/posts",
  "pathParameters": null,
  "queryStringParameters": null,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"title\":\"Test post\",\"content\":\"Test content\",\"publication_date\":\"2026-10-17\",\"author_id\":\"author-001\",\"author_name\":\"Test Author\"}",
  "isBase64Encoded": false
}
```

> Expected response: 201 Created. The publication is automatically assigned a UUID and the status Published.

### Edit Post

`PATCH /posts/8b15e8e2-6f2b-4f1c-a239-9ad2b3d61c4a`
```
{
  "httpMethod": "PUT",
  "path": "/posts/<ID>",
  "pathParameters": {
    "id": "<ID>"
  },
  "body": "{\"title\":\"My updated post\",\"content\":\"The post has been updated successfully.\"}",
  "isBase64Encoded": false
}

```

> Expected response: 200 OK, data updated.

### Delete Post

```
{
  "httpMethod": "DELETE",
  "path": "/posts/<ID>",
  "pathParameters": {
    "id": "<ID>"
  }
}
```

> Expected response: 200 OK. The record remains in DynamoDB, but its status changes to Deleted.



### Query with filters


| Goal             | Example                                                |
| -------------------- | ------------------------------------------------------ |
| All post | `GET /posts?status=Published`                          |
| Search by code   | `GET /posts?code=8b15e8e2-6f2b-4f1c-a239-9ad2b3d61c4a` |
| by author     | `GET /posts?authorId=USR-001`                          |
| by name   | `GET /posts?authorName=Carlos`                         |
| by date         | `GET /posts?date=2026-10-15`                           |
| by date range      | `GET /posts?startDate=2026-10-01&endDate=2026-10-31`   |
| pagination           | `GET /posts?limit=20&nextToken=...`                    |

```
{
  "httpMethod": "GET",
  "path": "/posts",
  "queryStringParameters": null
}
```

The query response includes `items`, `count`, and `nextToken`. If there are no more pages, `nextToken` will be `null`..

## DynamoDB Table
In the AWS console, create a table with the following configuration:

| Setting       | Value     |
|---------------|-----------|
| Table name    | `BlogPosts` |
| Partition key | `post_id`   |
| Key type      | String    |
| Sort key      | None      |

Then, in the Lambda configuration, add this environment variable:

`TABLE_NAME = BlogPosts`

The Lambda execution role requires permissions for the `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:Scan`, and `dynamodb:UpdateItem` operations on that table. Restrict the permissions to the table's ARN, rather than granting general access to DynamoDB.

## Security

Create a new policy `BlogDynamoDBCrudPolicy` and add permissions to the table and resources, with minimal privileges for the region, and a specific account and resource. 

> Note: The values ​​REGION and ACCOUNT_ID are placeholders; they must be replaced with values.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BlogTableCrud",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:<REGION>:<ACCOUNT_ID>:table/BlogPosts",     "arn:aws:dynamodb:<REGION>:<ACCOUNT_ID>:table/BlogPosts/index/*"
      ]
    }
  ]
}

```

Create a new Role `WebBlogLambdaCRUDRole` and add policies `BlogDynamoDBCrudPolicy` and `AWSLambdaBasicExecutionRole` that have the minimal access to cloudwatch to register logs.

## API Gateway Config.

Create an HTTP API and connect its routes to the same Lambda function:

| route                 | Integration |
| -------------------- | ----------- |
| `POST /posts`        | Lambda      |
| `GET /posts`         | Lambda      |
| `PUT /posts/{id}`    | Lambda      |
| `PATCH /posts/{id}`  | Lambda      |
| `DELETE /posts/{id}` | Lambda      |

Configure the proxy integration so that Lambda receives the method, path, parameters, and body of each request.

## Labeled

All resources, roles, and policies are tagged with the values ​​`project:webpost`.

| Type       | Name| Labels     |
|--------------|-|-----------|
| Table DynamoDB   | `BlogPosts` | ​​`project:webpost`, `env:test` |
| Lambda | `BlogPosts` | ​​`project:webpost`   |
| IAM Policy   |  `BlogDynamoDBCrudPolicy` | ​​`project:webpost`    |
| IAM Role    | `WebBlogLambdaCRUDRole` | ​​`project:webpost`      |
| API GTW   |  | ​​`project:webpost`      |