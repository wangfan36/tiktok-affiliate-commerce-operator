# Measurement, experiments, and private state

Use this reference for post-publish diagnosis, controlled experiments, operating
decisions, and authorized persistence.

## Normalize before comparison

For every video record account, product ID, version, publish date/time, duration,
organic/paid source, price, stock, shipping, promotion, linked SKU, observation
window, and attribution definition. Compare videos only within a coherent cohort or
state the confounders.

Preferred funnel metrics:

```text
3s hold rate = viewers reaching 3 seconds / video starts
completion rate = completed views / video starts
product CTR = product clicks / qualified video views
click-to-order CVR = attributed orders / product clicks
GPM = attributed GMV / qualified video views × 1000
commission GPM = attributed commission / qualified video views × 1000
net contribution = collected commission − refunds/clawbacks − creative − ads − tools
```

Use the platform's definition when it differs. A zero or incompatible denominator
means the metric is unavailable, not zero performance. External benchmark ranges are
hypotheses; compare first with the account's rolling median and same-product cohort.

## Diagnose the first failing transition

```text
qualified view → retained view → product click → order
→ attributed commission → net contribution
```

| Pattern | First likely bottleneck | Next single-variable test |
|---|---|---|
| Weak 3s hold | Opening is slow, unclear, or attracts the wrong buyer | Replace first frame/action/line only |
| Good hold, weak completion | Promise pays off late or proof drags | Move proof earlier or remove setup |
| Good completion, weak CTR | Product value or click reason is unclear | Change value expression or CTA only |
| Good CTR, weak order CVR | PDP, price, reviews, shipping, stock, variant, or trust | Audit listing/offer before more traffic |
| Good orders, weak commission GPM | Order value, commission, attribution, or qualified volume | Recheck economics and denominator |
| High GMV, weak net contribution | Refunds, costs, or commission economics | `PAUSE` until profit passes |
| Strong funnel, limited reach | Creative volume, eligibility, account fit, or cohort size | Check policy/account health; test hooks |

These are hypotheses to test, not claims about TikTok's proprietary algorithm.

## Experiment contract

Pre-register:

```text
decision | hypothesis | scope | treatment | control | assignment
| primary metric | secondary metrics | guardrails | sample/duration rule
| pass/fail/inconclusive thresholds | confounders | stop condition
```

Change one major variable per test. Do not stop only because a favorable spike
appears. Do not repost an identical protected video and call duplication a valid
creative experiment.

Use actions:

- `TEST`: bounded evidence-gathering experiment.
- `SCALE`: repeatable conversion and positive net contribution with inventory and
  policy gates passed.
- `PAUSE`: stop traffic or production pending a correctable blocker.
- `MONITOR`: no action yet; wait for a predefined data event.
- `INVESTIGATE`: resolve data quality, attribution, compliance, or causal ambiguity.
- `RETIRE`: economics, demand, policy, or fatigue fails the threshold.

## First-hour behavior

Treat the first hour as monitoring and customer response, not a manipulation window.
Verify the SKU, caption, disclosure, sound, and availability; answer genuine
questions; record real metrics. Never coordinate fake completion, likes, comments,
clicks, or orders. Prefer a new controlled variant over assuming a title or music
edit will reset distribution.

## Private state

Default private root, created only after explicit save authorization:

```text
E:\出海生意\运营数据\tiktok-affiliate-commerce-operator\
|-- profile.yaml
|-- candidates\YYYY-MM-DD.json
|-- experiments\experiments.jsonl
|-- metrics\video_metrics.csv
`-- sources\source_ledger.jsonl
```

Read existing relevant private state when available. A request to run analysis does
not authorize writing. Ask for or rely on explicit wording such as “保存这次结果”
before creating or updating state.

### State contracts

`profile.yaml` may contain market, price band, commission floor, categories,
business model, risk preference, and default cohort settings. Current instructions
override it for the current run; do not silently rewrite it.

Candidate snapshots preserve schema version, access time, filters, pages scanned,
provider fields, normalized values, status, reasons, formulas, assumptions, and
source URLs/IDs.

Each experiment JSONL record contains a unique experiment ID, product/video IDs,
hypothesis, one changed variable, controls, primary metric, attribution window,
thresholds, guardrails, stop condition, dates, result, and decision.

`video_metrics.csv` columns:

```text
video_id,version,product_id,account,published_at,observed_at,duration_seconds,
traffic_source,attribution_window,qualified_views,views_3s,completed_views,
average_watch_seconds,product_clicks,attributed_orders,attributed_gmv,
attributed_commission,refunds_clawbacks,creative_cost,ad_cost,tool_cost,
price,commission_rate,stock_status,notes
```

Source ledger records the claim, title, publisher, direct URL, event/effective date,
published/updated date, accessed date, market/category, evidence level, confidence,
conflicts, and caveats.

Never persist keys, tokens, cookies, session URLs, customer data, private messages,
creator contact details, payment data, precise private account identifiers, or KYC
documents. Never publish or commit private state.

## Post-publish output

Return the data window and definitions, verified observations, first failing funnel
transition, likely causes ranked by evidence, exact next variant, variables held
constant, threshold versus baseline, unknowns, and one operating action. End with no
more than three next tasks and a clear “do not do yet” restraint when relevant.
