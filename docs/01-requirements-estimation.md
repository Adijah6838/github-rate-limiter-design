# 01 — Requirements & Estimation

## 1. Functional Requirements
- **Limit requests** per user (API token), per endpoint, and per time window (e.g., 5,000 requests per hour).
- **Reject requests** that exceed the limit with an HTTP `429 Too Many Requests`.
- **Return headers** on every response indicating the current limit, remaining requests, and reset time (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`).
- **Dynamic configuration**: Limits should be configurable without redeploying the service (e.g., different limits for free vs. enterprise users).

## 2. Non-Functional Requirements
- **Low Latency**: The rate limiter must add < 10 ms of overhead to the request path.
- **Distributed**: Must work across multiple API gateway instances (no single point of failure).
- **Resilient**: If the counter store (e.g., Redis) goes down, the system should degrade gracefully (fail-open) rather than blocking all traffic.
- **Accuracy**: Must prevent race conditions where multiple concurrent requests bypass the limit.

## 3. Back-of-the-Envelope Estimation
- **Traffic**: Assume 1,000,000 Daily Active Users (DAU). 
- **Requests**: Average 20 API calls per user per day = 20,000,000 requests/day.
- **QPS (Average)**: 20,000,000 / 86,400 seconds ≈ **231 QPS**.
- **QPS (Peak)**: Assuming a 3x peak multiplier, peak traffic is ≈ **700 QPS**.
- **Read/Write Ratio**: Every API request triggers a "write" to the rate limiter (to increment the counter/consume a token). This is extremely **write-heavy**.
- **Storage**: We only need to store state for active users. If 1M users are active, and each state requires ~100 bytes (User ID, Tokens, Timestamp), memory footprint is ~**100 MB**. This easily fits in RAM.

## 4. Algorithm Choice: Token Bucket
We evaluated **Fixed Window**, **Leaky Bucket**, and **Token Bucket**.

**Decision:** We will use the **Token Bucket** algorithm.

**Justification:**
- **Fixed Window** suffers from the "boundary problem" (a user can make 2x the limit by bursting at the end of one window and the start of the next).
- **Leaky Bucket** enforces a rigid output rate, which penalizes legitimate bursts of traffic.
- **Token Bucket** allows bursts up to the bucket capacity (great for GitHub API clients syncing data) while still enforcing a strict long-term average. It is also highly memory-efficient: we only need to store `{tokens: float, last_refill_timestamp: float}` per user.