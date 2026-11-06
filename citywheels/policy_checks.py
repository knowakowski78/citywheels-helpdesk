"""Provider-independent policy validation shared by local and hosted agents."""
import re
from functools import partial

from .agent import SYSTEM_PROMPT
from .answers import polish, safe_answer
from .tools import CONTACT, TOOL_SCHEMAS, Tools

ONES = dict(zip("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(), range(20)))
TENS = dict(zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10)))
NUMBER = r"(?:\d{1,3}|" + "|".join(ONES) + "|(?:" + "|".join(TENS) + r")(?:[- ](?:" + "|".join(list(ONES)[1:10]) + r"))?)"


def stated_ages(question):
    # These formats need clarification rather than treating their first number as an age.
    if re.search(r"\b(?:months?|weeks?|days?)\s+old\b|\bhundred\b|\b\d+\.\d+\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|(?<!\w)-\s*\d+", question, re.I):
        return set()
    # Do not interpret a negated age as the actual age.
    if re.search(r"\b(?:not|isn't)\s+(?:(?:age|aged)\s+)?" + NUMBER + r"\b", question, re.I):
        return set()
    pattern = r"\b(" + NUMBER + r")[- ]years?[- ]old\b|\bage(?:d)?\s+(" + NUMBER + r")\b|\b(?:son|daughter|child|rider)\s+is\s+(" + NUMBER + r")\b"
    ages = set()
    for match in re.finditer(pattern, question, re.I):
        if re.match(r"\s+of\b", question[match.end():], re.I):
            continue  # "my child is one of ..." does not state an age.
        value = next(value.lower() for value in match.groups() if value)
        if value.isdigit():
            ages.add(int(value))
        else:
            parts = value.replace('-', ' ').split()
            ages.add(sum(ONES.get(part, TENS.get(part, 0)) for part in parts))
    return ages


class PolicyTools(Tools):
    def execute(self, name, arguments):
        if name != "check_rider_eligibility":
            return super().execute(name, arguments)
        if not isinstance(arguments, dict) or set(arguments) != {"age", "bike_type"}:
            return {"error": "Expected age and bike_type."}
        age, bike = arguments["age"], arguments["bike_type"]
        if (
            type(age) is not int or not 0 <= age <= 120
            or not isinstance(bike, str) or bike not in {"city", "e-bike", "kids"}
        ):
            return {"error": "Age must be an integer 0–120; bike_type must be city, e-bike or kids."}
        faq = next((text for filename, text in self.policies if filename == "faq.md"), "")
        label = {"city": "City bikes", "e-bike": "Electric bikes", "kids": "Kids bikes"}[bike]
        line = re.search(re.escape(label) + r": [^\n]+", faq)
        if not line:
            return {"error": "Age policy not found; contact staff.", "contact": CONTACT}
        pattern = re.escape(label) + (r": for children from (\d+) to (\d+) years old" if bike == "kids" else r": from (\d+) years old")
        rule = re.search(pattern, line[0])
        guardian = re.search(r"Riders under (\d+) need a parent or guardian to sign the rental", line[0])
        if (
            not rule
            or (bike != "kids" and not guardian)
            or (bike == "kids" and "rented by a parent or guardian" not in line[0])
        ):
            return {"error": "Age policy format changed; staff review is required.", "contact": CONTACT}
        minimum = int(rule[1])
        maximum = int(rule[2]) if bike == "kids" else None
        eligible = age >= minimum and (maximum is None or age <= maximum)
        return {"found": True, "age": age, "bike_type": bike, "eligible": eligible,
                "minimum_age": minimum, "maximum_age": maximum,
                "guardian_required": eligible and (bike == "kids" or age < int(guardian[1])),
                "source": "data/policies/faq.md", "rule": rule[0],
                "note": "Age eligibility only; no availability check or booking change."}


