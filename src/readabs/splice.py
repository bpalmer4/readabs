"""Priority splicing of mixed-frequency time series.

This module has two layers:

``splice``
    The core primitive.  Deliberately *source-agnostic*: it takes pandas Series
    you have already fetched (by description, by ID, however you like) and
    splices them into one series.  It knows nothing about the ABS, ships no
    static lookup table, and makes no guesses about which series belong together
    — that judgement stays with the caller.

``select`` / ``select_one`` / ``select_and_splice``
    A thin ABS-aware convenience layer over ``splice``.  Each resolves
    ``(data, meta, selector)`` sources to Series via ``readabs.find_abs_id``
    (carrying each series' ABS unit on ``.attrs["unit"]``), so the common case —
    splice a few ABS series selected by description/frequency — is one call,
    while ``select`` stays exposed for when you need a transform between
    selecting and splicing.  A *selector* is either a ``{search_value:
    meta_column}`` dict, or a bare ABS Series ID string when you already know
    exactly which series you want.

Splice design
-------------
Given an ordered list of segments (highest priority / most authoritative
first), :func:`splice`:

1. **align**   — put every segment on one common ``PeriodIndex``.  By default
                 the grid is the *finest* frequency present, which dissolves
                 anchor clashes (Q-NOV vs Q-DEC, A-JUN vs A-DEC) because every
                 coarse period maps cleanly onto a finer one.  Coarser segments
                 are placed at their period-*end*; finer segments are
                 aggregated down with ``agg``.
2. **rebase**  — *(opt-in; off by default)* for each junction,
                 *multiplicatively* scale the lower-priority segment so its level
                 matches the running result over the *overlapping date window*
                 (phase-agnostic; works even when two series never share an exact
                 period).  Falls back to a single junction point if there is no
                 overlap, and flags it.  Off by default because it transforms
                 your data — nothing is silently rescaled unless you ask.

                 Rebasing assumes **ratio-scale** inputs — series whose zero is
                 meaningful and whose discrepancy between segments is
                 *proportional*.  Indexes (CPI, price/volume indices on different
                 base periods) are the canonical case; a proportional benchmark
                 revision of a count works too.  It is **wrong** for series that
                 cross zero (rates of change, balances, net flows) or whose
                 segments differ by an *additive* offset rather than a scale
                 factor — a negative or non-finite factor is caught and raises.
                 With ``rebase=False`` (the default) the raw levels are coalesced
                 as-is: if two same-unit segments already agree, rebasing only
                 invents a discrepancy to "correct".
3. **coalesce**— ``combine_first`` down the priority chain: take segment 1,
                 fill gaps from segment 2, then 3, ...  The result keeps only
                 the periods that actually carry data — a coarse back-history
                 stays sparse on a finer grid rather than being NaN-filled, and
                 nothing is interpolated (pass ``fill=`` to densify).
4. **resample**— (optional) resample the spliced result to a chosen output
                 frequency/anchor.

The returned join report makes every rebase factor and overlap visible, so a
splice can be audited rather than trusted blindly.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Literal, cast

import pandas as pd
from pandas import DataFrame, PeriodIndex, Series

from readabs.abs_meta_data import metacol as mc  # used by the select() layer
from readabs.search_abs_meta import find_abs_id  # used by the select() layer

# Frequency rank — higher number = finer frequency.
_FREQ_RANK: dict[str, int] = {"Y": 0, "A": 0, "Q": 1, "M": 2, "W": 3, "D": 4}


def _base(freqstr: str) -> str:
    """Return the base frequency character (``"Q-NOV"`` -> ``"Q"``, ``"A-JUN"`` -> ``"Y"``)."""
    char = freqstr.split("-", maxsplit=1)[0][0].upper()
    return "Y" if char == "A" else char


def _rank(freqstr: str) -> int:
    """Return the frequency rank for a PeriodIndex freq string."""
    return _FREQ_RANK[_base(freqstr)]


def _as_period_index(s: Series) -> Series:
    """Ensure *s* has a PeriodIndex; convert from DatetimeIndex if needed."""
    if isinstance(s.index, PeriodIndex):
        return s
    if isinstance(s.index, pd.DatetimeIndex):
        return s.set_axis(s.index.to_period())
    raise TypeError(f"Series '{s.name}' must have a PeriodIndex or DatetimeIndex, got {type(s.index).__name__}.")


def _pidx(s: Series) -> PeriodIndex:
    """Return *s*'s index as a (typed) PeriodIndex, converting if necessary."""
    return cast("PeriodIndex", _as_period_index(s).index)


