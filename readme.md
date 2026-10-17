# API Specifications for Blog Post Management

## Overview
Development of a set of REST API endpoints is required to manage the full lifecycle of blog posts on the website. The goal of this project is to implement a serverless architecture and justify this decision. At the code level, there are certain areas for improvement that are not being addressed, given the focus on the implementation itself.

## Required Endpoints

1. **Create Post (`POST /posts`)**
* **Description:** Creates a new blog post.
* **Required Fields:** Title, content, publication date, and author (ID or name).
* **Behavior:** Assigns a unique identifier/code and sets the initial post status (*Published*).


2. **Edit Post (`PUT /posts/{id}` or `PATCH /posts/{id}`)**
* **Description:** Updates the information of an existing post (title, content, etc.).


3. **Delete Post (`DELETE /posts/{id}` or `PATCH /posts/{id}/status`)**
* **Description:** Performs a soft delete by changing the post's status to `Deleted`.


4. **Get / Filter Posts (`GET /posts`)**
* **Description:** Retrieves a list of posts with support for query parameters/filters.
* **Filter Options:**
* **Status:** `Published`, `Deleted`.
* **Date:** Specific date or date range.
* **Author:** By author ID or name.
* **Code:** By unique post identifier/code.

**Post Statuses:**

* `Published`: Live and publicly available.
* `Deleted`: Soft-deleted.


## Architecture Decision 
![alt text](<AWS Serverless API Architecture.png>)

## Technologies
Api GTW, Lambda, DynamoDB, Cognito, CloudWatch

## Options Considered
**Docker/ECS, Database: RDS**
* It makes it easier to move the application between container-compatible platforms.
* Payment based on allocated resources while tasks are running. With high and stable traffic, a container service can be more cost-competitive.

## Decision

**Lambda:**
* Small APIs, short-lived operations, unpredictable traffic, event-driven processing, and minimal infrastructure maintenance.
* Easy to configure and scale; AWS manages a large part of the runtime environment.


**DynamoDB:**

**Api Gateway:**

**Cognito:**

**CloudWatch:**


## Consequences

* Greater operational dependence on AWS; if a migration were desired, the APIs would have to be rebuilt.
* Dependency on execution traffic; payment based on invocations and execution time.

## Challenges
```
seguridad (VPC)
costo
resiliencia
Monitoreo
networking
Backups
DRP
```

## More documents
See `Resources Documentation.md` for instructions on how to create the DynamoDB table, configure the API Gateway, and view examples of how to call the Lambda API.

See `example.json` for the JSON structure.