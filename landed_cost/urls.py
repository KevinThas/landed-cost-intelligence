from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import deploy

urlpatterns = [
    path("hooks/deploy/", deploy.trigger, name="deploy_trigger"),
    path("hooks/deploy/status/", deploy.status, name="deploy_status"),
    path("admin/", admin.site.urls),
    path("connexion/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("vetements/", include("customs.urls")),
    path("", include("calculator.urls")),
]
