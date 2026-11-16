from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from opportunities.models import Reminder


class Command(BaseCommand):
    help = "Send due opportunity reminders by email and close expired reminders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen without sending email or changing the database.",
        )

    def _mark_sent(self, reminder):
        with transaction.atomic():
            reminder.sent = True
            reminder.save(update_fields=["sent"])

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        today = timezone.localdate()
        site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")

        due = (
            Reminder.objects.filter(sent=False, remind_on__lte=today)
            .select_related("user", "opportunity")
            .order_by("remind_on", "id")
        )

        sent = expired = failed = emails_sent = 0

        for reminder in due:
            user = reminder.user
            opp = reminder.opportunity

            try:
                if opp.deadline < today:
                    self.stdout.write(
                        f"[SKIPPED] To {user.get_username()}: "
                        f"'{opp.title}' closed on {opp.deadline} (deadline passed)."
                    )
                    if not dry_run:
                        self._mark_sent(reminder)
                    expired += 1
                    continue

                self.stdout.write(
                    f"[REMINDER] To {user.get_username()}: "
                    f"'{opp.title}' closes on {opp.deadline}."
                )

                if dry_run:
                    sent += 1
                    continue

                if user.email:
                    subject = f"Reminder: {opp.title} (deadline {opp.deadline})"
                    message = (
                        f"Hello {user.get_username()},\n\n"
                        "This is a reminder about the following opportunity:\n\n"
                        f"Title: {opp.title}\n"
                        f"Deadline: {opp.deadline}\n"
                        f"Details: {opp.link}\n\n"
                        f"Visit the portal: {site_url}\n\n"
                        "- Campus Portal"
                    )
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    emails_sent += 1
                else:
                    self.stdout.write(
                        f"[NOTICE] {user.get_username()} has no email address; "
                        "processing reminder without email."
                    )

                self._mark_sent(reminder)
                sent += 1

            except Exception as exc:  # continue processing other reminders
                failed += 1
                self.stderr.write(f"[ERROR] Reminder id={reminder.pk}: {exc}")

        processed = sent + expired
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            f"{prefix}{processed} reminder(s) processed "
            f"({sent} sent, {expired} expired, {failed} failed; "
            f"{emails_sent} email(s) sent)"
        )

        if failed:
            raise CommandError(f"{failed} reminder(s) failed; see errors above.")
