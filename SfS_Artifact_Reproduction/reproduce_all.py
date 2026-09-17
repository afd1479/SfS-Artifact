#!/usr/bin/env python3
"""Reproduce SfS paper Figures 3–11 from experimental Excel files.

The script calculates evaluation metrics directly from packet-level
experimental records and generates the corresponding CSV tables and figures.

Requirements: Python 3.10+ and matplotlib.
"""
from __future__ import annotations

import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit(
        "matplotlib is required. Install it with: pip install -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DERIVED = ROOT / "derived"
FIGURES = ROOT / "figures"

DERIVED.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)

THVS = [0, 200, 400, 600, 800, 1000]
SEC_DELAYS = [1, 2, 3, 4, 5]
MS_DELAYS = [100, 300, 500, 700, 900]
FIG11_MS_DELAYS = [500, 700, 900]
FIG11_SEC_DELAYS = [1, 2, 3, 4, 5]

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        raise ValueError(f"Invalid Excel cell reference: {cell_ref}")

    value = 0
    for ch in match.group(1):
        value = value * 26 + ord(ch) - 64
    return value - 1


def read_xlsx_sheet(path: Path, sheet_name: str | None = None) -> list[list[object]]:
    """Read one XLSX worksheet using only the Python standard library.

    If ``sheet_name`` is omitted, the first worksheet is read.
    Formula cells are read using their cached values.
    """
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(NS + "si"):
                shared_strings.append(
                    "".join(t.text or "" for t in item.iter(NS + "t"))
                )

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets_element = workbook.find(NS + "sheets")
        if sheets_element is None:
            raise ValueError(f"No worksheets found in {path}")

        sheets = sheets_element.findall(NS + "sheet")
        if not sheets:
            raise ValueError(f"No worksheets found in {path}")

        if sheet_name is None:
            sheet = sheets[0]
        else:
            try:
                sheet = next(s for s in sheets if s.attrib["name"] == sheet_name)
            except StopIteration as exc:
                raise KeyError(
                    f"Worksheet {sheet_name!r} not found in {path}"
                ) from exc

        relationship_id = sheet.attrib[RID]
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(
            rel.attrib["Target"]
            for rel in rels
            if rel.attrib.get("Id") == relationship_id
        )

        sheet_path = (
            target.lstrip("/")
            if target.startswith("/")
            else "xl/" + target.lstrip("./")
        )
        root = ET.fromstring(archive.read(sheet_path))

        rows: list[list[object]] = []
        for row in root.iter(NS + "row"):
            values: dict[int, object] = {}

            for cell in row.findall(NS + "c"):
                index = _column_index(cell.attrib["r"])
                cell_type = cell.attrib.get("t")
                value_node = cell.find(NS + "v")

                if cell_type == "inlineStr":
                    inline = cell.find(NS + "is")
                    value: object = (
                        ""
                        if inline is None
                        else "".join(t.text or "" for t in inline.iter(NS + "t"))
                    )
                elif value_node is None:
                    value = None
                else:
                    raw = value_node.text or ""
                    if cell_type == "s":
                        value = shared_strings[int(raw)]
                    elif cell_type == "b":
                        value = raw == "1"
                    elif cell_type in ("str", "e"):
                        value = raw
                    else:
                        try:
                            number = float(raw)
                            value = int(number) if number.is_integer() else number
                        except ValueError:
                            value = raw

                values[index] = value

            if values:
                row_values = [None] * (max(values) + 1)
                for idx, value in values.items():
                    row_values[idx] = value
                rows.append(row_values)

        return rows


def _get(row: list[object], idx: int) -> object:
    return row[idx] if idx < len(row) else None


