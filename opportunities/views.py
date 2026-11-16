from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
class StyledUserCreationForm(UserCreationForm):
    """UserCreationForm with Bootstrap classes on every input."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

def register(request):
    """Register a new student account and log them in."""
    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login after sign-up
            return redirect("home")
    else:
        form = StyledUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def home(request):
    """Temporary landing page; replace with the opportunity list later."""
    return render(request, "home.html")