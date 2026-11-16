from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from opportunities.models import Category, Opportunity, Reminder


class SendReminderEmailTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.category = Category.objects.create(name="Internship")
        self.opp = Opportunity.objects.create(
            title="Google Summer Internship",
            description="A summer internship opportunity.",
            category=self.category,
            organization="Google",
            deadline=self.today + timedelta(days=5),
            link="https://example.com/apply",
            is_published=True,
        )

    def _reminder(self, user, opportunity=None, remind_on=None):
        return Reminder.objects.create(
            user=user,
            opportunity=opportunity or self.opp,
            remind_on=remind_on or self.today,
            sent=False,
        )

    def _run(self, *args):
        out = StringIO()
        call_command("send_reminders", *args, stdout=out)
        return out.getvalue()

    def test_email_sent_for_user_with_email(self):
        user = User.objects.create_user("asha", email="asha@example.com", password="x")
        reminder = self._reminder(user)

        output = self._run()

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["asha@example.com"])
        self.assertIn("Google Summer Internship", msg.subject)
        self.assertIn("https://example.com/apply", msg.body)
        reminder.refresh_from_db()
        self.assertTrue(reminder.sent)
        self.assertIn("1 reminder(s) processed", output)
        self.assertIn("1 email(s) sent", output)

    def test_no_email_user_is_processed_without_sending(self):
        user = User.objects.create_user("ravi", password="x")
        reminder = self._reminder(user)

        output = self._run()

        self.assertEqual(len(mail.outbox), 0)
        reminder.refresh_from_db()
        self.assertTrue(reminder.sent)
        self.assertIn("1 reminder(s) processed", output)
        self.assertIn("0 email(s) sent", output)
        self.assertIn("no email address", output)

    def test_reminder_not_marked_sent_when_sending_fails(self):
        user = User.objects.create_user("neha", email="neha@example.com", password="x")
        reminder = self._reminder(user)
        out = StringIO()
        err = StringIO()

        with patch(
            "opportunities.management.commands.send_reminders.send_mail",
            side_effect=Exception("SMTP down"),
        ):
            with self.assertRaises(CommandError):
                call_command("send_reminders", stdout=out, stderr=err)

        reminder.refresh_from_db()
        self.assertFalse(reminder.sent)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("[ERROR]", err.getvalue())
        self.assertIn("0 reminder(s) processed", out.getvalue())
        self.assertIn("1 failed", out.getvalue())

    def test_dry_run_does_not_send_or_change_database(self):
        user = User.objects.create_user("rohit", email="rohit@example.com", password="x")
        reminder = self._reminder(user)

        output = self._run("--dry-run")

        reminder.refresh_from_db()
        self.assertFalse(reminder.sent)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("[REMINDER] To rohit: 'Google Summer Internship'", output)
        self.assertIn("[DRY RUN]", output)
        self.assertIn("1 reminder(s) processed", output)

    def test_expired_deadline_marked_sent_without_email(self):
        user = User.objects.create_user("olduser", email="old@example.com", password="x")
        expired_opp = Opportunity.objects.create(
            title="Old Internship",
            description="Expired opportunity.",
            category=self.category,
            organization="Old Org",
            deadline=self.today - timedelta(days=2),
            link="https://example.com/old",
            is_published=True,
        )
        reminder = self._reminder(user, opportunity=expired_opp)

        output = self._run()

        reminder.refresh_from_db()
        self.assertTrue(reminder.sent)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("[SKIPPED]", output)
        self.assertNotIn("[REMINDER]", output)
        self.assertIn("1 expired", output)

    def test_deadline_today_is_still_open(self):
        user = User.objects.create_user("todayuser", email="today@example.com", password="x")
        today_opp = Opportunity.objects.create(
            title="Closes Today",
            description="Still open today.",
            category=self.category,
            organization="Today Org",
            deadline=self.today,
            link="https://example.com/today",
            is_published=True,
        )
        reminder = self._reminder(user, opportunity=today_opp)

        output = self._run()

        reminder.refresh_from_db()
        self.assertTrue(reminder.sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("1 sent", output)
        self.assertIn("0 expired", output)

    def test_future_reminder_is_not_processed(self):
        user = User.objects.create_user("futureuser", email="future@example.com", password="x")
        reminder = self._reminder(user, remind_on=self.today + timedelta(days=2))

        output = self._run()

        reminder.refresh_from_db()
        self.assertFalse(reminder.sent)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("0 reminder(s) processed", output)

    def test_summary_counts_open_and_expired_reminders(self):
        open_user = User.objects.create_user("openuser", email="open@example.com", password="x")
        expired_user = User.objects.create_user("expireduser", email="expired@example.com", password="x")
        self._reminder(open_user)
        expired_opp = Opportunity.objects.create(
            title="Expired Opportunity",
            description="Expired.",
            category=self.category,
            organization="Expired Org",
            deadline=self.today - timedelta(days=1),
            link="https://example.com/expired",
            is_published=True,
        )
        self._reminder(expired_user, opportunity=expired_opp)

        output = self._run()

        self.assertIn("2 reminder(s) processed", output)
        self.assertIn("1 sent", output)
        self.assertIn("1 expired", output)
        self.assertIn("0 failed", output)
