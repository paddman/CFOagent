import json
import tempfile
import unittest
from pathlib import Path

from cfo_agent.router import route_task
from cfo_agent.skills import (
    SKILLS,
    catalog_json,
    generate_skill_tree,
    render_skill_md,
    search_skills,
)


class SkillRouterTests(unittest.TestCase):
    def test_exact_skill_count_and_unique_slugs(self):
        self.assertEqual(len(SKILLS), 99)
        self.assertEqual(len({skill.slug for skill in SKILLS}), 99)

    def test_ifrs15_search(self):
        matches = search_skills("IFRS 15 revenue recognition", limit=3)
        self.assertTrue(matches)
        self.assertEqual(matches[0]["slug"], "revenue-recognition-ifrs15")

    def test_treasury_routing(self):
        routed = route_task("build a 13 week cash forecast and liquidity plan")
        self.assertEqual(routed["specialist"], "Treasury Lead")
        self.assertTrue(routed["skills"])

    def test_tax_routing(self):
        routed = route_task("prepare Thailand VAT and withholding tax compliance")
        self.assertEqual(routed["specialist"], "Thailand Tax Lead")

    def test_catalog_json(self):
        catalog = json.loads(catalog_json())
        self.assertEqual(len(catalog), 99)
        self.assertTrue(all(item["slug"] for item in catalog))

    def test_rendered_skill_has_safe_frontmatter_and_controls(self):
        text = render_skill_md(SKILLS[0])
        self.assertTrue(text.startswith("---\n"))
        self.assertIn('tags: ["finance"', text)
        self.assertIn("Control boundary", text)
        self.assertIn("authorized human approval", text)

    def test_generate_skill_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            written = generate_skill_tree(root)
            self.assertEqual(len(written), 99)
            self.assertTrue((root / "revenue-recognition-ifrs15" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
