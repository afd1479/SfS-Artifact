# SfS Claim-to-Artifact Mapping

This directory maps the main evaluated claims of *Shuffling for Safeguarding
(SfS): Replay Protection in Wireless Broadcast Systems* to the corresponding
artifact components, execution instructions, and expected evidence.

| Claim | Paper results supported | Primary evaluation path | Special hardware |
|---|---|---|---|
| [Claim 1](claim1_figures_3_11/README.md): supplied data reproduce the reported detection results | Figures 3--11 | Run the offline reproduction script | No |
| [Claim 2](claim2_ordinary_replay/README.md): SfS processes legitimate traffic and detects delayed ordinary replays | No-attack and ordinary-replay evaluation underlying Figures 3--10 | Inspect full data; optionally run the scaled three-Pi experiment | Three Raspberry Pis for a fresh live run |
| [Claim 3](claim3_permutation_aware_replay/README.md): SfS evaluates permutation-aware delayed replays | Figure 11 | Inspect full data; optionally run the scaled three-Pi experiment | Three Raspberry Pis for a fresh live run |
| [Claim 4](claim4_performance/README.md): the prototype reports signing, verification, throughput, and latency measurements | Prototype performance results | Run the scaled performance procedure | Two Raspberry Pis; the third should remain connected for closest sender behavior |

The deterministic paper-figure evaluation is Claim 1. Claims 2--4 explain how
the supplied data relate to the optional live testbed. Exact live timing and
packet counts can vary with hardware, operating-system scheduling, storage,
clock synchronization, and wireless conditions.

The offline reproduction requires a normal Python workstation and no GPU. A
fresh over-the-air run requires the hardware and network configuration listed
in `SfS_RaspberryPi_Testbed_v1.0/docs/RASPBERRY_PI_SETUP.md`.

