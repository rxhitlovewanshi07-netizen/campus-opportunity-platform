"""Simple rule-based recommendations (no machine learning)."""
from collections import Counter
from datetime import date

from .models import Application, Bookmark, Opportunity

SOON_DAYS = 14


def _deadline_text(days):
    if days == 0:
        return "Closes today"
    return f"Closes in {days} day{'s' if days != 1 else ''}"


def score_opportunity(opportunity, preferred_category_ids, preferred_eligibility, today):
    """Return a transparent (score, reasons) pair for one opportunity."""
    score, reasons = 0, []

    if opportunity.category_id in preferred_category_ids:
        score += 3
        reasons.append(
            f"You bookmarked or applied to other {opportunity.category.name} listings"
        )

    eligibility = (opportunity.eligibility or "").strip()
    if eligibility.lower() == "all":
        score += 2
        reasons.append("Open to all students")
    elif preferred_eligibility and eligibility == preferred_eligibility:
        score += 2
        display = getattr(opportunity, "get_eligibility_display", None)
        eligibility_label = display() if callable(display) else eligibility
        reasons.append(f"Matches your usual eligibility ({eligibility_label})")

    days = (opportunity.deadline - today).days
    if 0 <= days <= SOON_DAYS:
        score += 1
        reasons.append(_deadline_text(days))

    return score, reasons


def recommend_for(user, limit=6, today=None):
    """Return (opportunity, score, reasons) tuples, best match first."""
    today = today or date.today()

    bookmarked = Bookmark.objects.filter(user=user).select_related("opportunity")
    applied = Application.objects.filter(user=user).select_related("opportunity")
    past = [item.opportunity for item in bookmarked] + [item.opportunity for item in applied]
    tracked_ids = {opportunity.pk for opportunity in past}

    candidates = (
        Opportunity.objects.filter(is_published=True, deadline__gte=today)
        .exclude(pk__in=tracked_ids)
        .select_related("category")
    )

    if not past:
        return [
            (opportunity, 0, [_deadline_text((opportunity.deadline - today).days)])
            for opportunity in candidates.order_by("deadline", "pk")[:limit]
        ]

    category_ids = {opportunity.category_id for opportunity in past}
    eligibility_counts = Counter(
        (opportunity.eligibility or "").strip()
        for opportunity in past
        if (opportunity.eligibility or "").strip().lower() != "all"
    )
    preferred_eligibility = (
        eligibility_counts.most_common(1)[0][0] if eligibility_counts else None
    )

    results = []
    for opportunity in candidates:
        score, reasons = score_opportunity(
            opportunity, category_ids, preferred_eligibility, today
        )
        results.append(
            (opportunity, score, reasons or ["Currently open for applications"])
        )

    results.sort(key=lambda result: (-result[1], result[0].deadline, result[0].pk))
    return results[:limit]
