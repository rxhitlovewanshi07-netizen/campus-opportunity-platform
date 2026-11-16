from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from opportunities.models import Reminder


class Command(BaseCommand):
    help = "Send opportunity reminders scheduled for today."

    def handle(self, *args, **options):
        today = timezone.localdate()
        reminders = Reminder.objects.filter(remind_on__lte=today, sent=False).select_related("user", "opportunity")
        processed = 0
        skipped = 0

        for reminder in reminders:
            email = reminder.user.email
            if not email:
                self.stdout.write(self.style.WARNING(
                    f"Skipped reminder #{reminder.pk}: {reminder.user} has no email address."
                ))
                skipped += 1
                continue

            subject = f"Reminder: {reminder.opportunity.title} deadline"
            message = (
                f"Hello {reminder.user.get_username()},\n\n"
                f"This is your reminder about {reminder.opportunity.title} "
                f"({reminder.opportunity.organization}).\n"
                f"Application deadline: {reminder.opportunity.deadline:%d %b %Y}.\n"
                f"Opportunity link: {reminder.opportunity.link}\n"
            )
            sent_count = send_mail(subject, message, None, [email], fail_silently=False)
            if sent_count:
                reminder.sent = True
                reminder.save(update_fields=["sent"])
                processed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Reminder run complete. Sent: {processed}; skipped (no email): {skipped}."
        ))
