# TODO

## Type-checker issues (pre-existing, not runtime bugs)

These are flagged by `pyright src/readabs` and/or `mypy src/readabs`. All 14
module self-tests pass; these are type-checker friction only.

- [ ] **`grab_abs_url.py` — `url` declared twice.** `grab_abs_url()` has an explicit
  `url: str = ""` parameter *and* `**kwargs: Unpack[ReadArgs]`, where `ReadArgs`
  also declares `url: NotRequired[str]` (`read_support.py:29`). This produces three
  errors: the param/TypedDict overlap (line 37/40) and the `check_kwargs`/`get_args`
  arg-type mismatches (lines 78-79). `read_support.py:33` already documents that
  `url` is meant to be handled separately — fix by dropping `url` from `ReadArgs`.

- [ ] **`grab_abs_url.py:359` — `ExcelFile.parse` not in stubs.** `excel.parse(sheet_name)`
  works at runtime but the pandas type stubs don't expose `.parse` on `ExcelFile`.
  Add a targeted `# type: ignore` / `# pyright: ignore`, or switch to `pd.read_excel`.

- [ ] **`recalibrate.py:78,80` — `Series | DataFrame` union not narrowed by `.shape`.**
  `result` is typed `Series | DataFrame`; the `len(data.shape) == ...` guards don't
  narrow the runtime class, so `result.columns` (line 78) and `result.name` (line 80)
  each flag on the type that lacks the attribute. Narrow the branches with
  `isinstance` so both checkers agree.
