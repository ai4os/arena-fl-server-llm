"""arena-fedllm: shared config utilities used by both server_app.py and
client_app.py. Kept separate from dataset.py on purpose, since it has
nothing to do with loading data -- the server needs this function but not 
the dataset which is only on the client's side."""


def replace_keys(input_dict, match="-", target="_"):
    """Recursively replace match string with target string in dictionary keys.

    Flower's run_config uses hyphenated keys (e.g. "num-server-rounds"), but
    omegaconf's DictConfig attribute access needs underscores
    ("num_server_rounds"). This converts one to the other.
    """
    new_dict = {}
    for key, value in input_dict.items():
        new_key = key.replace(match, target)
        if isinstance(value, dict):
            new_dict[new_key] = replace_keys(value, match, target)
        else:
            new_dict[new_key] = value
    return new_dict
