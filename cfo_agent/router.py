from __future__ import annotations

from .skills import search_skills


SPECIALISTS = {
    "fpna": "FP&A Lead",
    "accounting": "Group Financial Controller",
    "treasury": "Treasury Lead",
    "corporate-finance": "Corporate Finance and M&A Lead",
    "risk-controls": "Internal Controls and Audit Lead",
    "tax-thailand": "Thailand Tax Lead",
    "industry-data": "Finance Data and Industry Analytics Lead",
}


def route_task(text: str, *, limit: int = 5) -> dict[str, object]:
    matches = search_skills(text, limit=limit)
    if not matches:
        return {
            "specialist": "Group CFO",
            "skills": [],
            "reason": "No specialist skill matched; Group CFO triage required.",
        }
    categories: dict[str, int] = {}
    for match in matches:
        categories[match["category"]] = categories.get(match["category"], 0) + int(
            match.get("score", 1)
        )
    category = max(categories, key=categories.get)
    specialist = SPECIALISTS.get(category, "Group CFO")
    return {
        "specialist": specialist,
        "category": category,
        "skills": [match["slug"] for match in matches],
        "matches": matches,
        "reason": f"Highest weighted skill match is in {category}.",
    }
