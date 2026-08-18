"""
merge_labels.py

Merge several copies of the same quench HDF5 file - each labeled by a
different person - into one file with everyone's labels combined. Assumes
the signal data is identical across inputs; only the labeling attrs differ.

Usage:
    python merge_labels.py output.h5 alice.h5 bob.h5 carol.h5
    python merge_labels.py output.h5 alice.h5 bob.h5 --on-conflict newest

--on-conflict:
    error (default) stop and report conflicts, write nothing
    first / last    keep whichever input file was listed first/last
    newest          keep whichever labeler's checked_at is most recent
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import shutil
from pathlib import Path

import h5py

from interface.quench_config import LABELS, CHECKED, NOTE, CHECKED_AT, NEEDS_SPECIALIST
from h5_reader import find_event_groups, read_event_status as read_status


def pick_winner(candidates, on_conflict):
    """candidates: [(source_filename, status_dict), ...], all checked=True for one event."""
    if len({status["label"] for _, status in candidates}) == 1:
        return candidates[0], False  # everyone agrees - not a real conflict

    if on_conflict == "error":
        raise ValueError(", ".join(f"{src}={s['label']}" for src, s in candidates))
    if on_conflict == "first":
        return candidates[0], True
    if on_conflict == "last":
        return candidates[-1], True
    if on_conflict == "newest":
        return max(candidates, key=lambda item: item[1]["checked_at"] or ""), True
    raise ValueError(f"unknown --on-conflict value: {on_conflict!r}")


def plan_merge(input_paths, on_conflict):
    """Read-only pass: figure out the merged result per event. No writes."""
    readers = [h5py.File(p, "r") for p in input_paths]
    try:
        decisions, conflicts = {}, []

        for event_path in find_event_groups(readers[0]):
            candidates = [
                (p.name, read_status(r[event_path]))
                for p, r in zip(input_paths, readers)
                if event_path in r and read_status(r[event_path])["checked"]
            ]
            if not candidates:
                continue

            try:
                (winner_src, winner), had_conflict = pick_winner(candidates, on_conflict)
            except ValueError:
                conflicts.append((event_path, candidates))
                continue

            if had_conflict:
                conflicts.append((event_path, candidates))

            # Keep "needs specialist" if ANY labeler flagged it, regardless of who won.
            needs_specialist = any(s["needs_specialist"] for _, s in candidates)
            decisions[event_path] = {**winner, "needs_specialist": needs_specialist}

        return decisions, conflicts
    finally:
        for r in readers:
            r.close()


def apply_merge(output_path, base_input, decisions):
    shutil.copyfile(base_input, output_path)
    with h5py.File(output_path, "a") as out_f:
        for event_path, status in decisions.items():
            group = out_f[event_path]
            group.attrs[CHECKED] = True
            group.attrs[LABELS] = status["label"]
            group.attrs[NOTE] = status["note"] or ""
            group.attrs[CHECKED_AT] = status["checked_at"] or ""
            group.attrs[NEEDS_SPECIALIST] = status["needs_specialist"]


def print_conflicts(conflicts):
    print(f"\n{len(conflicts)} event(s) had conflicting labels:")
    for event_path, candidates in conflicts:
        print(f"  {event_path}: " + ", ".join(f"{src}={s['label']}" for src, s in candidates))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", help="Path to write the merged h5 file to")
    parser.add_argument("inputs", nargs="+", help="Input h5 files to merge (2 or more)")
    parser.add_argument("--on-conflict", choices=["first", "last", "newest", "error"], default="error")
    args = parser.parse_args()

    if len(args.inputs) < 2:
        parser.error("Provide at least 2 input files to merge")

    input_paths = [Path(p) for p in args.inputs]
    for p in input_paths:
        if not p.is_file():
            parser.error(f"Input file not found: {p}")

    decisions, conflicts = plan_merge(input_paths, args.on_conflict)

    if conflicts and args.on_conflict == "error":
        print("Merge aborted - conflicting labels found (nothing was written).")
        print_conflicts(conflicts)
        print("\nRe-run with --on-conflict first|last|newest to resolve automatically.")
        sys.exit(1)

    apply_merge(args.output, input_paths[0], decisions)
    print(f"Merged {len(input_paths)} files into {args.output}")
    print(f"{len(decisions)} labeled event(s) written")
    if conflicts:
        print_conflicts(conflicts)


if __name__ == "__main__":
    main()