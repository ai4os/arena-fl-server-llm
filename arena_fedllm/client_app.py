"""arena-fedllm: A Flower / FlowerTune app."""

# This file is available from the server side only for configuration 
# purposes. The processing of the data or any specific aspects 
# relating to it are not included.

import os
import warnings

from flwr.app import ArrayRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp
from flwr.common.config import unflatten_dict
from omegaconf import DictConfig
from peft import get_peft_model_state_dict, set_peft_model_state_dict
from trl import SFTConfig, SFTTrainer

from arena_fedllm.dataset import (
    get_tokenizer_and_data_collator_and_propt_formatting,
    load_local_data,
)
from arena_fedllm.models import cosine_annealing, get_model
from arena_fedllm.utils import replace_keys
from transformers import TrainingArguments

# Avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "true"
os.environ["RAY_DISABLE_DOCKER_CPU_WARNING"] = "1"
warnings.filterwarnings("ignore", category=UserWarning)


# Flower ClientApp
app = ClientApp()


@app.train()
def train(msg: Message, context: Context):
    """Train the model on local data."""
    # Parse config
    num_rounds = context.run_config["num-server-rounds"]
    cfg = DictConfig(replace_keys(unflatten_dict(context.run_config)))
    training_arguments = TrainingArguments(**cfg.train.training_arguments)

    # Each machine holds its own private data. Start this SuperNode with:
    #    flower-supernode --node-config="dataset-path='/path/on/this/machine.csv'"
    # No data is ever centralized or shared with other clients or the
    # server -- only the trained weights are.
    local_dataset_path = context.node_config.get("dataset-path")
    if not local_dataset_path:
        raise ValueError(
            "This client requires its own local dataset. Start the "
            "SuperNode with "
            "--node-config=\"dataset-path='/path/to/local.csv'\" "
            "(see scripts/start_supernode.sh)."
        )
    trainset = load_local_data(local_dataset_path)

    (
        tokenizer,
        data_collator,
        formatting_prompts_func,
    ) = get_tokenizer_and_data_collator_and_propt_formatting(cfg.model.name)

    # Load the model and initialize it with the received weights
    model = get_model(cfg.model)
    set_peft_model_state_dict(model, msg.content["arrays"].to_torch_state_dict())

    # Set learning rate for current round
    new_lr = cosine_annealing(
        msg.content["config"]["server-round"],
        num_rounds,
        cfg.train.learning_rate_max,
        cfg.train.learning_rate_min,
    )

    training_arguments.learning_rate = new_lr

    # Construct trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_arguments,
        max_seq_length=cfg.train.seq_length,
        train_dataset=trainset,
        formatting_func=formatting_prompts_func,
        data_collator=data_collator,
    )

    # Do local training
    results = trainer.train()

    # Construct and return reply Message
    model_record = ArrayRecord(get_peft_model_state_dict(model))
    metrics = {
        "train_loss": results.training_loss,
        "num-examples": len(trainset),
    }
    metric_record = MetricRecord(metrics)
    content = RecordDict({"arrays": model_record, "metrics": metric_record})
    return Message(content=content, reply_to=msg)