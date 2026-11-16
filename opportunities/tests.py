from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Application, Bookmark, Category, Opportunity, Reminder

User = get_user_model()


class CampusOpportunityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="test-password-123")
        self.category = Category.objects.create(name="Internship")
        self.opportunity = Opportunity.objects.create(
            title="Software Intern",
            description="A software internship opportunity.",
            category=self.category,
            organization="Example Org",
            eligibility="Undergraduate students",
            deadline=timezone.localdate() + timedelta(days=20),
            link="https://example.com/apply",
            is_published=True,
        )

    def test_opportunity_list_shows_published_opportunities(self):
        response = self.client.get(reverse("opportunities:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Intern")

    def test_unpublished_opportunity_is_not_listed(self):
        self.opportunity.is_published = False
        self.opportunity.save()
        response = self.client.get(reverse("opportunities:list"))
        self.assertNotContains(response, "Software Intern")

    def test_bookmark_requires_login(self):
        response = self.client.post(reverse("opportunities:toggle_bookmark", args=[self.opportunity.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_student_can_add_and_remove_bookmark(self):
        self.client.login(username="student", password="test-password-123")
        url = reverse("opportunities:toggle_bookmark", args=[self.opportunity.pk])
        self.client.post(url)
        self.assertTrue(Bookmark.objects.filter(user=self.user, opportunity=self.opportunity).exists())
        self.client.post(url)
        self.assertFalse(Bookmark.objects.filter(user=self.user, opportunity=self.opportunity).exists())

    def test_my_bookmarks_only_shows_current_users_bookmarks(self):
        Bookmark.objects.create(user=self.user, opportunity=self.opportunity)
        self.client.login(username="student", password="test-password-123")
        response = self.client.get(reverse("opportunities:my_bookmarks"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Intern")

    def test_student_can_add_application_to_tracker(self):
        self.client.login(username="student", password="test-password-123")
        response = self.client.post(reverse("opportunities:application_tracker"), {
            "opportunity": self.opportunity.pk,
            "status": Application.Status.APPLIED,
            "notes": "Applied through the company website.",
        })
        self.assertRedirects(response, reverse("opportunities:application_tracker"))
        application = Application.objects.get(user=self.user, opportunity=self.opportunity)
        self.assertEqual(application.status, Application.Status.APPLIED)
        self.assertEqual(application.applied_on, timezone.localdate())

    def test_student_cannot_edit_another_users_application(self):
        other_user = User.objects.create_user(username="other", password="test-password-123")
        application = Application.objects.create(user=other_user, opportunity=self.opportunity)
        self.client.login(username="student", password="test-password-123")
        response = self.client.get(reverse("opportunities:application_update", args=[application.pk]))
        self.assertEqual(response.status_code, 404)

    def test_student_can_create_future_reminder(self):
        self.client.login(username="student", password="test-password-123")
        remind_on = timezone.localdate() + timedelta(days=2)
        response = self.client.post(reverse("opportunities:set_reminder"), {
            "opportunity": self.opportunity.pk,
            "remind_on": remind_on.isoformat(),
        })
        self.assertRedirects(response, reverse("opportunities:application_tracker"))
        self.assertTrue(Reminder.objects.filter(user=self.user, opportunity=self.opportunity, remind_on=remind_on).exists())

    def test_reminder_cannot_be_after_deadline(self):
        self.client.login(username="student", password="test-password-123")
        response = self.client.post(reverse("opportunities:set_reminder"), {
            "opportunity": self.opportunity.pk,
            "remind_on": (self.opportunity.deadline + timedelta(days=1)).isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reminder.objects.count(), 0)


class RegistrationEmailTests(TestCase):
    def test_registration_form_requires_email(self):
        from opportunities.forms import RegisterForm

        form = RegisterForm(data={
            "username": "studentemail",
            "email": "",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_registration_form_accepts_email(self):
        from opportunities.forms import RegisterForm

        form = RegisterForm(data={
            "username": "studentemail",
            "email": "student@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertTrue(form.is_valid(), form.errors)
