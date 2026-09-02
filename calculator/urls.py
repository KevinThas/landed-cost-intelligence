from django.urls import path

from . import views

urlpatterns = [
    path("", views.calculate, name="calculate"),
    path("resultat/<int:pk>/", views.calculation_result, name="calculation_result"),
    path("historique/", views.calculation_history, name="calculation_history"),
]
