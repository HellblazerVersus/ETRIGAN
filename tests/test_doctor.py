import os
import tempfile
from unittest import mock
from etrigan.diagnostics import check_ram, check_gpu, check_disk, check_dependencies, get_python_version

def test_check_ram_success():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("MemTotal:        3916404 kB\nMemFree:         2704184 kB\nMemAvailable:    3059520 kB\n")
        temp_path = f.name
    
    try:
        total, available = check_ram(temp_path)
        assert total == 3916404
        assert available == 3059520
    finally:
        os.remove(temp_path)

def test_check_ram_missing_file():
    total, available = check_ram("/does/not/exist/meminfo")
    assert total is None
    assert available is None

@mock.patch("subprocess.check_output")
def test_check_gpu_success(mock_check_output):
    mock_check_output.return_value = "NVIDIA GeForce RTX 2050, 2969 MiB\n"
    name, free = check_gpu()
    assert name == "NVIDIA GeForce RTX 2050"
    assert free == 2969

@mock.patch("subprocess.check_output")
def test_check_gpu_failure(mock_check_output):
    mock_check_output.side_effect = FileNotFoundError()
    name, free = check_gpu()
    assert name is None
    assert free is None

@mock.patch("shutil.disk_usage")
def test_check_disk(mock_disk_usage):
    import collections
    Usage = collections.namedtuple('usage', 'total used free')
    mock_disk_usage.return_value = Usage(total=100*(1024**3), used=20*(1024**3), free=80*(1024**3))
    free_gb = check_disk("/mnt/d")
    assert free_gb == 80.0

@mock.patch("shutil.which")
@mock.patch("os.path.exists")
def test_check_dependencies(mock_exists, mock_which):
    # Mock global commands not found, but local ollama exists
    mock_which.return_value = None
    mock_exists.return_value = True
    
    deps = check_dependencies()
    assert deps["ollama"] == "./bin/ollama"
    assert deps["soup"] is None
    assert deps["herdr"] is None
    
    # Mock herdr found globally
    def which_side_effect(cmd):
        if cmd == "herdr": return "/usr/bin/herdr"
        return None
    mock_which.side_effect = which_side_effect
    
    deps = check_dependencies()
    assert deps["herdr"] == "/usr/bin/herdr"

def test_get_python_version():
    v = get_python_version()
    assert v.major == 3
    assert v.minor >= 10