def _pick_target(segments: Sequence[Series]) -> str:
    """Choose the default common-grid freq: the finest present.

    If two or more segments share the *finest* rank but with different anchors
    (e.g. ``Q-NOV`` and ``Q-DEC``) and there is nothing finer to splice them
    onto, raise — picking one anchor would silently reanchor the other and
    could assume wrong.  Resolve it by passing a finer ``target`` (e.g.
    ``"M"``), or by including a finer-frequency segment.
    """
    freqs = [str(_pidx(s).freqstr) for s in segments]
    ranks = [_rank(f) for f in freqs]
    top = max(ranks)
    top_freqs = {f for f, r in zip(freqs, ranks, strict=True) if r == top}
    if len(top_freqs) > 1:
        raise ValueError(
            f"Clashing anchors at the finest frequency: {sorted(top_freqs)}. "
            f"Pass a finer target (e.g. target='M') to splice them on a common grid."
        )
    return next(iter(top_freqs))


def _to_grid(s: Series, target: str, agg: str) -> Series:
    """Map *s* onto the *target* PeriodIndex frequency.

    Finer-than-target segments are aggregated down with *agg*; equal-or-coarser
    segments are placed at their period-end on the target grid.
    """
    s = _as_period_index(s).dropna()
    idx = cast("PeriodIndex", s.index)
    src = str(idx.freqstr)
    if _rank(src) > _rank(target):
        # finer -> coarser: aggregate the sub-periods that fall in each target period
        out = s.groupby(idx.asfreq(target)).agg(agg)
    elif _rank(src) == _rank(target) and _base(src) == _base(target) and src != target:
        # same frequency, different anchor (e.g. Q-NOV vs Q-DEC) — reanchoring
        # would silently shift every period, so refuse rather than assume.
        raise ValueError(
            f"Cannot place '{s.name}' ({src}) onto a {target} grid without reanchoring. "
            f"Use a finer target (e.g. target='M')."
        )
    else:
        # coarser (or identical) -> place each value at its period-end on the grid
        out = Series(s.to_numpy(), index=idx.asfreq(target, how="E"), name=s.name)
        out = out[~out.index.duplicated(keep="last")]
    return out.sort_index()


def _rebase_factor(result: Series, seg: Series) -> tuple[float, str, int, pd.Period | None, pd.Period | None]:
    """Compute the factor to bring *seg* onto *result*'s level.

    Measured as the ratio of mean levels over the overlapping *date span*, so
    it is phase-agnostic — it works even when the two series share no exact
    period (e.g. Q-NOV vs Q-DEC mapped onto a monthly grid).  Falls back to a
    single junction point when the spans do not overlap at all.

    Returns ``(factor, method, overlap_n, window_start, window_end)``.
    """
    r, s = result.dropna(), seg.dropna()
    if len(r) and len(s):
        lo = max(r.index.min(), s.index.min())
        hi = min(r.index.max(), s.index.max())
        if lo <= hi:
            r_win, s_win = r.loc[lo:hi], s.loc[lo:hi]
            if len(r_win) and len(s_win) and s_win.mean():
                return float(r_win.mean() / s_win.mean()), "window", min(len(r_win), len(s_win)), lo, hi
    # No overlapping span — fall back to the nearest junction point.
    r0 = result.first_valid_index()
    if r0 is not None:
        before = s.loc[:r0]
        if len(before) and before.iloc[-1]:
            return float(result.loc[r0] / before.iloc[-1]), "junction", 0, None, None
    return 1.0, "none", 0, None, None


