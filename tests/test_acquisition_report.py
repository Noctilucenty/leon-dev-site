import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import acquisition_report as reporter  # noqa: E402


DAY = "2026-08-03T12:00:00.000Z"


def complete_config():
    return {
        "schemaVersion": 1,
        "testComplete": True,
        "limits": {"totalMediaBudgetUsd": 100, "calendarDays": 10},
        "window": {"startDate": "2026-08-01", "endDate": "2026-08-10"},
        "scope": {"mode": "campaign-only-files", "utmCampaign": "", "utmSource": ""},
        "dataReadiness": {
            "eventsComplete": True,
            "leadsComplete": True,
            "acquisitionComplete": True,
        },
        "intentReview": {
            "completed": True,
            "definition": "Active intent to hire a contractor for the advertised service.",
            "reviewedClicks": 20,
            "qualifiedIntentClicks": 16,
            "minimumQualifiedIntentRate": 0.75,
        },
    }


def complete_economics():
    return {
        "average_contract_revenue": "3000",
        "direct_delivery_cost": "1000",
        "acceptable_acquisition_share": "0.25",
        "expected_show_rate": "0.8",
        "expected_qualification_rate": "0.75",
        "expected_close_rate": "0.5",
        "target_booked_calls_per_week": "4",
        "actual_ad_spend": "90",
        "actual_clicks": "20",
        "actual_booked_calls": "2",
        "actual_held_calls": "2",
        "actual_qualified_calls": "2",
        "actual_won_clients": "1",
        "actual_contribution_profit": "2000",
        "maximum_zero_booking_spend": "60",
        "maximum_cost_per_booked_call_override": "",
        "minimum_qualified_call_rate": "0.5",
        "minimum_contribution_return": "1.5",
        "minimum_wins_before_profit_rule": "1",
        "approved_test_media_cap": "100",
        "approved_test_days": "10",
        "google_test_allocation": "100",
        "meta_test_allocation": "0",
    }


def events():
    return [
        {
            "ts": DAY,
            "name": "page_view",
            "sessionId": f"session-{index:02d}",
            "firstCampaign": "contractor-test",
            "firstUtm": "google",
        }
        for index in range(10)
    ]


def leads():
    return [
        {
            "ts": DAY,
            "receiptId": f"lead_{index}",
            "firstUtmCampaign": "contractor-test",
            "firstUtmSource": "google",
        }
        for index in range(4)
    ]


def stage(uid, name):
    return {
        "schemaVersion": 1,
        "kind": "funnel_stage",
        "stage": name,
        "bookingUid": uid,
        "occurredAt": DAY,
        "attribution": {
            "utmCampaign": "contractor-test",
            "utmSource": "google",
        },
    }


def acquisition():
    rows = []
    for uid in ("booking_001", "booking_002"):
        rows.extend([stage(uid, "booked"), stage(uid, "attended"), stage(uid, "qualified")])
    rows.append(stage("booking_001", "won"))
    return rows


def input_data(path, records):
    return reporter.JsonlInput(path, True, records, [])


