import json
import unittest

from citywheels.agent import Agent
from citywheels.model import ModelError


def call(name, arguments):
    return {"function": {"name": name, "arguments": arguments}}


class FakeModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def chat(self, messages, tools):
        # Snapshot the actual history, so assertions also verify ordering.
        self.requests.append(json.loads(json.dumps(messages)))
        return next(self.responses)


class AgentTests(unittest.TestCase):
    def test_multiple_rounds_feed_real_results_to_model(self):
        class CheckingModel(FakeModel):
            def chat(self, messages, tools):
                if len(self.requests) == 2:
                    result = json.loads(messages[-1]["content"])
                    self_result = result["total_refund_eur"]
                    if self_result != "340.00":
                        raise AssertionError("Wrong refund fed back to model")
                return super().chat(messages, tools)

        model = CheckingModel([
            {"tool_calls": [call("get_booking", {"booking_id": "CW-1002"})]},
            {"tool_calls": [call("calculate_refund", {"booking_id": "CW-1002"})]},
            {"content": "Your total refund is 340.00 EUR."},
        ])
        answer = Agent(model).ask("Cancel CW-1002; how much comes back?")
        self.assertIn("340.00", answer.text)
        self.assertEqual([t["tool"] for t in answer.trace], ["get_booking", "calculate_refund"])
        self.assertEqual(model.requests[1][-1]["role"], "tool")
        self.assertEqual(model.requests[1][-1]["tool_name"], "get_booking")

    def test_multiple_calls_in_one_turn_and_string_json_arguments(self):
        model = FakeModel([
            {"tool_calls": [call("search_policies", '{"query":"refund"}'), call("get_booking", {"booking_id": "CW-9999"})]},
            {"content": "Booking not found. Contact staff."},
        ])
        result = Agent(model).ask("CW-9999?")
        self.assertEqual(len(result.trace), 2)
        self.assertFalse(result.trace[-1]["result"]["found"])
        self.assertEqual([m["role"] for m in model.requests[1][-3:]], ["assistant", "tool", "tool"])

    def test_invalid_calls_return_errors_instead_of_crashing(self):
        model = FakeModel([
            {"tool_calls": [call("get_booking", "bad json"), call("get_booking", []), call("invent", {}), {"function": None}]},
            {"content": "Please contact staff."},
        ])
        result = Agent(model).ask("test")
        self.assertTrue(all("error" in item["result"] for item in result.trace))

    def test_tool_loop_has_bound(self):
        model = FakeModel([{"tool_calls": [call("get_booking", {"booking_id": "CW-1001"})]}] * 3)
        result = Agent(model, max_rounds=3).ask("test")
        self.assertIn("limit", result.text)
        self.assertEqual(len(result.trace), 3)

    def test_empty_or_malformed_model_output_is_error(self):
        for response in (None, {}, {"tool_calls": "wrong"}, {"tool_calls": [call("get_booking", {})] * 13}):
            with self.subTest(response=response):
                with self.assertRaises(ModelError):
                    Agent(FakeModel([response])).ask("test")

    def test_questions_do_not_share_history(self):
        model = FakeModel([{"content": "Please provide a booking ID."}] * 4)
        agent = Agent(model)
        agent.ask("One")
        agent.ask("Two")
        self.assertEqual(len(model.requests[2]), 2)
        self.assertEqual(model.requests[2][-1]["content"], "Two")

    def test_refund_prose_cannot_override_tool_amount_or_payment_method(self):
        model = FakeModel([
            {"tool_calls": [call("calculate_refund", {"booking_id": "CW-1004"})]},
            {"content": "Cash refund yes: 999 EUR. Your booking is now cancelled."},
        ])
        answer = Agent(model).ask("Refund for CW-1004?")
        self.assertIn("73.00 EUR", answer.text)
        self.assertIn("no cash refund", answer.text)
        self.assertIn("no booking has been cancelled", answer.text)
        self.assertNotIn("999", answer.text)

    def test_unguarded_general_knowledge_is_replaced_with_referral(self):
        model = FakeModel([{"content": "The capital is Canberra."}] * 2)
        answer = Agent(model).ask("What is the capital of Australia?")
        self.assertNotIn("Canberra", answer.text)
        self.assertIn("help@citywheels.example", answer.text)
        self.assertEqual(len(model.requests), 2)

    def test_model_cannot_lookup_a_booking_id_not_supplied_by_customer(self):
        model = FakeModel([
            {"tool_calls": [call("get_booking", {"booking_id": "CW-1001"})]},
            {"content": "Here are your booking details."},
        ])
        answer = Agent(model).ask("How much is my refund?")
        self.assertIn("error", answer.trace[0]["result"])
        self.assertIn("provide its booking ID", answer.text)

    def test_booking_id_must_match_a_complete_supplied_id(self):
        model = FakeModel([
            {"tool_calls": [call("get_booking", {"booking_id": "CW-1001"})]},
            {"content": "Here are your booking details."},
        ])
        answer = Agent(model).ask("Details of CW-10010?")
        self.assertIn("error", answer.trace[0]["result"])
        self.assertNotIn('"status": "confirmed"', answer.text)

    def test_unknown_booking_cannot_be_overridden_by_generated_prose(self):
        model = FakeModel([
            {"tool_calls": [call("get_booking", {"booking_id": "CW-9999"})]},
            {"content": "Found your booking; its price is 100 EUR."},
        ])
        answer = Agent(model).ask("Details of CW-9999")
        self.assertIn("not found", answer.text)
        self.assertNotIn("100 EUR", answer.text)

    def test_known_booking_details_are_rendered_from_data(self):
        model = FakeModel([
            {"tool_calls": [call("get_booking", {"booking_id": "CW-1001"})]},
            {"content": "Your booking is completed and cost 999 EUR."},
        ])
        answer = Agent(model).ask("Details of CW-1001")
        self.assertIn('"status": "confirmed"', answer.text)
        self.assertNotIn("999", answer.text)

    def test_wrong_policy_interpretation_is_replaced_with_source_excerpt(self):
        model = FakeModel([
            {"tool_calls": [call("search_policies", {"query": "opening hours Saturday June"})]},
            {"content": "In June Saturday hours are 09:00-17:00."},
        ])
        answer = Agent(model).ask("Saturday opening hours in June?")
        self.assertIn("April to October: every day, 08:00–20:00", answer.text)
        self.assertIn("data/policies/faq.md", answer.text)
        self.assertNotIn("In June Saturday hours are", answer.text)

    def test_empty_answer_is_a_safe_referral(self):
        answer = Agent(FakeModel([{"content": " "}])).ask("What is the capital of Australia?")
        self.assertIn("cannot answer", answer.text)
        self.assertIn("help@citywheels.example", answer.text)

    def test_truncated_output_after_lookup_still_returns_verified_not_found(self):
        class TruncatedModel(FakeModel):
            def chat(self, messages, tools):
                if self.requests:
                    from citywheels.model import ModelOutputError
                    raise ModelOutputError("generation limit")
                return super().chat(messages, tools)
        answer = Agent(TruncatedModel([{"tool_calls": [call("get_booking", {"booking_id": "CW-9999"})]}])).ask("CW-9999 details?")
        self.assertIn("not found", answer.text)


if __name__ == "__main__":
    unittest.main()