def splice(
    segments: Iterable[Series],
    *,
    target: str | None = None,
    rebase: bool = False,
    agg: str = "mean",
    output: str | None = None,
    fill: Literal["ffill", "interpolate"] | None = None,
    name: str | None = None,
) -> tuple[Series, DataFrame]:
    """Splice mixed-frequency *segments* into one series, highest priority first.

    Parameters
    ----------
    segments
        Ordered list of pandas Series (PeriodIndex or DatetimeIndex).  The
        first is highest priority: it wins where periods overlap and (when
        ``rebase`` is on) sets the level everything else is rebased to.
    target
        Common-grid frequency (e.g. ``"M"``, ``"Q-DEC"``).  Defaults to the
        finest frequency present (anchor clashes step one rank finer).
    rebase
        Off by default — segments are coalesced at their **raw** levels, with no
        silent transformation of your data.  Set ``True`` to *multiplicatively*
        rescale each lower-priority segment to the running result's level before
        coalescing.  Rebasing assumes **ratio-scale** inputs (meaningful zero,
        proportional discrepancy between segments) — splicing index series on
        different base periods (CPI, price/volume indices) is the case that
        needs it.  It is wrong for zero-crossing series (rates, balances) or
        additive level breaks, and it *invents* a correction when same-unit
        segments already agree — which is why it is opt-in.  A non-finite or
        non-positive factor raises.  See the module docstring's *rebase* step.
    agg
        Aggregator used when a segment is finer than the grid (or when
        downsampling to *output*).  ``"mean"`` for index levels; use ``"sum"``
        for flows.
    output
        Optional final frequency to resample the spliced result to.
    fill
        Optional gap fill.  By default (``None``) the result contains only the
        periods that actually have data — no NaN rows are inserted for the gaps
        a coarse segment leaves on a finer grid, and nothing is interpolated.
        ``"ffill"`` or ``"interpolate"`` densify the result onto the full grid
        first and then fill.
    name
        Name for the result series (defaults to the first segment's name).

    Returns
    -------
    tuple[Series, DataFrame]
        The spliced series and a one-row-per-junction report.

    """
    segments = list(segments)
    if not segments:
        raise ValueError("splice() needs at least one segment.")

    grid = target or _pick_target(segments)
    on_grid = [_to_grid(s, grid, agg) for s in segments]

    result = on_grid[0].copy()
    rows: list[dict[str, object]] = []
    for i, seg in enumerate(on_grid[1:], start=1):
        if rebase:
            factor, method, n, lo, hi = _rebase_factor(result, seg)
            # Multiplicative rebasing assumes ratio-scale inputs.  A non-finite
            # factor (near-zero denominator) or a non-positive one (the overlap
            # means have opposite signs, which would flip the back-history) means
            # the data is not ratio-scale — fail loud rather than ship it.  A
            # large *magnitude* is fine: a legitimate base-period difference can
            # need a 50x factor, so only sign and finiteness are guarded.
            if not (math.isfinite(factor) and factor > 0):
                raise ValueError(
                    f"splice: rebase factor for segment {i} ('{seg.name}') is {factor} over "
                    f"{lo}..{hi}. Multiplicative rebasing needs ratio-scale inputs (meaningful "
                    f"zero, proportional discrepancy); a non-finite or non-positive factor means "
                    f"the segments cross zero or differ additively. Pass rebase=False to coalesce "
                    f"raw levels instead."
                )
        else:
            factor, method, n, lo, hi = 1.0, "off", 0, None, None
        seg_rebased = seg * factor
        rows.append(
            {
                "segment": i,
                "name": str(seg.name),
                "freq_in": str(_pidx(segments[i]).freqstr),
                "method": method,
                "overlap_n": n,
                "window_start": str(lo) if lo is not None else "",
                "window_end": str(hi) if hi is not None else "",
                "factor": round(factor, 6),
                "fills_from": str(seg.dropna().index.min()),
            }
        )
        result = result.combine_first(seg_rebased)

    # By default keep only the periods that actually carry data: do NOT reindex
    # onto a dense grid (which would manufacture NaN for the gaps a coarse
    # back-history leaves on a finer grid) and do NOT interpolate.  A long-run
    # series therefore stays sparse where it is old and coarse, and plots as one
    # continuous line with no holes and no invented points.
    result = result.dropna().sort_index()

    if output and output != grid:
        result = _to_grid(result, output, agg).dropna().sort_index()
        grid = output

    if fill in ("ffill", "interpolate") and len(result):
        # Explicit opt-in: densify onto the full grid, then fill.
        full = pd.period_range(result.index.min(), result.index.max(), freq=grid)
        result = result.reindex(full)
        result = result.ffill() if fill == "ffill" else result.interpolate()

    result.name = name or str(segments[0].name)
    report = DataFrame(rows)
    return result, report


