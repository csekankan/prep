#!/usr/bin/env python3
from rich.console import Console

from inference_scheduler_lab.simulator import InferenceSimulator, Request, kv_gib_for_prompt

console = Console()


def main() -> None:
    sim = InferenceSimulator(kv_pool_gib=10.0)
    for i in range(5):
        pt = 8192
        sim.submit(
            Request(
                req_id=f"r{i}",
                prompt_tokens=pt,
                completion_tokens=50,
                kv_gib=kv_gib_for_prompt(pt),
            )
        )
    m = sim.run_until_done()
    console.print(f"Completed {m.completed} requests; peak KV {m.peak_kv_gib:.2f} GiB (pool=10)")
    console.print(f"Still queued: {len(sim.queue)} — KV pool limits concurrency, not FLOPs")


if __name__ == "__main__":
    main()
