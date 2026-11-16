from django.urls import path

from . import views

app_name = "opportunities"

urlpatterns = [
    path("", views.OpportunityListView.as_view(), name="list"),
    path("bookmarks/", views.my_bookmarks, name="my_bookmarks"),
    path("recommended/", views.recommended, name="recommended"),
    path("analytics/", views.analytics, name="analytics"),
    path("tracker/", views.application_tracker, name="application_tracker"),
    path("applications/<int:pk>/edit/", views.application_update, name="application_update"),
    path("reminders/new/", views.set_reminder, name="set_reminder"),
    path("bookmark/<int:pk>/", views.toggle_bookmark, name="toggle_bookmark"),
    path("<int:pk>/", views.OpportunityDetailView.as_view(), name="detail"),
]
