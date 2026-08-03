# EOSC ARENA Flower LLM Server

This repository contains a Flower-based Federated LLM server deployment intended to run on EOSC ARENA / AI4EOSC platform. Clients (SuperNodes) run on separate nodes and connect to the SuperLink (server) deployed on the platform.

## Overview
- **Server (SuperLink):** runs the Flower SuperLink process that accepts connections from SuperNodes. The provided script to start it is `start_superlink.sh`.
- **Clients (SuperNodes):** run on separate machines, each with its own local dataset. Clients connect to the deployed server and perform local training.

## Step-by step workflow:

1. Ensure the Flower CLI config file exists and points the `exec` API address to the SuperLink exec API. By default the file is: `$HOME/.flwr/config.toml` (in the server container this is usually `/root/.flwr/config.toml`).

2. Verify the config path with:

```
flwr config list
```

This prints the active Flower config file path (look for the line labeled `Flower Config file`). If the file does not exist you can initialize it with:

```
flwr config init
```

3. Update the config so that the `exec` API address matches the SuperLink `--exec-api-address` (the default used by `start_superlink.sh` is `127.0.0.1:9093`). Example `sed` commands used to update the config file:

```
sed -i \
  -e 's|address = "SUPERLINK_HOST:9093"|address = "127.0.0.1:9093"|' \
  -e '/root-certificates = "\/srv\/arena-fl-server-llm\/deploy\/certificates\/ca.crt"/d' \
  -e 's|insecure = false|insecure = true|' \
  $(flwr config list | grep "Flower Config file" | awk '{print $NF}')
```
Note that removing `root-certificates` and setting `insecure = true` disables certificate verification for the CLI (this is often necessary inside deployments where Traefik handles TLS). Use with caution.

4. Start the SuperLink on the server side (this script expects Traefik routing to terminate TLS):

```
cd arena-fl-server-llm
```

```
./start_superlink.sh
```

If you changed the config file after starting the SuperLink, stop and restart the SuperLink so any new `flwr` run use the updated configuration.

## Client-side (SuperNode) workflow:

1. On each client machine create and activate a Python virtual environment:

```
virtualenv .venv -p python3
source .venv/bin/activate
```

2. Install dependencies using the same `pyptoject.toml` file as in the server side:

```
pip install -e .
```

3. Each client must have its own local dataset (never centrally shared). Then run the SuperNode start script with the server route, the path to the local dataset, and the local port the SuperNode will expose. Example:

```
./start_supernode.sh fedserver-88face77-8b34-11f1-908b-771de29c9404.psnc-deployments.cloud.ai4eosc.eu data/eosc_sample.csv 9094
```

- The last argument `9094` is the local port used by the SuperNode and can be changed if needed (make sure it does not conflict with other services on the same machine).

## Starting a remote run and checking status

After the SuperLink is running on the server side and the clients (SuperNodes) have connected, start the federated run from the server container using the Flower CLI:

```
cd arena-fl-server-llm
flwr run . remote
```

Then, you can check the runs:

```
flwr run list
```

If you want to check the logs of an specific run: 

```
flwr log <run_ID>
```

## Recommendations
- Run `flwr config list` to locate the config file before editing.
- If the config file does not exist, run `flwr config init` (or run a `flwr` command) to create it, then perform the `sed` edits and start the SuperLink.
- Restart the SuperLink after modifying the config to ensure changes take effect.
- Keep each client's dataset private and isolated on the client node.

### Warning
This project is under active development. 

## License
This project is licensed under the [Apache 2.0 license](https://github.com/ai4os/arena-fl-server-llm/blob/main/LICENSE).

## Funding and acknowledgments
This work is funded by European Union through the EOSC-ARENA project (Horizon Europe) under Grant number [101292597](https://cordis.europa.eu/project/id/101292597).
<p>
<img align="center" width="250" src="https://raw.githubusercontent.com/AI4EOSC/.github/ai4eosc/profile/EN-Funded.jpg">
<img align="center" width="300" src="https://ai4eosc.eu/_astro/arena_logo_white.CRdi1OPK.png">
<p>
