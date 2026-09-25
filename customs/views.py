from django.shortcuts import get_object_or_404, redirect, render

from .classification import classify
from .fibres import FIBRE_LABELS, GROUP_CHOICES
from .forms import GarmentForm
from .models import ACCESSORY_CHOICES, ClassificationRule, Garment, TariffLine


def garment_create(request):
    form = GarmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        garment = form.save()
        return redirect("garment_detail", pk=garment.pk)
    return render(request, "customs/garment_form.html", {
        "form": form,
        "has_rules": ClassificationRule.objects.exists(),
    })


def garment_detail(request, pk):
    garment = get_object_or_404(Garment.objects.prefetch_related("fibres"), pk=pk)
    result = classify(garment.garment_type, garment.fibre_pairs(), garment.accessory_materials)
    accessory_labels = dict(ACCESSORY_CHOICES)
    return render(request, "customs/garment_detail.html", {
        "garment": garment,
        "result": result,
        "fibres": [(FIBRE_LABELS[code], percent) for code, percent in garment.fibre_pairs()],
        "groups": sorted(
            ((label, result.totals[code], code == result.group) for code, label in GROUP_CHOICES if code in result.totals),
            key=lambda row: -row[1],
        ),
        "accessories": [accessory_labels[code] for code in garment.accessory_materials],
        "jurisdictions": TariffLine.Jurisdiction.choices,
    })


def garment_list(request):
    garments = Garment.objects.prefetch_related("fibres")
    return render(request, "customs/garment_list.html", {"garments": garments})
