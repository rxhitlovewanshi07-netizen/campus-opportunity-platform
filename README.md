# Campus Opportunity Platform

A Django web application for students to discover campus opportunities, bookmark listings, track application progress, and schedule deadline reminders.

## Requirements

- Python 3.12 or later
- Django 6.1.3 (as pinned in `requirements.txt`)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Create a student account using **Register**. Staff can manage categories and opportunities at `/admin/`.

## Main features

- Browse published opportunities and filter by title, category, deadline, and eligibility.
- Bookmark and remove bookmarked opportunities.
- Track application status and notes.
- Set reminders for a date up to the opportunity deadline.
- Admin management for opportunities, categories, bookmarks, applications, and reminders.

## Processing reminders

Run the following command on the day reminders should be delivered:

```bash
python manage.py send_reminders
```

The default email backend is Django's console backend, so reminder messages are printed in the terminal during development. Configure a real email backend through environment variables before production use. The command marks a reminder as processed only after the email backend reports a successful send. Users need an email address on their account.

## Tests

```bash
python manage.py test opportunities
```

## Security notes

The included SQLite database is for local development only and should not be committed or published. `DJANGO_SECRET_KEY` should be set to a private, randomly generated value outside local development. Set `DEBUG=False`, configure `ALLOWED_HOSTS`, and configure real email delivery before deployment.
## Email reminders

Email reminders use the console backend by default. To enable Gmail SMTP, follow the setup instructions in [docs/EMAIL_SETUP.md](docs/EMAIL_SETUP.md). Keep SMTP credentials in environment variables; never commit them.
