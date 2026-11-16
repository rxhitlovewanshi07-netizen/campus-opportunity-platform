from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from opportunities import views

urlpatterns = [
    path("admin/", admin.site.urls),  # admin dashboard
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    # Built-in auth views
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),  # POST only in Django 5
]