---
name: tiktok-affiliate-commerce-operator
description: Select, evaluate, produce, and optimize US TikTok Shop affiliate products and shoppable-video experiments using FastMoss evidence, commission economics, visual AI feasibility, creator intelligence, and post-publish funnel data. Use for US affiliate product selection, expected earnings, creator-product fit, conversion-focused AI video production, or scale/pause decisions; do not use for generic TikTok content, basic navigation, or autonomous publishing, outreach, uploads, or spend.
---

# TikTok US Affiliate Commerce Operator

Operate one evidence-backed loop:

```text
Product discovery → economics → creator and creative intelligence
→ controlled production → pre-publish gate → funnel review → decision
```

Default to the United States, TikTok Shop affiliate creator model, USD, and the
user's saved profile when one exists. A current user instruction overrides every
default and saved preference for that run.

## Route the request

- **Selection scan:** find and rank products. Read
  [references/selection-and-economics.md](references/selection-and-economics.md).
- **Product deep dive:** verify product, rating, inventory, trend, creators, and
  selling videos. Read the selection reference and
  [references/evidence-and-creators.md](references/evidence-and-creators.md).
- **Creator matching:** analyze creator performance, audience fit, and repeatable
  content patterns. Read the evidence and creators reference.
- **Creative production:** produce a single commercial hypothesis, A/B/C variants,
  director package, and generation tasks. Read
  [references/creative-production.md](references/creative-production.md).
- **Pre-publish audit:** inspect the actual 0–3 seconds, SKU match, claims,
  disclosures, legibility, and CTA. Read the creative production reference.
- **Post-publish optimization:** diagnose the first failing funnel transition and
  choose the next controlled test. Read
  [references/measurement-and-state.md](references/measurement-and-state.md).

Load only the references required for the current request. When the request spans
the full loop, use them in the order above.

## Evidence contract

Keep these visibly separate in every material result:

1. **Verified fact:** current product page, official policy, or first-party account
   analytics.
2. **Third-party platform data:** FastMoss or another named provider, with market,
   window, metric definition, and access date.
3. **Creative judgment:** visual suitability, audience inference, hook quality, or
   proposed story.
4. **Operating hypothesis:** an explanation or expected result that still needs a
   controlled test.
5. **Unknown:** missing data that could reverse the decision.

Never convert GMV, views, attributed ROAS, or a third-party estimate directly into
a profit claim. Never present generic TikTok distribution numbers as confirmed
platform rules.

## Decisions

Use product-gate statuses:

- `ELIGIBLE`: every required product, visual, trend, and inventory gate is proven.
- `HOLD`: a required field or proof is missing, incomplete, or ambiguous.
- `REJECT`: a verified hard condition fails.

Use operating actions only after reviewing the relevant evidence:

`TEST | SCALE | PAUSE | MONITOR | INVESTIGATE | RETIRE`

`SCALE` requires coherent downstream conversion, contribution economics, current
inventory, and no unresolved policy or claim blocker. Views alone never qualify.

## Tool and authorization boundaries

- FastMoss is the default product, creator, and video data provider. Use its live
  tool schema rather than inventing fields. Label the result as a screened subset
  unless the requested market was exhaustively covered.
- PixVerse is the default video-generation provider when available. Treat real
  product images as identity evidence; do not ask a model to redraw packaging
  text that must remain exact.
- Clipcat is disabled by default. Use it only when the user explicitly requests
  Clipcat for the current task and follow the approval sequence in the creative
  production reference.
- Before any paid generation or external upload, show the available price or quote,
  identify files leaving the machine, and obtain explicit approval.
- Do not publish, contact creators, send samples, alter listings, change budgets,
  buy traffic, or update external accounts without explicit authorization for
  that action.
- Do not manufacture engagement or recommend coordinated fake views, completion,
  likes, comments, clicks, or orders.

## Persistence

Read prior private state when it is relevant and available. Write or update state
only when the user explicitly asks to save the current result. Follow
[references/measurement-and-state.md](references/measurement-and-state.md) and
never store credentials, cookies, personal contacts, customer data, or private
authentication artifacts.

## Completion standard

A complete decision must state the market, SKU, data window, source, verified
facts, calculations, assumptions, unknowns, gate status, next action, primary
metric, stopping condition, and what must not happen yet. A creative result must
also include the first-three-seconds label packet, one visible proof chain, three
single-variable variants, production constraints, and a measurement plan.
