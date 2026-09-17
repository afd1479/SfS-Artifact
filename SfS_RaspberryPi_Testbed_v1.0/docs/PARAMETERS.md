# Experiment Parameters

The programs provide command-line options for the network addresses, packet
count, THV, replay delay, timing calibration, and output filenames. The default
values correspond to the documented laboratory setup. Run each program with
`--help` before an experiment and record any non-default values alongside the
generated results.

## Network and run parameters

| Parameter | Command-line option | Supplied value | When to change |
|---|---|---:|---|
| Receiver address | `--receiver-ip` in both sender and attacker programs | `192.168.1.12` | When Raspberry Pi 2 uses another address |
| Attacker address | `--attacker-ip` in both sender programs | `192.168.1.10` | When Raspberry Pi 3 uses another address |
| UDP port | `--port`, `--listen-port`, and `--receiver-port` as applicable | `5005` | Only when the same new port is applied everywhere |
| Packet count | `--packet-count` in sender and throughput programs | 1,000 | Packet-count experiments |
| Main receiver THV | `receiver.py --thv-ms` | 1,000 ms | THV sweep |
| Performance receiver THV | `receiver_throughput.py --thv-ms` | 300 ms | Separate performance setting |
| Ordinary replay delay | `ordinary_replay_attacker.py --delay-s` | 3 s | Replay-delay experiment |
| Smart replay delay | `smart_replay_attacker.py --delay-s` | 0.9 s | Smart replay-delay experiment |
| Replay selection interval | `--replay-every` in both attacker programs | 20 packets | Attack-frequency experiments |

## Timing and sequence parameters

| Parameter | Supplied value | Notes |
|---|---:|---|
| Mean-delay calibration | 0.29 s | Mean measured from 1,000 packets in the laboratory setup |
| Time quantization | `round()` | Used for the supplied experimental data |
| Sequence length | 112 | Sender, receiver, and smart attacker must agree |

### Mean-delay calibration

Both receiver programs default to:

~~~python
computed_seed = receiving_time - 0.29
~~~

For your setup, measure the mean delay using synchronized devices as described
in `RASPBERRY_PI_SETUP.md`, then pass it with `--mean-delay-s`.

### THV

The main receiver evaluates:

~~~text
estimated sending time - THV
estimated sending time + THV
~~~

To perform a THV sweep, run `receiver.py` separately for each value using
`--thv-ms`. Use `--output` to save every run under a distinct filename.

### Round and floor

The supplied sender, receiver, performance programs, and smart attacker use `round()`. This is the configuration associated with the supplied data.

If evaluating `floor()` as a separate design configuration, update all time-to-seed operations consistently:

- `sender.py`;
- `sender_throughput.py`;
- `receiver.py`;
- `receiver_throughput.py`; and
- `smart_replay_attacker.py`.

The ordinary replay attacker does not derive a seed and therefore does not require this change.

Do not compare a sender using `floor()` with a receiver or smart attacker using `round()`. Label floor-based outputs as a separate experiment because packets close to a second boundary can map to different seeds.

## Location Information and Timing Calibration

In a real-world deployment, the sender and receiver may obtain accurate
location and timing information from trusted GPS/GNSS devices or another
positioning and synchronization source. This information can support a
distance-based estimate of the signal-propagation component of the expected
packet arrival time.

Our Raspberry Pi testbed did not include GPS/GNSS hardware. Therefore, the
coordinate values included in the supplied programs are illustrative metadata
and are not used by the active verification calculation. Instead, we
synchronized the devices and performed a no-attack calibration using 1,000
packets. The measured mean end-to-end delay was 0.29 s, and the receiver
estimates the sending time as:

    estimated_sending_time = receiving_time - mean_delay

The supplied programs consequently use 0.29 s as the default
`--mean-delay-s` value. This value is specific to our hardware, software,
wireless environment, and experimental configuration.

Evaluators reproducing the Raspberry Pi experiment should first measure the
mean end-to-end delay in their own synchronized testbed and provide the
measured value through `--mean-delay-s`. Evaluators with trusted GPS/GNSS
hardware may instead implement the location-based timing approach, but they
must also account for processing, operating-system, and network delays; GPS
coordinates alone do not replace this calibration.

Merely changing the coordinate values in the supplied implementation does not
change packet verification because the active receiver currently uses the
calibrated mean-delay method.

## Change-control checklist

For every new run:

1. record the original and new value;
2. change one experimental factor at a time where possible;
3. keep matching parameters consistent across devices;
4. restart the affected program;
5. save outputs under a setting-specific name; and
6. record the software, network, synchronization, and physical environment.
