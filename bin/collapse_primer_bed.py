#!/usr/bin/env python3
import os
import sys
import re
import errno
import argparse

def parse_args(args=None):
    description = "Collapse LEFT/RIGHT primers in primer BED to single intervals."
    epilog = "Example usage: python collapse_primer_bed.py <FILE_IN> <FILE_OUT>"

    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("FILE_IN", help="Input BED file.")
    parser.add_argument("FILE_OUT", help="Output BED file.")
    parser.add_argument(
        "-lp",
        "--left_primer_suffix",
        type=str,
        dest="LEFT_PRIMER_SUFFIX",
        default="_LEFT",
        help="Suffix for left primer in name column of BED file (default: '_LEFT').",
    )
    parser.add_argument(
        "-rp",
        "--right_primer_suffix",
        type=str,
        dest="RIGHT_PRIMER_SUFFIX",
        default="_RIGHT",
        help="Suffix for right primer in name column of BED file (default: '_RIGHT').",
    )
    return parser.parse_args(args)

def make_dir(path):
    if path:
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

def collapse_primer_bed(file_in, file_out, left_primer_suffix, right_primer_suffix):
    """
    Collapse LEFT/RIGHT primers in BED into a single amplicon interval.
    Preserves extra columns beyond BED6.
    """
    interval_dict = {}
    start_pos_list = {}

    with open(file_in, "r") as fin:
        for line in fin:
            if not line.strip() or line.startswith(("#", "track")):
                continue

            cols = line.strip().split("\t")
            if len(cols) < 4:
                # Skip lines that are too short
                continue

            chrom = cols[0]
            start = int(cols[1])
            end = int(cols[2])
            name = cols[3]
            score = cols[4] if len(cols) > 4 else "0"
            strand = cols[5] if len(cols) > 5 else "+"
            extra_cols = cols[6:] if len(cols) > 6 else []

            # Remove LEFT/RIGHT suffix to get amplicon ID
            primer = re.sub(
                f"(?:{re.escape(left_primer_suffix)}|{re.escape(right_primer_suffix)}).*", "", name
            )

            if primer not in interval_dict:
                interval_dict[primer] = []

            # Store (chrom, start, end, score, strand, extra_cols)
            interval_dict[primer].append((chrom, start, end, score, strand, extra_cols))

            # Track first start position for ordering
            if primer not in start_pos_list:
                start_pos_list[primer] = start
            else:
                start_pos_list[primer] = min(start_pos_list[primer], start)

    # Write collapsed BED
    with open(file_out, "w") as fout:
        # Sort primers by first start position
        for primer in sorted(start_pos_list, key=start_pos_list.get):
            entries = interval_dict[primer]
            chrom = entries[0][0]
            start = min(e[1] for e in entries)
            end = max(e[2] for e in entries)
            score = entries[0][3]
            strand = entries[0][4]

            # Merge extra columns from all entries (concatenate with ";")
            max_cols_len = max(len(e[5]) for e in entries)
            merged_extra = []
            for i in range(max_cols_len):
                # Collect i-th column from all entries, if exists
                col_vals = [e[5][i] for e in entries if len(e[5]) > i]
                merged_extra.append(";".join(col_vals))

            fout.write("\t".join([chrom, str(start), str(end), primer, score, strand] + merged_extra) + "\n")

    print(f"✔ Collapsed BED written to: {file_out}")

def main(args=None):
    args = parse_args(args)
    collapse_primer_bed(args.FILE_IN, args.FILE_OUT, args.LEFT_PRIMER_SUFFIX, args.RIGHT_PRIMER_SUFFIX)

if __name__ == "__main__":
    sys.exit(main())
