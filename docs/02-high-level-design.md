# 02 — High-Level Design

## Integration Strategy
We will implement the rate limiter as a **Sidecar Proxy** (or middleware) sitting in front of the service that makes outbound requests to the GitHub API. 
- **Client-side**: Hard to enforce across multiple services and languages.
- **API Gateway (Inbound)**: Protects our *own* API from our users, but doesn't help us limit our *outbound* calls to GitHub.
- **Sidecar (Outbound)**: All internal services route their GitHub API requests through this sidecar. It intercepts the request, checks the rate limit, and either forwards it to GitHub or returns a `429`.

## System Components
1. **Rate Limiter Middleware**: Intercepts outbound requests, extracts the user/token ID, and executes the limit check.
2. **Config Service**: A lightweight database or config file storing limits per user tier (e.g., Free: 5,000/hr, Enterprise: 15,000/hr).
3. **Redis Counter Store**: An in-memory datastore that holds the Token Bucket state (`tokens`, `last_refill_time`) for millions of users with sub-millisecond latency.
4. **Fallback Mechanism**: If Redis is unreachable, the system falls back to a local, in-memory cache to prevent a complete outage (fail-open strategy).

## Architecture Diagram

```mermaid
graph TD
    subgraph Internal Infrastructure
        Client[Internal Service] -->|1. Outbound Request| Gateway[Rate Limiter Sidecar]
        Gateway <-->|2. Fetch Limits| Config[Config Service]
        Gateway <-->|3. Check/Update Tokens| Redis[(Redis Cluster)]
    end

    Gateway -->|4a. Allowed| GitHub[GitHub REST API]
    Gateway -.->|4b. Rejected (429)| Client

    %% Fallback Flow
    Redis -.->|Redis Down| LocalCache[Local In-Memory Cache]
    Gateway -.->|Degraded Check| LocalCache