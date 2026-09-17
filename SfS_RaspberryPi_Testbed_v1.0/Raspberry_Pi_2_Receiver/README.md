# Raspberry Pi 2 — Receiver

Assign this device the testbed address `192.168.1.12/24`.

## Files

| File | Purpose |
|---|---|
| `receiver.py` | The single main receiver for legitimate, ordinary-replay, smart-replay, and THV runs |
| `receiver_throughput.py` | Instrumented receiver for throughput and latency measurements |
| `requirements.txt` | Python dependencies for this device |

## Installation

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 -m pip install -r requirements.txt
~~~

## Main receiver

Start this program before the attacker and sender:

~~~bash
python3 receiver.py \
  --bind-ip 0.0.0.0 \
  --port 5005 \
  --thv-ms 1000 \
  --mean-delay-s 0.29 \
  --output receiver_results.xlsx
~~~

It binds to `0.0.0.0:5005`, receives packets, reconstructs the indexed binary payload, generates its candidate sequences locally, verifies the signature, and records the result.

The default sending-time estimate is:

~~~python
computed_seed = receiving_time - 0.29
~~~

The 0.29 s value is the mean delay measured from 1,000 calibration packets in
the laboratory setup. For a materially different testbed, first run a
synchronized calibration and pass the new value with `--mean-delay-s`.

Use `--thv-ms` for each THV run; do not edit the source file. The receiver
evaluates the two candidate time points implemented in this program:

~~~text
estimated sending time - THV
estimated sending time + THV
~~~

The supplied data use `round()` when converting each candidate time to its sequence seed.

The transmitted packet timestamp and sequence are recorded for measurements and comparison. Packet acceptance is based on sequences generated locally by the receiver.

Press `Ctrl+C` after the run. The receiver then writes the final workbook and prints its summary.

## Throughput receiver

For a performance run:

~~~bash
python3 receiver_throughput.py \
  --bind-ip 0.0.0.0 \
  --port 5005 \
  --packet-count 1000 \
  --thv-ms 300 \
  --mean-delay-s 0.29 \
  --output receiver_results.xlsx
~~~


This program reports:

- average verification time;
- theoretical verification throughput;
- receiver throughput;
- average end-to-end latency; and
- 95th-percentile latency.

Start it before `sender_throughput.py`. With the default `--packet-count 1000`,
it stops automatically after processing 1,000 packets, saves the final
workbook, and prints the summaries. Use `--packet-count 0` only when an
unbounded run that is stopped with `Ctrl+C` is required. Run
`python3 receiver_throughput.py --help` for checkpoint, buffer, and coordinate
options.

## Coordinates

The programs contain configured sender and receiver coordinates, but the active estimate uses the calibrated 0.29 s mean delay. Merely changing the coordinates does not change the active timing estimate.

## Preserve outputs

Both receiver programs default to `receiver_results.xlsx` in the current
directory and checkpoint it every ten packets. Use `--output` for a
run-specific filename. The throughput receiver also supports `--save-every`.

The receiver unpickles UDP data. Run it only on the isolated testbed network.
