from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")


class SkillContractTests(unittest.TestCase):
    def test_competitor_analysis_is_pattern_only(self):
        text = read("references/evidence-and-creators.md")
        self.assertIn("Replicate only abstract patterns", text)
        for protected_element in ("identity", "script", "shot sequence", "music", "protected footage"):
            self.assertIn(protected_element, text)

    def test_paid_generation_upload_and_external_actions_require_authorization(self):
        skill = read("SKILL.md")
        creative = read("references/creative-production.md")
        state = read("references/measurement-and-state.md")
        self.assertIn("obtain explicit approval", skill)
        self.assertIn("Before uploading a local file", creative)
        self.assertIn("explicitly requests", creative)
        self.assertIn("created only after explicit save authorization", state)
        self.assertIn("without explicit authorization", skill)

    def test_good_retention_weak_clicks_changes_value_or_cta_only(self):
        text = read("references/measurement-and-state.md")
        self.assertIn("Good completion, weak CTR", text)
        self.assertIn("Change value expression or CTA only", text)

    def test_first_three_seconds_and_product_visibility_are_hard_gates(self):
        text = read("references/creative-production.md")
        self.assertIn("First-three-seconds label packet", text)
        self.assertIn("product or proof action is obscured", text)


if __name__ == "__main__":
    unittest.main()
