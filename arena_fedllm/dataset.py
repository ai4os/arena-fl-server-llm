"""arena-fedllm: A Flower / FlowerTune app.

The server imports this module but it has no access
to any client's local CSV data.
"""

import os

from datasets import load_dataset
from transformers import AutoTokenizer

try:
    from trl.trainer.sft_trainer import DataCollatorForCompletionOnlyLM
except ImportError:
    try:
        from trl.trainer import DataCollatorForCompletionOnlyLM
    except ImportError:
        from trl import DataCollatorForCompletionOnlyLM


def formatting_prompts_func(example):
    """Construct prompts from instruction/input/response columns."""
    output_texts = []
    mssg = (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request."
    )
    instructions = example.get("instruction", [])
    responses = example.get("response", [])
    inputs = example.get("input", [""] * len(instructions))

    for instruction, response, user_input in zip(instructions, responses, inputs):
        instruction_text = instruction.strip()
        if user_input:
            instruction_text = f"{instruction_text}\n{user_input}".strip()
        text = (
            f"{mssg}\n### Instruction:\n{instruction_text}\n"
            f"### Response: {response}"
        )
        output_texts.append(text)
    return output_texts


def get_tokenizer_and_data_collator_and_propt_formatting(model_name: str):
    """Get tokenizer, data_collator and prompt formatting."""
    # Gated models on the Hub need the same HF_TOKEN used in models.py.
    hf_token = os.environ.get("HF_TOKEN")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, use_fast=True, padding_side="right", token=hf_token
    )
    tokenizer.pad_token = tokenizer.eos_token
    response_template_with_context = "\n### Response:"
    response_template_ids = tokenizer.encode(
        response_template_with_context, add_special_tokens=False
    )[2:]
    
    data_collator = DataCollatorForCompletionOnlyLM(
        response_template=response_template_ids,
        tokenizer=tokenizer
    )

    return tokenizer, data_collator, formatting_prompts_func


def load_local_data(dataset_path: str):
    """Load a client's own private, local CSV file -- no partitioning, no
    sharing with other clients or the server.

    Each machine points at its own file, e.g. via:
        flower-supernode --node-config="dataset-path='/data/site_a.csv'"

    The file must contain "instruction" and "response" columns, plus an
    optional "input" column.
    """
    resolved_path = dataset_path
    if not os.path.exists(resolved_path):
        resolved_path = os.path.join(os.getcwd(), dataset_path)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(
            f"Could not find local CSV dataset at '{dataset_path}' or "
            f"'{resolved_path}'. Check the --node-config dataset-path used "
            "to start this SuperNode."
        )

    dataset = load_dataset("csv", data_files=resolved_path, split="train")

    missing_cols = {"instruction", "response"} - set(dataset.column_names)
    if missing_cols:
        raise ValueError(
            f"CSV dataset is missing required column(s): {missing_cols}. "
            f"Found columns: {dataset.column_names}"
        )
    return dataset