def classification_counts(path: Path) -> dict[str, int]:
    """Return TP/TN/FP/FN counts for baseline and replay workbooks.

    Positive class = legitimate packet.
    Negative class = replay packet.
    """
    rows = read_xlsx_sheet(path)
    if not rows:
        raise ValueError(f"No data found in {path}")

    header = rows[0]
    actual_idx = header.index("Actual")
    predicted_idx = header.index("Predicted")

    counts = Counter(TP=0, TN=0, FP=0, FN=0)

    for row in rows[1:]:
        actual = _get(row, actual_idx)
        predicted = _get(row, predicted_idx)

        if actual == "Legit" and predicted == "Legit":
            counts["TP"] += 1
        elif actual == "Legit" and predicted == "Replayed":
            counts["FN"] += 1
        elif actual == "Replayed" and predicted == "Replayed":
            counts["TN"] += 1
        elif actual == "Replayed" and predicted == "Legit":
            counts["FP"] += 1

    return dict(counts)


def fig11_counts(path: Path) -> dict[str, int]:
    """Return counts for the Figure 11 replay-delay sweep workbooks.

    Figure 11 TNR is calculated from replay rows as:
        rejected replay packets / observed replay packets
    """
    rows = read_xlsx_sheet(path)
    if not rows:
        raise ValueError(f"No data found in {path}")

    header = rows[0]
    attack_idx = header.index("AttackType")
    valid_idx = header.index("Valid?")

    counts = Counter(TP=0, TN=0, FP=0, FN=0, legit_total=0, replay_total=0)

    for row in rows[1:]:
        attack_type = _get(row, attack_idx)
        valid = _get(row, valid_idx)

        if attack_type == "legitimate":
            counts["legit_total"] += 1
            if valid is True:
                counts["TP"] += 1
            elif valid is False:
                counts["FN"] += 1

        elif attack_type == "smart_replay":
            counts["replay_total"] += 1
            if valid is False:
                counts["TN"] += 1
            elif valid is True:
                counts["FP"] += 1

    return dict(counts)


def safe_rate(num: int, den: int) -> float:
    return float("nan") if den == 0 else num / den


def rates(counts: dict[str, int]) -> dict[str, float]:
    tp, tn, fp, fn = (counts.get(k, 0) for k in ("TP", "TN", "FP", "FN"))

    return {
        "TPR": safe_rate(tp, tp + fn),
        "FNR": safe_rate(fn, tp + fn),
        "TNR": safe_rate(tn, tn + fp),
        "FPR": safe_rate(fp, tn + fp),
    }


def thv_name(thv: int) -> str:
    return f"thv_{thv:04d}"


def no_attack_path(thv: int) -> Path:
    return DATA / "no_attack" / f"{thv_name(thv)}.xlsx"


def sec_path(thv: int, delay: int) -> Path:
    return DATA / "replay_seconds" / thv_name(thv) / f"delay_{delay}s.xlsx"


def ms_path(thv: int, delay: int) -> Path:
    return DATA / "replay_milliseconds" / thv_name(thv) / f"delay_{delay}ms.xlsx"


