"""arena-fl-server-llm: A FlowerTune app for real distributed federated LLM fine-tuning."""

import logging
import os

os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")
os.environ.setdefault("RAY_DISABLE_DOCKER_CPU_WARNING", "1")
os.environ.setdefault("RAY_DISABLE_IMPORT_WARNING", "1")

logging.getLogger("ray").setLevel(logging.ERROR)
logging.getLogger("ray._private").setLevel(logging.ERROR)
