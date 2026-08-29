#!/usr/bin/env python3
"""Rank US TikTok Shop affiliate candidates from a versioned JSON input.

The script is deliberately offline and deterministic. It never reads credentials,
browser state, cookies, or environment variables.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCHEMA_VERSION = "1.0"
STABLE_INVENTORY_EVIDENCE = {
    "sku_stock_history",
    "days_of_cover",
    "seller_replenishment",
}
CONFIDENCE_SCORE = {"high": 3, "medium": 2, "low": 1, "unknown": 0}


class InputError(ValueError):
    """Raised when the top-level input cannot be evaluated safely."""


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def rounded(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(float(value), 6)


def add_reason(reasons: List[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def parse_iso_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str):
        raise InputError(f"{field_name} must be an ISO date string")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise InputError(f"{field_name} must use YYYY-MM-DD") from exc


def validate_scenarios(raw: Any) -> List[Dict[str, float | str]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise InputError("scenario_assumptions must be a list")

    validated: List[Dict[str, float | str]] = []
    names: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise InputError(f"scenario_assumptions[{index}] must be an object")
        name = item.get("name")
        ctr = item.get("product_ctr")
        cvr = item.get("click_to_order_cvr")
        cost = item.get("cost_per_1000_qualified_views", 0)
        if not isinstance(name, str) or not name.strip():
            raise InputError(f"scenario_assumptions[{index}].name is required")
        if name in names:
            raise InputError(f"duplicate scenario name: {name}")
        if not is_number(ctr) or not 0 <= ctr <= 1:
            raise InputError(f"scenario {name}: product_ctr must be between 0 and 1")
        if not is_number(cvr) or not 0 <= cvr <= 1:
            raise InputError(f"scenario {name}: click_to_order_cvr must be between 0 and 1")
        if not is_number(cost) or cost < 0:
            raise InputError(f"scenario {name}: cost must be non-negative")
        names.add(name)
        validated.append(
            {
                "name": name,
                "product_ctr": float(ctr),
                "click_to_order_cvr": float(cvr),
                "cost_per_1000_qualified_views": float(cost),
            }
        )
    return validated


def evaluate_history(
    raw_history: Any, as_of: date, hold_reasons: List[str]
) -> Tuple[Optional[float], Optional[float], Optional[float], bool]:
    if not isinstance(raw_history, list):
        add_reason(hold_reasons, "missing_daily_unit_history")
        return None, None, None, False

    units_by_date: Dict[date, float] = {}
    seen_dates: List[date] = []
    invalid = False
    for index, row in enumerate(raw_history):
        if not isinstance(row, dict):
            add_reason(hold_reasons, f"invalid_daily_unit_row:{index}")
            invalid = True
            continue
        try:
            day = datetime.strptime(str(row.get("date")), "%Y-%m-%d").date()
        except ValueError:
            add_reason(hold_reasons, f"invalid_daily_unit_date:{index}")
            invalid = True
            continue
        units = row.get("units")
        if not is_number(units) or units < 0:
            add_reason(hold_reasons, f"invalid_daily_units:{index}")
            invalid = True
            continue
        seen_dates.append(day)
        units_by_date[day] = float(units)

    duplicate_dates = sorted(day.isoformat() for day, count in Counter(seen_dates).items() if count > 1)
    if duplicate_dates:
        add_reason(hold_reasons, "duplicate_daily_dates:" + ",".join(duplicate_dates))
        invalid = True

    expected_dates = [as_of - timedelta(days=offset) for offset in range(55, -1, -1)]
    missing = [day.isoformat() for day in expected_dates if day not in units_by_date]
    if missing:
        add_reason(hold_reasons, f"incomplete_56_day_history:{len(missing)}_missing")
        invalid = True

    if invalid:
        return None, None, None, False

    previous_dates = expected_dates[:28]
    recent_dates = expected_dates[28:]
    previous = sum(units_by_date[day] for day in previous_dates)
    recent = sum(units_by_date[day] for day in recent_dates)
    return recent, previous, recent - previous, True


def resolve_observed_funnel(
    funnel: Any, economics_reasons: List[str]
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    if not isinstance(funnel, dict):
        add_reason(economics_reasons, "missing_comparable_funnel")
        return None, None, None

    cohort_flags = (
        funnel.get("same_account") is True,
        funnel.get("same_product") is True,
        funnel.get("same_attribution_window") is True,
    )
    if not all(cohort_flags):
        add_reason(economics_reasons, "funnel_not_same_account_product_and_window")
        return None, None, None

    cost = funnel.get("cost_per_1000_qualified_views")
    if not is_number(cost) or cost < 0:
        add_reason(economics_reasons, "missing_or_invalid_cost_per_1000_qualified_views")
        return None, None, None

    ctr = funnel.get("product_ctr")
    cvr = funnel.get("click_to_order_cvr")
    if ctr is not None or cvr is not None:
        if not is_number(ctr) or not 0 <= ctr <= 1:
            add_reason(economics_reasons, "invalid_product_ctr")
            return None, None, None
        if not is_number(cvr) or not 0 <= cvr <= 1:
            add_reason(economics_reasons, "invalid_click_to_order_cvr")
            return None, None, None
        return float(ctr), float(cvr), float(cost)

    views = funnel.get("qualified_views")
    clicks = funnel.get("product_clicks")
    orders = funnel.get("attributed_orders")
    if not all(is_number(value) for value in (views, clicks, orders)):
        add_reason(economics_reasons, "missing_funnel_rates_or_counts")
        return None, None, None
    if views <= 0 or clicks <= 0:
        add_reason(economics_reasons, "zero_funnel_denominator")
        return None, None, None
    if clicks < 0 or orders < 0 or clicks > views or orders > clicks:
        add_reason(economics_reasons, "invalid_funnel_counts")
        return None, None, None
    return float(clicks / views), float(orders / clicks), float(cost)


def evaluate_candidate(
    candidate: Dict[str, Any],
    as_of: date,
    scenarios: Iterable[Dict[str, float | str]],
    duplicate_product_id: bool,
) -> Dict[str, Any]:
    reject_reasons: List[str] = []
    hold_reasons: List[str] = []
    economics_reasons: List[str] = []

    product_id = candidate.get("product_id")
    name = candidate.get("name")
    if not isinstance(product_id, str) or not product_id.strip():
        add_reason(hold_reasons, "missing_product_id")
        product_id = None
    if not isinstance(name, str) or not name.strip():
        add_reason(hold_reasons, "missing_product_name")
        name = None
    if duplicate_product_id:
        add_reason(hold_reasons, "duplicate_product_id")

    region = candidate.get("region")
    if region is None:
        add_reason(hold_reasons, "missing_region")
    elif str(region).upper() != "US":
        add_reason(reject_reasons, "region_not_US")

    local_warehouse = candidate.get("is_local_warehouse")
    if local_warehouse is None:
        add_reason(hold_reasons, "missing_local_warehouse_status")
    elif local_warehouse is not True:
        add_reason(reject_reasons, "not_US_local_warehouse")

    listing_status = candidate.get("listing_status")
    if listing_status is None:
        add_reason(hold_reasons, "missing_listing_status")
    elif listing_status != "on_sale":
        add_reason(reject_reasons, "listing_not_on_sale")

    price = candidate.get("price")
    if not is_number(price):
        add_reason(hold_reasons, "missing_or_invalid_price")
        price_value = None
    else:
        price_value = float(price)
        if not 25 <= price_value <= 45:
            add_reason(reject_reasons, "price_outside_25_to_45_USD")

    commission_percent = candidate.get("commission_rate_percent")
    if not is_number(commission_percent):
        add_reason(hold_reasons, "missing_or_invalid_commission_rate")
        commission_value = None
    else:
        commission_value = float(commission_percent)
        if commission_value < 15:
            add_reason(reject_reasons, "commission_below_15_percent")

    rating = candidate.get("rating")
    if not is_number(rating):
        add_reason(hold_reasons, "missing_or_invalid_rating")
        rating_value = None
    else:
        rating_value = float(rating)
        if rating_value < 4.5:
            add_reason(reject_reasons, "rating_below_4_5")

    inventory = candidate.get("inventory")
    if not isinstance(inventory, dict):
        add_reason(hold_reasons, "missing_inventory_evidence")
        current_in_stock = None
        stability_evidence = None
        days_of_cover = None
    else:
        current_in_stock = inventory.get("current_in_stock")
        stability_evidence = inventory.get("stability_evidence")
        days_of_cover = inventory.get("days_of_cover")
        if current_in_stock is None:
            add_reason(hold_reasons, "missing_current_stock_status")
        elif current_in_stock is not True:
            add_reason(reject_reasons, "currently_out_of_stock")
        if stability_evidence not in STABLE_INVENTORY_EVIDENCE:
            add_reason(hold_reasons, "inventory_stability_not_proven")
        elif stability_evidence == "days_of_cover" and (
            not is_number(days_of_cover) or days_of_cover <= 0
        ):
            add_reason(hold_reasons, "missing_or_invalid_days_of_cover")

    visual = candidate.get("visual")
    if not isinstance(visual, dict):
        add_reason(hold_reasons, "missing_visual_fit_assessment")
        visual_values = {
            "photo_self_explanatory": None,
            "ai_material_feasible": None,
            "requires_face_or_body_application": None,
            "requires_complex_instruction": None,
        }
    else:
        visual_values = {
            field: visual.get(field)
            for field in (
                "photo_self_explanatory",
                "ai_material_feasible",
                "requires_face_or_body_application",
                "requires_complex_instruction",
            )
        }
        for field, value in visual_values.items():
            if value is None:
                add_reason(hold_reasons, f"missing_visual_field:{field}")
        if visual_values["photo_self_explanatory"] is False:
            add_reason(reject_reasons, "not_photo_self_explanatory")
        if visual_values["ai_material_feasible"] is False:
            add_reason(reject_reasons, "primary_material_not_AI_feasible")
        if visual_values["requires_face_or_body_application"] is True:
            add_reason(reject_reasons, "requires_face_or_body_application")
        if visual_values["requires_complex_instruction"] is True:
            add_reason(reject_reasons, "requires_complex_instruction")

    recent_units, previous_units, absolute_growth, history_complete = evaluate_history(
        candidate.get("daily_units"), as_of, hold_reasons
    )

    gross_commission = None
    if price_value is not None and commission_value is not None:
        gross_commission = price_value * commission_value / 100

    refund_rate = candidate.get("refund_cancel_rate")
    per_order_cost = candidate.get("attributable_cost_per_order")
    net_commission = None
    if gross_commission is None:
        add_reason(economics_reasons, "gross_commission_unavailable")
    elif not is_number(refund_rate) or not 0 <= refund_rate <= 1:
        add_reason(economics_reasons, "missing_or_invalid_refund_cancel_rate")
    elif not is_number(per_order_cost) or per_order_cost < 0:
        add_reason(economics_reasons, "missing_or_invalid_attributable_cost_per_order")
    else:
        net_commission = gross_commission * (1 - float(refund_rate)) - float(per_order_cost)

    observed_ctr, observed_cvr, cost_per_1000 = resolve_observed_funnel(
        candidate.get("funnel"), economics_reasons
    )
    observed_gpm = None
    if net_commission is not None and observed_ctr is not None and observed_cvr is not None:
        observed_gpm = 1000 * observed_ctr * observed_cvr * net_commission - float(cost_per_1000)
    elif net_commission is None:
        add_reason(economics_reasons, "net_commission_unavailable_for_GPM")

    scenario_results: List[Dict[str, Any]] = []
    if net_commission is not None:
        for scenario in scenarios:
            scenario_gpm = (
                1000
                * float(scenario["product_ctr"])
                * float(scenario["click_to_order_cvr"])
                * net_commission
                - float(scenario["cost_per_1000_qualified_views"])
            )
            scenario_results.append(
                {
                    "name": scenario["name"],
                    "assumed": True,
                    "product_ctr": scenario["product_ctr"],
                    "click_to_order_cvr": scenario["click_to_order_cvr"],
                    "cost_per_1000_qualified_views": scenario[
                        "cost_per_1000_qualified_views"
                    ],
                    "expected_net_commission_gpm": rounded(scenario_gpm),
                }
            )

    if reject_reasons:
        status = "REJECT"
    elif hold_reasons:
        status = "HOLD"
    else:
        status = "ELIGIBLE"

    confidence = candidate.get("evidence_confidence")
    if confidence not in CONFIDENCE_SCORE:
        confidence = "unknown"

    completeness_values = [
        region,
        local_warehouse,
        listing_status,
        price_value,
        commission_value,
        rating_value,
        current_in_stock,
        stability_evidence,
        visual_values["photo_self_explanatory"],
        visual_values["ai_material_feasible"],
        visual_values["requires_face_or_body_application"],
        visual_values["requires_complex_instruction"],
        True if history_complete else None,
    ]
    completeness = sum(value is not None for value in completeness_values) / len(completeness_values)

    return {
        "product_id": product_id,
        "name": name,
        "status": status,
        "eligible_rank": None,
        "reject_reasons": reject_reasons,
        "hold_reasons": hold_reasons,
        "price": rounded(price_value),
        "commission_rate_percent": rounded(commission_value),
        "rating": rounded(rating_value),
        "recent_28d_units": rounded(recent_units),
        "previous_28d_units": rounded(previous_units),
        "absolute_28d_unit_growth": rounded(absolute_growth),
        "gross_commission_per_order": rounded(gross_commission),
        "net_commission_per_order": rounded(net_commission),
        "observed_product_ctr": rounded(observed_ctr),
        "observed_click_to_order_cvr": rounded(observed_cvr),
        "expected_net_commission_gpm": rounded(observed_gpm),
        "scenario_estimates": scenario_results,
        "economics_status": "COMPLETE" if observed_gpm is not None else "HOLD",
        "economics_reasons": economics_reasons,
        "data_completeness": round(completeness, 3),
        "evidence_confidence": confidence,
        "inventory_evidence": {
            "current_in_stock": current_in_stock,
            "stability_evidence": stability_evidence,
            "days_of_cover": rounded(float(days_of_cover)) if is_number(days_of_cover) else None,
        },
    }


def rank_document(document: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(document, dict):
        raise InputError("input must be a JSON object")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise InputError(f"schema_version must be {SCHEMA_VERSION}")
    as_of = parse_iso_date(document.get("as_of"), "as_of")
    raw_candidates = document.get("candidates")
    if not isinstance(raw_candidates, list):
        raise InputError("candidates must be a list")
    if len(raw_candidates) > 30:
        raise InputError("candidates exceeds the maximum scan size of 30")
    if any(not isinstance(item, dict) for item in raw_candidates):
        raise InputError("each candidate must be an object")
    scenarios = validate_scenarios(document.get("scenario_assumptions"))

    product_ids = [item.get("product_id") for item in raw_candidates]
    duplicate_ids = {
        product_id
        for product_id, count in Counter(product_ids).items()
        if product_id is not None and count > 1
    }
    evaluated = [
        evaluate_candidate(item, as_of, scenarios, item.get("product_id") in duplicate_ids)
        for item in raw_candidates
    ]

    eligible = [item for item in evaluated if item["status"] == "ELIGIBLE"]
    eligible.sort(
        key=lambda item: (
            -(item["absolute_28d_unit_growth"] if item["absolute_28d_unit_growth"] is not None else -math.inf),
            -(item["net_commission_per_order"] if item["net_commission_per_order"] is not None else -math.inf),
            -(item["recent_28d_units"] if item["recent_28d_units"] is not None else -math.inf),
            -CONFIDENCE_SCORE[item["evidence_confidence"]],
            item["product_id"] or "",
        )
    )
    for index, item in enumerate(eligible, start=1):
        item["eligible_rank"] = index

    hold = [item for item in evaluated if item["status"] == "HOLD"]
    reject = [item for item in evaluated if item["status"] == "REJECT"]
    ordered = eligible + hold + reject

    return {
        "schema_version": SCHEMA_VERSION,
        "as_of": as_of.isoformat(),
        "ranking_basis": [
            "absolute_28d_unit_growth_desc",
            "net_commission_per_order_desc",
            "recent_28d_units_desc",
            "evidence_confidence_desc",
        ],
        "summary": {
            "candidate_count": len(evaluated),
            "eligible_count": len(eligible),
            "hold_count": len(hold),
            "reject_count": len(reject),
        },
        "candidates": ordered,
    }


def read_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise InputError(f"cannot read input file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON: {exc}") from exc


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank up to 30 US TikTok Shop affiliate product candidates."
    )
    parser.add_argument("input", type=Path, help="Version 1.0 candidate JSON")
    parser.add_argument("--output", "-o", type=Path, help="Write ranked JSON to this path")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = rank_document(read_json(args.input))
        if args.output:
            write_json(args.output, result)
        else:
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
