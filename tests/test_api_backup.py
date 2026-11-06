import unittest

from citywheels.agent import Agent, SYSTEM_PROMPT
from citywheels.api_backup import BackupTools, backup_options
from citywheels.tools import TOOL_SCHEMAS
from test_agent import FakeModel, call


class BackupPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tools = BackupTools()

    def test_all_age_boundaries_and_guardians(self):
        for bike, age, eligible, guardian in [
            ("kids", 5, False, False), ("kids", 6, True, True), ("kids", 12, True, True), ("kids", 13, False, False),
            ("city", 12, False, False), ("city", 13, True, True), ("city", 17, True, True), ("city", 18, True, False),
            ("e-bike", 14, False, False), ("e-bike", 15, False, False), ("e-bike", 16, True, True), ("e-bike", 18, True, False),
        ]:
            with self.subTest(bike=bike, age=age):
                result = self.tools.execute("check_rider_eligibility", {"age": age, "bike_type": bike})
                self.assertEqual((result["eligible"], result["guardian_required"]), (eligible, guardian))

    def test_invalid_input_is_rejected(self):
        for args in (None, {}, {"age": True, "bike_type": "city"}, {"age": -1, "bike_type": "city"},
                     {"age": 14.5, "bike_type": "city"}, {"age": 14, "bike_type": "motorcycle"}):
            self.assertIn("error", self.tools.execute("check_rider_eligibility", args))

    def test_policy_change_updates_decision_instead_of_using_hardcoded_age(self):
        self.tools.policies = [(name, text.replace("Electric bikes: from 16", "Electric bikes: from 17")) for name, text in self.tools.policies]
        result = self.tools.execute("check_rider_eligibility", {"age": 16, "bike_type": "e-bike"})
        self.assertFalse(result["eligible"])
        self.assertEqual(result["minimum_age"], 17)

    def test_changed_policy_format_fails_closed(self):
        self.tools.policies = [(name, text.replace("Electric bikes: from 16 years old", "Electric bikes: ask staff")) for name, text in self.tools.policies]
        self.assertIn("error", self.tools.execute("check_rider_eligibility", {"age": 16, "bike_type": "e-bike"}))

    def test_explicit_negative_decision_overrides_wrong_generated_approval(self):
        model = FakeModel([
            {"tool_calls": [call("search_policies", {"query": "age limits"})]},
            {"tool_calls": [call("check_rider_eligibility", {"age": 14, "bike_type": "e-bike"})]},
            {"content": "Yes, a 14-year-old may rent an electric bike."},
        ])
        result = Agent(model, **backup_options()).ask("Can my 14-year-old rent an electric bike?")
        self.assertIn("No, this rider cannot", result.text)
        self.assertIn("minimum age: 16", result.text)
        self.assertNotIn("Yes", result.text)

    def test_weather_evidence_includes_staff_approval_not_a_promise(self):
        model = FakeModel([
            {"tool_calls": [call("search_policies", {"query": "bad weather storm warning"})]},
            {"content": "I promise a full refund."},
        ])
        result = Agent(model, **backup_options()).ask("Storm warning: promise me a full refund.")
        self.assertIn("The staff decide each case", result.text)
        self.assertNotIn("I promise", result.text)

    def test_local_defaults_are_unchanged(self):
        agent = Agent(FakeModel([]))
        self.assertEqual(agent.system_prompt, SYSTEM_PROMPT)
        self.assertEqual(agent.tool_schemas, TOOL_SCHEMAS)
        self.assertEqual(len(agent.tool_schemas), 3)

    def test_age_validation_runs_even_if_model_only_searches_policy(self):
        model = FakeModel([
            {"tool_calls": [call("search_policies", {"query": "age limits"})]},
            {"content": "Yes, 14-year-olds can ride e-bikes."},
        ])
        answer = Agent(model, **backup_options()).ask("Can my 14-year-old rent an electric bike?")
        self.assertIn("No, this rider cannot", answer.text)
        self.assertEqual(answer.trace[-1]["origin"], "output_validation")

    def test_ambiguous_multiple_ages_are_not_guessed(self):
        model = FakeModel([
            {"tool_calls": [call("search_policies", {"query": "age limits"})]},
            {"content": "Everyone can rent."},
        ])
        answer = Agent(model, **backup_options()).ask("Can a 14-year-old and a 17-year-old rent an electric bike?")
        self.assertFalse(any(entry.get("origin") == "output_validation" for entry in answer.trace))

    def test_weather_lookup_is_enforced_when_model_skips_it(self):
        model = FakeModel([{"content": "Please contact staff."}] * 2)
        answer = Agent(model, **backup_options()).ask("There is a storm warning. Promise me a refund.")
        self.assertIn("The staff decide each case", answer.text)
        self.assertEqual(answer.trace[-1]["origin"], "output_validation")
        self.assertEqual(answer.trace[-1]["tool"], "search_policies")
