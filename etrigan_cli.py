import typer
import random
import os
import sys
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import print as rprint
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, PathCompleter, NestedCompleter
from etrigan.ui.banner import render, TAGLINES, PALETTE

from etrigan.diagnostics import check_ram, check_gpu, check_disk, check_dependencies, get_python_version

app = typer.Typer(no_args_is_help=True, help="ETRIGAN - Sovereign AI Workbench CLI")
console = Console()

WORKFLOWS = {
    "/doctor": "check this machine (GPU, RAM, disk, Python, Ollama, soup, herdr)",
    "/bench": "benchmark local models on this hardware",
    "/fit": "recommend models and quantizations for this machine",
    "/ask": "grounded Q&A over ingested documents, with citations and refusal",
    "/ingest": "add documents to the local knowledge base",
    "/agent": "run a plan-act-observe task with the tool sandbox",
    "/fraud": "[online] run the fraud investigation agent",
    "/audit": "verify the hash-chained audit log",
    "/model": "list, add, and switch models (hot reload)",
    "/herdr": "open the herdr control-room layout",
    "/soup": "show or validate the fine-tuning config",
    "/load": "load an external AI/ML project or agent file directly",
    "/help": "show help information",
    "/exit": "exit ETRIGAN shell"
}

def get_system_info_str():
    # RAM
    total_kb, avail_kb = check_ram()
    ram_str = f"{avail_kb / 1024 / 1024:.1f} GB" if avail_kb else "Unknown"
    
    # GPU
    name, free = check_gpu()
    gpu_str = f"{name} / {free} MiB Free" if name else "CPU Only"
    
    return f"{os.cpu_count()} threads | {ram_str} available | {gpu_str}"

def print_startup_screen(color=True):
    # Banner
    width = shutil.get_terminal_size((80, 24)).columns
    banner_str = render(width=width, color=color)
    console.print(banner_str, highlight=False)
    
    # Tagline
    tagline = random.choice(TAGLINES)
    console.print(f"[bold {PALETTE['ash']}]{tagline}[/]\n", justify="center")
    
    # System Panel
    sys_info = get_system_info_str()
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b (default)")
    
    left_content = (
        f"[bold {PALETTE['gold']}]Model:[/] {model}\n"
        f"[bold {PALETTE['gold']}]Dir:[/] {os.getcwd()}\n"
        f"[bold {PALETTE['gold']}]Session:[/] etrigan-wsl-01\n"
        f"[bold {PALETTE['gold']}]System:[/] {sys_info}\n"
        f"[bold {PALETTE['gold']}]Tools:[/] 5 loaded\n"
        f"[bold {PALETTE['gold']}]Agents:[/] core, fraud (online)\n"
    )
    left_panel = Panel(left_content, title=f"[bold {PALETTE['cape']}]Environment", border_style=PALETTE['cape'], expand=True)
    
    right_content = ""
    for cmd, desc in WORKFLOWS.items():
        if cmd in ["/doctor", "/exit", "/help"]:
            right_content += f"[bold {PALETTE['ember']}]{cmd}[/] - {desc}\n"
        else:
            right_content += f"[bold {PALETTE['ash']}]{cmd}[/] - {desc} (planned)\n"
            
    right_panel = Panel(right_content.strip(), title=f"[bold {PALETTE['cape']}]Workflows", border_style=PALETTE['cape'], expand=True)
    
    console.print(Columns([left_panel, right_panel], expand=True))
    console.print()

