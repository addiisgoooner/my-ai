"""
models.py

Reference list of small/local LLMs to run with Ollama, organized by
hardware tier. Built while upgrading a local Ollama + FastAPI chat app.

To use a model:
    1. Pull it:      ollama pull <model_name>
    2. Update main.py:   MODEL = "<model_name>"

Run this file directly to print a readable list:
    python models.py
"""

MODELS = {
    "8gb_ram_cpu_only": {
        "qwen3:4b": "Best all-rounder for chat + code. ~2.5GB. Has a /think mode for harder problems.",
        "phi4-mini": "Fastest on CPU, strong at reasoning and debugging. ~3.8B params.",
        "gemma3:4b": "Google's small model. Well-rounded chat + code, similar size to Qwen3:4B.",
    },

    "16gb_ram_cpu_only": {
        "qwen3.5:9b": "Best all-rounder. Multimodal, 262K context, has a thinking mode.",
        "qwen2.5-coder:7b": "Best for coding specifically. 80.1% on the HumanEval benchmark.",
        "llama3.1:8b": "Stays in the Llama family. Widest ecosystem/tutorial support.",
    },

    "16gb_vram_gpu": {
        "gpt-oss:20b": "Best all-rounder for a 16GB GPU. Strong reasoning + agentic tasks. OpenAI open-weights.",
        "devstral-small-2": "Best local coding model for 16GB VRAM. 68.0% SWE-Bench Verified. "
                             "Uses most of the VRAM, so long conversations can run out of headroom.",
        "qwen3.5:9b": "Fastest pick if 20B/24B models feel slow. Still a big step up from a 3B model.",
    },
}


def print_models():
    for tier, models in MODELS.items():
        print(f"\n{tier.replace('_', ' ').upper()}")
        print("-" * len(tier))
        for name, description in models.items():
            print(f"  ollama pull {name}")
            print(f"    -> {description}\n")


if __name__ == "__main__":
    print_models()
