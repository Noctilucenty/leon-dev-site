# Acquisition decision report

`tools/acquisition_report.py` turns the existing first-party acquisition records
and a reconciled economics worksheet into one fail-closed decision report. It is
read-only: it cannot create, enable, pause, increase, or otherwise change an ad.

The only possible decisions are:

- `PAUSE` — a hard safety, economics, intent-quality, or data-integrity rule failed.
- `ITERATE` — no hard stop fired, but evidence is incomplete or unreconciled.
- `ELIGIBLE_TO_REVIEW` — every declared gate passed. This means human review is
  allowed; it is never an instruction or authorization to raise spend.

## Source of each number

The sources stay separate so the report cannot turn a proxy into a sale:

| Measure | Source | Counting rule |
| --- | --- | --- |
| Clicks and spend | Filled economics CSV | Reconciled Google Ads values; never impressions |
| Sessions | `events.jsonl` | Unique `sessionId` on scoped `page_view` records |
| Inquiries | `leads.jsonl` | Unique `receiptId` |
| Booked | `acquisition.jsonl` | Unique `bookingUid` with authoritative `booked` stage |
| Qualified | `acquisition.jsonl` | Unique `bookingUid` with human-confirmed `qualified` stage |
| Won | `acquisition.jsonl` | Unique `bookingUid` with authoritative `won` stage |

The reporter also reads `attended` for the held-to-qualified economics rule. A
browser calendar-success event is attribution evidence only; it does not create a
booking. Missing files produce `unknown`, and a downstream stage never fills a
missing upstream stage. The weakest transition is selected only from adjacent
transitions whose two counts are both available and whose populations are
numerically coherent.

## Prepare a review

Keep completed inputs private. The `data/` directory is ignored by Git for this
reason.

```bash
cp data/acquisition-ops-run.template.json data/acquisition-ops-run.json
cp data/acquisition-ops-economics.template.csv data/acquisition-ops-economics.csv
```

Fill the run manifest:

- Keep `totalMediaBudgetUsd` at or below `100` and `calendarDays` at or below
  `10`. The window uses inclusive calendar dates, so August 1 through August 10
  is ten days.
- Use `utm-campaign` with the exact campaign and optional source when the JSONL
  exports contain other traffic. First touch, current touch, and last touch are
  all recognized using the existing server field names.
- Use `campaign-only-files` only when every row in each supplied JSONL file was
  deliberately exported for this campaign. It skips attribution filtering.
- Set each `dataReadiness` flag to `true` only after confirming that its export
  covers the complete review window. The production default JSONL can be
  replaceable unless durable storage or a verified sink is configured.
- Set `testComplete` only after the bounded review window has ended and platform
  values have been reconciled.

Fill every non-optional row in the economics copy. Actual booked, held,
qualified, and won counts must equal the authoritative JSONL counts. The booked
call override is the only optional row and, when used, must be stricter than the
calculated limit.

Qualified intent is reviewed separately from click volume. Before it can pass:

- define what an intent-qualified search term means;
- review every eligible platform click in the window;
- record both reviewed and qualified-intent click counts; and
- meet the predeclared minimum intent rate.

A click ID, UTM, session, form submission, or raw click count does not prove
qualified intent.

## Run it

The defaults read the private working copies and the server's standard JSONL
paths:

```bash
python3 tools/acquisition_report.py
python3 tools/acquisition_report.py --format json
```

Explicit exports can be supplied without moving them:

```bash
python3 tools/acquisition_report.py \
  --run /private/path/run.json \
  --economics /private/path/economics.csv \
  --events /private/path/events.jsonl \
  --leads /private/path/leads.jsonl \
  --acquisition /private/path/acquisition.jsonl \
  --format json
```

The tool writes only to stdout. Exit status is `0` for `ITERATE` or
`ELIGIBLE_TO_REVIEW`, and `2` for `PAUSE` or an unreadable control input.

## Non-negotiable gates

The reporter independently enforces these limits even if a platform export or
manifest says otherwise:

- no more than `$100` total media spend;
- no more than `10` inclusive calendar days;
- no more than `$100` allocated to Google;
- exactly `$0` allocated to Meta for this test;
- Google plus Meta cannot exceed the declared total cap;
- complete and valid planning plus actual economics inputs;
- reconciled authoritative lifecycle counts;
- complete first-party exports;
- a completed, full-coverage qualified-intent review above its declared floor;
- every economics stop rule within its owner-declared limit; and
- the owner-declared minimum won-client evidence threshold.

Economics stop rules cover zero-booking spend, cost per booked call,
held-to-qualified rate, and contribution return after the minimum won-client
threshold. Revenue ROAS is not substituted for contribution return. A low-volume
result can therefore remain `ITERATE` even when early conversion rates look good.

No report is a performance guarantee. `ELIGIBLE_TO_REVIEW` exists to permit a
deliberate human decision after evidence is complete, not to automate one.
