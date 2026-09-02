from django.shortcuts import redirect, render

from .forms import CalculationForm
from .models import Calculation


def calculate(request):
    """Formulaire de calcul du landed cost. Sauvegarde le calcul et affiche le resultat."""
    if request.method == "POST":
        form = CalculationForm(request.POST)
        if form.is_valid():
            calculation = form.save()
            return redirect("calculation_result", pk=calculation.pk)
    else:
        form = CalculationForm()

    return render(request, "calculator/calculate.html", {"form": form})


def calculation_result(request, pk):
    calculation = Calculation.objects.select_related("category").get(pk=pk)
    return render(request, "calculator/result.html", {"calculation": calculation})


def calculation_history(request):
    calculations = Calculation.objects.select_related("category").all()
    return render(request, "calculator/history.html", {"calculations": calculations})
