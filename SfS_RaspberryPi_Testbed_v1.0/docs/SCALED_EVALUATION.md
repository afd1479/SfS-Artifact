# Scaled Evaluation for Artifact Review

This procedure is a short functional evaluation of the same sender, receiver,
ordinary-replay attacker, permutation-aware attacker, and performance programs
used by the full SfS testbed. It reduces each sender run from 1,000 packets to
100 packets and evaluates one representative THV and replay delay.

The scaled evaluation is intended for artifact kick-the-tires testing. It does
not replace the full experimental matrix, and its small sample is not intended
to re-estimate the paper's TPR, TNR, ROC, AUC, throughput, or latency values.
Figures 3--11 should be reproduced from the supplied raw workbooks using the
separate `SfS_Artifact_Reproduction` package.

## Evaluation summary

| Run | Programs | Packets | Attacker setting | Purpose |
|---|---|---:|---|---|
| A | `sender_throughput.py`, `receiver_throughput.py` | 100 | None | Confirm execution, collect timing summaries, and measure the local mean delay |
| B | `sender.py`, `receiver.py` | 100 | None | Confirm legitimate signed-packet processing |
| C | `sender.py`, `receiver.py`, `ordinary_replay_attacker.py` | 100 | 3 s; every 20th packet | Confirm capture and delayed unmodified replay |
| D | `sender.py`, `receiver.py`, `smart_replay_attacker.py` | 100 | 3 s; every 20th packet | Confirm permutation-aware packet modification and replay |

With 100 sender packets and `--replay-every 20`, each attacker selects five
packets if all sender-to-attacker datagrams arrive. Allow approximately 15--30
minutes for the four runs after the three-device testbed has been configured.
Runtime varies with the Raspberry Pi model, storage, CPU load, and Wi-Fi
conditions.

## Prerequisites

Complete `RASPBERRY_PI_SETUP.md` first. In particular:

- use the isolated 2.4 GHz IBSS/ad-hoc network;
- assign sender `192.168.1.11`, receiver `192.168.1.12`, and attacker
  `192.168.1.10`;
- verify bidirectional connectivity;
- synchronize all three clocks with Chrony; and
- install each role's Python requirements.

Do not run both attacker programs simultaneously because both bind UDP port
`5005` on Raspberry Pi 3.

## Run A: performance and local-delay calibration

No attacker process is used. Keep Raspberry Pi 3 connected because the sender
still transmits its second packet copy to `192.168.1.10`.

On Raspberry Pi 2, start the receiver first:

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver_throughput.py --packet-count 100 --thv-ms 1000 \
  --mean-delay-s 0.29 --output receiver_scaled_calibration.xlsx
~~~

On Raspberry Pi 1:

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender_throughput.py --packet-count 100 \
  --output sender_scaled_calibration.xlsx
~~~

The receiver normally stops automatically after processing 100 packets. If
packet loss prevents it from reaching 100, wait until the sender has finished,
then stop the receiver with `Ctrl+C` and record the received row count.

On Raspberry Pi 2, calculate the mean observed end-to-end delay:

~~~bash
python3 - <<'PY'
import pandas as pd

df = pd.read_excel("receiver_scaled_calibration.xlsx")
mean_delay = df["Travel Time (s)"].mean()
print(f"Calibrated mean delay: {mean_delay:.6f} s")
PY
~~~

Record the printed value as `CALIBRATED_DELAY`. Use it for Runs B--D instead
of `0.29`. The supplied `0.29` s value is the mean measured in the authors'
laboratory and is not universal.

The sender and receiver coordinates are retained as experimental metadata.
They are not live GPS/GNSS readings, and changing them does not replace this
end-to-end calibration in the current implementation.

Expected evidence from Run A:

- `sender_scaled_calibration.xlsx` on Raspberry Pi 1;
- `receiver_scaled_calibration.xlsx` on Raspberry Pi 2;
- 100 sender rows and normally 100 receiver rows; and
- sender signing/throughput plus receiver verification/throughput/latency
  summaries in the terminals.

Exact performance numbers are environment-dependent and are not pass/fail
targets for the scaled run.

## Run B: legitimate traffic

Replace `<CALIBRATED_DELAY>` below with the value obtained in Run A. Do not
start an attacker process.

On Raspberry Pi 2:

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver.py --thv-ms 1000 \
  --mean-delay-s <CALIBRATED_DELAY> \
  --output receiver_scaled_legitimate.xlsx
~~~

