# Claim 3: Permutation-Aware Replay

## Claim

The permutation-aware attacker can update public time-derived packet fields
for a later epoch without possessing the private signing key, while the
receiver evaluates the modified replay under the configured THV.

## Artifact components

- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_1_Sender/sender.py`;
- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_2_Receiver/receiver.py`;
- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_3_Attacker/smart_replay_attacker.py`;
- `SfS_RaspberryPi_Testbed_v1.0/docs/SCALED_EVALUATION.md`, Run D; and
- `SfS_Artifact_Reproduction/data/permutation_aware/`, which supports Figure
  11.

## Evaluation

The deterministic evaluation uses Claim 1 to reproduce Figure 11 across the
supplied THV and replay-delay combinations. Evaluators with the required
three-Pi testbed may additionally run the 100-packet procedure in Run D of
`SCALED_EVALUATION.md`.

## Expected evidence from the scaled run

- with 100 packets and `--replay-every 20`, the attacker schedules up to five
  modified replays;
- the receiver records delivered modified packets with the `smart_replay`
  attack label; and
- 3-second permutation-aware replays are expected to fail verification at THV
  1,000 ms. Legitimate rows are recorded separately; their exact scaled-run
  verification rate is environment-dependent.

The 100-packet run demonstrates the execution path only. Figure 11, reproduced
from the complete supplied data, is the quantitative evaluation.
