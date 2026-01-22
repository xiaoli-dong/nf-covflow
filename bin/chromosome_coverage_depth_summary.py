#!/usr/bin/env python3
"""
coverage_stats_summary.py

Generate a chromosome-wise coverage summary by merging Samtools flagstat and Mosdepth outputs.
Outputs TSV with sample name, chromosome, reads mapped, total bases mapped, depth statistics.

Example:
python chromosome_coverage_depth_summary.py \
    --samtools_flagstat results/samtools/barcode49.flagstat \
    --mosdepth_summary results/mosdepth/genome/barcode49.mosdepth.summary.txt \
    --sample barcode49 \
    --output test.tsv
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
parser.add_argument("--sample", required=True, help="Sample name for output")
parser.add_argument("--output", required=True, help="Output TSV file")
args = parser.parse_args()

# -----------------------------
# Read Samtools flagstat
# -----------------------------
mapped_reads = None
with open(args.samtools_flagstat) as f:
    for line in f:
        line = line.strip()
        # Match the line like "38057 + 0 mapped (100.00% : N/A)"
        if re.search(r'\s+mapped\s*\(', line):
            m = re.match(r'(\d+)\s+\+\s+\d+\s+mapped', line)
            if m:
                mapped_reads = int(m.group(1))
                break

if mapped_reads is None:
    raise ValueError("Could not parse mapped_reads from Samtools flagstat")

# -----------------------------
# Read Mosdepth summary
# -----------------------------
df_summary = pd.read_csv(args.mosdepth_summary, sep="\t")

# Keep only real chromosomes (drop total and *_region rows)
df_summary = df_summary[
    (~df_summary["chrom"].str.contains("_region")) &
    (df_summary["chrom"] != "total")
]

# -----------------------------
# Prepare output per chromosome
# -----------------------------
rows = []
for _, row in df_summary.iterrows():
    row_dict = {
        "sample": args.sample,
        "chrom": row['chrom'],
        "length": int(row['length']),
        "mapped_reads": int(mapped_reads),
        "mapped_bases": int(row['bases']),
        "mean_depth": round(float(row['mean']), 2),
        "min_depth": round(float(row['min']), 2),
        "max_depth": round(float(row['max']), 2),
    }
    rows.append(row_dict)

# -----------------------------
# Save output TSV
# -----------------------------
out_df = pd.DataFrame(rows)
ordered_cols = ["sample", "chrom", "length", "mapped_reads", "mapped_bases",
                "mean_depth", "min_depth", "max_depth"]
out_df = out_df[ordered_cols]

out_df.to_csv(args.output, sep="\t", index=False)
print(f"Saved chromosome-wise coverage summary to {args.output}")
