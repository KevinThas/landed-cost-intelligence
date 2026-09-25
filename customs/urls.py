from django.urls import path

from . import views

urlpatterns = [
    path("", views.garment_list, name="garment_list"),
    path("nouveau/", views.garment_create, name="garment_create"),
    path("<int:pk>/", views.garment_detail, name="garment_detail"),
]
