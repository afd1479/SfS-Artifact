# Raspberry Pi 1 — Sender

Assign this device the testbed address `192.168.1.11/24`.

## Files

| File | Purpose |
|---|---|
| `sender.py` | Main 1,000-packet sender used for legitimate, ordinary-replay, and smart-replay runs |
| `sender_throughput.py` | Instrumented sender used for sender-throughput measurements |
| `requirements.txt` | Python dependencies for this device |

## Installation

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 -m pip install -r requirements.txt
~~~

## Main sender

Run:

~~~bash
python3 sender.py
~~~

The command above uses the published defaults. To set the endpoints, packet
count, or output workbook explicitly, use:

~~~bash
python3 sender.py \
  --receiver-ip 192.168.1.12 \
  --attacker-ip 192.168.1.10 \
  --port 5005 \
  --packet-count 1000 \
  --output sender_results.xlsx
~~~

The program:

1. generates 1,000 messages;
2. derives the sequence from the sending time;
3. creates and signs the shuffled packet;
4. serializes the packet with pickle;
5. sends an identical serialized copy to the receiver and attacker; and
6. writes `sender_results.xlsx` in the current directory.

### Values to check before a run

Run `python3 sender.py --help` to list the available arguments. Change the IP
addresses only if the Raspberry Pi addresses differ from the documented
testbed, and keep the same UDP port in the sender, receiver, and selected
attacker. Use `--packet-count` for a different run size and `--output` to avoid
overwriting a previous workbook.

The supplied data use:

~~~python
current_time = round(sending_time)
~~~

If `floor()` is evaluated in a separate run, make the corresponding quantization change in the receiver and smart attacker as well. Do not mix `round()` and `floor()` across the devices.

The configured sender latitude, longitude, and altitude are packet metadata. The supplied receiver uses the calibrated 0.29 s mean delay for its active sending-time estimate.

## Throughput sender

For a performance run:

~~~bash
python3 sender_throughput.py \
  --receiver-ip 192.168.1.12 \
  --attacker-ip 192.168.1.10 \
  --port 5005 \
  --packet-count 1000 \
  --output sender_results.xlsx
~~~

Use it with `receiver_throughput.py` on Raspberry Pi 2. This sender reports:

- average signing, sequence-generation, and shuffling time;
- theoretical signing throughput; and
- total sender throughput.

It writes `sender_results.xlsx` by default. Run
`python3 sender_throughput.py --help` for the complete option list, including
the sender-coordinate metadata arguments.

The program still sends an identical second copy to `192.168.1.10`. No attacker process should run during the baseline performance measurement, but keeping Raspberry Pi 3 connected at that address most closely preserves the intended network path.

The total sender-throughput interval follows the measurement boundaries already present in the program. It includes the surrounding Python execution, serialization, UDP transmission, result collection, and workbook creation that occur before the final timer is read.

## Preserve outputs

Both programs default to the same output filename. Use `--output` to select a
run-specific workbook, or rename or move `sender_results.xlsx` before starting
another experiment.
