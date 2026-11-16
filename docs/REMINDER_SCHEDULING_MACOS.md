# Scheduling Campus Portal reminders on macOS

The Windows `.bat` file and Windows Task Scheduler instructions do not apply to this Mac. Use the included `run_reminders.sh` script and macOS `cron` instead.

## 1. Check the script

The script expects the project virtual environment at `venv/` inside the project directory. If your virtual environment is stored elsewhere, edit `VENV_PYTHON` in `run_reminders.sh` to its full Python path.

Make it executable (run from the project directory):

```bash
chmod +x run_reminders.sh
```

Run it once manually:

```bash
./run_reminders.sh
```

Check `reminders.log` in the project directory. The script records a timestamp, command output, and exit code.

## 2. Schedule it daily at 8:00 AM

Open the cron editor:

```bash
crontab -e
```

Add one line, replacing the path with the full path to your project directory:

```cron
0 8 * * * /bin/bash /Users/your-username/path/to/campus-opportunity-platform/run_reminders.sh
```

Save and exit. Cron uses the Mac's local time zone. The Mac must be awake and available at the scheduled time; missed runs are not automatically replayed by cron.

Check the installed schedule with:

```bash
crontab -l
```

## 3. Important email environment variables

Cron does not necessarily inherit variables exported in an interactive Terminal session. For scheduled email delivery, define `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and any other required settings in a secure environment-loading method available to the script, or configure them in the script's launch environment without committing secrets to Git. Never put an App Password in a tracked file.

## 4. Test safely

From the project directory, preview due reminders without sending emails or changing the database:

```bash
venv/bin/python manage.py send_reminders --dry-run
```

Then run normally when ready:

```bash
venv/bin/python manage.py send_reminders
```

A successful run reports sent, expired, failed, and email counts. Failed email reminders remain unsent so they can be retried on a later run.
