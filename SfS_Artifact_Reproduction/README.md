# SfS Figure Reproduction Package

This package contains only the raw experiment workbooks needed to reproduce **Figures 3–11** of *Shuffling for Safeguarding (SfS): Replay Protection in Wireless Broadcast Systems*.


The `data/` directory contains the experimental `.xlsx` files used to reproduce the evaluation results presented in the paper. The files are organized by experiment type, replay delay, and Threshold Value (THV). The reproduction script reads the packet-level records from these files, computes the evaluation metrics, and generates the corresponding CSV tables and figures.

## Quick reproduction

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python reproduce_all.py
```

The script writes:

- PNG and PDF figures to `figures/`
- the numerical data behind each figure to `derived/`


Running `python reproduce_all.py` again creates or overwrites the generated files in `figures/` and `derived/`; the raw files in `data/` are never modified.

## Data organization

```text
data/
├── no_attack/                         # Fig. 3
├── replay_seconds/                    # Figs. 4–7
│   ├── thv_0000/
│   ├── thv_0200/
│   ├── thv_0400/
│   ├── thv_0600/
│   ├── thv_0800/
│   └── thv_1000/
├── replay_milliseconds/               # Figs. 8–10
│   └── thv_XXXX/delay_{100..900}ms.xlsx
└── permutation_aware/                 # Fig. 11
    ├── milliseconds/
    │   └── delay_{500,700,900}ms/thv_XXXX.xlsx
    └── seconds/
        └── delay_{1..5}s/thv_XXXX.xlsx
```

`THV` values are in milliseconds. For example, `thv_0200` means THV = 200 ms.

## Classification definitions

For Figures 3–10, the raw workbooks contain `Actual` and `Predicted` columns. We use:

- **TP:** Actual = `Legit`, Predicted = `Legit`
- **FN:** Actual = `Legit`, Predicted = `Replayed`
- **TN:** Actual = `Replayed`, Predicted = `Replayed`
- **FP:** Actual = `Replayed`, Predicted = `Legit`

The rates are calculated as:

- `TPR = TP / (TP + FN)`
- `TNR = TN / (TN + FP)`
- `FPR = FP / (TN + FP)`
- `FNR = FN / (TP + FN)`

For Figure 11, TNR is calculated as the proportion of replay packets rejected by the receiver.

## Figure derivation

| Figure | Source data | Reproduction rule |
|---|---|---|
| **3** | `data/no_attack/` | TP/FN counts from 1,000 legitimate packets at each THV |
| **4** | `data/replay_seconds/` | Aggregate TP/TN/FP/FN across 1–5 s replay runs for each THV |
| **5** | `data/replay_seconds/` | ROC per replay delay using per-run TPR and FPR; `(0,0)` and `(1,1)` endpoints added for display |
| **6** | `data/replay_seconds/` | TNR per replay delay plus cumulative TPR across all five replay runs |
| **7** | `data/replay_seconds/` | `J = wTP·TPR + wTN·TNR`, using per-run TPR/TNR for three weighting settings |
| **8** | `data/replay_milliseconds/` | ROC per 100/300/500/700/900-ms replay delay |
| **9** | `data/replay_milliseconds/` | Same weighted cost as Fig. 7 for millisecond replays |
| **10** | `data/replay_milliseconds/` | TNR per replay delay plus cumulative TPR across all five millisecond runs |
| **11** | `data/permutation_aware/` | TNR of smart/permutation-aware replay for each delay and THV |






