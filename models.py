"""
models.py
 
Detects your computer's RAM and GPU (VRAM), then recommends and installs
the best local Ollama model for your hardware.
 
Setup (one time):
    pip install psutil
 
Run it:
    python models.py
 
Requires Ollama to already be installed and running (https://ollama.com).
"""
 
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
 
try:
    import psutil
except ImportError:
    print("Missing dependency. Run this first:\n    pip install psutil")
    sys.exit(1)
 
 
# ---------------------------------------------------------------------------
# Hardware detection
# ---------------------------------------------------------------------------
 
def get_ram_gb() -> float:
    """Total system RAM in GB."""
    return round(psutil.virtual_memory().total / (1024 ** 3), 1)
 
 
def get_vram_gb() -> float | None:
    """
    Best-effort GPU VRAM detection in GB.
    Returns None if no GPU could be detected (assume CPU-only).
    """
    # Try NVIDIA first (works on Windows/Linux/Mac if drivers installed)
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            mb = int(out.stdout.strip().splitlines()[0])
            return round(mb / 1024, 1)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
 
    # Try AMD/other GPUs on Windows via the registry (works for most vendors)
    if platform.system() == "Windows":
        try:
            import winreg
            base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as key:
                i = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(key, i)
                    except OSError:
                        break
                    i += 1
                    try:
                        with winreg.OpenKey(key, sub_name) as sub_key:
                            mem_bytes, _ = winreg.QueryValueEx(sub_key, "HardwareInformation.qwMemorySize")
                            if mem_bytes:
                                return round(mem_bytes / (1024 ** 3), 1)
                    except (FileNotFoundError, OSError):
                        continue
        except Exception:
            pass
 
    # Try AMD ROCm on Linux
    try:
        out = subprocess.run(["rocm-smi", "--showmeminfo", "vram"], capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            match = re.search(r"Total.*?(\d+)\s*MB", out.stdout)
            if match:
                return round(int(match.group(1)) / 1024, 1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
 
    return None  # couldn't detect a GPU -> treat as CPU-only
 
 
# ---------------------------------------------------------------------------
# Model catalog + recommendation logic
# ---------------------------------------------------------------------------
 
CATALOG = {
    "gpu_16gb_code":  ("devstral-small-2",   "Best local coding model that fits 16GB VRAM (68% SWE-Bench Verified)."),
    "gpu_16gb_chat":  ("qwen3.5:9b",         "Fast, capable, multimodal chat model with room to spare on 16GB VRAM."),
    "gpu_16gb_both":  ("gpt-oss:20b",        "Best all-rounder for chat + coding on a 16GB GPU."),
    "gpu_8gb_code":   ("qwen2.5-coder:7b",   "Strong coding model that fits comfortably in 8GB VRAM."),
    "gpu_8gb_chat":   ("llama3.1:8b",        "Well-rounded chat model for an 8GB GPU."),
    "gpu_8gb_both":   ("llama3.1:8b",        "Solid all-rounder for chat + coding on 8GB VRAM."),
    "ram_16gb_code":  ("qwen2.5-coder:7b",   "Best coding model for 16GB RAM, CPU-only."),
    "ram_16gb_chat":  ("qwen3.5:9b",         "Best chat model for 16GB RAM, CPU-only."),
    "ram_16gb_both":  ("qwen3.5:9b",         "Best all-rounder for 16GB RAM, CPU-only."),
    "ram_8gb_code":   ("qwen3:4b",           "Best small coding model for 8GB RAM, CPU-only."),
    "ram_8gb_chat":   ("qwen3:4b",           "Best small chat model for 8GB RAM, CPU-only."),
    "ram_8gb_both":   ("qwen3:4b",           "Best all-rounder for 8GB RAM, CPU-only."),
    "ram_low":        ("qwen3:1.7b",         "Very lightweight model for limited RAM."),
}
 
 
def recommend(ram_gb: float, vram_gb: float | None, priority: str) -> tuple[str, str]:
    if vram_gb and vram_gb >= 16:
        tier = "gpu_16gb"
    elif vram_gb and vram_gb >= 8:
        tier = "gpu_8gb"
    elif ram_gb >= 16:
        tier = "ram_16gb"
    elif ram_gb >= 8:
        tier = "ram_8gb"
    else:
        return CATALOG["ram_low"]
 
    return CATALOG[f"{tier}_{priority}"]
 
 
# ---------------------------------------------------------------------------
# Install + wire up main.py
# ---------------------------------------------------------------------------
 
def pull_model(model_name: str) -> bool:
    if shutil.which("ollama") is None:
        print("Ollama isn't installed or not on PATH. Install it from https://ollama.com first.")
        return False
 
    print(f"\nPulling {model_name} ... (this can take a while, it's downloading several GB)\n")
    result = subprocess.run(["ollama", "pull", model_name])
    return result.returncode == 0
 
 
def update_main_py(model_name: str):
    main_py = Path("main.py")
    if not main_py.exists():
        return
    text = main_py.read_text()
    new_text, count = re.subn(r'MODEL\s*=\s*".*?"', f'MODEL = "{model_name}"', text)
    if count:
        answer = input(f"\nFound main.py — update its MODEL to \"{model_name}\"? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            main_py.write_text(new_text)
            print("main.py updated.")
 
 
# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
 
def main():
    print("Detecting your hardware...")
    ram_gb = get_ram_gb()
    vram_gb = get_vram_gb()
 
    print(f"  System RAM: {ram_gb} GB")
    print(f"  GPU VRAM:   {vram_gb} GB" if vram_gb else "  GPU VRAM:   not detected (will assume CPU-only)")
 
    print("\nWhat do you mainly want the model for?")
    print("  1) Chat / general Q&A")
    print("  2) Coding")
    print("  3) Both equally")
    choice = input("Enter 1, 2, or 3: ").strip()
    priority = {"1": "chat", "2": "code", "3": "both"}.get(choice, "both")
 
    model_name, reason = recommend(ram_gb, vram_gb, priority)
    print(f"\nRecommended model: {model_name}")
    print(f"  -> {reason}")
 
    answer = input(f"\nPull \"{model_name}\" now? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        if pull_model(model_name):
            print(f"\n{model_name} installed successfully.")
            update_main_py(model_name)
        else:
            print("\nSomething went wrong during the pull. Scroll up for the error.")
    else:
        print(f"\nSkipped. You can install it later with:\n    ollama pull {model_name}")
 
 
if __name__ == "__main__":
    main()