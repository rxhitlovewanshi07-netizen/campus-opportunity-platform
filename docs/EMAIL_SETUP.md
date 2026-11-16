# Email reminder setup (Gmail SMTP)

The portal uses Django's console email backend by default. This prints reminder emails in the terminal and does not send real email. SMTP is selected automatically when both `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are set, unless `EMAIL_BACKEND` is explicitly configured.

## 1. Create a Gmail App Password

1. Open [Google Account Security](https://myaccount.google.com/security).
2. Enable 2-Step Verification.
3. Open [Google App Passwords](https://myaccount.google.com/apppasswords).
4. Create an app password (for example, name it `campus_portal`).
5. Copy the 16-character password. Use it without spaces.

Google may not offer App Passwords for some account types or security configurations.

## 2. Set environment variables on macOS / Linux

In the same terminal session used to run Django, enter:

```bash
export EMAIL_HOST_USER="yourname@gmail.com"
export EMAIL_HOST_PASSWORD="your-16-character-app-password"
export EMAIL_HOST="smtp.gmail.com"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export DEFAULT_FROM_EMAIL="yourname@gmail.com"
export SITE_URL="http://127.0.0.1:8000"
```

These exports apply to the current terminal session. To persist them, add the lines to `~/.zshrc` (zsh) or `~/.bashrc` (bash), then open a new terminal. Do not put real credentials in source files, README files, screenshots, or Git commits.

For Windows PowerShell, use `$env:EMAIL_HOST_USER = "yourname@gmail.com"` and `$env:EMAIL_HOST_PASSWORD = "your-app-password"` in the current session.

## 3. Run the reminder command

Activate the project's virtual environment, then run:

```bash
python manage.py send_reminders
```

Only reminders with `sent=False` and `remind_on` today or earlier are processed. Users with an email address receive an email. Users without an email address are reported in the terminal and their reminder is marked processed. If sending fails, the reminder remains unsent so it can be retried.

Without SMTP credentials, the console backend prints email contents to the terminal. This is useful for local development.

## 4. Test safely

Automated tests use Django's in-memory email backend and do not contact Gmail:

```bash
python manage.py test opportunities
```

To send a real test email, create a due reminder for a test user whose email address you control, then run the management command. Check Spam if the message does not appear.

## Troubleshooting

- `SMTPAuthenticationError`: verify that 2-Step Verification is enabled and the App Password is correct and entered without spaces.
- No email is sent: check that both `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are set in the same terminal that runs Django.
- The reminder is not processed: its date must be today or earlier, and `sent` must be `False`.
- To use a deployed site's URL in the message, set `SITE_URL` to that site's public base URL.
