# Claim 1: Reproduce Figures 3--11

## Claim

The supplied packet-level experimental workbooks and analysis program reproduce
the quantitative results plotted in Figures 3--11 of the paper.

## Artifact components

- `SfS_Artifact_Reproduction/data/`: raw experimental workbooks;
- `SfS_Artifact_Reproduction/reproduce_all.py`: analysis and plotting program;
- `SfS_Artifact_Reproduction/PLOT_MAPPING.md`: mapping from inputs and outputs
  to paper figures;
- `SfS_Artifact_Reproduction/derived/`: numerical CSV outputs; and
- `SfS_Artifact_Reproduction/figures/`: generated PDF and PNG figures.

## Setup

From the repository root:

~~~bash
bash install.sh analysis
~~~

## Run

From the repository root:

~~~bash
bash claims/claim1_figures_3_11/run.sh
~~~

The runner uses `.venv-analysis/bin/python`, changes to the reproduction
directory, and invokes `reproduce_all.py` without modifying the raw workbooks.

## Expected evidence

- the command exits successfully;
- Figure 3 through Figure 11 outputs are written under `figures/` in PDF and
  PNG formats;
- the numerical values used for the plots are written under `derived/`; and
- the generated outputs follow `PLOT_MAPPING.md` and support the trends and
  quantitative results reported in the paper.

Minor visual differences caused by Matplotlib versions are not failures. The
derived counts and rates are the primary numerical evidence.
