import os
import sys
import shutil
import subprocess

def check_ram(meminfo_path="/proc/meminfo"):
    """Parses meminfo and returns (total_kb, available_kb)."""
    if not os.path.exists(meminfo_path):
        return None, None
    total, available = None, None
    try:
        with open(meminfo_path, "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    available = int(line.split()[1])
    except Exception:
        pass
    return total, available

def check_gpu():
    """Runs nvidia-smi and returns (gpu_name, free_vram_mb) or (None, None)."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.free", "--format=csv,noheader"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if out:
            parts = out.split(", ")
            if len(parts) == 2:
                name = parts[0]
                free_str = parts[1].replace(" MiB", "")
                return name, int(free_str)
    except Exception:
        pass
    return None, None

def check_disk(path="/mnt/d"):
    """Returns free space in GB for the given path."""
    try:
        usage = shutil.disk_usage(path)
        return usage.free / (1024**3)
    except Exception:
        return None

def check_dependencies():
    """Checks for required external tools."""
    deps = {
        "ollama": shutil.which("ollama") or (os.path.exists("./bin/ollama") and "./bin/ollama") or None,
        "soup": shutil.which("soup"),
        "herdr": shutil.which("herdr")
    }
    return deps

def get_python_version():
    return sys.version_info
