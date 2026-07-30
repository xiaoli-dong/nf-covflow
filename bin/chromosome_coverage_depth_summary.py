#!/usr/bin/env python3
"""
coverage_stats_summary.py

Generate a chromosome-wise coverage summary by merging Samtools flagstat and
Mosdepth outputs.

Outputs a TSV containing:
    sample
    chromosome
    chromosome length
    mapped reads
    mapped bases
    mean depth
    minimum depth
    maximum depth
"""

import argparse
import pandas as pd
import re

# -----------------------------
# Argument parsing
# -----------------------------
parser = argparse.ArgumentParser(
    description="Generate chromosome-wise coverage summary from Samtools flagstat and Mosdepth outputs"
)
parser.add_argument("--samtools_flagstat", required=True, help="Samtools flagstat file")
parser.add_argument("--mosdepth_summary", required=True, help="Mosdepth summary.txt file")
parser.add_argument("--sample", required=True, help="Sample name")
parser.add_argument("--output", required=True, help="Output TSV file")
args = parser.parse_args()

# -----------------------------
# Read Samtools flagstat
# -----------------------------
mapped_reads = None

with open(args.samtools_flagstat) as f:
    for line in f:
        line = line.strip()

        # Match:
        # 38057 + 0 mapped (100.00% : N/A)
        if re.search(r"\smapped\s*\(", line):
            m = re.match(r"(\d+)\s+\+\s+\d+\s+mapped", line)
            if m:
                mapped_reads = int(m.group(1))
                break

if mapped_reads is None:
    raise ValueError(
        f"Could not parse mapped reads from {args.samtools_flagstat}"
    )

# -----------------------------
# Read Mosdepth summary
# -----------------------------
df_summary = pd.read_csv(args.mosdepth_summary, sep="\t")

# Remove summary rows
df_summary = df_summary[
    (~df_summary["chrom"].str.contains("_region", na=False)) &
    (df_summary["chrom"] != "total")
]

if df_summary.empty:
    print(
        f"Warning: No chromosome-level entries found in {args.mosdepth_summary}. "
        "Writing an empty summary."
    )

# -----------------------------
# Prepare output
# -----------------------------
rows = []

for _, row in df_summary.iterrows():
    rows.append({
        "sample": args.sample,
        "chrom": row["chrom"],
        "length": int(row["length"]),
        "mapped_reads": mapped_reads,
        "mapped_bases": int(row["bases"]),
        "mean_depth": round(float(row["mean"]), 2),
        "min_depth": round(float(row["min"]), 2),
        "max_depth": round(float(row["max"]), 2),
    })

ordered_cols = [
    "sample",
    "chrom",
    "length",
    "mapped_reads",
    "mapped_bases",
    "mean_depth",
    "min_depth",
    "max_depth",
]

# Works whether rows is empty or not
out_df = pd.DataFrame(rows, columns=ordered_cols)

out_df.to_csv(args.output, sep="\t", index=False)

print(f"Saved chromosome-wise coverage summary to {args.output}")
