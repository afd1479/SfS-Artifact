# Claim 4: Prototype Performance Measurements

## Claim

The instrumented SfS sender and receiver report signing, verification,
throughput, and end-to-end latency measurements for the Raspberry Pi
prototype.

## Artifact components

- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_1_Sender/sender_throughput.py`;
- `SfS_RaspberryPi_Testbed_v1.0/Raspberry_Pi_2_Receiver/receiver_throughput.py`;
- `SfS_RaspberryPi_Testbed_v1.0/docs/SCALED_EVALUATION.md`, Run A; and
- `SfS_RaspberryPi_Testbed_v1.0/docs/OUTPUTS_AND_PERFORMANCE.md`.

## Evaluation

Follow Run A of `SCALED_EVALUATION.md` using 100 packets and no active attacker.
The same run records the local end-to-end delay used to calibrate the remaining
scaled live experiments.

## Expected evidence

- sender and receiver workbooks are created;
- the sender prints signing cost, theoretical signing throughput, and measured
  sender throughput;
- the receiver prints verification cost, theoretical verification throughput,
  measured receiver throughput, average latency, and 95th-percentile latency;
  and
- the receiver normally stops automatically after processing 100 packets.

Exact values are not pass/fail targets. They depend on the Raspberry Pi model,
operating system, Python and package versions, CPU load, storage, Wi-Fi
conditions, device placement, packet loss, and clock synchronization. The
measurement boundaries are documented in `OUTPUTS_AND_PERFORMANCE.md`.

