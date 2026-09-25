from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("connexion/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("vetements/", include("customs.urls")),
    path("", include("calculator.urls")),
]
