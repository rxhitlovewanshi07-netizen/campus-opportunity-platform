# Platform Analytics

The staff-only analytics page summarizes total and published opportunities, users, applications, bookmarks, and the accepted-to-decided outcome rate. It visualizes opportunities by category, application statuses, and application updates over the last 30 days, and lists the five most-bookmarked opportunities.

Application update activity is tracked using the `Application.updated_at` timestamp. Apply the new migration before using the page:

```bash
python manage.py migrate
```

Only authenticated staff users can access analytics.
