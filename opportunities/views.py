from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .forms import ApplicationForm, ApplicationUpdateForm, RegisterForm, ReminderForm
from .models import Application, Bookmark, Category, Opportunity, Reminder
from .recommend import recommend_for


class OpportunityListView(ListView):
    model = Opportunity
    template_name = "opportunities/opportunity_list.html"
    context_object_name = "opportunities"
    paginate_by = 9

    def get_queryset(self):
        qs = Opportunity.objects.filter(is_published=True).select_related("category").order_by("deadline")
        q = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        days = self.request.GET.get("days", "").strip()
        eligibility = self.request.GET.get("eligibility", "").strip()
        if q:
            qs = qs.filter(title__icontains=q)
        if category.isdigit():
            qs = qs.filter(category_id=int(category))
        if days.isdigit():
            today = timezone.localdate()
            qs = qs.filter(deadline__gte=today, deadline__lte=today + timedelta(days=int(days)))
        if eligibility:
            qs = qs.filter(eligibility__icontains=eligibility)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["filters"] = {key: self.request.GET.get(key, "") for key in ("q", "category", "days", "eligibility")}
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        if self.request.user.is_authenticated:
            bookmarked_ids = Bookmark.objects.filter(user=self.request.user).values_list("opportunity_id", flat=True)
            context["bookmarked_ids"] = set(bookmarked_ids)
        else:
            context["bookmarked_ids"] = set()
        return context


class OpportunityDetailView(DetailView):
    model = Opportunity
    template_name = "opportunities/opportunity_detail.html"
    context_object_name = "opportunity"

    def get_queryset(self):
        return Opportunity.objects.filter(is_published=True).select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["days_left"] = (self.object.deadline - timezone.localdate()).days
        context["is_bookmarked"] = self.request.user.is_authenticated and Bookmark.objects.filter(user=self.request.user, opportunity=self.object).exists()
        return context


@login_required
@require_POST
def toggle_bookmark(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, is_published=True)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, opportunity=opportunity)
    if not created:
        bookmark.delete()
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("opportunities:list")


@login_required
def my_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user, opportunity__is_published=True).select_related("opportunity", "opportunity__category").order_by("opportunity__deadline")
    return render(request, "opportunities/my_bookmarks.html", {"bookmarks": bookmarks})


@login_required
def application_tracker(request):
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            opportunity = form.cleaned_data["opportunity"]
            if Application.objects.filter(user=request.user, opportunity=opportunity).exists():
                messages.warning(request, "You are already tracking this opportunity. Use Edit to update its status.")
            else:
                application = form.save(commit=False)
                application.user = request.user
                if application.status == Application.Status.APPLIED and not application.applied_on:
                    application.applied_on = timezone.localdate()
                application.save()
                messages.success(request, "Opportunity added to your application tracker.")
                return redirect("opportunities:application_tracker")
    else:
        form = ApplicationForm()
    applications = Application.objects.filter(user=request.user).select_related("opportunity", "opportunity__category").order_by("-id")
    reminders = Reminder.objects.filter(user=request.user).select_related("opportunity").order_by("remind_on")
    return render(request, "opportunities/application_tracker.html", {"form": form, "applications": applications, "reminders": reminders})


@login_required
def application_update(request, pk):
    application = get_object_or_404(Application, pk=pk, user=request.user)
    if request.method == "POST":
        form = ApplicationUpdateForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            return redirect("opportunities:application_tracker")
    else:
        form = ApplicationUpdateForm(instance=application)
    return render(request, "opportunities/application_edit.html", {"form": form, "application": application})