On Raspberry Pi 1:

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender.py --packet-count 100 \
  --output sender_scaled_legitimate.xlsx
~~~

After the sender finishes, allow the receiver to drain queued packets and then
press `Ctrl+C` on Raspberry Pi 2 so it saves the final workbook.

Expected evidence from Run B:

- sender and receiver workbooks are created;
- receiver IDs correspond to the sender IDs received over UDP; and
- most legitimate packets are marked `True` in `Valid?` when clocks are
  synchronized and the mean delay is calibrated.

The exact received count and classification rate are not fixed pass/fail
values because this is a small UDP wireless run.

## Run C: ordinary replay

On Raspberry Pi 2, start the receiver first:

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver.py --thv-ms 1000 \
  --mean-delay-s <CALIBRATED_DELAY> \
  --output receiver_scaled_ordinary_3s.xlsx
~~~

On Raspberry Pi 3, start the ordinary attacker second:

~~~bash
cd ~/SfS/Raspberry_Pi_3_Attacker
python3 ordinary_replay_attacker.py --delay-s 3 --replay-every 20
~~~

On Raspberry Pi 1, start the sender last:

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender.py --packet-count 100 \
  --output sender_scaled_ordinary_3s.xlsx
~~~

After the sender finishes, wait at least 20 seconds so the ordinary attacker
can complete its sequential 3-second replay operations. Stop the attacker with
`Ctrl+C` first and retain its printed replayed-ID list. Then stop the receiver
with `Ctrl+C`.

Expected evidence from Run C:

- the attacker selects up to five packets and prints their IDs;
- the receiver workbook contains the original traffic plus any delivered
  replays, visible as repeated packet IDs; and
- 3-second stale replays are expected to fail verification at THV 1,000 ms.

The ordinary attacker forwards the original serialized datagram and therefore
does not add an `AttackType` field. Use its printed ID list and repeated IDs in
the receiver workbook to identify its replay rows.

## Run D: permutation-aware replay

On Raspberry Pi 2, start the receiver first:

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver.py --thv-ms 1000 \
  --mean-delay-s <CALIBRATED_DELAY> \
  --output receiver_scaled_smart_3s.xlsx
~~~

On Raspberry Pi 3, start the smart attacker second:

~~~bash
cd ~/SfS/Raspberry_Pi_3_Attacker
python3 smart_replay_attacker.py --delay-s 3 --replay-every 20
~~~

On Raspberry Pi 1, start the sender last:

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender.py --packet-count 100 \
  --output sender_scaled_smart_3s.xlsx
~~~

After the sender finishes, wait at least 5 seconds for all scheduled replay
threads to complete. Stop the attacker with `Ctrl+C` first and retain its
printed attacked-ID list. Then stop the receiver with `Ctrl+C`.

Expected evidence from Run D:

- the attacker schedules up to five packets and prints their IDs;
- delivered modified replays are labeled `smart_replay` in the receiver's
  `AttackType` column; and
- 3-second permutation-aware replays are expected to fail verification at THV
  1,000 ms. Legitimate rows are recorded separately; their exact scaled-run
  verification rate is environment-dependent.

## Compact workbook summary

After copying the four receiver workbooks into one directory on a workstation,
the following optional command prints row counts, verification counts, attack
labels, and duplicated IDs without modifying the workbooks:

~~~bash
python3 - <<'PY'
from pathlib import Path
import pandas as pd

for path in sorted(Path(".").glob("receiver_scaled_*.xlsx")):
    df = pd.read_excel(path)
    print(f"\n{path.name}: rows={len(df)}")
    if "Valid?" in df:
        print("  Valid?:", df["Valid?"].value_counts(dropna=False).to_dict())
    if "AttackType" in df:
        print(
            "  AttackType:",
            df["AttackType"].value_counts(dropna=False).to_dict(),
        )
    if "ID" in df:
        duplicate_ids = sorted(
            df.loc[df.duplicated("ID", keep=False), "ID"].dropna().unique()
        )
        print("  duplicated IDs:", duplicate_ids)
PY
~~~

## Interpreting the scaled evaluation

The scaled evaluation passes its functional purpose when the programs execute
without an unhandled exception, create the documented workbooks and terminal
summaries, and provide evidence that the selected replay operations reached
the receiver. Small differences in counts and timing are expected for UDP and
wireless execution.

A scaled run is not considered evidence of the paper's exact statistical
rates. Use `SfS_Artifact_Reproduction/reproduce_all.py` and its complete raw
data to verify the published Figures 3--11.
