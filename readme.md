# API Specifications for Blog Post Management

## Overview
Development of a set of REST API endpoints is required to manage the full lifecycle of blog posts on the website. The goal of this project is to implement a **serverless architecture** and justify this decision. At the code level, there are certain areas for improvement that are not being addressed, given the focus on the implementation itself.

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
Api GTW, Lambda, DynamoDB, Cognito, CloudWatch, IAM (minimal privileges)

## Options Considered
**Docker/ECS, Database: RDS**
* It makes it easier to move the application between container-compatible platforms.
* Payment based on allocated resources while tasks are running. With high and stable traffic, a container service can be more cost-competitive.
**Security**
* WAF and Shield are not used for this initial phase.

## Decision

**Lambda:**
* Small APIs, short-lived operations, unpredictable traffic, event-driven processing, and minimal infrastructure maintenance.
* Easy to configure and scale; AWS manages a large part of the runtime environment.


**DynamoDB:**

* DynamoDB offers resilience, automatically replicating data across three Availability Zones within a region, and scalability, as it can handle significant fluctuations in request volume. It also provides high availability by minimizing the impact of failures, along with low latency.

**Api Gateway and Cognito:**
* Allows for the association of a **Cognito** authorizer to reject unauthenticated requests before invoking Lambda.
Includes controls such as throttling to limit the request rate.
Publishes metrics on requests, errors, and latency, and can generate logs in **CloudWatch**. WAF and Shield are not used for this initial phase.

**CloudWatch:**
* Collect logs and metrics to diagnose failures, measure performance, and detect operational issues.

## Consequences

* Greater operational dependence on AWS; if a migration were desired, the APIs would have to be rebuilt.
* Dependency on execution traffic; payment based on invocations and execution time.

## Challenges

**Security:**
Regarding security, roles based on the principle of least privilege were implemented for accessing resources such as DynamoDB, API Gateway, and Lambda. An API Gateway layer was incorporated to better manage request limits and prevent the direct exposure of internal servers. Furthermore, Cognito is used for user authentication via tokens, which helps avoid over-exposing user credentials; additionally, all communication is secured using TLS.

**Serverless Architecture:** The entire architecture is serverless, which translates to a lower operational burden and greater resilience, agility, and availability.

**Cost:** Keeping costs under control is always a challenge; however, this architecture offers low, consumption-based costs, which can be capped within API Gateway to avoid unexpected surprises.

**Monitoring:** All monitoring is managed through CloudWatch controls, which helps identify errors or alerts and enables responses to them—even before a problem actually occurs.

## Next Steps

* Backup Plan with AWS Backup
* Monitoring Plan for Lambda, Api Gateway, DynamoDB
* Cost Estimate


## More documents
See `Resources Documentation.md` for instructions on how to create the DynamoDB table, configure the API Gateway, and view examples of how to call the Lambda API.

See `json_example.json` for the JSON structure.

See `Cloudformation.yaml` to recreate the infraestructure using IaC.