#!/usr/bin/env python3
import argparse
import random
import hashlib
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path


# =========================================================
# Deterministic permutation generation
# =========================================================

def generate_permutation(seed, message_length):
    rng = random.Random(seed)
    indexed_bits = list(range(message_length))
    rng.shuffle(indexed_bits)
    return indexed_bits


# =========================================================
# Time to seed
# =========================================================

def time_to_seed(current_time, scale="second"):
    """Convert a UTC time point to its second- or millisecond-scale seed."""
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    else:
        current_time = current_time.astimezone(timezone.utc)

    ts = current_time.timestamp()

    if scale == "second":
        return int(ts)
    elif scale == "millisecond":
        return int(ts * 1000)
    else:
        raise ValueError("scale must be 'second' or 'millisecond'")


# =========================================================
# Generate data
# =========================================================

def generate_time_permutation_data(
    bits=112,
    scale="second",
    start_time_str="2026-03-01 00:00:00",
    days=7,
    max_rows=None,
    progress_every=50000,
):
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")

    if scale == "second":
        total_steps = days * 24 * 60 * 60
        delta = timedelta(seconds=1)
    elif scale == "millisecond":
        total_steps = days * 24 * 60 * 60 * 1000
        delta = timedelta(milliseconds=1)
    else:
        raise ValueError("scale must be 'second' or 'millisecond'")

    if max_rows is not None:
        total_steps = min(total_steps, max_rows)

    rows = []
    current_time = start_time

    for i in range(total_steps):
        seed = time_to_seed(current_time, scale=scale)
        permutation = generate_permutation(seed, bits)
        perm_hash = hashlib.sha256(str(permutation).encode()).hexdigest()

        rows.append({
            "time": current_time,
            "seed": seed,
            "permutation": str(permutation),
            "perm_hash": perm_hash
        })

        current_time += delta

        if progress_every and (i + 1) % progress_every == 0:
            print(f"Generated {i+1} rows...")

    return pd.DataFrame(rows)


# =========================================================
# Repeat analysis
# =========================================================

def analyze_repeats(df):
    df = df.sort_values("time").copy()

    first_seen = {}
    previous_seen = {}
    counts = defaultdict(int)

    occurrence_index = []
    first_seen_time_list = []
    gap_from_first_seconds = []
    gap_from_previous_seconds = []

    for _, row in df.iterrows():
        h = row["perm_hash"]
        t = row["time"]

        counts[h] += 1
        occurrence_index.append(counts[h])

        if h not in first_seen:
            first_seen[h] = t
            previous_seen[h] = t

            first_seen_time_list.append(t)
            gap_from_first_seconds.append(None)
            gap_from_previous_seconds.append(None)
        else:
            first_seen_time_list.append(first_seen[h])
            gap_from_first_seconds.append((t - first_seen[h]).total_seconds())
            gap_from_previous_seconds.append((t - previous_seen[h]).total_seconds())
            previous_seen[h] = t

    df["occurrence_index"] = occurrence_index
    df["first_seen_time"] = first_seen_time_list
    df["gap_from_first_seconds"] = gap_from_first_seconds
    df["gap_from_previous_seconds"] = gap_from_previous_seconds

    return df


def build_repeat_events_table(df):
    return df[df["occurrence_index"] > 1].copy().sort_values("time")


# =========================================================
# Plots
# =========================================================

def plot_repetition_frequency(repeat_events, output_png):
    if repeat_events.empty:
        print("No repeats found.")
        return

    freq = repeat_events["occurrence_index"].value_counts().sort_index()

    plt.figure(figsize=(10, 6))
    plt.bar(freq.index, freq.values)
    plt.xlabel("Repetition order")
    plt.ylabel("Number of repeated events")
    plt.title("Frequency of permutation repetitions")
    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    plt.close()


def plot_gap_distribution(repeat_events, output_png):
    gaps = repeat_events["gap_from_previous_seconds"].dropna()

    if gaps.empty:
        print("No repetition-gap data.")
        return

    plt.figure(figsize=(10, 6))
    plt.hist(gaps, bins=50)
    plt.xlabel("Gap between repetitions (seconds)")
    plt.ylabel("Count")
    plt.title("Gap distribution between repeated permutations")
    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    plt.close()


# =========================================================
# Main
# =========================================================


def positive_int(value):
    """Return a positive integer for argparse."""
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def non_negative_int(value):
    """Return a non-negative integer for argparse."""
    value = int(value)
    if value < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return value


def start_time_value(value):
    """Validate the documented start-time format while retaining the string."""
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "must use the format YYYY-MM-DD HH:MM:SS"
        ) from exc
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic time-seeded permutations and analyze "
            "their recurrence gaps."
        )
    )
    parser.add_argument(
        "--bits",
        type=positive_int,
        default=112,
        help="permutation length in bits (default: %(default)s)",
    )
    parser.add_argument(
        "--scale",
        choices=("second", "millisecond"),
        default="second",
        help="time-to-seed resolution (default: %(default)s)",
    )
    parser.add_argument(
        "--start-time",
        type=start_time_value,
        default="2026-03-01 00:00:00",
        help=(
            "UTC analysis start in YYYY-MM-DD HH:MM:SS format "
            "(default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--days",
        type=positive_int,
        default=7,
        help="requested analysis duration in days (default: %(default)s)",
    )
    parser.add_argument(
        "--max-rows",
        type=positive_int,
        default=None,
        help="optional cap for shorter or memory-limited runs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="directory for CSV and PNG outputs (default: current directory)",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="filename prefix (default: perm_<bits>bits_<scale>)",
    )
    parser.add_argument(
        "--progress-every",
        type=non_negative_int,
        default=50000,
        help="print progress every N rows; use 0 to disable (default: %(default)s)",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="write the CSV tables without generating PNG plots",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_prefix = args.output_prefix or f"perm_{args.bits}bits_{args.scale}"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    full_csv = args.output_dir / f"{output_prefix}_full.csv"
    repeats_csv = args.output_dir / f"{output_prefix}_repeats.csv"
    frequency_png = args.output_dir / f"{output_prefix}_figure1_frequency.png"
    gap_png = args.output_dir / f"{output_prefix}_figure2_gap.png"

    requested_rows = args.days * 24 * 60 * 60
    if args.scale == "millisecond":
        requested_rows *= 1000
    effective_rows = min(requested_rows, args.max_rows) if args.max_rows else requested_rows

    print(
        f"Configuration: bits={args.bits}, scale={args.scale}, "
        f"start={args.start_time} UTC, days={args.days}, "
        f"rows={effective_rows}, output={args.output_dir}"
    )

    print("Generating data...")
    df = generate_time_permutation_data(
        bits=args.bits,
        scale=args.scale,
        start_time_str=args.start_time,
        days=args.days,
        max_rows=args.max_rows,
        progress_every=args.progress_every,
    )

    print("Analyzing repeats...")
    df = analyze_repeats(df)
    repeat_events = build_repeat_events_table(df)

    print("Saving results...")
    df.to_csv(full_csv, index=False)
    repeat_events.to_csv(repeats_csv, index=False)

    if not args.skip_plots:
        print("Generating plots...")
        plot_repetition_frequency(repeat_events, frequency_png)
        plot_gap_distribution(repeat_events, gap_png)

    print(
        f"Rows: {len(df)}; unique permutations: {df['perm_hash'].nunique()}; "
        f"repeat events: {len(repeat_events)}"
    )
    print("Done.")


if __name__ == "__main__":
    main()
