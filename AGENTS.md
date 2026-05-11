# Agent preferences for this repository

Notes for AI coding assistants (e.g. GitHub Copilot) working in this repo.
These reflect preferences established during pair-programming sessions and
should be followed unless the user says otherwise in a specific request.

## Operational safety

- **Never run destructive shell commands without explicit approval.** This
  includes `rm`, `rm -rf`, `git reset --hard`, `git push --force`, dropping
  tables, `--no-verify`, etc. If a tool call fails (for example
  `create_file` reporting that a file already exists), switch to an in-place
  edit tool — do **not** propose deleting the file as a workaround.
- Prefer in-place edits (`replace_string_in_file` /
  `multi_replace_string_in_file`) over recreating files from scratch.
- Read a file before modifying it; never edit blind.

## Working style

- Keep responses brief. Skip filler intros/outros.
- For multi-step refactors, **stop between steps and wait for confirmation**
  before continuing. Do not chain steps together unless explicitly told to.
- Before implementing a non-trivial plan, lay it out and ask for sign-off.
- Don't add features, refactors, docstrings, comments, type hints, or
  error handling that weren't requested.
- Don't delete commented-out code unless asked.
- Don't create markdown documentation files unless asked.

## Data-format preferences in this repo

- **HDF5 files (`quench_data_L*.h5`) are the portable source of truth** for
  quench data. Plotting / analysis code should load from these.
- Avoid pickle (`.pkl`) for any artifact meant to outlive a single Python
  environment — pickle breaks across pandas/numpy versions
  (`NDArrayBacked.__setstate__` style errors). Use pickle only as a
  short-lived local cache that the script can regenerate.
- For tabular interchange prefer Parquet; for small dict-like summaries
  prefer JSON.
- Per-event quench records use timestamps in the format `YYYYMMDD_HHMMSS`
  as the HDF5 group name under `CM*/CAV*/`.

## Code-shape preferences

- Prefer one flat events DataFrame (one row per quench event) over nested
  `dict[cm][sub] = count` structures. Let plotting code do its own
  `groupby` rather than precomputing many parallel aggregations.
- Keep loader/adapter modules small; push aggregation into the call site.
- When a plotting function would create a figure per loop iteration,
  that's a bug — create the figure once outside the loop.

## Plotting conventions in this repo

- The canonical data shape for plots is the events DataFrame returned by
  `quench_data_summary.load_quench_events`, with columns
  ``source_file, cm, cav, date, year, month, day, is_real``.
- Plot functions live in `quench_plots.py`. Each takes the events frame
  (plus optional filters like `classification` ∈ {"all","real","fake"}
  and `cryo_slice=(start, stop)`) and does its own aggregation.
- Plot functions share the helpers `_filter_class`, `_annotate_bars`,
  `_style`, and `_finish`. New plots should reuse them.
- `save_path=None` means "don't save"; passing a path writes PNG at
  300 dpi via `_finish`. `show=False` is the default; the figure is
  closed after save to keep memory bounded.

## File-link / output formatting

- Use Markdown links to workspace-relative paths for file references
  (e.g. `[slacq/foo.py](slacq/foo.py)`), not inline code spans.
- Use KaTeX (`$...$` / `$$...$$`) for math.
