from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Application, Category, Opportunity
from .views import calc_outcome_rate

User = get_user_model()


class AnalyticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("student", password="pass12345")
        cls.staff = User.objects.create_user("staff", password="pass12345", is_staff=True)
        cls.url = reverse("opportunities:analytics")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse('login')}?next={self.url}", fetch_redirect_response=False
        )

    def test_normal_user_gets_403(self):
        self.client.login(username="student", password="pass12345")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_staff_gets_200_and_expected_template(self):
        self.client.login(username="staff", password="pass12345")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "opportunities/analytics.html")
        self.assertEqual(response.context["stats"]["users"], 2)

    def test_outcome_rate_calculation(self):
        category = Category.objects.create(name="Internship")
        opportunity = Opportunity.objects.create(
            title="Summer Intern",
            description="Internship",
            category=category,
            organization="Example Org",
            deadline=timezone.localdate() + timedelta(days=10),
            link="https://example.com",
            is_published=True,
        )
        for index, status in enumerate(["accepted", "accepted", "accepted", "rejected", "applied"]):
            applicant = User.objects.create_user(f"applicant{index}", password="pass12345")
            Application.objects.create(user=applicant, opportunity=opportunity, status=status)

        self.client.login(username="staff", password="pass12345")
        response = self.client.get(self.url)
        self.assertEqual(response.context["outcome_rate"], 75.0)
        self.assertEqual(calc_outcome_rate(1, 3), 25.0)
        self.assertIsNone(calc_outcome_rate(0, 0))
