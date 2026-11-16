from django import forms
from django.utils import timezone

from .models import Application, Opportunity, Reminder


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            field.widget.attrs["class"] = css_class


class ApplicationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ("opportunity", "status", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["opportunity"].queryset = Opportunity.objects.filter(is_published=True).select_related("category")
        self.fields["opportunity"].label_from_instance = lambda obj: f"{obj.title} — {obj.organization}"
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == Application.Status.APPLIED and not self.instance.applied_on:
            self.instance.applied_on = timezone.localdate()
        return cleaned


class ApplicationUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ("status", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == Application.Status.APPLIED and not self.instance.applied_on:
            self.instance.applied_on = timezone.localdate()
        return cleaned


class ReminderForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ("opportunity", "remind_on")
        widgets = {"remind_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["opportunity"].queryset = Opportunity.objects.filter(is_published=True).select_related("category")
        self.fields["opportunity"].label_from_instance = lambda obj: f"{obj.title} — {obj.organization}"
        self.apply_bootstrap()

    def clean_remind_on(self):
        remind_on = self.cleaned_data["remind_on"]
        if remind_on < timezone.localdate():
            raise forms.ValidationError("Choose today or a future date.")
        return remind_on

    def clean(self):
        cleaned = super().clean()
        opportunity = cleaned.get("opportunity")
        remind_on = cleaned.get("remind_on")
        if opportunity and remind_on and remind_on > opportunity.deadline:
            self.add_error("remind_on", "Reminder date cannot be after the opportunity deadline.")
        return cleaned