# A select_and_splice() source: the fetched data dict, its meta, and either a
# {search_value: meta_column} selector (readabs' find_abs_id convention) or a
# bare ABS Series ID string (matched exactly against the Series ID column).
Source = tuple[dict[str, DataFrame], DataFrame, dict[str, str] | str]


def select_one(data: dict[str, DataFrame], meta: DataFrame, selector: dict[str, str] | str) -> Series:
    """Select the single Series for one ``(data, meta, selector)`` — the single-source wrapper.

    Convenience for the common one-selector case; equivalent to
    ``select([(data, meta, selector)])[0]``.  The *selector* is either a
    ``{search_value: meta_column}`` dict for ``find_abs_id``, or a bare ABS
    Series ID string, matched exactly against the metadata's Series ID column.
    Returns the Series named by its Series ID, with its ABS unit on
    ``.attrs["unit"]``.
    """
    if isinstance(selector, str):
        # A bare Series ID — same find_abs_id machinery, but exact-match on the
        # Series ID column so one ID cannot substring-match another.
        try:
            table, series_id, unit = find_abs_id(meta, {selector: mc.id}, exact_match=True, validate_unique=True)
        except ValueError as exc:
            raise ValueError(f"select: series ID {selector!r} not found in the supplied metadata.") from exc
    else:
        table, series_id, unit = find_abs_id(meta, selector, validate_unique=True)
    s = data[table][series_id].copy()
    s.name = series_id
    s.attrs["unit"] = str(unit)
    return s


def select(sources: Iterable[Source], *, require_same_units: bool = True) -> list[Series]:
    """Select a series for each ``(data, meta, selector)`` — the iterable in, iterable out.

    The composable selection primitive: takes the iterable of ``(data, meta,
    selector)`` sources and returns the matching list of Series, ready to hand to
    :func:`splice` (directly, or after a per-series transform).  Each selection
    goes through ``readabs.find_abs_id`` with ``validate_unique=True``, which
    de-duplicates on Series ID first — so a selector matching the same series in
    several tables resolves cleanly, while one matching two genuinely different
    series raises rather than guessing.

    Parameters
    ----------
    sources
        Iterable of ``(data, meta, selector)``:

        - ``data``   — ``dict[table_name, DataFrame]`` from ``read_abs_cat``.
        - ``meta``   — the matching metadata DataFrame.
        - ``selector`` — ``{search_value: meta_column}`` for ``find_abs_id``, e.g.
          ``{"Index Numbers ;  All groups CPI ;  Australia ;": mc.did,
          "Index Numbers": mc.unit, "Quarter": mc.freq}``; or a bare ABS Series
          ID string (e.g. ``"A2325846C"``), matched exactly.
    require_same_units
        If ``True`` (default) **raise** when the selected series do not all share
        the same ABS unit — units must cohere to be spliced.  Set ``False`` when
        you deliberately select different-unit series together (e.g. two counts
        and a rate that you will combine yourself).

    Returns
    -------
    list[Series]
        One Series per source, each named by its Series ID with its ABS unit in
        ``series.attrs["unit"]``.  Unpack it (``a, b = select([...])``), map a
        transform over it, or pass it straight to :func:`splice`.  A later
        transform drops the unit attr — correctly, since the unit is then no
        longer the ABS one.

    Raises
    ------
    ValueError
        If ``require_same_units`` and the selected series carry mixed units.

    """
    segments = [select_one(data, meta, selector) for data, meta, selector in sources]
    if require_same_units:
        units = [str(s.attrs.get("unit", "")) for s in segments]
        if len(set(units)) > 1:
            detail = ", ".join(f"{s.name}={u!r}" for s, u in zip(segments, units, strict=True))
            raise ValueError(
                f"select: selected series have mismatched units ({detail}). Pass "
                f"require_same_units=False to select different-unit series together."
            )
    return segments


