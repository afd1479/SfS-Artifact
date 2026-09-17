# Raspberry Pi 3 — Attacker

Assign this device the testbed address `192.168.1.10/24`.

## Files

| File | Purpose |
|---|---|
| `ordinary_replay_attacker.py` | Selects captured packets, delays them, and retransmits the same UDP datagram |
| `smart_replay_attacker.py` | Selects every 20th captured packet, derives its later sequence, reshuffles the payload, and forwards it without changing the original signature |
| `requirements.txt` | Dependency note for this device |

Both programs listen on `0.0.0.0:5005` and forward packets to `192.168.1.12:5005`.

Run exactly one attacker program at a time.

## Installation

These attacker programs use only Python standard-library modules:

~~~bash
cd ~/SfS/Raspberry_Pi_3_Attacker
python3 -m pip install -r requirements.txt
~~~

## ordinary replay

Run with the supplied defaults:

~~~bash
python3 ordinary_replay_attacker.py \
  --bind-ip 0.0.0.0 \
  --listen-port 5005 \
  --receiver-ip 192.168.1.12 \
  --receiver-port 5005 \
  --delay-s 3 \
  --replay-every 20
~~~

The supplied default delays every 20th captured packet by 3 seconds. Use
`--delay-s` and `--replay-every` for another replay-delay or attack-frequency
experiment. The program retransmits the exact captured datagram without
modifying it.

The supplied program processes captured packets sequentially: it waits for the configured delay before returning to receive the next queued packet. Allow sufficient time for the intended replay run to finish.

Before a high-volume ordinary-replay run, apply the receive-buffer settings documented in `docs/RASPBERRY_PI_SETUP.md`.

## Permutation-aware replay

Run with the supplied defaults:

~~~bash
python3 smart_replay_attacker.py \
  --bind-ip 0.0.0.0 \
  --listen-port 5005 \
  --receiver-ip 192.168.1.12 \
  --receiver-port 5005 \
  --delay-s 0.9 \
  --replay-every 20
~~~

The supplied 0.9-second default corresponds to the 900-ms replay experiment.
For the complete delay sweep, pass 0.5, 0.7, 0.9, 1.0, 2.0, 3.0, 4.0, or
5.0 to `--delay-s` in separate runs.

The attacker selects every 20th captured packet, corresponding to 50 smart replays during a complete 1,000-packet experiment. It reconstructs the original binary message, derives the sequence associated with the later timestamp, reshuffles the payload, and forwards the modified packet while preserving the original signature.

The attacker adds `AttackType = smart_replay` and `Original_Timestamp` for offline analysis. These fields are not used by the receiver when deciding whether the packet is valid.

Wait at least the configured replay delay, plus a small margin, after the sender finishes before stopping the attacker. Do not run the ordinary and smart attacker programs simultaneously because both listen on UDP port 5005.

## Values to check

Run the selected program with `--help` to review its endpoint, delay, and
attack-frequency options. Keep its receiver endpoint consistent with Raspberry
Pi 2 and do not run both attacker programs simultaneously.