def policy_answer(question, content, trace, *, tools=None):
    weather_request = re.search(r"\b(?:thunder)?storm\s+(?:warning|alert)\b|\b(?:bad|severe)\s+weather\b|\bweather\s+exception\b", question, re.I)
    weather_evidence = any(
        entry["tool"] == "search_policies"
        and any(
            match["source"] == "data/policies/cancellations.md" and "## Bad weather" in match["text"]
            for match in entry["result"].get("matches", [])
        )
        and re.search(r"weather|storm", entry["arguments"].get("query", ""), re.I)
        for entry in trace
    )
    if tools and weather_request and not weather_evidence:
        arguments = {"query": "bad weather storm warning"}
        result = tools.execute("search_policies", arguments)
        trace.append({"tool": "search_policies", "arguments": arguments, "result": result, "origin": "output_validation"})
    results = [
        entry["result"] for entry in trace
        if entry["tool"] == "check_rider_eligibility" and entry["result"].get("found")
    ]
    age_evidence = any(
        entry["tool"] == "search_policies"
        and any(
            match["source"] == "data/policies/faq.md" and "## Are there age limits?" in match["text"]
            for match in entry["result"].get("matches", [])
        )
        for entry in trace
    )
    if not results and tools and age_evidence:
        ages = stated_ages(question)
        bikes = {bike for bike, pattern in {
            "e-bike": r"\belectric\s+bikes?\b|\be[- ]?bikes?\b", "city": r"\bcity\s+bikes?\b", "kids": r"\bkids\s+bikes?\b",
        }.items() if re.search(pattern, question, re.I)}
        if len(ages) == len(bikes) == 1:
            arguments = {"age": ages.pop(), "bike_type": bikes.pop()}
            result = tools.execute("check_rider_eligibility", arguments)
            trace.append({"tool": "check_rider_eligibility", "arguments": arguments, "result": result, "origin": "output_validation"})
            if result.get("found"):
                results = [result]
    # A failed tool call should not hide an otherwise valid age answer.
    booking = any(
        entry["tool"] in {"get_booking", "calculate_refund"} and "found" in entry["result"]
        for entry in trace
    )
    if results and not booking:
        result = results[-1]
        pl = polish(question)
        if pl:
            decision = "Tak, wiek spełnia wymagania." if result["eligible"] else "Nie, ten wiek nie spełnia wymagań."
            text = f"{decision} Wiek: {result['age']}; typ roweru: {result['bike_type']}; minimum: {result['minimum_age']}."
            if result["maximum_age"] is not None:
                text += f" Maksimum: {result['maximum_age']}."
            if result["guardian_required"]:
                text += " Wymagany jest rodzic lub opiekun podpisujący wynajem."
        else:
            decision = "Yes, this rider meets the age requirement." if result["eligible"] else "No, this rider cannot rent this bike under the age rules."
            text = f"{decision} Rider age: {result['age']}; bike type: {result['bike_type']}; minimum age: {result['minimum_age']}."
            if result["maximum_age"] is not None:
                text += f" Maximum age: {result['maximum_age']}."
            if result["guardian_required"]:
                text += " A parent or guardian must sign the rental."
        return text + f" Source: {result['source']}. " + CONTACT
    return safe_answer(question, content, trace)


def policy_options():
    tools = PolicyTools()
    return {
        "tools": tools,
        "tool_schemas": TOOL_SCHEMAS,
        "renderer": partial(policy_answer, tools=tools),
        "system_prompt": SYSTEM_PROMPT + """
For a rider-age eligibility question, search_policies for age limits. Do not guess a missing age
or bike type. The application validates clear, explicit age/bike pairs in code after retrieval.
A request for a promise, waiver or exception is still a shop-policy question. Retrieve the relevant
policy before refusing to promise anything. In particular, weather/storm-warning requests ALWAYS
require search_policies with 'bad weather storm warning'. Explain the staff decision required by
the retrieved rule; never guarantee a refund or claim to verify an actual weather warning.
""",
    }
