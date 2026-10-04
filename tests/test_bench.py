from etrigan.bench import parse_benchmark_log

def test_parse_benchmark_log_success():
    # 50 tokens in 2.5 seconds (2,500,000,000 ns)
    # TTFT is 0.5 seconds (500,000,000 ns)
    metrics = {
        "eval_count": 50,
        "eval_duration": 2500000000,
        "prompt_eval_duration": 500000000
    }
    
    res = parse_benchmark_log(metrics)
    assert res["tokens_per_sec"] == 20.0  # 50 / 2.5
    assert res["ttft_ms"] == 500.0        # 500M ns = 500 ms

def test_parse_benchmark_log_error():
    metrics = {"error": "connection refused"}
    res = parse_benchmark_log(metrics)
    assert "error" in res
    assert res["error"] == "connection refused"

def test_parse_benchmark_log_zero_duration():
    metrics = {
        "eval_count": 10,
        "eval_duration": 0,
        "prompt_eval_duration": 0
    }
    res = parse_benchmark_log(metrics)
    assert res["tokens_per_sec"] == 0
    assert res["ttft_ms"] == 0
