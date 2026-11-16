# 03 — Deep Dive on Trade-offs

## 1. Redis Failure Modes and Graceful Degradation
If the Redis cluster goes down, the Rate Limiter cannot definitively know if a user has exceeded their limit.

**Options:**
- **Fail-Closed:** Block all requests. (Ensures we never violate GitHub's limits, but causes a complete outage for our users).
- **Fail-Open:** Allow all requests. (Keeps the service running, but risks hitting GitHub's limits and getting our IP banned).

**Decision:** **Fail-Open with Local Fallback.**
If Redis is unreachable, the Sidecar immediately degrades to an in-memory, per-instance token bucket. This is less accurate (since multiple sidecar instances will each have their own local count), but it prevents a total outage. We log a high-severity alert to trigger an SRE investigation.

## 2. Race Conditions on Counter Increments
In a highly concurrent system, two requests might arrive at the exact same millisecond. If we do a standard `GET` (check tokens) followed by a `SET` (decrement tokens), both requests might read `tokens = 1`, and both will succeed (over-consuming the limit).

**Options:**
- **Optimistic Locking (WATCH/MULTI/EXEC):** Redis transactions. Can fail and require retries under high contention.
- **Lua Script:** Upload a script to Redis that executes the Read-Refill-Decrement logic atomically in a single thread.

**Decision:** **Lua Script.**
Redis executes Lua scripts atomically. By passing the user's state and the current timestamp to a Lua script, Redis guarantees no other command can interleave, completely eliminating race conditions without network round-trips for retries.

## 3. Per-User vs. Per-Token Limiting & Fairness
GitHub's limits apply to the *token* (or the user if unauthenticated).
- **Per-User:** If a user has 5 tokens, they could theoretically make 5x the requests. But it protects our system from a single user monopolizing resources.
- **Per-Token:** Matches GitHub's exact enforcement model, but allows a malicious user to rotate tokens to bypass our internal limits.

**Decision:** **Per-Token (mapped to User context).**
We enforce strictly per-token to mirror GitHub's limits, but we maintain a secondary, looser aggregate limit per-user to detect and block abuse (e.g., if a user spins up 50 tokens to scrape).

## 4. Algorithm Selection (Stuck-Detection Trigger Applied)
*Note: As per the challenge instructions, here is the documented decision for the algorithm choice.*

**Option A: Fixed Window** (Simple, but suffers from boundary bursts).
**Option B: Token Bucket** (Allows controlled bursts, slightly more complex state).

**Decision:** We chose **Token Bucket (Option B)**. 
**Justification:** GitHub's limits are designed to allow occasional bursts but enforce a long-term average. Token Bucket models this perfectly. The failure mode of Fixed Window (allowing 2x the traffic at the window boundary) is unacceptable for strict API compliance. Token Bucket requires storing a float (tokens) and a timestamp, which easily fits in Redis.