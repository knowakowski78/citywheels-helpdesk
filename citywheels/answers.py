"""Render financial facts from trusted tool output, never from generated prose."""
import re
import json

from .tools import CONTACT


def polish(question):
    return bool(re.search(r"[ąćęłńóśźż]|\b(ile|zwrot|teraz|rezerwacja|dostane|jakie|godziny|stolica)\b", question, re.I))


def policy_excerpt(match, query):
    terms = set(re.findall(r"[\w-]+", query.casefold())) - {"the", "a", "an", "for", "of", "in", "on", "and", "to", "is", "are", "can", "what"}
    for word, related in {"opening": "open", "hours": "open", "pricing": "price", "prices": "price", "helmet": "helmets"}.items():
        if word in terms:
            terms.add(related)
    sections = re.split(r"(?m)(?=^## )", match["text"])
    scored = [(len(terms & set(re.findall(r"[\w-]+", section.casefold()))), index, section.strip()) for index, section in enumerate(sections)]
    scored.sort(key=lambda item: (-item[0], item[1]))
    relevant = [item for item in scored if item[0] and item[0] >= scored[0][0] / 2][:2]
    if not relevant:
        return match["text"].strip()
    relevant.sort(key=lambda item: item[1])
    return "\n\n".join(item[2] for item in relevant)


def safe_answer(question, content, trace):
    pl = polish(question)
    booking_results = [entry["result"] for entry in trace if entry["tool"] in {"get_booking", "calculate_refund"} and "found" in entry["result"]]
    if booking_results and not booking_results[-1]["found"]:
        result = booking_results[-1]
        prefix = "Nie znaleziono rezerwacji" if pl else "Booking not found:"
        return f"{prefix} {result['booking_id']}. {CONTACT}"
    refunds = [entry["result"] for entry in trace if entry["tool"] == "calculate_refund" and entry["result"].get("found")]
    if refunds:
        result = refunds[-1]
        if pl:
            status = "Można anulować tę rezerwację." if result["can_cancel"] else f"Nie można anulować rezerwacji (status: {result['status']}); brak zwrotu."
            method = "Nowy voucher; bez zwrotu gotówki. Depozyt wraca pierwotną metodą płatności." if "voucher" in result["refund_method"] else "Na pierwotną kartę w ciągu 5 dni roboczych." if result["can_cancel"] else "Brak."
            return (f"Rezerwacja {result['booking_id']}, wycena na {result['as_of']}. {status}\n"
                    f"Zwrot za wynajem: {result['rental_refund_eur']} EUR. Zwrot depozytu: {result['deposit_refund_eur']} EUR. "
                    f"Łącznie: {result['total_refund_eur']} EUR. Opłata rezerwacyjna nie podlega zwrotowi (zwrot: 0.00 EUR).\n"
                    f"Sposób zwrotu: {method}\nTo tylko wycena; rezerwacja nie została anulowana. Wyjątek pogodowy wymaga decyzji obsługi. "
                    f"Źródło: {result['source']}. {CONTACT}")
        status = "This booking can be cancelled." if result["can_cancel"] else f"This booking cannot be cancelled (status: {result['status']}); nothing is refunded."
        method = result["refund_method"] + ("; no cash refund" if "voucher" in result["refund_method"] else "")
        return (f"Booking {result['booking_id']}; quote as of {result['as_of']}. {status}\n"
                f"Rental refund: {result['rental_refund_eur']} EUR. Deposit refund: {result['deposit_refund_eur']} EUR. "
                f"Total refund: {result['total_refund_eur']} EUR. The booking fee is non-refundable (refund: 0.00 EUR).\n"
                f"Refund method: {method}.\nQuote only; no booking has been cancelled. Storm-warning exceptions require staff approval. "
                f"Source: {result['source']}. {CONTACT}")
    has_evidence = any(entry["result"].get("found") for entry in trace)
    if booking_results and "booking" in booking_results[-1]:
        heading = "Dane rezerwacji z data/bookings.json:" if pl else "Booking details from data/bookings.json:"
        return heading + "\n" + json.dumps(booking_results[-1]["booking"], ensure_ascii=False, indent=2)
    searches = [entry for entry in trace if entry["tool"] == "search_policies" and entry["result"].get("found")]
    if searches:
        search = searches[-1]
        match = search["result"]["matches"][0]
        excerpt = policy_excerpt(match, search["arguments"]["query"])
        heading = "Fragmenty regulaminu CityWheels" if pl else "CityWheels policy excerpts"
        return f"{heading} — {match['source']}:\n\n{excerpt}\n\n{CONTACT}"
    if not has_evidence:
        if pl:
            return "Nie mogę odpowiedzieć bez potwierdzenia w danych CityWheels. Jeśli pytanie dotyczy rezerwacji, podaj jej numer. " + CONTACT
        return "I cannot answer without verified CityWheels data. If this concerns a booking, please provide its booking ID. " + CONTACT
    return content