class AcquisitionReportTests(unittest.TestCase):
    def build(self, config=None, economics=None, event_rows=None, lead_rows=None, acquisition_rows=None):
        return reporter.build_report(
            config if config is not None else complete_config(),
            economics if economics is not None else complete_economics(),
            input_data(Path("events.jsonl"), events() if event_rows is None else event_rows),
            input_data(Path("leads.jsonl"), leads() if lead_rows is None else lead_rows),
            input_data(
                Path("acquisition.jsonl"),
                acquisition() if acquisition_rows is None else acquisition_rows,
            ),
        )

    def test_complete_evidence_is_only_eligible_for_human_review(self):
        report = self.build()
        self.assertEqual(report["verdict"], "ELIGIBLE_TO_REVIEW")
        self.assertEqual(
            {key: report["funnel"][key] for key in ("clicks", "sessions", "inquiries", "booked", "qualified", "won")},
            {"clicks": 20, "sessions": 10, "inquiries": 4, "booked": 2, "qualified": 2, "won": 1},
        )
        self.assertEqual(
            report["funnel"]["weakestMeasurableTransition"]["from"], "clicks"
        )
        self.assertEqual(
            report["funnel"]["weakestMeasurableTransition"]["to"], "inquiries"
        )
        self.assertAlmostEqual(
            report["funnel"]["weakestMeasurableTransition"]["rate"], 0.2
        )
        self.assertTrue(report["intentReview"]["passed"])
        self.assertNotIn("SCALE", json.dumps(report))

    def test_budget_duration_and_meta_allocation_fail_closed(self):
        config = complete_config()
        config["limits"]["totalMediaBudgetUsd"] = 101
        config["window"]["endDate"] = "2026-08-11"
        economics = complete_economics()
        economics["actual_ad_spend"] = "101"
        economics["google_test_allocation"] = "90"
        economics["meta_test_allocation"] = "10"
        report = self.build(config=config, economics=economics)
        self.assertEqual(report["verdict"], "PAUSE")
        reasons = " ".join(report["findings"]["pause"])
        self.assertIn("no more than $100", reasons)
        self.assertIn("above the allowed duration", reasons)
        self.assertIn("Meta allocation must remain $0", reasons)
        self.assertIn("Actual spend $101.00", reasons)

    def test_incomplete_economics_and_intent_cannot_be_eligible(self):
        config = complete_config()
        config["testComplete"] = False
        config["intentReview"].update(
            {"completed": False, "reviewedClicks": None, "qualifiedIntentClicks": None}
        )
        economics = complete_economics()
        economics["average_contract_revenue"] = ""
        economics["actual_contribution_profit"] = ""
        report = self.build(config=config, economics=economics)
        self.assertEqual(report["verdict"], "ITERATE")
        self.assertFalse(report["economics"]["inputsComplete"])
        self.assertFalse(report["intentReview"]["passed"])

    def test_missing_acquisition_file_keeps_stages_unknown(self):
        config = complete_config()
        config["dataReadiness"]["acquisitionComplete"] = False
        report = reporter.build_report(
            config,
            complete_economics(),
            input_data(Path("events.jsonl"), events()),
            input_data(Path("leads.jsonl"), leads()),
            reporter.JsonlInput(Path("missing-acquisition.jsonl"), False, [], []),
        )
        self.assertEqual(report["verdict"], "ITERATE")
        self.assertIsNone(report["funnel"]["booked"])
        self.assertIsNone(report["funnel"]["qualified"])
        self.assertIsNone(report["funnel"]["won"])
        self.assertFalse(report["funnel"]["transitions"][1]["measurable"])

    def test_missing_booked_stage_is_not_inferred_from_qualified_or_won(self):
        economics = complete_economics()
        economics.update(
            {
                "actual_booked_calls": "0",
                "actual_held_calls": "1",
                "actual_qualified_calls": "1",
                "actual_won_clients": "1",
            }
        )
        rows = [
            stage("booking_001", "attended"),
            stage("booking_001", "qualified"),
            stage("booking_001", "won"),
        ]
        report = self.build(economics=economics, acquisition_rows=rows)
        self.assertEqual(report["funnel"]["booked"], 0)
        self.assertEqual(report["funnel"]["qualified"], 1)
        booked_to_qualified = report["funnel"]["transitions"][2]
        self.assertFalse(booked_to_qualified["measurable"])
        self.assertIn("upstream count is zero", booked_to_qualified["reason"])
        self.assertNotEqual(report["verdict"], "ELIGIBLE_TO_REVIEW")

    def test_first_touch_booking_attribution_scopes_authoritative_stages(self):
        config = complete_config()
        config["scope"] = {
            "mode": "utm-campaign",
            "utmCampaign": "contractor-test",
            "utmSource": "google",
        }
        rows = []
        for uid in ("booking_001", "booking_002"):
            rows.append(
                {
                    "kind": "booking_attribution",
                    "bookingUid": uid,
                    "ts": DAY,
                    "firstAttribution": {
                        "utmCampaign": "contractor-test",
                        "utmSource": "google",
                    },
                    "lastAttribution": {
                        "utmCampaign": "different-retargeting",
                        "utmSource": "meta",
                    },
                }
            )
            for name in ("booked", "attended", "qualified"):
                record = stage(uid, name)
                record["attribution"] = {}
                rows.append(record)
        won = stage("booking_001", "won")
        won["attribution"] = {}
        rows.append(won)
        report = self.build(config=config, acquisition_rows=rows)
        self.assertEqual(report["funnel"]["booked"], 2)
        self.assertEqual(report["funnel"]["qualified"], 2)
        self.assertEqual(report["funnel"]["won"], 1)
        self.assertEqual(report["verdict"], "ELIGIBLE_TO_REVIEW")

    def test_reschedule_chain_is_one_booking_and_old_slot_cancellations_are_ignored(self):
        first = stage("booking_original_001", "booked")
        first_cancelled = stage("booking_original_001", "cancelled")
        second = stage("booking_rescheduled_002", "booked")
        second["context"] = {
            "triggerEvent": "BOOKING_RESCHEDULED",
            "previousBookingUid": "booking_original_001",
        }
        second_cancelled = stage("booking_rescheduled_002", "cancelled")
        third = stage("booking_rescheduled_003", "booked")
        third["context"] = {
            "triggerEvent": "BOOKING_RESCHEDULED",
            "previousBookingUid": "booking_rescheduled_002",
        }
        qualified = stage("booking_rescheduled_003", "qualified")
        rows = [first, first_cancelled, second, second_cancelled, third, qualified]

        selected = reporter.acquisition_records(
            input_data(Path("acquisition.jsonl"), rows),
            reporter.parse_day("2026-08-01"),
            reporter.parse_day("2026-08-10"),
            "campaign-only-files",
            "",
            "",
        )
        self.assertEqual(
            {record["bookingUid"] for record in selected},
            {"booking_rescheduled_003"},
        )
        self.assertNotIn("cancelled", {record["stage"] for record in selected})

        report = self.build(acquisition_rows=rows)
        self.assertEqual(report["funnel"]["booked"], 1)
        self.assertEqual(report["funnel"]["qualified"], 1)

    def test_rescheduled_booking_inherits_original_uid_campaign_attribution(self):
        config = complete_config()
        config["scope"] = {
            "mode": "utm-campaign",
            "utmCampaign": "contractor-test",
            "utmSource": "google",
        }
        browser_touch = {
            "kind": "booking_attribution",
            "bookingUid": "booking_original_001",
            "ts": DAY,
            "firstAttribution": {
                "utmCampaign": "contractor-test",
                "utmSource": "google",
            },
        }
        original = stage("booking_original_001", "booked")
        original["attribution"] = {}
        replacement = stage("booking_rescheduled_002", "booked")
        replacement["attribution"] = {}
        replacement["context"] = {
            "triggerEvent": "BOOKING_RESCHEDULED",
            "previousBookingUid": "booking_original_001",
        }
        qualified = stage("booking_rescheduled_002", "qualified")
        qualified["attribution"] = {}
        rows = [browser_touch, original, replacement, qualified]

        selected = reporter.acquisition_records(
            input_data(Path("acquisition.jsonl"), rows),
            reporter.parse_day("2026-08-01"),
            reporter.parse_day("2026-08-10"),
            "utm-campaign",
            "contractor-test",
            "google",
        )
        self.assertEqual(
            {record["bookingUid"] for record in selected},
            {"booking_rescheduled_002"},
        )
        self.assertEqual({record["stage"] for record in selected}, {"booked", "qualified"})

        report = self.build(config=config, acquisition_rows=rows)
        self.assertEqual(report["funnel"]["booked"], 1)
        self.assertEqual(report["funnel"]["qualified"], 1)

    def test_jsonl_corruption_pauses_and_cli_csv_schema_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            broken = root / "events.jsonl"
            broken.write_text('{"ts":"2026-08-03T12:00:00Z"}\nnot-json\n', encoding="utf-8")
            parsed = reporter.read_jsonl(broken)
            self.assertTrue(parsed.errors)
            report = reporter.build_report(
                complete_config(),
                complete_economics(),
                parsed,
                input_data(root / "leads.jsonl", leads()),
                input_data(root / "acquisition.jsonl", acquisition()),
            )
            self.assertEqual(report["verdict"], "PAUSE")

            economics_csv = root / "economics.csv"
            with economics_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["row_type", "key", "label", "input", "calculated_value", "unit", "decision_note"],
                )
                writer.writeheader()
                for key, value in complete_economics().items():
                    writer.writerow({"row_type": "input", "key": key, "input": value})
            parsed_economics, errors = reporter.read_economics(economics_csv)
            self.assertEqual(errors, [])
            self.assertEqual(parsed_economics["approved_test_media_cap"], "100")


if __name__ == "__main__":
    unittest.main()
