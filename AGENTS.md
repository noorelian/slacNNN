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
- Inline single-use helpers. If a private function (`_foo`) is called
  from exactly one place and is only a thin wrapper around a few lines,
  fold it back into its caller. Example: `_events_from_h5` was removed
  once `_resolve_paths` existed because `load_quench_events` could do
  the walk inline with no loss of clarity.

## Plotting conventions in this repo

- The canonical data shape for plots is the events DataFrame returned by
  `quench_data_summary.load_quench_events`, with columns
  ``source_file, cm, cav, date, year, month, day, is_real``.
- Plot functions live in `quench_plots.py`. Each takes the events frame
  (plus optional filters like `classification` ∈ {"all","real","false"}
  and `cm_slice=(start, stop)`) and does its own aggregation.
- Plot functions share the helpers `_filter_class`, `_annotate_bars`,
  `_style`, and `_finish`. New plots should reuse them.
- `save_path=None` means "don't save"; passing a path writes PNG at
  300 dpi via `_finish`. `show=False` is the default; the figure is
  closed after save to keep memory bounded.

## Palette and styling defaults

- Color-blind-friendly palette is the default:
  - `REAL_COLOR = "#009E73"` (Okabe-Ito green)
  - `FALSE_COLOR = "#8C1515"` (Stanford cardinal red)
  - `BAR_COLOR  = "#0072B2"` (Okabe-Ito blue, generic single-color bars)
- Linac sections (`SECTIONS` table) use distinct CB-safe colors:
  L0 `#0072B2`, L1 `#009E73`, HL `#D55E00`, L2 `#AA4499`, L3 `#E69F00`.
- For grayscale legibility, the False (red) series carries a `//` hatch
  in both the pie chart and the stacked bar chart. When adding new red
  series, mirror that pattern.
- Default font / figsize constants live at the top of `quench_plots.py`
  (`DEFAULT_FONT`, `DEFAULT_FIGSIZE`). Reuse them; don't sprinkle magic
  numbers in plot calls.
- Common axis labels are centralized as `XLABEL_CM = "Cryomodule Number"`
  and `YLABEL_COUNT = "Number of Quenches"`. Pass `None` to `_style` for
  these defaults; pass a string only when the axis is genuinely different
  (e.g. `"Cavity Number"`, `"Month"`).
- Plot titles use **sentence case**: capitalize only the first word and
  proper identifiers (e.g. `CM01-CM35`). Do not Title-Case every word.

## Cryomodule ordering

- Physical CM order is
  `["CM01","CM02","CM03","CMH1","CMH2"] + [f"CM{n:02d}" for n in range(4,36)]`.
  The driver script applies this as a `pd.Categorical` to `events["cm"]`
  before plotting.
- Always pass `observed=True` to `groupby` on Categorical columns to
  silence the pandas FutureWarning and avoid empty-category rows.

## Common data gotchas

- `events["year"]`, `events["month"]`, `events["day"]` are **strings**
  (zero-padded), not ints. Filter with `== "2022"`, not `== 2022`.
- `add_section_dividers`/`add_section_decorations` will index out of
  range on an empty `cms` list. If a filter could produce an empty
  frame, guard the call site rather than the helper.

## Helper functions in `quench_data_summary.py`

- `mp_events(events, keep=False)` — filter against `data/MPdates.csv`
  (match key `(cm, cav, YYYYMMDD)`). `keep=True` returns only MP rows.
- `peak_quench_day_per_cavity(events, top_n=N, real_only=True)` —
  per-cavity busiest days; returns columns
  `cm, cav, year, month, day, count, rank` (rank 1 = busiest, ties
  broken by earliest date). Also writes
  `data/peak_quench_days.csv`.
- `print_peak_quench_day_summary(...)` — pretty-printed table of the
  same data.
- `peak_days_not_in_mp(peak, mp_events_df)` — set-difference on
  `(cm, cav, year, month, day)`; returns peak rows whose date is not
  in the MP frame. Useful for finding candidate missing MP entries.
- One-liner for "real quenches on quiet (cavity, day) groups":
  ```python
  quiet_real = real_events.groupby(
      ["cm","cav","year","month","day"], observed=True
  ).filter(lambda g: len(g) < THRESHOLD)
  ```

## Driver script conventions (`hdf5_file_plot.py`)

- All plot calls are gated by a `PLOTS = {...}` toggle dict at the top
  of the script. Add new plots there; don't comment whole blocks in/out.
- Slice-derived filenames should be built from the slice itself, e.g.
  `f"..._{cm_slice[0]}-{cm_slice[1]-1}.png"` — don't hardcode CM numbers
  in path strings.
- Keep magic thresholds named (e.g. `PEAK_TOP_N`, `PEAK_MIN_COUNT`) so
  the print line can describe the filter parameters.

## File-link / output formatting

- Use Markdown links to workspace-relative paths for file references
  (e.g. `[slacq/foo.py](slacq/foo.py)`), not inline code spans.
- Use KaTeX (`$...$` / `$$...$$`) for math.
