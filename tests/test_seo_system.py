import copy
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import seo_system as seo


class SeoSystemTests(unittest.TestCase):
    def test_owned_variants_and_reviewed_inventory_pass(self):
        self.assertGreater(seo.validate_topics(), 40)
        seo.assert_publication_paths(seo.sitemap_paths())

    def test_every_canonical_route_has_one_honest_owner_including_translations(self):
        topics = seo.read_json("topics.json")["topics"]
        self.assertEqual(len(topics), 50)
        self.assertEqual({topic["canonical_path"] for topic in topics}, set(seo.sitemap_paths()))
        self.assertEqual(sum(bool(topic["translation_of"]) for topic in topics), 15)
        self.assertEqual(sum(topic["editorial_status"] == "legacy_review_pending" for topic in topics), 49)
        self.assertEqual({seo.language_family(topic["language"]) for topic in topics}, {"en", "es", "pt", "zh"})

    def test_missing_duplicate_and_noncanonical_owners_fail_closed(self):
        for mutation, message in [("missing", "missing intent ownership"),
                                  ("duplicate", "multiple topic owners"),
                                  ("alias_route", "noncanonical path")]:
            data = seo.read_json("topics.json")
            if mutation == "missing":
                data["topics"].pop()
            elif mutation == "duplicate":
                duplicate = copy.deepcopy(data["topics"][0])
                duplicate["id"] = "shadow-owner"
                data["topics"].append(duplicate)
            else:
                data["topics"][0]["canonical_path"] += ".html"
            with self.assertRaisesRegex(ValueError, message):
                seo.validate_topics(data)

    def test_same_language_intent_cannot_get_a_second_url(self):
        data = seo.read_json("topics.json")
        data["topics"][1]["intent_key"] = data["topics"][0]["intent_key"]
        with self.assertRaisesRegex(ValueError, "same-language intent"):
            seo.validate_topics(data)

    def test_conservative_paraphrase_guard_catches_word_order_and_inflection(self):
        data = seo.read_json("topics.json")
        data["topics"][1]["aliases"].append("web design for small businesses")
        with self.assertRaisesRegex(ValueError, "lexically equivalent"):
            seo.validate_topics(data)
        self.assertEqual(seo.semantic_query_key("hire a website developer", "en"),
                         seo.semantic_query_key("hire website developers", "en"))
        self.assertNotEqual(seo.semantic_query_key("what should AI answer", "en"),
                            seo.semantic_query_key("what should AI not answer", "en"))
        self.assertNotEqual(seo.semantic_query_key("contractor website", "en"),
                            seo.semantic_query_key("restaurant website", "en"))
        # No claim that word-token heuristics understand arbitrary Chinese paraphrases.
        self.assertNotEqual(seo.semantic_query_key("网站制作", "zh-Hans"),
                            seo.semantic_query_key("制作网站", "zh-Hans"))

    def test_candidate_cannot_claim_a_paraphrase_of_an_existing_owner(self):
        data = seo.read_json("topics.json")
        data["candidates"].append({"primary_query": "web design for small businesses",
                                   "canonical_path": "/guides/another-website-page"})
        with self.assertRaisesRegex(ValueError, "candidate duplicates an owned intent"):
            seo.validate_topics(data)

    def test_translation_family_matches_visible_language_and_reciprocal_hreflang(self):
        for mutation, message in [("language", "language differs"),
                                  ("parent", "not in page hreflang"),
                                  ("missing_parent", "translation family")]:
            data = seo.read_json("topics.json")
            topic = next(row for row in data["topics"] if row["canonical_path"] == "/es/pagina-web")
            if mutation == "language":
                topic["language"] = "pt-BR"
                topic["intent_key"] = "different-to-reach-page-check"
            elif mutation == "parent":
                topic["translation_of"] = "phone-agent"
                topic["intent_key"] = next(row["intent_key"] for row in data["topics"] if row["id"] == "phone-agent")
            else:
                topic["translation_of"] = None
            with self.assertRaisesRegex(ValueError, message):
                seo.validate_topics(data)

    def test_mapping_does_not_upgrade_legacy_editorial_approval(self):
        data = seo.read_json("topics.json")
        data["topics"][0]["editorial_status"] = "publication_reviewed"
        with self.assertRaisesRegex(ValueError, "fresh legacy editorial approval"):
            seo.validate_topics(data)

    def test_aliases_are_arrays_and_intent_boundaries_are_required(self):
        for change in [{"aliases": "keyword list"}, {"question_queries": [False]},
                       {"relationships": {}}, {"intent_boundary": "generic"}]:
            data = seo.read_json("topics.json")
            data["topics"][0].update(change)
            with self.assertRaises(ValueError):
                seo.validate_topics(data)

    def test_new_pages_need_review(self):
        with self.assertRaisesRegex(ValueError, "explicit publication review"):
            seo.assert_publication_paths(["/another-synonym-page"])

    def test_legacy_inventory_cannot_be_expanded_to_bypass_review(self):
        data = seo.read_json("publication.json")
        data["legacy_paths"].append("/another-synonym-page")
        with self.assertRaisesRegex(ValueError, "historical legacy inventory is frozen"):
            seo.assert_publication_paths(["/another-synonym-page"], data)

    def test_distinct_reviewers_and_valid_review_date_are_required(self):
        for change in [{"producer": ""}, {"reviewer": " "},
                       {"reviewer": seo.read_json("publication.json")["reviews"][0]["producer"]},
                       {"reviewed_at": "tomorrow"}, {"reviewed_at": "2099-01-01"}]:
            data = seo.read_json("publication.json")
            data["reviews"][0].update(change)
            with self.assertRaises(ValueError):
                seo.assert_publication_paths([data["reviews"][0]["path"]], data)

    def test_static_publication_locks_the_rendered_html_too(self):
        data = seo.read_json("publication.json")
        path = data["reviews"][0]["path"]
        seo.assert_publication_paths([path], data, check_rendered=True)
        data["reviews"][0]["rendered_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "rendered page changed"):
            seo.assert_publication_paths([path], data, check_rendered=True)

    def test_low_score_stale_hash_and_draft_fail(self):
        data = seo.read_json("publication.json")
        path = data["reviews"][0]["path"]
        for change, pattern in [
            ({"sha256": "0" * 64}, "content changed"),
            ({"scores": {key: 8 for key in seo.DIMENSIONS}}, "at least 9"),
            ({"scores": {key: True for key in seo.DIMENSIONS}}, "at least 9"),
            ({"decision": "IMPROVE"}, "explicit publication review"),
        ]:
            mutated = copy.deepcopy(data)
            mutated["reviews"][0].update(change)
            with self.assertRaisesRegex(ValueError, pattern):
                seo.assert_publication_paths([path], mutated)

    def test_legacy_noindex_review_overrides_grandfathering(self):
        data = seo.read_json("publication.json")
        data["reviews"].append({"path": "/about", "decision": "NOINDEX"})
        with self.assertRaisesRegex(ValueError, "explicit publication review"):
            seo.assert_publication_paths(["/about"], data)

    def test_duplicate_alias_and_broken_relationship_fail(self):
        for mutation in ["alias", "relationship"]:
            data = seo.read_json("topics.json")
            if mutation == "alias":
                data["topics"][1]["aliases"].append(data["topics"][0]["primary_query"])
            else:
                data["topics"][0]["relationships"][0]["path"] = "/missing"
            with self.assertRaises(ValueError):
                seo.validate_topics(data)

    def test_query_normalization_is_not_a_new_page_generator(self):
        self.assertEqual(seo.normalize_query("  Website—BUILDER!  "), "website builder")
        self.assertEqual(seo.normalize_query("做网站"), "做网站")
        self.assertIn("data-evt=\"seo_related_click\"", seo.related_html("/services/websites"))

    def test_search_export_requires_query_page_joint_rows(self):
        with self.assertRaisesRegex(ValueError, "together"):
            seo.analyze_search_csv("Query,Clicks,Impressions,Position\nwebsites,2,30,10\n", "2026-08-01", "2026-08-31")

    def test_search_report_aggregates_and_never_invents_conversions(self):
        csv = "Query,Page,Clicks,Impressions,Position\nwebsite builder,https://leonbuilds.org/services/websites,1,40,10\nwebsite builder,https://leonbuilds.org/services/websites,0,20,16\nwebsite builder,https://leonbuilds.org/services/,0,30,11\n"
        result = seo.analyze_search_csv(csv, "2026-08-01", "2026-08-31")
        row = next(row for row in result["rows"] if row["page"].endswith("/websites"))
        self.assertEqual(row["impressions"], 60)
        self.assertEqual(row["average_position"], 12)
        self.assertAlmostEqual(row["ctr"], 1 / 60)
        self.assertEqual(len(result["possible_cannibalization"]), 1)
        self.assertIsNone(result["qualified_inquiries"])
        self.assertIsNone(result["won_work"])

    def test_malformed_metrics_external_pages_and_bad_dates_fail(self):
        for values in ["1,-2,10", "NaN,20,10", "1,20,Infinity", "1.5,20,10"]:
            with self.assertRaises(ValueError):
                seo.analyze_search_csv("Query,Page,Clicks,Impressions,Position\nwebsite,https://leonbuilds.org/," + values, "2026-08-01", "2026-08-31")
        with self.assertRaises(ValueError):
            seo.analyze_search_csv("Query,Page,Clicks,Impressions,Position\nwebsite,https://other.org/,0,20,10", "2026-08-01", "2026-08-31")
        with self.assertRaises(ValueError):
            seo.analyze_search_csv("Query,Page,Clicks,Impressions,Position\n", "2026-09-01", "2026-08-31")

    def test_contacts_are_not_echoed_in_query_report(self):
        result = seo.analyze_search_csv("Query,Page,Clicks,Impressions,Position\nprivate@example.org,https://leonbuilds.org/,1,20,10", "2026-08-01", "2026-08-31")
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["privacy_withheld_rows"], 1)
        self.assertNotIn("private@example.org", json.dumps(result))

    def test_buyer_guide_has_visible_proof_scope_and_navigation(self):
        html = (ROOT / "guides/website-builder-or-custom-software.html").read_text()
        self.assertEqual(html.count("<h1 "), 1)
        self.assertIn('id="scope-checklist"', html)
        self.assertIn('rel="canonical" href="https://leonbuilds.org/guides/website-builder-or-custom-software"', html)
        self.assertIn("not an independent product review", html)
        self.assertIn("are simulations", html)
        self.assertNotIn("FAQPage", html)
        for route in ["/work/beastypages-website", "/work/allcpr-site-intelligence", "/guides/contractor-inquiry-workflow"]:
            self.assertIn(f'href="{route}"', html)

    def test_opportunities_are_inventory_and_hypotheses_not_fake_volume(self):
        rows = seo.opportunities()
        self.assertGreaterEqual(len(rows), len(seo.sitemap_paths()))
        self.assertLess(len(rows), 100)
        self.assertTrue(all("unknown" in row["search_potential"] for row in rows))
        self.assertTrue(all(row["competition_estimate"] == "unknown" for row in rows))

    def test_unchanged_page_dates_are_not_refreshed_by_generator_run(self):
        import subprocess
        import xml.etree.ElementTree as ET
        before = ET.fromstring(subprocess.check_output(["git", "show", "HEAD:sitemap.xml"], cwd=ROOT, text=True))
        after = ET.parse(ROOT / "sitemap.xml").getroot()
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        dates = lambda root: {row.findtext("sm:loc", namespaces=ns): row.findtext("sm:lastmod", namespaces=ns) for row in root.findall("sm:url", ns)}
        for url, prior_date in dates(before).items():
            route = url.removeprefix(seo.ORIGIN).strip("/")
            file = "homepage/index.html" if not route else (
                route + "/index.html" if (ROOT / route / "index.html").is_file() else route + ".html")
            prior_bytes = subprocess.check_output(["git", "show", "HEAD:" + file], cwd=ROOT)
            if prior_bytes == (ROOT / file).read_bytes():
                self.assertEqual(prior_date, dates(after)[url], url)


if __name__ == "__main__":
    unittest.main()
