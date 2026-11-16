import time
import threading

class TokenBucket:
    """A thread-safe Token Bucket rate limiter using standard library only."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self.lock = threading.Lock()  # Prevents race conditions

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        
        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

    def allow_request(self) -> bool:
        """Check if a request is allowed. If so, consume a token."""
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

def simulate_requests():
    # Setup: Capacity of 20 tokens, refilling at 5 tokens per second.
    # This simulates a strict API limit (e.g., 5 requests/sec burst up to 20).
    limiter = TokenBucket(capacity=20, refill_rate=5.0)
    
    allowed = 0
    blocked = 0
    lock = threading.Lock()

    def make_request(request_id):
        nonlocal allowed, blocked
        if limiter.allow_request():
            with lock:
                allowed += 1
            print(f"Request {request_id:03d}: [200 OK] Allowed")
        else:
            with lock:
                blocked += 1
            print(f"Request {request_id:03d}: [429 Too Many Requests] Blocked")

    print("Simulating 100 concurrent requests...")
    print("Bucket Capacity: 20 | Refill Rate: 5/sec")
    print("-" * 50)

    threads = []
    start_time = time.time()
    
    # Fire 100 requests nearly instantly
    for i in range(1, 101):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Wait for 2 seconds to let the bucket refill, then fire 15 more
    print("\nWaiting 2 seconds for tokens to refill...")
    time.sleep(2.0)
    
    print("\nSimulating 15 more requests after refill...")
    for i in range(101, 116):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads[-15:]:
        t.join()

    print("-" * 50)
    print(f"Total Requests: {allowed + blocked}")
    print(f"Allowed: {allowed}")
    print(f"Blocked: {blocked}")

if __name__ == "__main__":
    simulate_requests()