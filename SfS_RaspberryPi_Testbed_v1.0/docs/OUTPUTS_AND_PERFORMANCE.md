# Outputs and Performance Measurements

## Sender workbook

`sender.py` and `sender_throughput.py` create:

~~~text
sender_results.xlsx
~~~

This is the default filename; use `--output` to select a run-specific path.

The workbook records the packet number, sending time, and generated sequence. The throughput sender also keeps the packet ID internally and reports timing summaries in the terminal.

## Receiver workbook

`receiver.py` and `receiver_throughput.py` create:

~~~text
receiver_results.xlsx
~~~

This is the default filename; use `--output` to select a run-specific path.

Depending on the selected receiver program, the workbook includes:

- packet number and ID;
- experimental attack label, when present;
- sender timestamp;
- original timestamp supplied by the smart attacker, when present;
- receiver-computed sending-time candidate;
- receiving time;
- measured travel time;
- packet-provided sequence;
- receiver-generated expected sequence; and
- the verification result.

By default, the workbook is checkpointed every ten received packets. The main
receiver writes it again when stopped with `Ctrl+C`. The throughput receiver
writes it when the requested `--packet-count` is reached, or when an unbounded
run is stopped with `Ctrl+C`; its checkpoint interval can be changed with
`--save-every`.

## Sender performance values

`sender_throughput.py` reports:

### Average signing, sequence, and shuffle time

The program measures the call that:

- obtains the sending time;
- generates the sequence;
- converts the message to bits;
- shuffles the indexed bits;
- hashes and signs the signed input; and
- creates the packet dictionary.

### Theoretical signing throughput

The program measures the average execution time of the `sender(...)` function, including sequence generation, message conversion, shuffling, hashing, RSA signing, and packet construction.

It then calculates:

~~~text
1,000,000 microseconds / average sender-operation time
~~~



### Sender throughput

The sender wall-clock timer starts before processing the first packet and is read after the Excel workbook is written. Consequently, the result reflects the measurement boundary implemented in the supplied program, including surrounding Python processing, serialization, UDP sends, result collection, and workbook creation.

## Receiver performance values

`receiver_throughput.py` reports:

### Average verification time

This measures the receiver verification function for each packet, including candidate generation, message reconstruction, hashing, and RSA verification attempts.

### Theoretical verification throughput

This is calculated from the average measured verification time.

### Receiver throughput

The timer begins when the first packet is received and ends after the requested
number of packets has been processed. The default is 1,000 packets. When
`--packet-count 0` is used for an unbounded run, the interval ends when the
operator presses `Ctrl+C`.

### End-to-end latency

Latency is calculated from the packet timestamp and the local receiving time. Clock synchronization is therefore mandatory.

Use the performance programs without an active attacker when measuring the baseline sender/receiver latency. The smart attacker updates packet timestamp fields as part of its experiment, so its logged timing fields have a different experimental meaning.

## Environmental dependence

The reported performance values characterize the laboratory setup described in the paper. While the protocol behavior should remain consistent, exact throughput and latency values may vary slightly when the experiment is repeated in another environment because of differences in:

- Raspberry Pi model and clock frequency;
- CPU temperature and throttling;
- operating-system and Python versions;
- RSA, pandas, and openpyxl versions;
- concurrent processes and CPU load;
- Wi-Fi adapter, channel, signal quality, and interference;
- packet loss and socket-buffer behavior;
- physical distance, line of sight, and movement;
- clock-synchronization quality; and
- SD-card and filesystem performance.


## Protecting results

Use `--output` to give each workbook a run-specific name. If the default
filenames are used, move each workbook immediately after a run. A recommended
structure is:

~~~text
results/
├── legitimate/
│   └── run01/
├── ordinary_replay/
│   └── delay3s_thv1000ms_round_run01/
├── smart_replay/
│   └── delay900ms_thv1000ms_round_run01/
└── performance/
    └── thv300ms_round_run01/
~~~

Store terminal summaries and a short run-notes file alongside the workbooks.
