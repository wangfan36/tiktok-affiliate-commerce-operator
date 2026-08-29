from __future__ import annotations

import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from rank_candidates import InputError, rank_document  # noqa: E402


AS_OF = date(2026, 8, 29)


def history(previous_daily: float = 5, recent_daily: float = 10):
    first = AS_OF - timedelta(days=55)
    return [
        {
            "date": (first + timedelta(days=index)).isoformat(),
            "units": previous_daily if index < 28 else recent_daily,
        }
        for index in range(56)
    ]


def candidate(product_id="p1", **overrides):
    base = {
        "product_id": product_id,
        "name": f"Product {product_id}",
        "region": "US",
        "is_local_warehouse": True,
        "listing_status": "on_sale",
        "price": 30,
        "commission_rate_percent": 20,
        "rating": 4.8,
        "inventory": {
            "current_in_stock": True,
            "stability_evidence": "days_of_cover",
            "days_of_cover": 30,
        },
        "visual": {
            "photo_self_explanatory": True,
            "ai_material_feasible": True,
            "requires_face_or_body_application": False,
            "requires_complex_instruction": False,
        },
        "daily_units": history(),
        "refund_cancel_rate": 0.1,
        "attributable_cost_per_order": 1,
        "funnel": {
            "same_account": True,
            "same_product": True,
            "same_attribution_window": True,
            "product_ctr": 0.02,
            "click_to_order_cvr": 0.05,
            "cost_per_1000_qualified_views": 2,
        },
        "evidence_confidence": "high",
    }
    base.update(overrides)
    return base


def document(*candidates, scenarios=None):
    return {
        "schema_version": "1.0",
        "as_of": AS_OF.isoformat(),
        "scenario_assumptions": scenarios or [],
        "candidates": list(candidates),
    }


