# Results from New Runs

Store newly generated workbooks, CSV files, plots, terminal summaries, and run notes here after copying them from the Raspberry Pis.

The live programs use these default workbook names:

- `sender_results.xlsx`
- `receiver_results.xlsx`

Use each program's `--output` option or create a separate directory for every
parameter setting so that a later run does not replace an earlier result.

For example:

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

For each run, record:

- experiment and attacker type;
- packet count;
- THV;
- replay delay;
- time quantization;
- mean-delay calibration;
- run date;
- device and software versions;
- Chrony status;
- physical placement and wireless conditions; and
- any packet loss, interruption, or manual action.

The `results/` directory is a suggested location for collecting outputs from
new experimental runs. The Python programs generate `sender_results.xlsx` and
`receiver_results.xlsx` by default on their respective Raspberry Pis.
Evaluators can select unique names with `--output`, or copy, move, or rename
the default files after each run.