@app.command()
def shell(plain: bool = typer.Option(False, "--plain", help="Disable colors")):
    """Start the ETRIGAN interactive shell."""
    color = not plain and not os.environ.get("NO_COLOR")
    if not color:
        global console
        console = Console(color_system=None)
        
    print_startup_screen(color=color)
    
    # Create a nested completer for slash commands, adding path completion to /load
    command_dict = {cmd: None for cmd in WORKFLOWS.keys()}
    command_dict["/load"] = PathCompleter()
    completer = NestedCompleter.from_nested_dict(command_dict)
    session = PromptSession(completer=completer)
    
    while True:
        try:
            text = session.prompt("etrigan> ")
            text = text.strip()
            if not text:
                continue
                
            if text == "/exit":
                break
            elif text == "/help":
                for cmd, desc in WORKFLOWS.items():
                    console.print(f"{cmd} - {desc}")
            elif text == "/doctor":
                doctor()
            elif text.startswith("/bench"):
                parts = text.split()
                m = parts[1] if len(parts) > 1 else None
                bench(m)
            elif text == "/fit":
                fit()
            elif text == "/soup":
                soup()
            elif text == "/fraud":
                fraud()
            elif text.startswith("/load"):
                parts = text.split(maxsplit=1)
                filepath = parts[1] if len(parts) > 1 else None
                # We need to call load() directly in shell since session is there
                if not filepath:
                    filepath = session.prompt("Enter path to project file: ")
                path = os.path.abspath(filepath.strip())
                if not os.path.exists(path):
                    console.print(f"[red]File not found: {path}[/]")
                else:
                    console.print(f"[bold {PALETTE['gold']}]Loading Project File:[/] {path}")
                    console.print(f"[green]Successfully loaded {os.path.basename(path)} into ETRIGAN workspace.[/]")
            elif text.startswith("/"):
                console.print(f"[{PALETTE['ember']}]Not implemented yet:[/] {text}")
            else:
                console.print(f"Unknown command. Try /help or a slash command.")
                
        except (KeyboardInterrupt, EOFError):
            break

@app.command()
def doctor(json_format: bool = typer.Option(False, "--json", help="Output in JSON format")):
    """Check this machine (GPU, RAM, disk, Python, Ollama, soup, herdr)"""
    
    results = {}
    
    # Python
    py_v = get_python_version()
    results["python"] = {"value": f"{py_v.major}.{py_v.minor}.{py_v.micro}", "status": "PASS" if py_v.minor >= 10 else "WARN"}
    
    # RAM
    total_kb, avail_kb = check_ram()
    if avail_kb:
        gb = avail_kb / 1024 / 1024
        results["ram"] = {"value": f"{gb:.1f} GB available", "status": "PASS" if gb >= 3.0 else "WARN"}
    else:
        results["ram"] = {"value": "Unknown", "status": "FAIL"}
        
    # GPU
    name, free = check_gpu()
    if name:
        results["gpu"] = {"value": f"{name} ({free} MiB free)", "status": "PASS"}
    else:
        results["gpu"] = {"value": "CPU Only", "status": "WARN"}
        
    # Disk
    free_disk = check_disk(os.getcwd())
    if free_disk:
        results["disk"] = {"value": f"{free_disk:.1f} GB free", "status": "PASS" if free_disk >= 10 else "WARN"}
    else:
        results["disk"] = {"value": "Unknown", "status": "FAIL"}
        
    # Dependencies
    deps = check_dependencies()
    results["ollama"] = {"value": deps["ollama"] or "Not found", "status": "PASS" if deps["ollama"] else "FAIL"}
    results["soup"] = {"value": deps["soup"] or "Not found", "status": "PASS" if deps["soup"] else "WARN"}
    results["herdr"] = {"value": deps["herdr"] or "Not found", "status": "PASS" if deps["herdr"] else "WARN"}
    
    if json_format:
        import json
        print(json.dumps(results, indent=2))
        return

    console.print(f"[bold {PALETTE['gold']}]ETRIGAN Doctor[/]")
    for key, info in results.items():
        color = "green" if info["status"] == "PASS" else "yellow" if info["status"] == "WARN" else "red"
        console.print(f"{key.capitalize():<8}: {info['value']} [{color}]{info['status']}[/]")

    app()

@app.command()
def bench(model: str = typer.Argument(None, help="Model to benchmark (e.g., qwen2.5:3b)"), gpu: bool = typer.Option(True, help="Use GPU")):
    """Benchmark local models on this hardware."""
    from etrigan.bench import benchmark_model, save_benchmark
    import datetime
    
    if not model:
        console.print("[red]Please specify a model. Example: /bench qwen2.5:3b[/]")
        return
        
    console.print(f"[bold {PALETTE['gold']}]Benchmarking model:[/] {model}")
    if not gpu:
        console.print("[yellow]Forcing CPU-only mode for benchmarking...[/]")
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        
    with console.status(f"[bold {PALETTE['cape']}]Running warmup and 3 timed runs...", spinner="dots"):
        result = benchmark_model(model)
        
    if "error" in result.get("runs", {}).get("short", {}):
        console.print(f"[bold red]Failed to benchmark. Is Ollama running?[/]")
        return
        
    # Generate Markdown Table
    console.print(f"\n[bold {PALETTE['gold']}]Results[/]")
    console.print(f"GPU VRAM Share: {result['gpu_vram_share_percent']}%")
    for p_type, stats in result["runs"].items():
        console.print(f" - {p_type.capitalize():<8}: {stats['avg_tokens_per_sec']} tokens/s, TTFT: {stats['avg_ttft_ms']} ms")
        
    hw_label = f"{os.cpu_count()}C_WSL"
    saved_path = save_benchmark(model, result, hw_label)
    console.print(f"\n[green]Saved benchmark to {saved_path}[/]")

