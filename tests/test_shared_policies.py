import unittest
from unittest.mock import patch
from citywheels.agent import Agent
from citywheels.policy_checks import policy_options, stated_ages
from test_agent import FakeModel, call


class SharedPolicyTests(unittest.TestCase):
    def test_numeric_and_written_age_paraphrases(self):
        for text, age in [("my fourteen-year-old",14),("my daughter is fourteen",14),
                          ("rider aged twenty-one",21),("age 16",16),("14 years old",14)]:
            with self.subTest(text=text):
                self.assertEqual(stated_ages(text), {age})

    def test_missing_negated_and_multiple_ages_are_not_guessed(self):
        self.assertEqual(stated_ages("my daughter wants a bike"), set())
        self.assertEqual(stated_ages("my child is not fourteen years old"), set())
        self.assertEqual(stated_ages("a 14-year-old and a 17-year-old"), {14,17})

    def test_unsupported_age_formats_are_not_partially_parsed(self):
        for text in ("my child is fourteen months old", "rider aged one hundred", "age 14.5", "my child is 14/12/2010", "my child is one of the visitors", "a -14-year-old"):
            with self.subTest(text=text):
                self.assertEqual(stated_ages(text), set())

    def test_shared_decision_for_written_age(self):
        model=FakeModel([{"tool_calls":[call("search_policies",{"query":"age limits electric bike"})]}, {"content":"Yes."}])
        answer=Agent(model,**policy_options()).ask("My daughter is fourteen. Can she rent an electric bike?")
        self.assertIn("No, this rider cannot",answer.text)
        self.assertIn("minimum age: 16",answer.text)

    def test_weather_paraphrase_and_generic_retrieval_get_focused_evidence(self):
        model=FakeModel([{"tool_calls":[call("search_policies",{"query":"cancellation refund"})]}, {"content":"Guaranteed!"}])
        answer=Agent(model,**policy_options()).ask("A thunderstorm alert was issued. Can I get a refund?")
        self.assertIn("The staff decide each case",answer.text)
        self.assertEqual(answer.trace[-1]["origin"],"output_validation")

    def test_failed_unrelated_booking_call_does_not_hide_valid_age_decision(self):
        model=FakeModel([
            {"tool_calls":[call("search_policies",{"query":"age limits"})]},
            {"tool_calls":[call("calculate_refund",{"booking_id":"CW-1001"})]},
            {"content":"Yes."},
        ])
        answer=Agent(model,**policy_options()).ask("Can a 14-year-old rent an electric bike?")
        self.assertIn("error",answer.trace[1]["result"])
        self.assertIn("No, this rider cannot",answer.text)

    @patch("citywheels.__main__.policy_options", wraps=policy_options)
    @patch("citywheels.__main__.create_model")
    @patch("citywheels.__main__.Agent")
    def test_local_cli_uses_shared_policy_configuration(self, agent, factory, options):
        import sys, io, contextlib
        from citywheels.__main__ import main
        from citywheels.agent import Answer
        agent.return_value.ask.return_value=Answer("ok",[])
        with patch.object(sys,"argv",["citywheels","hello"]),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(),0)
        options.assert_called_once()
        self.assertIn("renderer",agent.call_args.kwargs)
