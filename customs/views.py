from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .classification import classify
from .fibres import FIBRE_LABELS, GROUP_CHOICES
from .forms import GarmentForm, ImportForm
from .importer import ImportFileError, build_template, import_workbook
from .models import ACCESSORY_CHOICES, ClassificationRule, Garment, TariffLine

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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


def garment_import(request):
    form = ImportForm(request.POST or None, request.FILES or None)
    reports = None
    if request.method == "POST" and form.is_valid():
        try:
            reports = import_workbook(form.cleaned_data["file"], allow_reference_data=request.user.is_staff)
        except ImportFileError as error:
            form.add_error("file", str(error))
    return render(request, "customs/garment_import.html", {
        "form": form,
        "reports": reports,
        "is_staff": request.user.is_staff,
    })


def garment_import_template(request):
    response = HttpResponse(build_template(), content_type=XLSX_TYPE)
    response["Content-Disposition"] = 'attachment; filename="modele_import_vetements.xlsx"'
    return response