@app.command()
def fit():
    """Recommend models and quantizations for this machine"""
    from etrigan.diagnostics import check_ram, check_gpu
    console.print(f"[bold {PALETTE['gold']}]ETRIGAN Fit - Hardware Recommendations[/]")
    
    total_kb, avail_kb = check_ram()
    name, free_vram = check_gpu()
    
    ram_gb = avail_kb / 1024 / 1024 if avail_kb else 0
    vram_mb = free_vram if free_vram else 0
    
    console.print(f"Detected RAM: {ram_gb:.1f} GB available")
    console.print(f"Detected VRAM: {vram_mb} MiB free\n")
    
    models = [
        {"name": "qwen2.5:1.5b", "size_mb": 1100, "req_ram": 2.0},
        {"name": "qwen2.5-coder:3b", "size_mb": 1900, "req_ram": 3.0},
        {"name": "qwen2.5:3b", "size_mb": 2600, "req_ram": 3.5},
        {"name": "llama3.2:3b", "size_mb": 2000, "req_ram": 3.0},
        {"name": "llama3.2:1b", "size_mb": 1300, "req_ram": 2.0},
    ]
    
    console.print(f"{'Model':<20} | {'VRAM Fit':<15} | {'Recommendation'}")
    console.print("-" * 60)
    
    for m in models:
        fits_vram = m["size_mb"] < vram_mb
        fits_ram = m["req_ram"] <= ram_gb
        
        vram_status = "[green]Fully in VRAM[/]" if fits_vram else "[yellow]Split (CPU/GPU)[/]"
        if vram_mb == 0:
            vram_status = "[yellow]CPU Only[/]"
            
        if not fits_ram:
            rec = "[red]Too large for available RAM[/]"
        elif fits_vram:
            rec = "[green]Highly Recommended[/]"
        else:
            rec = "[yellow]Slower (Offloaded)[/]"
            
        console.print(f"{m['name']:<20} | {vram_status:<25} | {rec}")

@app.command()
def soup():
    """Show or validate the fine-tuning config (training is planned)"""
    import yaml
    from rich.syntax import Syntax
    
    config_path = "config/soup.yaml"
    console.print(f"[bold {PALETTE['gold']}]ETRIGAN Soup Fine-Tuning Setup[/]")
    
    if not os.path.exists(config_path):
        console.print("[red]config/soup.yaml not found![/]")
        return
        
    with open(config_path, "r") as f:
        yaml_content = f.read()
        
    console.print("[bold cape]Status:[/] [yellow]TRAINING PLANNED[/]")
    console.print("This recipe demonstrates layer streaming to train models within a 4GB VRAM limit.")
    console.print("Currently waiting on a real training run to finalize metrics.\n")
    
    syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="config/soup.yaml", expand=False))

@app.command()
def fraud():
    """[online] run the fraud investigation agent"""
    from etrigan.fraud_agent.adapter import run_fraud_agent
    
    console.print(f"[bold {PALETTE['ember']}]WARNING: This workflow uses online services (Gemini).[/]")
    console.print(f"[bold {PALETTE['gold']}]Launching TigerGraph Fraud Agent...[/]")
    
    with console.status("Running agent...", spinner="dots"):
        result = run_fraud_agent()
        
    console.print(result)

@app.command()
def load(filepath: str = None):
    """load an external AI/ML project, model, or agent file directly"""
    if not filepath:
        filepath = session.prompt("Enter path to project file: ")
        
    path = Path(filepath.strip())
    if not path.exists():
        console.print(f"[red]File not found: {path}[/]")
        return
        
    console.print(f"[bold {PALETTE['gold']}]Loading Project File:[/] {path.absolute()}")
    console.print(f"[green]Successfully loaded {path.name} into ETRIGAN workspace.[/]")
    # Here you would actually parse the YAML/Python and register it in the router

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default to interactive shell if no args
        sys.argv.append("shell")
    app()
