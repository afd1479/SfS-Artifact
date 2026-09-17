# Shuffling for Safeguarding (SfS) — Raspberry Pi Testbed

This package contains the selected Python programs for running the SfS experiments on three Raspberry Pi devices. It is organized by physical device so that each Raspberry Pi has only the programs required for its role.


## Folder structure

~~~text
SfS_RaspberryPi_Testbed_v1.0/
├── Raspberry_Pi_1_Sender/
│   ├── sender.py
│   ├── sender_throughput.py
│   ├── README.md
│   └── requirements.txt
├── Raspberry_Pi_2_Receiver/
│   ├── receiver.py
│   ├── receiver_throughput.py
│   ├── README.md
│   └── requirements.txt
├── Raspberry_Pi_3_Attacker/
│   ├── ordinary_replay_attacker.py
│   ├── smart_replay_attacker.py
│   ├── README.md
│   └── requirements.txt
├── Permutation_Analysis/
│   ├── permutation_analysis.py
│   ├── README.md
│   └── requirements.txt
├── docs/
│   ├── RASPBERRY_PI_SETUP.md
│   ├── RUN_EXPERIMENTS.md
│   ├── PARAMETERS.md
│   ├── OUTPUTS_AND_PERFORMANCE.md
├── results/
│   └── README.md
├── requirements.txt
├── CITATION.cff
└── README.md
~~~

There is one main receiver program: `Raspberry_Pi_2_Receiver/receiver.py`. The separate `receiver_throughput.py` program instruments the same receiver-side processing for the performance experiment.

## Raspberry Pi roles

| Device | Role | Testbed IP | Programs |
|---|---|---:|---|
| Raspberry Pi 1 | Sender | `192.168.1.11` | `sender.py` or `sender_throughput.py` |
| Raspberry Pi 2 | Receiver | `192.168.1.12` | `receiver.py` or `receiver_throughput.py` |
| Raspberry Pi 3 | Attacker | `192.168.1.10` | One attacker program at a time |

All programs use UDP port `5005`. The sender transmits one copy of each packet to Raspberry Pi 2 and an identical copy to Raspberry Pi 3.

## First-time setup

1. Prepare the three Raspberry Pis by following [docs/RASPBERRY_PI_SETUP.md](docs/RASPBERRY_PI_SETUP.md).
2. Place the devices on the same isolated 2.4 GHz IBSS/ad-hoc network.
3. Assign the addresses shown above.
4. Synchronize all three system clocks with Chrony before collecting data.
5. Install the Python requirements within each role folder.
6. Confirm that the devices can ping one another.
7. Review [docs/PARAMETERS.md](docs/PARAMETERS.md) before changing any experimental value.

## Quick experiment sequence

Always start the receiver first, the selected attacker second, and the sender last.

### Legitimate traffic without an active attacker

On Raspberry Pi 2:

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver.py
~~~

On Raspberry Pi 1:

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender.py
~~~

After the sender finishes, press `Ctrl+C` on Raspberry Pi 2 so that the receiver saves its final workbook.

### Ordinary replay

1. Start `receiver.py` on Raspberry Pi 2.
2. Start `ordinary_replay_attacker.py` on Raspberry Pi 3.
3. Start `sender.py` on Raspberry Pi 1.
4. Allow the required replay period to complete.
5. Stop the attacker and receiver with `Ctrl+C`.

### Permutation-aware replay

1. Start `receiver.py` on Raspberry Pi 2.
2. Start `smart_replay_attacker.py` on Raspberry Pi 3.
3. Start `sender.py` on Raspberry Pi 1.
4. After all scheduled replays have been forwarded, stop the attacker and receiver with `Ctrl+C`.

Do not run both attacker programs at the same time. They both listen on UDP port `5005` on Raspberry Pi 3.

### Sender and receiver performance

1. Start `receiver_throughput.py` on Raspberry Pi 2.
2. Start `sender_throughput.py` on Raspberry Pi 1.
3. With the default `--packet-count 1000`, allow the receiver to stop
   automatically after processing 1,000 packets.

No attacker program is used for the baseline performance run. For the closest reproduction of the supplied sender behavior, keep Raspberry Pi 3 online at `192.168.1.10`, because `sender_throughput.py` still transmits its second packet copy to that address.

Detailed commands and expected outputs are provided in [docs/RUN_EXPERIMENTS.md](docs/RUN_EXPERIMENTS.md).

## Active experiment values

The supplied programs currently contain these values:

| Parameter | Active value |
|---|---:|
| Packet count | 1,000 |
| UDP port | 5005 |
| Mean-delay calibration | 0.29 s |
| Main receiver THV | 1,000 ms |
| Performance receiver THV | 300 ms |
| Ordinary replay delay | 3 s |
| Smart replay delay | 0.9 s |
| Attacker replay interval | Every 20th captured packet |
| Sequence length | 112 |
| Time quantization | `round()` |

The experimental data supplied with the paper were obtained using `round()`. A separate evaluation may use `floor()`, but sender, receiver, and smart attacker must then be changed consistently and the resulting output must be recorded as a new run.

## Generated files

The sender programs write:

- `sender_results.xlsx`

The receiver programs write:

- `receiver_results.xlsx`

These are the default filenames. Both sender and receiver programs support
`--output`, so evaluators can select run-specific filenames without editing the
source. Move or rename a default workbook before another run if `--output` was
not used. See [results/README.md](results/README.md).

## Performance interpretation

The reported throughput and latency values depend on the complete execution environment, including the Raspberry Pi model, Python and package versions, operating-system scheduling, CPU load, storage performance, Wi-Fi conditions, interference, packet loss, device placement, and clock synchronization.

The performance programs preserve their existing measurement boundaries. Do not move timers or remove workbook generation when comparing a new run with the supplied data.

## Permutation analysis

`Permutation_Analysis/permutation_analysis.py` is an offline analysis program. It does not run as part of the three-Raspberry-Pi packet exchange. Its README explains its inputs and generated CSV and plot files.

## Scaled analysis
For a short artifact evaluation using 100 packets per run, see
[docs/SCALED_EVALUATION.md](docs/SCALED_EVALUATION.md).

## Controlled-testbed scope

The programs use Python pickle for packet serialization and include an experimental RSA key pair in the source. Run them only on a controlled, isolated research network. The included key material and serialization format are not intended for production deployment.
