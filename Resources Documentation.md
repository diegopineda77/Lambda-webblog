# Step by Step

The steps taken to create the infrastructure that meets the requirements for the blog website are listed. It will be necessary to configure the following components.

| Type       | Name| Labels (tags)    |
|--------------|-|-----------|
| Table DynamoDB   | `BlogPosts` | ​​`project:webpost`, `env:test` |
| IAM Policy   |  `BlogDynamoDBCrudPolicy` | ​​`project:webpost`    |
| IAM Role    | `WebBlogLambdaCRUDRole`, `ApiGTWLogsCloudwatch` | ​​`project:webpost`     
| Lambda | `BlogPosts` | ​​`project:webpost`   | |
| Cognito   | `webpost` |  no label     |
| API GTW   | `webpost` |   ​`project:webpost`   |
| Cloudwatch   | Used for view metrics and logs |   no label   |


All resources, roles, and policies are tagged with the values ​​`project:webpost`.

## DynamoDB Table
In the AWS console, create a table with the following configuration:

| Setting       | Value     |
|---------------|-----------|
| Table name    | `BlogPosts` |
| Partition key | `post_id`   |
| Key type      | String    |
| Sort key      | None      |


## IAM Roles and Policies

### Lambda Role and Policies
Create a new **policy** `BlogDynamoDBCrudPolicy` and add permissions to the table and resources, with minimal privileges for the region, and a specific account and resource. 

> Note: The values ​​REGION and ACCOUNT_ID are placeholders; they must be replaced with values.

```json
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

Create a new **Role** `WebBlogLambdaCRUDRole` and add policies `BlogDynamoDBCrudPolicy` and `AWSLambdaBasicExecutionRole` that have the minimal access to cloudwatch to register logs.

### Api Gateway Role and Policies

Create a new **Role** `ApiGTWLogsCloudwatch` and add policy `AmazonAPIGatewayPushToCloudWatchLogs` to be able to record events in CloudWatch logs.



## Lambda Function

Create a Lambda function using the `lambda_function.py` file, with `BlogPosts` name. Create a label `project:webpost`.
Add the role `WebBlogLambdaCRUDRole` to Lambda Fuction `BlogPosts` in configuration/permissions.

The Lambda execution role requires permissions for the `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:Scan`, and `dynamodb:UpdateItem` operations on that table. Restrict the permissions to the table's ARN, rather than granting general access to DynamoDB.

Then, in the Lambda configuration, add this environment variable:
`TABLE_NAME = BlogPosts`




## Cognito configuration
Create a user pool in Amazon Cognito named `webpost`, the `ALLOW_USER_PASSWORD_AUTH` option must be selected, and create a user to be used for authentication.


## API Gateway Config.

Create an HTTP API REST and connect its routes to the same Lambda function:

| route                 | Integration |
| -------------------- | ----------- |
| `POST /posts`        | Lambda      |
| `GET /posts`         | Lambda      |
| `PUT /posts/{id}`    | Lambda      |
| `PATCH /posts/{id}`  | Lambda      |
| `DELETE /posts/{id}` | Lambda      |

Configure the proxy integration so that Lambda receives the method, path, parameters, and body of each request. Associate with the Cognito pool (Cognito-webpost) and define `Authorization` like origin token.

Under resources, link the authenticator; leave the request validator empty, and select the Lambda function configured with Lambda proxy integration.


## Backup plan
Although aspects related to backups are not explicitly specified for this project, it is recommended to define the **RPO** (Recovery Point Objective), **RTO** (Recovery Time Objective), and the **retention period** for these backups. At a minimum, it is advisable to design a basic daily backup plan with a 30-day retention period, using **AWS Backup**.


## Monitoring
Monitoring is performed using automated CloudWatch dashboards to track API Gateway, Lambda, and DynamoDB, with a focus on latencies, the number of API/Lambda calls, 500 and 400 errors, throttled requests, etc.

| Resource                 | More focused metrics |
| -------------------- | ----------- |
| Api gateway      | SuccessfulRequestLatency, ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits, UserErrors      |
| Lambda | Invocations, Duration, Errors, Throttles  |
| DynamoDB | SuccessfulRequestLatency, ThrottledRequests, UserErrors, ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits, ReturnedItemCount   |

# Testing

For first time to the new user if is necesary reset the password.

Create a user in cognito for Testing. Validate the user password for first time 

```Powershell
aws cognito-idp initiate-auth --region REGION --client-id CLIENT_ID --auth-flow USER_PASSWORD_AUTH --auth-parameters "USERNAME=EMAIL,PASSWORD=PASSWORD_TEMPORAL"
```
for new password

```powershell 
aws cognito-idp respond-to-auth-challenge --region REGION --client-id CLIENT_ID --challenge-name NEW_PASSWORD_REQUIRED --challenge-responses "USERNAME=EMAIL,NEW_PASSWORD=NEW_PASSWORD" --session "SESSION_RETURNBY_COGNITO"
```
or just confirme the password (just for testing). Replace `us-east-2_userid`, `user`, `pass`, `region us-east-2`.

```powershell
aws cognito-idp admin-set-user-password   --user-pool-id us-east-2_userid   --username user   --password "pass"   --permanent   --region us-east-2
```

## Token request using CLI

Request to token

```Bash
aws cognito-idp initiate-auth \
  --region <REGION> \
  --client-id <CLIENT_ID> \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="user",PASSWORD="password"
```
Json response. IdToken need to be used in autorized post

```json
{
  "AuthenticationResult": {
    "AccessToken": "eyJ...",
    "IdToken": "eyJ...",
    "RefreshToken": "eyJ...",
    "ExpiresIn": 3600,
    "TokenType": "Bearer"
  }
}
```

## Token request using Postman

URL: `https://cognito-idp.<region>.amazonaws.com/`

**Header**
|Key|	Value|
|----|-------|
|Content-Type	|application/x-amz-json-1.1|
|X-Amz-Target	|AWSCognitoIdentityProviderService.InitiateAuth|

**Body**

``` json
{
  "AuthFlow": "USER_PASSWORD_AUTH",
  "ClientId": "<CLIENT_ID>",
  "AuthParameters": {
    "USERNAME": "user",
    "PASSWORD": "pass"
  }
}
```

replae the user and pass for the cognito user, and Client_ID for the aplication ID in cognito.

## Api Call

Since authentication is being handled via Cognito, it is necessary to configure the header with a Bearer token and include the requested token.

Copy the URL for testing the API Gateway stage invocation URL. ex:
`https://x4xx1232.execute-api.us-east-2.amazonaws.com/dev`

**Header**
|Key|	Value|
|----|-------|
|Bearer Token	|"eyJ..."|

### Create Post

`POST /posts`

```json
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

`PATCH /posts/{post-id}`
```json
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

`DELETE /posts/{post-id}`

```json
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

```json
{
  "httpMethod": "GET",
  "path": "/posts",
  "queryStringParameters": null
}
```

The query response includes `items`, `count`, and `nextToken`. If there are no more pages, `nextToken` will be `null`..

>Expected response: 200 OK, query OK.