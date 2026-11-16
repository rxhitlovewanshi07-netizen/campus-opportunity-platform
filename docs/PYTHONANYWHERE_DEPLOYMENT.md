# PythonAnywhere deployment notes

## Current Beginner/free-plan constraints (checked 16 Nov 2026)

- One web app, one worker, one-month web-app expiry, two consoles, 512 MiB disk, and 100 CPU seconds/day. The CPU allowance applies to consoles and scheduled/always-on tasks, not web-app requests.
- New free accounts created on/after 15 Jan 2026 (8 Jan for EU accounts) do not include scheduled tasks or MySQL. Do not plan on a daily `send_reminders` task on a new free account.
- Free outbound internet is restricted to an HTTP(S) allowlist. Gmail SMTP on port 587 is not an HTTP(S) request and should be treated as unavailable unless the provider explicitly confirms support.
- Free accounts have no SSH access. Use the browser-based Bash console. The free hostname is `YOURUSERNAME.pythonanywhere.com`.
- Python versions depend on account system image; the current PythonAnywhere help page lists up to Python 3.13. Select a version offered in the account and use the same version for the web app and virtualenv.

Official references:
- https://help.pythonanywhere.com/pages/FreeAccountsFeatures/
- https://www.pythonanywhere.com/pricing/
- https://blog.pythonanywhere.com/221/
- https://help.pythonanywhere.com/pages/403ForbiddenError
- https://help.pythonanywhere.com/pages/PythonVersions

## Project setup changes

`settings.py` loads `.env` using `python-dotenv`, supports environment-driven `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS`, and defines `STATIC_ROOT`. `.env` is ignored by Git. Copy `.env.example` to `.env` for local testing and replace all placeholders. Never commit `.env`.

The project currently pins Django 6.1.3 and PythonAnywhere currently lists Python 3.13 as an available version. Use Python 3.13 if it is offered on the account and verify package installation before configuring the web app. Do not downgrade Django merely because an old guide says Django 5.x; downgrade only if the selected PythonAnywhere environment cannot install the current pinned Django version, then run the complete test suite against the downgraded version.

## Deploy outline

1. Create a Beginner account and confirm the email.
2. Open a browser Bash console; there is no SSH on the free plan.
3. Clone the public GitHub repository into `~/campus_portal`; check that `manage.py` is at that directory level.
4. Create a virtualenv using a Python version offered by the account (prefer 3.13 if available), then install `requirements.txt`.
5. Create `.env` from `.env.example`; set a fresh secret, `DJANGO_DEBUG=False`, the exact `YOURUSERNAME.pythonanywhere.com` host, and the HTTPS CSRF origin.
6. Run `python manage.py check --deploy`, `python manage.py migrate`, and `python manage.py collectstatic --noinput`; then create a superuser.
7. Add a Manual Configuration web app using the same Python version as the virtualenv. Configure source/working directory and virtualenv paths.
8. Edit the WSGI file to add `~/campus_portal` to `sys.path` and set `DJANGO_SETTINGS_MODULE` to `campus_portal.settings`.
9. Map `/static/` to `~/campus_portal/staticfiles`, enable Force HTTPS, and reload.
10. Test the homepage, login, admin, static CSS, recommendations, and analytics.

## Important project-specific notes

- This project does not currently contain a `seed_data` management command. Do not run `python manage.py seed_data`; create categories and opportunities through Django Admin after deployment, or add a separately tested idempotent seed command later.
- A new free account cannot schedule the daily reminder command. Run it manually in the Bash console when needed, or use a paid plan / external scheduler.
- Do not assume Gmail SMTP works from a free account. The free outbound allowlist is HTTP(S)-oriented. For testing, the Django console email backend prints messages to the console; it does not deliver email.
- SQLite is used by this project. Keep the database file on PythonAnywhere's persistent home filesystem and never commit it to Git. Back it up before migrations or deployment changes.
- The free web app expires after one month unless extended as prompted in the dashboard. Watch for renewal emails and use the Web tab's extension control.

## Updating the live site

After pushing tested changes from the local machine, use the Bash console:

```bash
cd ~/campus_portal
git pull
workon campusenv
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Then click **Reload** on the Web tab. Do not edit tracked code directly on the server; keep local Git as the source of truth.
