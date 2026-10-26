#!/usr/bin/env python3
from analytics_sketches_lab.hyperloglog import HyperLogLog

hll = HyperLogLog(precision=12)
true = 50_000
for i in range(true):
    hll.add(f"user-{i}")
print(f"True distinct: {true}, HLL estimate: {int(hll.estimate())}")
