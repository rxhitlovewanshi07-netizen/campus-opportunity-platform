from django.conf import settings
from django.db import models


class Category(models.Model):
    """Type of opportunity, e.g. Internship, Hackathon, Research."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Opportunity(models.Model):
    """A single opportunity published by an admin."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="opportunities"
    )
    organization = models.CharField(max_length=200)
    eligibility = models.TextField(blank=True)
    deadline = models.DateField(db_index=True)  # indexed for deadline filtering
    link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)  # only published ones are shown to students

    class Meta:
        verbose_name_plural = "opportunities"
        ordering = ["deadline"]

    def __str__(self):
        return f"{self.title} ({self.organization})"


class Bookmark(models.Model):
    """A student's saved opportunity (one bookmark per user per opportunity)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks"
    )
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, related_name="bookmarks"
    )

    class Meta:
        unique_together = ("user", "opportunity")

    def __str__(self):
        return f"{self.user} -> {self.opportunity}"


class Application(models.Model):
    """Tracks a student's application progress for an opportunity."""

    class Status(models.TextChoices):
        SAVED = "saved", "Saved"
        APPLIED = "applied", "Applied"
        UNDER_REVIEW = "under_review", "Under Review"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SAVED
    )
    applied_on = models.DateField(null=True, blank=True)  # set when status becomes Applied
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.opportunity} [{self.get_status_display()}]"


class Reminder(models.Model):
    """Deadline reminder for a student; 'sent' is flipped once it is delivered."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders"
    )
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, related_name="reminders"
    )
    remind_on = models.DateField()
    sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["remind_on"]

    def __str__(self):
        return f"Reminder for {self.user} on {self.remind_on}"