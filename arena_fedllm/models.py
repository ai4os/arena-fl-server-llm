import math
import os

import torch
from huggingface_hub import login
from omegaconf import DictConfig
from peft import (
    LoraConfig,
    get_peft_model,
    get_peft_model_state_dict,
    set_peft_model_state_dict,
)
from peft.utils import prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

# Mistral's attention/MLP projection layer names. These are the layers LoRA
# adapters are attached to; they work for Mistral-7B, Mistral-7B-Instruct,
# and Mixtral variants alike.
MISTRAL_LORA_TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def cosine_annealing(
    current_round: int,
    total_round: int,
    lrate_max: float = 0.001,
    lrate_min: float = 0.0,
) -> float:
    """Implement cosine annealing learning rate schedule."""

    cos_inner = math.pi * current_round / total_round
    return lrate_min + 0.5 * (lrate_max - lrate_min) * (1 + math.cos(cos_inner))


def get_model(model_cfg: DictConfig):
    """Load model with appropriate quantization config and other optimizations.

    Please refer to this example for `peft + BitsAndBytes`:
    https://github.com/huggingface/peft/blob/main/examples/fp4_finetuning/finetune_fp4_opt_bnb_peft.py

    Quantization (bitsandbytes) requires a GPU. This function is called on
    both the server (to derive the initial LoRA weight shapes and to save
    checkpoints -- it never actually trains) and on clients (which do train
    and benefit from the memory savings). On a machine without a GPU --
    typically the server -- quantization is skipped automatically and the
    model loads in full precision on CPU instead, since correctness (same
    LoRA structure/shapes) is all that's needed there, not training speed.
    """
    # Mistral models (e.g. mistralai/Mistral-7B-Instruct-v0.3) are gated on
    # the Hugging Face Hub. Accept the license on the model page, then set
    # the HF_TOKEN environment variable before launching the run.
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        login(token=hf_token, add_to_git_credential=False)

    has_gpu = torch.cuda.is_available()

    quantization_config = None
    if has_gpu:
        if model_cfg.quantization == 4:
            quantization_config = BitsAndBytesConfig(load_in_4bit=True)
        elif model_cfg.quantization == 8:
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        else:
            raise ValueError(
                f"Use 4-bit or 8-bit quantization. You passed: {model_cfg.quantization}/"
            )

    model = AutoModelForCausalLM.from_pretrained(
        model_cfg.name,
        quantization_config=quantization_config,
        torch_dtype=torch.bfloat16,
        token=hf_token,
    )

    if has_gpu:
        model = prepare_model_for_kbit_training(
            model, use_gradient_checkpointing=model_cfg.gradient_checkpointing
        )
    elif model_cfg.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    peft_config = LoraConfig(
        r=model_cfg.lora.peft_lora_r,
        lora_alpha=model_cfg.lora.peft_lora_alpha,
        lora_dropout=0.075,
        target_modules=MISTRAL_LORA_TARGET_MODULES,
        task_type="CAUSAL_LM",
    )

    return get_peft_model(model, peft_config)