def select_and_splice(
    sources: Iterable[Source],
    *,
    target: str | None = None,
    rebase: bool = False,
    agg: str = "mean",
    output: str | None = None,
    fill: Literal["ffill", "interpolate"] | None = None,
    name: str | None = None,
    require_same_units: bool = True,
) -> tuple[Series, str, DataFrame]:
    """Select one series per source and :func:`splice` them — the no-transform case.

    Sugar for ``splice(select(sources))`` with a unit guard.  When
    you need a transform *between* selecting and splicing (e.g. a growth rate),
    compose :func:`select` and :func:`splice` directly instead — that is the whole
    reason :func:`select` is exposed separately.

    Parameters
    ----------
    sources
        Ordered iterable of ``(data, meta, selector)``, **highest priority
        first** (same priority rule as :func:`splice`):

        - ``data``   — ``dict[table_name, DataFrame]`` from ``read_abs_cat``.
        - ``meta``   — the matching metadata DataFrame.
        - ``selector`` — ``{search_value: meta_column}`` for ``find_abs_id``,
          e.g. ``{"Index Numbers ;  All groups CPI ;  Australia ;": mc.did,
          "Index Numbers": mc.unit, "Quarter": mc.freq}``; or a bare ABS Series
          ID string (e.g. ``"A2325846C"``), matched exactly.  In the common case
          the only thing differing between two sources is the frequency, so a
          shared *base* selector composes with ``base | {"Quarter": mc.freq}``.
    target, rebase, agg, output, fill, name
        Passed straight through to :func:`splice`.
    require_same_units
        Forwarded to :func:`select`: if ``True`` (default) raise when the
        selected segments carry mixed units; ``False`` overrides (the result is
        then labelled with the highest-priority segment's unit).

    Returns
    -------
    tuple[Series, str, DataFrame]
        The spliced series, its unit (the highest-priority segment's unit), and
        the :func:`splice` join report, augmented with ``series_id`` and
        ``unit`` columns recording what each segment resolved to.

    """
    segments = select(sources, require_same_units=require_same_units)
    units = [str(s.attrs.get("unit", "")) for s in segments]

    result, report = splice(segments, target=target, rebase=rebase, agg=agg, output=output, fill=fill, name=name)
    # Audit trail: which Series ID / unit did each reported (lower-priority) segment use?
    if len(report):
        seg = [int(i) for i in report["segment"]]
        report.insert(1, "series_id", [str(segments[i].name) for i in seg])
        report.insert(2, "unit", [units[i] for i in seg])
    return result, units[0], report