class RankCandidatesTests(unittest.TestCase):
    def test_calculates_growth_commission_and_observed_gpm(self):
        result = rank_document(document(candidate()))
        item = result["candidates"][0]
        self.assertEqual(item["status"], "ELIGIBLE")
        self.assertEqual(item["recent_28d_units"], 280)
        self.assertEqual(item["previous_28d_units"], 140)
        self.assertEqual(item["absolute_28d_unit_growth"], 140)
        self.assertEqual(item["gross_commission_per_order"], 6)
        self.assertEqual(item["net_commission_per_order"], 4.4)
        self.assertEqual(item["expected_net_commission_gpm"], 2.4)

    def test_hard_filters_reject_low_commission(self):
        item = rank_document(document(candidate(commission_rate_percent=14.99)))["candidates"][0]
        self.assertEqual(item["status"], "REJECT")
        self.assertIn("commission_below_15_percent", item["reject_reasons"])

    def test_all_product_hard_filters_are_enforced(self):
        cases = [
            ({"region": "GB"}, "region_not_US"),
            ({"is_local_warehouse": False}, "not_US_local_warehouse"),
            ({"listing_status": "off_sale"}, "listing_not_on_sale"),
            ({"price": 24.99}, "price_outside_25_to_45_USD"),
            ({"price": 45.01}, "price_outside_25_to_45_USD"),
            ({"rating": 4.49}, "rating_below_4_5"),
        ]
        for overrides, expected_reason in cases:
            with self.subTest(expected_reason=expected_reason):
                item = rank_document(document(candidate(**overrides)))["candidates"][0]
                self.assertEqual(item["status"], "REJECT")
                self.assertIn(expected_reason, item["reject_reasons"])

    def test_absolute_growth_precedes_commission_in_ranking(self):
        growing = candidate("growing", commission_rate_percent=15, daily_units=history(2, 8))
        declining = candidate("declining", commission_rate_percent=40, daily_units=history(10, 9))
        result = rank_document(document(declining, growing))
        self.assertEqual(result["candidates"][0]["product_id"], "growing")
        self.assertEqual(result["candidates"][0]["eligible_rank"], 1)

    def test_missing_day_is_hold_and_not_ranked(self):
        incomplete = history()
        incomplete.pop(10)
        item = rank_document(document(candidate(daily_units=incomplete)))["candidates"][0]
        self.assertEqual(item["status"], "HOLD")
        self.assertIsNone(item["eligible_rank"])
        self.assertTrue(any(reason.startswith("incomplete_56_day_history") for reason in item["hold_reasons"]))

    def test_duplicate_day_is_hold(self):
        duplicated = history()
        duplicated.append(dict(duplicated[-1]))
        item = rank_document(document(candidate(daily_units=duplicated)))["candidates"][0]
        self.assertEqual(item["status"], "HOLD")
        self.assertTrue(any(reason.startswith("duplicate_daily_dates") for reason in item["hold_reasons"]))

    def test_face_application_and_complex_instruction_are_rejected(self):
        visual = candidate()["visual"]
        visual["requires_face_or_body_application"] = True
        visual["requires_complex_instruction"] = True
        item = rank_document(document(candidate(visual=visual)))["candidates"][0]
        self.assertEqual(item["status"], "REJECT")
        self.assertIn("requires_face_or_body_application", item["reject_reasons"])
        self.assertIn("requires_complex_instruction", item["reject_reasons"])

    def test_non_self_explanatory_product_is_rejected(self):
        visual = candidate()["visual"]
        visual["photo_self_explanatory"] = False
        item = rank_document(document(candidate(visual=visual)))["candidates"][0]
        self.assertEqual(item["status"], "REJECT")
        self.assertIn("not_photo_self_explanatory", item["reject_reasons"])

    def test_stock_snapshot_cannot_claim_stability(self):
        inventory = {
            "current_in_stock": True,
            "stability_evidence": "snapshot_only",
        }
        item = rank_document(document(candidate(inventory=inventory)))["candidates"][0]
        self.assertEqual(item["status"], "HOLD")
        self.assertIn("inventory_stability_not_proven", item["hold_reasons"])

    def test_missing_funnel_does_not_create_precise_gpm(self):
        item = rank_document(document(candidate(funnel=None)))["candidates"][0]
        self.assertEqual(item["status"], "ELIGIBLE")
        self.assertEqual(item["economics_status"], "HOLD")
        self.assertIsNone(item["expected_net_commission_gpm"])
        self.assertIn("missing_comparable_funnel", item["economics_reasons"])

    def test_scenarios_are_explicitly_labeled_assumptions(self):
        scenarios = [
            {
                "name": "low",
                "product_ctr": 0.01,
                "click_to_order_cvr": 0.02,
                "cost_per_1000_qualified_views": 0,
            }
        ]
        item = rank_document(document(candidate(funnel=None), scenarios=scenarios))["candidates"][0]
        self.assertTrue(item["scenario_estimates"][0]["assumed"])
        self.assertEqual(item["scenario_estimates"][0]["expected_net_commission_gpm"], 0.88)

    def test_zero_funnel_denominator_is_not_precise(self):
        funnel = {
            "same_account": True,
            "same_product": True,
            "same_attribution_window": True,
            "qualified_views": 1000,
            "product_clicks": 0,
            "attributed_orders": 0,
            "cost_per_1000_qualified_views": 0,
        }
        item = rank_document(document(candidate(funnel=funnel)))["candidates"][0]
        self.assertIsNone(item["expected_net_commission_gpm"])
        self.assertIn("zero_funnel_denominator", item["economics_reasons"])

    def test_output_is_whitelisted_and_drops_secrets_and_personal_data(self):
        excluded_fields = {
            "api" + "_key": "credential-placeholder",
            "coo" + "kie": "session-placeholder",
            "creator" + "_email": "contact-placeholder@example.invalid",
        }
        raw = candidate(**excluded_fields)
        serialized = json.dumps(rank_document(document(raw)))
        for field, value in excluded_fields.items():
            self.assertNotIn(field, serialized)
            self.assertNotIn(value, serialized)

    def test_rejects_more_than_thirty_candidates(self):
        with self.assertRaises(InputError):
            rank_document(document(*(candidate(str(index)) for index in range(31))))


if __name__ == "__main__":
    unittest.main()