def fig11_path(thv: int, delay: int, unit: str) -> Path:
    if unit == "ms":
        return (
            DATA
            / "permutation_aware"
            / "milliseconds"
            / f"delay_{delay}ms"
            / f"{thv_name(thv)}.xlsx"
        )

    return (
        DATA
        / "permutation_aware"
        / "seconds"
        / f"delay_{delay}s"
        / f"{thv_name(thv)}.xlsx"
    )


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_figure(fig, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def build_data():
    # Figure 3: no-attack correctness.
    fig3 = []
    for thv in THVS:
        counts = classification_counts(no_attack_path(thv))
        metric_rates = rates(counts)
        total = counts["TP"] + counts["FN"]

        fig3.append(
            {
                "THV_ms": thv,
                **counts,
                **metric_rates,
                "Total": total,
            }
        )

    # Figures 4–7: second-scale replay experiments.
    sec_rows = []
    sec_aggregate = []

    for thv in THVS:
        aggregate = Counter(TP=0, TN=0, FP=0, FN=0)

        for delay in SEC_DELAYS:
            counts = classification_counts(sec_path(thv, delay))
            aggregate.update(counts)
            metric_rates = rates(counts)

            sec_rows.append(
                {
                    "THV_ms": thv,
                    "Delay_s": delay,
                    **counts,
                    **metric_rates,
                }
            )

        aggregate_dict = dict(aggregate)
        sec_aggregate.append(
            {
                "THV_ms": thv,
                **aggregate_dict,
                **rates(aggregate_dict),
                "Total": sum(aggregate_dict.values()),
            }
        )

    # Figures 8–10: millisecond-scale replay experiments.
    ms_rows = []
    ms_aggregate = []

    for thv in THVS:
        aggregate = Counter(TP=0, TN=0, FP=0, FN=0)

        for delay in MS_DELAYS:
            counts = classification_counts(ms_path(thv, delay))
            aggregate.update(counts)
            metric_rates = rates(counts)

            ms_rows.append(
                {
                    "THV_ms": thv,
                    "Delay_ms": delay,
                    **counts,
                    **metric_rates,
                }
            )

        aggregate_dict = dict(aggregate)
        ms_aggregate.append(
            {
                "THV_ms": thv,
                **aggregate_dict,
                **rates(aggregate_dict),
                "Total": sum(aggregate_dict.values()),
            }
        )

    # Figure 11: replay-delay sweep across millisecond and second delays.
    fig11_rows = []

    for thv in THVS:
        for delay in FIG11_MS_DELAYS:
            counts = fig11_counts(fig11_path(thv, delay, "ms"))
            tnr = safe_rate(counts["TN"], counts["replay_total"])

            fig11_rows.append(
                {
                    "THV_ms": thv,
                    "Delay": f"{delay} ms",
                    "Delay_order": delay,
                    **counts,
                    "TNR": tnr,
                }
            )

        for delay in FIG11_SEC_DELAYS:
            counts = fig11_counts(fig11_path(thv, delay, "s"))
            tnr = safe_rate(counts["TN"], counts["replay_total"])

            fig11_rows.append(
                {
                    "THV_ms": thv,
                    "Delay": f"{delay} s",
                    "Delay_order": 1000 * delay,
                    **counts,
                    "TNR": tnr,
                }
            )

    return (
        fig3,
        sec_rows,
        sec_aggregate,
        ms_rows,
        ms_aggregate,
        fig11_rows,
    )


def write_derived(
    fig3,
    sec_rows,
    sec_aggregate,
    ms_rows,
    ms_aggregate,
    fig11_rows,
):
    write_csv(
        DERIVED / "fig3_no_attack.csv",
        ["THV_ms", "TP", "FN", "TPR", "FNR", "Total"],
        [
            {
                key: row[key]
                for key in ["THV_ms", "TP", "FN", "TPR", "FNR", "Total"]
            }
            for row in fig3
        ],
    )

    write_csv(
        DERIVED / "fig4_seconds_aggregate.csv",
        ["THV_ms", "TP", "TN", "FP", "FN", "TPR", "TNR", "FPR", "Total"],
        [
            {
                key: row[key]
                for key in [
                    "THV_ms",
                    "TP",
                    "TN",
                    "FP",
                    "FN",
                    "TPR",
                    "TNR",
                    "FPR",
                    "Total",
                ]
            }
            for row in sec_aggregate
        ],
    )

    write_csv(
        DERIVED / "fig5_seconds_roc.csv",
        ["THV_ms", "Delay_s", "TP", "TN", "FP", "FN", "TPR", "TNR", "FPR"],
        [
            {
                key: row[key]
                for key in [
                    "THV_ms",
                    "Delay_s",
                    "TP",
                    "TN",
                    "FP",
                    "FN",
                    "TPR",
                    "TNR",
                    "FPR",
                ]
            }
            for row in sec_rows
        ],
    )

    fig6_rows = []
    for thv in THVS:
        aggregate = next(row for row in sec_aggregate if row["THV_ms"] == thv)
        output_row = {
            "THV_ms": thv,
            "Cumulative_TPR": aggregate["TPR"],
        }

        for delay in SEC_DELAYS:
            output_row[f"TNR_{delay}s"] = next(
                row["TNR"]
                for row in sec_rows
                if row["THV_ms"] == thv and row["Delay_s"] == delay
            )

        fig6_rows.append(output_row)

    write_csv(
        DERIVED / "fig6_seconds_tradeoff.csv",
        ["THV_ms", "Cumulative_TPR"] + [f"TNR_{delay}s" for delay in SEC_DELAYS],
        fig6_rows,
    )

    fig7_rows = []
    for row in sec_rows:
        fig7_rows.append(
            {
                "THV_ms": row["THV_ms"],
                "Delay_s": row["Delay_s"],
                "TPR": row["TPR"],
                "TNR": row["TNR"],
                "Performance_critical_wTP_0.8": 0.8 * row["TPR"]
                + 0.2 * row["TNR"],
                "Balanced_wTP_0.5_wTN_0.5": 0.5 * row["TPR"]
                + 0.5 * row["TNR"],
                "Security_critical_wTN_0.8": 0.2 * row["TPR"]
                + 0.8 * row["TNR"],
            }
        )

    write_csv(
        DERIVED / "fig7_seconds_weighted.csv",
        [
            "THV_ms",
            "Delay_s",
            "TPR",
            "TNR",
            "Performance_critical_wTP_0.8",
            "Balanced_wTP_0.5_wTN_0.5",
            "Security_critical_wTN_0.8",
        ],
        fig7_rows,
    )

    write_csv(
        DERIVED / "fig8_milliseconds_roc.csv",
        ["THV_ms", "Delay_ms", "TP", "TN", "FP", "FN", "TPR", "TNR", "FPR"],
        [
            {
                key: row[key]
                for key in [
                    "THV_ms",
                    "Delay_ms",
                    "TP",
                    "TN",
                    "FP",
                    "FN",
                    "TPR",
                    "TNR",
                    "FPR",
                ]
            }
            for row in ms_rows
        ],
    )

    fig9_rows = []
    for row in ms_rows:
        fig9_rows.append(
            {
                "THV_ms": row["THV_ms"],
                "Delay_ms": row["Delay_ms"],
                "TPR": row["TPR"],
                "TNR": row["TNR"],
                "Performance_critical_wTP_0.8": 0.8 * row["TPR"]
                + 0.2 * row["TNR"],
                "Balanced_wTP_0.5_wTN_0.5": 0.5 * row["TPR"]
                + 0.5 * row["TNR"],
                "Security_critical_wTN_0.8": 0.2 * row["TPR"]
                + 0.8 * row["TNR"],
            }
        )

    write_csv(
        DERIVED / "fig9_milliseconds_weighted.csv",
        [
            "THV_ms",
            "Delay_ms",
            "TPR",
            "TNR",
            "Performance_critical_wTP_0.8",
            "Balanced_wTP_0.5_wTN_0.5",
            "Security_critical_wTN_0.8",
        ],
        fig9_rows,
    )

    fig10_rows = []
    for thv in THVS:
        aggregate = next(row for row in ms_aggregate if row["THV_ms"] == thv)
        output_row = {
            "THV_ms": thv,
            "Cumulative_TPR": aggregate["TPR"],
        }

        for delay in MS_DELAYS:
            output_row[f"TNR_{delay}ms"] = next(
                row["TNR"]
                for row in ms_rows
                if row["THV_ms"] == thv and row["Delay_ms"] == delay
            )

        fig10_rows.append(output_row)

    write_csv(
        DERIVED / "fig10_milliseconds_tradeoff.csv",
        ["THV_ms", "Cumulative_TPR"]
        + [f"TNR_{delay}ms" for delay in MS_DELAYS],
        fig10_rows,
    )

    write_csv(
        DERIVED / "fig11_replay_ms_seconds_all_thv.csv",
        [
            "THV_ms",
            "Delay",
            "Delay_order",
            "legit_total",
            "replay_total",
            "TP",
            "TN",
            "FP",
            "FN",
            "TNR",
        ],
        fig11_rows,
    )

    return fig6_rows, fig7_rows, fig9_rows, fig10_rows


def plot_all(
    fig3,
    sec_rows,
    sec_aggregate,
    ms_rows,
    ms_aggregate,
    fig11_rows,
    fig6_rows,
    fig7_rows,
    fig9_rows,
    fig10_rows,
):
    x = list(range(len(THVS)))
    labels = [str(thv) for thv in THVS]

    # Figure 3
    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    tp = [row["TP"] for row in fig3]
    fn = [row["FN"] for row in fig3]

    ax.bar(x, tp, label="TP")
    ax.bar(x, fn, bottom=tp, label="FN")
    ax.set_xticks(x, labels)
    ax.set_xlabel("THV (ms)")
    ax.set_ylabel("Packets")
    ax.set_ylim(0, 1050)
    ax.legend(ncol=2, frameon=False)
    ax.grid(axis="y", alpha=0.25)

    save_figure(fig, "fig3_no_attack")

    # Figure 4
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    bottoms = [0] * len(THVS)

    for key in ["TP", "TN", "FP", "FN"]:
        values = [row[key] for row in sec_aggregate]
        ax.bar(x, values, bottom=bottoms, label=key)
        bottoms = [a + b for a, b in zip(bottoms, values)]

    ax.set_xticks(x, labels)
    ax.set_xlabel("THV (ms)")
    ax.set_ylabel("Packets")
    ax.set_ylim(0, 5500)
    ax.legend(ncol=4, frameon=False)
    ax.grid(axis="y", alpha=0.25)

    save_figure(fig, "fig4_replay_aggregate")

    # Figure 5
    fig, ax = plt.subplots(figsize=(5.2, 4.1))

    for delay in SEC_DELAYS:
        points = sorted(
            (row for row in sec_rows if row["Delay_s"] == delay),
            key=lambda row: row["THV_ms"],
        )
        fpr = [0.0] + [row["FPR"] for row in points] + [1.0]
        tpr = [0.0] + [row["TPR"] for row in points] + [1.0]
        ax.plot(
            fpr,
            tpr,
            marker="o",
            markersize=3,
            linewidth=1.3,
            label=f"{delay} s",
        )

    ax.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        linewidth=1.0,
        label="Random classifier",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)

    save_figure(fig, "fig5_roc_seconds")

    # Figure 6
    fig, ax = plt.subplots(figsize=(6.7, 4.0))
    width = 0.14

    for i, delay in enumerate(SEC_DELAYS):
        values = [row[f"TNR_{delay}s"] for row in fig6_rows]
        offsets = [position + (i - 2) * width for position in x]
        ax.bar(offsets, values, width=width, label=f"{delay} s TNR")

    ax.plot(
        x,
        [row["Cumulative_TPR"] for row in fig6_rows],
        marker="o",
        linewidth=1.7,
        label="TPR",
    )
    ax.set_xticks(x, labels)
    ax.set_xlabel("THV (ms)")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=3, frameon=False, fontsize=8)

    save_figure(fig, "fig6_tnr_tpr_seconds")

    # Figures 7a–7c
    weight_specs = [
        ("Performance_critical_wTP_0.8", "Performance-critical ($w_{TP}=0.8$)"),
        ("Balanced_wTP_0.5_wTN_0.5", "Balanced ($w_{TP}=w_{TN}=0.5$)"),
        ("Security_critical_wTN_0.8", "Security-critical ($w_{TN}=0.8$)"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.25), sharey=True)

    for ax, (field, title) in zip(axes, weight_specs):
        for delay in SEC_DELAYS:
            values = [
                next(
                    row[field]
                    for row in fig7_rows
                    if row["THV_ms"] == thv and row["Delay_s"] == delay
                )
                for thv in THVS
            ]
            ax.plot(
                x,
                values,
                marker="o",
                markersize=3,
                linewidth=1.1,
                label=f"{delay} s",
            )

        ax.set_xticks(x, labels)
        ax.set_xlabel("THV (ms)")
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.25)

    axes[0].set_ylabel("Weighted score")
    axes[0].legend(frameon=False, fontsize=7, ncol=2)

    save_figure(fig, "fig7_weighted_seconds")

    # Figure 8
    fig, ax = plt.subplots(figsize=(5.2, 4.1))

    for delay in MS_DELAYS:
        points = sorted(
            (row for row in ms_rows if row["Delay_ms"] == delay),
            key=lambda row: row["THV_ms"],
        )
        fpr = [0.0] + [row["FPR"] for row in points] + [1.0]
        tpr = [0.0] + [row["TPR"] for row in points] + [1.0]
        ax.plot(
            fpr,
            tpr,
            marker="o",
            markersize=3,
            linewidth=1.3,
            label=f"{delay} ms",
        )

    ax.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        linewidth=1.0,
        label="Random classifier",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)

    save_figure(fig, "fig8_roc_milliseconds")

    # Figures 9a–9c
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.25), sharey=True)

    for ax, (field, title) in zip(axes, weight_specs):
        for delay in MS_DELAYS:
            values = [
                next(
                    row[field]
                    for row in fig9_rows
                    if row["THV_ms"] == thv and row["Delay_ms"] == delay
                )
                for thv in THVS
            ]
            ax.plot(
                x,
                values,
                marker="o",
                markersize=3,
                linewidth=1.1,
                label=f"{delay} ms",
            )

        ax.set_xticks(x, labels)
        ax.set_xlabel("THV (ms)")
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.25)

    axes[0].set_ylabel("Weighted score")
    axes[0].legend(frameon=False, fontsize=7, ncol=2)

    save_figure(fig, "fig9_weighted_milliseconds")

    # Figure 10
    fig, ax = plt.subplots(figsize=(6.7, 4.0))
    width = 0.14

    for i, delay in enumerate(MS_DELAYS):
        values = [row[f"TNR_{delay}ms"] for row in fig10_rows]
        offsets = [position + (i - 2) * width for position in x]
        ax.bar(offsets, values, width=width, label=f"{delay} ms TNR")

    ax.plot(
        x,
        [row["Cumulative_TPR"] for row in fig10_rows],
        marker="o",
        linewidth=1.7,
        label="TPR",
    )
    ax.set_xticks(x, labels)
    ax.set_xlabel("THV (ms)")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=3, frameon=False, fontsize=8)

    save_figure(fig, "fig10_tnr_tpr_milliseconds")

    # Figure 11
    delay_labels = [
        "500 ms",
        "700 ms",
        "900 ms",
        "1 s",
        "2 s",
        "3 s",
        "4 s",
        "5 s",
    ]
    delay_x = list(range(len(delay_labels)))

    fig, ax = plt.subplots(figsize=(6.8, 4.0))

    for thv in THVS:
        values = [
            next(
                row["TNR"]
                for row in fig11_rows
                if row["THV_ms"] == thv and row["Delay"] == label
            )
            for label in delay_labels
        ]

        ax.plot(
            delay_x,
            values,
            marker="o",
            markersize=3.5,
            linewidth=1.25,
            label=str(thv),
        )

    ax.set_xticks(delay_x, delay_labels)
    ax.set_xlabel("Replay delay $\\Delta t$")
    ax.set_ylabel("TNR")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(
        title="THV (ms)",
        frameon=False,
        ncol=3,
        fontsize=8,
        title_fontsize=8,
    )

    save_figure(fig, "fig11_replay_ms_seconds_all_thv")


def main() -> int:
    (
        fig3,
        sec_rows,
        sec_aggregate,
        ms_rows,
        ms_aggregate,
        fig11_rows,
    ) = build_data()

    fig6_rows, fig7_rows, fig9_rows, fig10_rows = write_derived(
        fig3,
        sec_rows,
        sec_aggregate,
        ms_rows,
        ms_aggregate,
        fig11_rows,
    )

    plot_all(
        fig3,
        sec_rows,
        sec_aggregate,
        ms_rows,
        ms_aggregate,
        fig11_rows,
        fig6_rows,
        fig7_rows,
        fig9_rows,
        fig10_rows,
    )

    print("Reproduction complete.")
    print(f"Derived tables: {DERIVED}")
    print(f"Figures: {FIGURES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
