#!/usr/bin/env python3
import time

from rate_limiter_lab.token_bucket import TokenBucket

bucket = TokenBucket.create(capacity=5, refill_rate=2)
for i in range(8):
    ok = bucket.allow()
    print(f"request {i}: {'OK' if ok else '429'}")
    time.sleep(0.2)
