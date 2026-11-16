from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Application, Bookmark, Category, Opportunity
from .recommend import recommend_for, score_opportunity


class RecommendationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="rohit", password="pass12345"
        )
        self.today = date.today()
        self.hack = Category.objects.create(name="Hackathon")
        self.intern = Category.objects.create(name="Internship")

    def make(self, title, category=None, days=30, eligibility="all", published=True):
        return Opportunity.objects.create(
            title=title,
            description=f"Description for {title}",
            category=category or self.hack,
            organization="Org",
            eligibility=eligibility,
            deadline=self.today + timedelta(days=days),
            link="https://example.com/apply",
            is_published=published,
        )

    def test_category_preference_raises_score(self):
        opportunity = self.make("Hack A", eligibility="3rd")
        with_preference, _ = score_opportunity(
            opportunity, {self.hack.pk}, None, self.today
        )
        without_preference, _ = score_opportunity(
            opportunity, set(), None, self.today
        )
        self.assertEqual(with_preference - without_preference, 3)

    def test_expired_opportunities_excluded(self):
        seen = self.make("Seen")
        Bookmark.objects.create(user=self.user, opportunity=seen)
        expired = self.make("Old", days=-2)
        titles = [opportunity.title for opportunity, _, _ in recommend_for(self.user, today=self.today)]
        self.assertNotIn(expired.title, titles)

    def test_bookmarked_and_applied_opportunities_are_excluded(self):
        bookmarked = self.make("Bookmarked")
        applied = self.make("Applied")
        other = self.make("Other", category=self.intern)
        Bookmark.objects.create(user=self.user, opportunity=bookmarked)
        Application.objects.create(
            user=self.user,
            opportunity=applied,
            status=Application.Status.APPLIED,
        )
        titles = [opportunity.title for opportunity, _, _ in recommend_for(self.user, today=self.today)]
        self.assertNotIn(bookmarked.title, titles)
        self.assertNotIn(applied.title, titles)
        self.assertIn(other.title, titles)

    def test_new_user_fallback_orders_by_soonest_deadline(self):
        self.make("Late", days=20)
        self.make("Soon", days=5)
        self.make("Mid", days=10)
        results = recommend_for(self.user, today=self.today)
        self.assertEqual(
            [opportunity.title for opportunity, _, _ in results],
            ["Soon", "Mid", "Late"],
        )
        self.assertTrue(all(score == 0 for _, score, _ in results))

    def test_recommendations_include_explanations_and_expected_score(self):
        seen = self.make("Seen", eligibility="3rd")
        Bookmark.objects.create(user=self.user, opportunity=seen)
        self.make("Next Hack", days=5, eligibility="all")
        opportunity, score, reasons = recommend_for(self.user, today=self.today)[0]
        reason_text = " ".join(reasons)
        self.assertEqual(opportunity.title, "Next Hack")
        self.assertIn("other Hackathon listings", reason_text)
        self.assertIn("Open to all students", reason_text)
        self.assertIn("Closes in 5 days", reason_text)
        self.assertEqual(score, 6)

    def test_unpublished_opportunities_are_excluded(self):
        seen = self.make("Seen")
        Bookmark.objects.create(user=self.user, opportunity=seen)
        unpublished = self.make("Unpublished", published=False)
        results = recommend_for(self.user, today=self.today)
        self.assertNotIn(unpublished, [opportunity for opportunity, _, _ in results])

    def test_recommendations_page_requires_login(self):
        response = self.client.get(reverse("opportunities:recommended"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_view_recommendations(self):
        self.client.login(username="rohit", password="pass12345")
        self.make("Upcoming", days=4)
        response = self.client.get(reverse("opportunities:recommended"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommended for you")
        self.assertContains(response, "Upcoming")
