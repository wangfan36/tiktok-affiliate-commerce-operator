# Selection and economics

Use this reference for selection scans, product deep dives, absolute-growth
ranking, and earnings estimates.

## Default business profile

Apply these defaults unless the current request overrides them:

| Field | Default |
|---|---|
| Market | United States (`US`) |
| Business model | TikTok Shop affiliate creator |
| Currency | USD |
| Warehouse | US local warehouse |
| Listing | On sale |
| Effective selling price | $25–$45 |
| Commission | At least 15% |
| Rating | At least 4.5 |
| Growth definition | Recent rolling 28-day units minus preceding 28-day units |
| Product form | Photo-self-explanatory standard product |
| Production | Major selling assets feasible with product images and AI video |

Use the current effective selling price, not an unverifiable list price. Record the
access time because price, commission, rating, and stock can change.

## FastMoss call plan

Check `fastmoss --version` and `fastmoss whoami`; use the existing OAuth session.
Never request or echo an API key in chat. Inspect live schemas with
`fastmoss tools --search <tool>` when a field is uncertain.

1. Call `product_search` with:
   - `region: US`
   - `is_local_warehouse: true`
   - `listing_status: on_sale`
   - `floor_price_range: {min: 25, max: 45}`
   - `commission_rate_range: {min: 15}`
   - a relevant category or keyword when supplied.
2. Scan at most 30 candidates by default. State the pages and sort used. Do not call
   this a complete market rank unless every eligible page was covered.
3. Apply the photo-understandability gate before expensive enrichment. Deep-dive at
   most 10 candidates by default with `product_detail_info`, `product_sku`, and
   `product_sales_trend` using `time_range_days: 90`.
4. Rank only candidates with a complete 56-calendar-day comparison. Retain at most
   five for creator and video analysis.
5. When TikTok or FastMoss detail links are required, obtain the current link rules
   from `fastmoss_detail_url_examples`; do not invent URLs.

FastMoss is a third-party data source. Preserve the returned product ID and metric
window, and distinguish estimated/provider fields from TikTok product-page facts.

## Hard gates

Treat a verified failure as `REJECT`; treat missing or ambiguous evidence as `HOLD`.

### Product gates

- Region is `US`.
- `is_local_warehouse` is true.
- `listing_status` is `on_sale`.
- Effective price is within $25–$45 inclusive.
- Commission is at least 15 percent.
- Current rating is at least 4.5.
- Product is currently in stock.

### Inventory gate

A single in-stock snapshot proves only **currently in stock**. It does not prove
stability. `ELIGIBLE` requires at least one of:

- usable SKU stock or inventory history;
- a positive days-of-cover calculation based on current usable units and adjusted
  daily demand;
- documented seller replenishment evidence relevant to the current SKU.

Snapshot-only, stale, contradictory, or missing evidence is `HOLD`.

### Photo-self-explanatory AI gate

All must pass:

- a buyer can infer the product's basic use from one clear image;
- the selling action needs no complex assembly or long tutorial;
- the benefit can be shown without an unsupported transformation or fake result;
- AI scenes can preserve the product's shape, parts, scale, color, and identity;
- the concept does not require face/body application or anatomy-dependent proof;
- the main story can be generated from product images, environments, hands, or
  simple adult actions.

Explicitly reject face-applied cosmetics, body-transformation demonstrations,
products whose value depends on fit or diagnosis, and complex-use products when
the user requested photo-self-explanatory standard goods. Regulated or sensitive
claims require separate evidence and policy review.

## Absolute growth

Use exact calendar dates:

```text
recent_28d_units = sum(as_of-27d through as_of)
previous_28d_units = sum(as_of-55d through as_of-28d)
absolute_28d_unit_growth = recent_28d_units - previous_28d_units
```

Do not substitute percentage growth. Do not silently treat missing dates as zero.
If the provider explicitly documents omitted dates as zero-sales days, calendarize
them before running the script and record that rule. Duplicate dates, negative
units, or fewer than 56 complete dates are `HOLD`.

Run the deterministic calculator after normalizing FastMoss output:

```powershell
python scripts\rank_candidates.py candidate-input.json --output ranked.json
```

Input schema version `1.0`:

```json
{
  "schema_version": "1.0",
  "as_of": "2026-08-29",
  "scenario_assumptions": [],
  "candidates": [
    {
      "product_id": "required",
      "name": "required",
      "region": "US",
      "is_local_warehouse": true,
      "listing_status": "on_sale",
      "price": 29.99,
      "commission_rate_percent": 20,
      "rating": 4.7,
      "inventory": {
        "current_in_stock": true,
        "stability_evidence": "sku_stock_history",
        "days_of_cover": null
      },
      "visual": {
        "photo_self_explanatory": true,
        "ai_material_feasible": true,
        "requires_face_or_body_application": false,
        "requires_complex_instruction": false
      },
      "daily_units": [{"date": "2026-08-29", "units": 10}],
      "refund_cancel_rate": 0.08,
      "attributable_cost_per_order": 0.5,
      "funnel": {
        "same_account": true,
        "same_product": true,
        "same_attribution_window": true,
        "product_ctr": 0.02,
        "click_to_order_cvr": 0.05,
        "cost_per_1000_qualified_views": 1.5
      },
      "evidence_confidence": "high"
    }
  ]
}
```

Valid inventory evidence values are `sku_stock_history`, `days_of_cover`,
`seller_replenishment`, and `snapshot_only`. `days_of_cover` evidence also requires
a positive numeric value.

## Earnings

```text
gross commission/order = effective price × commission rate

net commission/order
= gross commission/order × (1 − refund/cancel rate)
− attributable cost/order

expected net commission GPM
= 1000 × product CTR × click-to-order CVR × net commission/order
− cost per 1000 qualified views
```

Use product/account metrics from the same cohort and attribution window. If that
condition is not proven, leave expected GPM null. Raw funnel counts may be used to
derive rates only when qualified views and clicks have positive denominators.

Scenario assumptions may be supplied as named `low`, `base`, and `high` objects
containing `product_ctr`, `click_to_order_cvr`, and optionally
`cost_per_1000_qualified_views`. Label every scenario as assumed, not observed.

Default eligible ranking:

1. absolute 28-day unit growth, descending;
2. net commission per order, descending;
3. recent 28-day units, descending;
4. evidence confidence, descending.

Keep `HOLD` and `REJECT` products outside the eligible rank. A negative-growth
eligible product may remain in the table but must not outrank a larger absolute
increase merely because its percentage growth or commission is high.

## Selection output

Return a compact table with product name and ID, direct/detail link when verified,
price, commission, gross and net commission per order, rating, warehouse, inventory
proof, recent/prior 28-day units, absolute unit increase, visual-gate result,
confidence, status, and reason. Follow it with unknowns, earnings scenarios, and no
more than three next actions.
