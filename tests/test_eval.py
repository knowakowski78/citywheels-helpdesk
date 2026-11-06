import unittest
import json
from pathlib import Path

from citywheels.agent import Answer
from eval.run import check


class EvalTests(unittest.TestCase):
    def test_correct_text_without_tool_does_not_pass_refund(self):
        case = {"tools": ["calculate_refund"], "patterns": ["340"], "refund": "340.00"}
        problems = check(case, Answer("340.00 EUR", []))
        self.assertEqual(len(problems), 2)

    def test_forbidden_general_knowledge_is_caught(self):
        case = {"forbidden": ["Canberra"]}
        self.assertTrue(check(case, Answer("The capital is Canberra.", [])))

    def test_valid_answer_and_trace_pass(self):
        case = {"tools": ["calculate_refund"], "patterns": ["340"], "refund": "340.00"}
        answer = Answer("340 EUR", [{"tool": "calculate_refund", "result": {"total_refund_eur": "340.00"}}])
        self.assertEqual(check(case, answer), [])

    def test_refund_for_wrong_booking_is_rejected(self):
        case = {"tools": ["calculate_refund"], "refund": "340.00", "booking_id": "CW-1002"}
        answer = Answer("340 EUR", [{"tool": "calculate_refund", "arguments": {"booking_id": "CW-9999"}, "result": {"booking_id": "CW-9999", "total_refund_eur": "340.00"}}])
        self.assertTrue(check(case, answer))

    def voucher_case_and_trace(self):
        cases_path = Path(__file__).resolve().parent.parent / "eval" / "cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        case = next(case for case in cases if case["id"] == "voucher")
        trace = [{"tool": "calculate_refund", "result": {
            "booking_id": "CW-1004", "total_refund_eur": "73.00"}}]
        return case, trace

    def test_voucher_cash_promises_are_rejected_even_with_correct_tool_result(self):
        case, trace = self.voucher_case_and_trace()
        for text in [
            "Yes, your 73 EUR refund can be paid in cash instead of a voucher.",
            "Your 73 EUR voucher refund: you can get cash.",
            "No cash refund for this 73 EUR voucher. However, you can receive it in cash.",
            "No cash refund for the 73 EUR voucher. Cash refunds are available on request.",
        ]:
            with self.subTest(text=text):
                problems = check(case, Answer(text, trace))
                self.assertTrue(any(problem.startswith("Forbidden pattern:") for problem in problems))

    def test_voucher_answer_must_explicitly_rule_out_cash(self):
        case, trace = self.voucher_case_and_trace()
        self.assertTrue(check(case, Answer("Total refund: 73 EUR as a voucher.", trace)))

    def test_voucher_no_cash_answers_pass(self):
        case, trace = self.voucher_case_and_trace()
        for text in [
            "Total refund: 73.00 EUR. New voucher; no cash refund.",
            "73 EUR as a voucher; you cannot get cash.",
            "73 EUR as a voucher. Cash refunds are not available.",
        ]:
            with self.subTest(text=text):
                self.assertEqual(check(case, Answer(text, trace)), [])

    def test_zero_check_does_not_accept_digits_in_booking_id_or_other_amounts(self):
        cases_path = Path(__file__).resolve().parent.parent / "eval" / "cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        for case_id, text in [("refund-late", "Booking CW-1003: total refund 50.00 EUR."),
                              ("in-progress", "Booking CW-1008: total refund 150.00 EUR.")]:
            case = next(case for case in cases if case["id"] == case_id)
            with self.subTest(case=case_id):
                # Isolate the zero/no-refund assertion: IDs and other amounts contain zeros.
                self.assertTrue(check({"patterns": [case["patterns"][1]]}, Answer(text, [])))


if __name__ == "__main__":
    unittest.main()