@login_required
def set_reminder(request):
    if request.method == "POST":
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            reminder.save()
            return redirect("opportunities:application_tracker")
    else:
        form = ReminderForm()
    return render(request, "opportunities/set_reminder.html", {"form": form})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def dashboard(request):
    """Show a summary of the signed-in student's campus activity."""
    today = timezone.localdate()
    application_count = Application.objects.filter(user=request.user).count()
    bookmarks_count = Bookmark.objects.filter(user=request.user).count()
    reminders_count = Reminder.objects.filter(
        user=request.user, sent=False, remind_on__gte=today
    ).count()
    upcoming_opportunities = (
        Opportunity.objects.filter(is_published=True, deadline__gte=today)
        .select_related("category")
        .order_by("deadline")[:5]
    )
    recent_applications = (
        Application.objects.filter(user=request.user)
        .select_related("opportunity", "opportunity__category")
        .order_by("-id")[:5]
    )
    return render(
        request,
        "dashboard.html",
        {
            "application_count": application_count,
            "bookmarks_count": bookmarks_count,
            "reminders_count": reminders_count,
            "upcoming_opportunities": upcoming_opportunities,
            "recent_applications": recent_applications,
        },
    )


@login_required
def home(request):
    return redirect("opportunities:list")


@login_required
def recommended(request):
    recommendations = recommend_for(request.user, limit=6, today=timezone.localdate())
    bookmarked_ids = set(
        Bookmark.objects.filter(user=request.user).values_list("opportunity_id", flat=True)
    )
    return render(
        request,
        "opportunities/recommended.html",
        {
            "recommendations": recommendations,
            "bookmarked_ids": bookmarked_ids,
        },
    )


STATUS_LABELS = {
    "saved": "Saved",
    "applied": "Applied",
    "under_review": "Under review",
    "accepted": "Accepted",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
}


def calc_outcome_rate(accepted, rejected):
    """Return accepted / (accepted + rejected) as a percentage."""
    decided = accepted + rejected
    if decided == 0:
        return None
    return round(accepted / decided * 100, 1)


@login_required
def analytics(request):
    """Display platform-wide analytics to staff users only."""
    if not request.user.is_staff:
        raise PermissionDenied

    opportunity_totals = Opportunity.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(is_published=True)),
    )
    stats = {
        "total_opportunities": opportunity_totals["total"],
        "published": opportunity_totals["published"],
        "users": get_user_model().objects.count(),
        "applications": Application.objects.count(),
        "bookmarks": Bookmark.objects.count(),
    }

    category_rows = (
        Opportunity.objects.values("category__name")
        .annotate(n=Count("id"))
        .order_by("category__name")
    )
    status_counts = {
        row["status"]: row["n"]
        for row in Application.objects.values("status").annotate(n=Count("id"))
    }

    today = timezone.localdate()
    start = today - timedelta(days=29)
    daily_counts = {
        row["day"]: row["n"]
        for row in (
            Application.objects.filter(updated_at__date__gte=start)
            .annotate(day=TruncDate("updated_at"))
            .values("day")
            .annotate(n=Count("id"))
        )
    }
    days = [start + timedelta(days=i) for i in range(30)]

    top_bookmarked = (
        Bookmark.objects.values(
            "opportunity__id", "opportunity__title", "opportunity__category__name"
        )
        .annotate(n=Count("id"))
        .order_by("-n", "opportunity__title")[:5]
    )

    chart_data = {
        "categories": {
            "labels": [row["category__name"] or "Uncategorised" for row in category_rows],
            "values": [row["n"] for row in category_rows],
        },
        "status": {
            "labels": list(STATUS_LABELS.values()),
            "values": [status_counts.get(key, 0) for key in STATUS_LABELS],
        },
        "activity": {
            "labels": [day.strftime("%d %b") for day in days],
            "values": [daily_counts.get(day, 0) for day in days],
        },
    }

    return render(
        request,
        "opportunities/analytics.html",
        {
            "stats": stats,
            "outcome_rate": calc_outcome_rate(
                status_counts.get("accepted", 0), status_counts.get("rejected", 0)
            ),
            "top_bookmarked": top_bookmarked,
            "chart_data": chart_data,
        },
    )
