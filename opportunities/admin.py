from django.contrib import admin

from .models import Application, Bookmark, Category, Opportunity, Reminder


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "category", "deadline", "is_published", "created_at")
    list_filter = ("category", "is_published", "deadline")
    search_fields = ("title", "organization", "description", "eligibility")
    list_editable = ("is_published",)  # quick publish/unpublish from the list page
    date_hierarchy = "deadline"


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "opportunity")
    list_filter = ("opportunity__category",)
    search_fields = ("user__username", "opportunity__title")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "opportunity", "status", "applied_on")
    list_filter = ("status", "applied_on")
    search_fields = ("user__username", "opportunity__title", "notes")


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("user", "opportunity", "remind_on", "sent")
    list_filter = ("sent", "remind_on")
    search_fields = ("user__username", "opportunity__title")