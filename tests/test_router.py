from etrigan.router.router import MemoryAwareRouter
from unittest import mock

@mock.patch("etrigan.router.router.check_ram")
def test_router_normal_memory(mock_ram):
    # 4GB available -> 4194304 kb
    mock_ram.return_value = (8000000, 4194304)
    router = MemoryAwareRouter()
    
    res = router.route("Write a python script")
    assert res["task_type"] == "code"
    assert res["keep_alive"] == "5m"
    assert "Memory is sufficient" in res["rationale"]

@mock.patch("etrigan.router.router.check_ram")
def test_router_low_memory_fallback(mock_ram):
    # 2GB available -> 2097152 kb
    mock_ram.return_value = (8000000, 2097152)
    router = MemoryAwareRouter()
    
    # We need to temporarily force a 3b model in config for the test
    router.local_models["code"] = "qwen2.5-coder:3b"
    
    res = router.route("Write a python script")
    assert res["task_type"] == "code"
    assert res["selected_model"] == "llama3.2:1b"
    assert res["fallback_triggered"] is True
    assert res["keep_alive"] == "0"
    assert "critically low" in res["rationale"]
    assert "keep_alive=0" in res["rationale"]

