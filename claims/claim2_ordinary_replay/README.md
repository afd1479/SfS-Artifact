# Claim 2: Legitimate Traffic and Ordinary Replay

## Claim

The three-device SfS implementation processes signed legitimate traffic and
evaluates delayed, unmodified replay packets under the configured time-hash
validity margin (THV).

## Artifact components

- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_1_Sender/sender.py`;
- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_2_Receiver/receiver.py`;
- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_3_Attacker/ordinary_replay_attacker.py`;
- `SfS_RaspberryPi_Testbed_v1.0/docs/SCALED_EVALUATION.md`, Runs B and C; and
- the no-attack and ordinary-replay workbooks in
  `SfS_Artifact_Reproduction/data/`, which support Figures 3--10.

## Evaluation

The deterministic evaluation uses Claim 1 to reproduce Figures 3--10 from the
complete supplied data. Evaluators with the required three-Pi testbed may also
run the 100-packet procedures in Runs B and C of `SCALED_EVALUATION.md`.

The live procedure remains manual because the receiver, attacker, and sender
must be started in order on three distinct devices. Hiding those operations in
a one-machine wrapper would not reproduce the physical setup.

## Expected evidence from the scaled run

- sender and receiver workbooks are created;
- most synchronized legitimate packets verify after local mean-delay
  calibration;
- with 100 packets and `--replay-every 20`, the attacker selects up to five
  packets;
- delivered ordinary replays appear as duplicated IDs in the receiver
  workbook; and
- 3-second replays are expected to fail verification at THV 1,000 ms.

UDP loss, Wi-Fi conditions, and scheduling can change the exact row count. The
100-packet procedure is a functional check and not a new estimate of the
paper's statistical rates.