# ---------------------------------------------------------------------------
# Self-tests — `python splice.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import numpy as np

    def _show(title: str, s: Series, rep: DataFrame) -> None:
        print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
        print(
            f"freq={cast('PeriodIndex', s.index).freqstr}  n={len(s)}  non-null={s.notna().sum()}  "
            f"range={s.index.min()}..{s.index.max()}"
        )
        if len(rep):
            print(rep.to_string(index=False))

    # --- Case 1: monthly (new) + quarterly (old), level shift via index rebase
    q = Series(
        np.arange(100, 100 + 4 * 20, dtype=float),  # 20 years quarterly, base ~100
        index=pd.period_range("2000Q1", periods=80, freq="Q-DEC"),
        name="cpi",
    )
    m = Series(
        np.arange(50.0, 50.0 + 60) * 0.5 + 130,  # monthly on a *different* base
        index=pd.period_range("2018-01", periods=60, freq="M"),
        name="cpi",
    )
    out, rep = splice([m, q], rebase=True)  # monthly priority, quarterly fills the back-history
    _show("Case 1 — M (priority) spliced with Q-DEC, auto-grid", out, rep)
    print(f"check: rebased Q value at 2018-03 = {out.loc['2018-03']:.3f} (monthly 2018-01 = {m.iloc[0]:.3f})")

    # --- Case 2: the anchor clash — Q-NOV vs Q-DEC, overlapping in time
    q_dec = Series(
        np.arange(200.0, 200 + 40),
        index=pd.period_range("2010Q1", periods=40, freq="Q-DEC"),
        name="x",
    )
    q_nov = Series(
        np.arange(80.0, 80 + 60),  # 2000Q1..2014Q4 — overlaps q_dec over 2010-2014
        index=pd.period_range("2000Q1", periods=60, freq="Q-NOV"),
        name="x",
    )
    print(f"\n{'=' * 70}\nCase 2 — Q-DEC + Q-NOV anchor clash\n{'=' * 70}")
    try:
        splice([q_dec, q_nov])  # no target -> must refuse rather than reanchor
    except ValueError as exc:
        print(f"default (no target) correctly raised:\n  {exc}")
    out2, rep2 = splice([q_dec, q_nov], target="M", rebase=True)  # resolve on a common finer grid
    _show("Case 2b — same, resolved with target='M' (window rebase across anchors)", out2, rep2)

    # --- Case 3: daily + monthly.  Default grid is the finest present = D.
    d = Series(
        np.linspace(10, 12, 365),
        index=pd.period_range("2023-01-01", periods=365, freq="D"),
        name="rate",
    )
    mth = Series(
        np.linspace(12, 13, 18),  # 2023-07..2024-12 — overlaps the daily over 2023-H2
        index=pd.period_range("2023-07", periods=18, freq="M"),
        name="rate",
    )
    out3, rep3 = splice([d, mth])  # daily priority -> finest grid = D, monthly placed sparsely
    _show("Case 3 — D (priority) + M, default finest grid = D", out3, rep3)
    out3b, rep3b = splice([mth, d], target="M", agg="mean")  # explicitly ask for a monthly result
    _show("Case 3b — same data, target='M' so daily is aggregated down", out3b, rep3b)

    # --- Case 4: CPI-style 3-way chain (new monthly + indicator + quarterly)
    new_m = Series(np.arange(135.0, 135 + 12), index=pd.period_range("2024-01", periods=12, freq="M"), name="cpi")
    indic = Series(np.arange(120.0, 120 + 30), index=pd.period_range("2022-07", periods=30, freq="M"), name="cpi")
    old_q_index = pd.period_range("1995Q1", periods=120, freq="Q-DEC")
    old_q = Series(np.arange(40.0, 40 + 120), index=old_q_index, name="cpi")
    out4, rep4 = splice([new_m, indic, old_q], name="cpi_long", rebase=True)
    _show("Case 4 — 3-way: new monthly + indicator + quarterly", out4, rep4)
    print(
        f"\nfull series spans {out4.index.min()} .. {out4.index.max()}, {out4.notna().sum()} observations present"
    )

    # --- Case 5: same, but ask for a clean quarterly output (downsample)
    out5, rep5 = splice([new_m, indic, old_q], output="Q-DEC", name="cpi_long_q", rebase=True)
    _show("Case 5 — same 3-way, resampled to a clean Q-DEC output", out5, rep5)

    # --- Case 6: the select() layer — dict selector vs bare Series ID string
    fake_meta = DataFrame(
        {
            mc.did: ["Index Numbers ;  All groups CPI ;  Australia ;"] * 2,
            mc.id: ["A2325846C", "A128478317T"],
            mc.unit: ["Index Numbers", "Index Numbers"],
            mc.freq: ["Quarter", "Month"],
            mc.table: ["640101", "648601"],
        }
    )
    fake_data = {
        "640101": DataFrame({"A2325846C": q.to_numpy()[:40]}, index=q.index[:40]),
        "648601": DataFrame({"A128478317T": m.to_numpy()}, index=m.index),
    }
    by_id = select_one(fake_data, fake_meta, "A2325846C")  # bare Series ID string
    by_dict = select_one(fake_data, fake_meta, {"Month": mc.freq})  # selector dict
    print(f"\n{'=' * 70}\nCase 6 — select_one: bare Series ID vs selector dict\n{'=' * 70}")
    print(f"by ID:   name={by_id.name} unit={by_id.attrs['unit']!r} n={len(by_id)}")
    print(f"by dict: name={by_dict.name} unit={by_dict.attrs['unit']!r} n={len(by_dict)}")
    out6, unit6, rep6 = select_and_splice(
        [(fake_data, fake_meta, "A128478317T"), (fake_data, fake_meta, "A2325846C")], rebase=True
    )
    _show(f"Case 6b — select_and_splice by bare Series IDs (unit={unit6!r})", out6, rep6)
    try:
        select_one(fake_data, fake_meta, "NOSUCHID")  # unknown ID -> fail loud
    except ValueError as exc:
        print(f"unknown ID correctly raised:\n  {exc}")

    print("\nAll cases ran.")
