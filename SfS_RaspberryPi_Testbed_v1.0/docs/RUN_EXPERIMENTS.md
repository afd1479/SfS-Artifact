# Running the Experiments

This guide gives the command order for each experiment. The three terminals correspond to the three physical Raspberry Pis.

For a 15--30 minute artifact kick-the-tires procedure using 100 packets per
run, see [SCALED_EVALUATION.md](SCALED_EVALUATION.md). The scaled procedure
uses the same programs but is not intended to reproduce the paper's exact
statistical rates.

## Common pre-run checks

On all devices:

~~~bash
date --iso-8601=ns
chronyc tracking
~~~

Confirm connectivity:

~~~bash
ping -c 2 192.168.1.12
~~~

Record the intended packet count, THV, replay delay, quantization rule, date, and physical setup before starting.

The following commands assume that the required Python packages have already been installed. A virtual environment may be used, but it is not required to run the SfS programs.

## 1. Legitimate traffic

No attacker program is started. The sender still transmits its second copy to Raspberry Pi 3, but no process replays it.

### Raspberry Pi 2

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver.py --thv-ms 1000 --mean-delay-s 0.29 \
  --output receiver_results.xlsx
~~~

### Raspberry Pi 1

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender.py --packet-count 1000 --output sender_results.xlsx
~~~

After the sender reports that `sender_results.xlsx` was saved, press `Ctrl+C` on Raspberry Pi 2. Confirm that `receiver_results.xlsx` was saved.

## 2. Ordinary replay

The ordinary attacker retransmits the same serialized datagram after the configured delay.

### Raspberry Pi 2 — start first

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver.py --thv-ms 1000 --mean-delay-s 0.29 \
  --output receiver_ordinary_delay3s_thv1000ms.xlsx
~~~

### Raspberry Pi 3 — start second

~~~bash
cd ~/SfS/Raspberry_Pi_3_Attacker
python3 ordinary_replay_attacker.py --delay-s 3 --replay-every 20
~~~

### Raspberry Pi 1 — start last

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender.py --packet-count 1000 \
  --output sender_ordinary_delay3s.xlsx
~~~

The supplied ordinary attacker replays every 20th captured packet and processes
selected packets sequentially with a 3-second delay. Allow the intended replay
processing to finish before stopping it. Use `--delay-s` or `--replay-every`
for another experiment.

Stop Raspberry Pi 3 and then Raspberry Pi 2 with `Ctrl+C` after all selected
replays have been processed.

## 3. Permutation-aware replay

The smart attacker schedules a delayed operation for every configured Nth
captured packet, generates the later sequence, reshuffles the indexed bits, and
forwards the modified packet without access to the private key.

### Raspberry Pi 2 — start first

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver.py --thv-ms 1000 --mean-delay-s 0.29 \
  --output receiver_smart_delay900ms_thv1000ms.xlsx
~~~

### Raspberry Pi 3 — start second

~~~bash
cd ~/SfS/Raspberry_Pi_3_Attacker
python3 smart_replay_attacker.py --delay-s 0.9 --replay-every 20
~~~

### Raspberry Pi 1 — start last

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender.py --packet-count 1000 \
  --output sender_smart_delay900ms.xlsx
~~~

Wait until the scheduled replays have been sent. Stop Raspberry Pi 3 and then Raspberry Pi 2 with `Ctrl+C`.

## 4. THV runs

For each THV value:

1. start a fresh receiver with the required `--thv-ms` value;
2. use a THV-specific filename with `--output`;
3. record the selected THV value;
4. run the selected traffic or replay experiment; and
5. stop the receiver with `Ctrl+C` after the run.

For example:

~~~bash
python3 receiver.py --thv-ms 300 --mean-delay-s 0.29 \
  --output receiver_ordinary_delay3s_thv300ms.xlsx
~~~

Example result names:

~~~text
receiver_ordinary_delay3s_thv300ms.xlsx
receiver_ordinary_delay3s_thv500ms.xlsx
receiver_ordinary_delay3s_thv1000ms.xlsx
~~~

The receiver evaluates the implemented negative and positive THV candidate points for each packet.

## 5. Sender and receiver performance

Do not run an attacker process. For the closest reproduction, leave Raspberry Pi 3 connected at `192.168.1.10`, because the throughput sender still transmits an identical second copy to that address.

### Raspberry Pi 2 — start first

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 receiver_throughput.py --packet-count 1000 --thv-ms 300 \
  --mean-delay-s 0.29 --output receiver_results.xlsx
~~~

### Raspberry Pi 1 — start second

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 sender_throughput.py --packet-count 1000 \
  --output sender_results.xlsx
~~~

With `--packet-count 1000`, the receiver stops automatically after processing
1,000 packets, writes its final workbook, and prints its summaries. Confirm
that both workbooks were saved and retain both terminal summaries. If
`--packet-count 0` is used for an unbounded run, stop the receiver with
`Ctrl+C`.

## 6. Preserve the outputs

The programs provide `--output` for run-specific workbook names. If the default
filenames were used, move them after every run:

~~~bash
mkdir -p ~/SfS_results/<run_name>
mv sender_results.xlsx ~/SfS_results/<run_name>/  # on Raspberry Pi 1
mv receiver_results.xlsx ~/SfS_results/<run_name>/  # on Raspberry Pi 2
~~~

Replace `<run_name>` with a descriptive name such as:

~~~text
ordinary_delay3s_thv1000ms_round_run01
smart_delay900ms_thv1000ms_round_run01
performance_thv300ms_round_run01
~~~

Also record:

~~~bash
date --iso-8601=seconds
python3 --version
python3 -m pip freeze
uname -a
chronyc tracking
iwconfig wlan0
~~~

These details are important when interpreting timing and throughput differences between environments.
