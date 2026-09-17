# Permutation Analysis

This directory contains the offline permutation-recurrence analysis. It is independent of the live three-Raspberry-Pi packet experiment and can be run on a workstation.

## Installation

~~~bash
cd Permutation_Analysis
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
~~~

## Configuration

The analysis is configured through command-line options; the source file does
not need to be edited. Run `python3 permutation_analysis.py --help` for the
complete list. The main options are `--bits`, `--scale`, `--start-time`,
`--days`, `--max-rows`, `--output-dir`, and `--output-prefix`.

A seven-day second-scale run creates 604,800 rows. A seven-day millisecond-scale run would request 604,800,000 rows, so set `max_rows` to an appropriate value before attempting a millisecond run on a machine with limited memory.

## Run

~~~bash
python3 permutation_analysis.py
~~~

An explicit equivalent of the default seven-day, second-scale run is:

~~~bash
python3 permutation_analysis.py \
  --bits 112 \
  --scale second \
  --start-time "2026-03-01 00:00:00" \
  --days 7 \
  --output-dir .
~~~

For a bounded millisecond-scale run, use `--max-rows`, for example:

~~~bash
python3 permutation_analysis.py \
  --scale millisecond \
  --days 7 \
  --max-rows 1000000 \
  --output-dir results/millisecond
~~~

With the default settings, the program creates:

- `perm_112bits_second_full.csv`
- `perm_112bits_second_repeats.csv`
- `perm_112bits_second_figure1_frequency.png`, when repeats are present
- `perm_112bits_second_figure2_gap.png`, when repetition-gap data are present

The full CSV records each time, seed, permutation, permutation hash, occurrence count, and recurrence-gap fields. The repeats CSV contains only repeated permutations.
