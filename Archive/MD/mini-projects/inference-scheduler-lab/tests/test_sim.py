from inference_scheduler_lab.simulator import InferenceSimulator, Request, kv_gib_for_prompt


def test_only_three_8k_fit_in_10gib_pool() -> None:
    sim = InferenceSimulator(kv_pool_gib=10.0)
    kv = kv_gib_for_prompt(8192)
    for i in range(4):
        sim.submit(Request(f"r{i}", 8192, 1, kv))
    sim.run_until_done(max_ticks=500)
    assert sim.metrics.completed == 4
    assert sim.metrics.peak_kv_gib <= 10.0 + 0.01
