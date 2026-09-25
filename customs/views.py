from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .classification import classify
from .costing import DESTINATIONS, is_eu_origin
from .fibres import FIBRE_LABELS, GROUP_CHOICES
from .forms import GarmentForm, ImportForm, QuoteForm
from .importer import ImportFileError, build_template, import_workbook
from .models import ACCESSORY_CHOICES, ClassificationRule, Garment, GarmentQuote, TariffLine

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PAGE_SIZE = 25


def _paginate(request, queryset, extra=None):
    page = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))
    return page, urlencode({key: value for key, value in (extra or {}).items() if value})


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
        "quote_destinations": [(code.lower(), rules.label) for code, rules in DESTINATIONS.items()],
        "quotes": garment.quotes.all()[:10],
    })


def garment_list(request):
    query = request.GET.get("q", "").strip()
    garment_type = request.GET.get("type", "").strip()
    garments = Garment.objects.prefetch_related("fibres")
    if query:
        garments = garments.filter(Q(name__icontains=query) | Q(reference__icontains=query))
    if garment_type:
        garments = garments.filter(garment_type=garment_type)
    page, querystring = _paginate(request, garments, {"q": query, "type": garment_type})
    return render(request, "customs/garment_list.html", {
        "page": page,
        "query": query,
        "selected_type": garment_type,
        "types": sorted(set(Garment.objects.values_list("garment_type", flat=True))),
        "querystring": querystring,
    })


def quote_create(request, pk, destination):
    code = destination.upper()
    if code not in DESTINATIONS:
        raise Http404
    garment = get_object_or_404(Garment.objects.prefetch_related("fibres"), pk=pk)
    result = classify(garment.garment_type, garment.fibre_pairs(), garment.accessory_materials)
    form = QuoteForm(request.POST or None, destination=code, matches=result.lines.get(code, []))
    if request.method == "POST" and result.hs6 and form.is_valid():
        quote = form.save(garment)
        return redirect("quote_detail", pk=quote.pk)
    return render(request, "customs/quote_form.html", {
        "garment": garment,
        "form": form,
        "result": result,
        "rules": DESTINATIONS[code],
        "non_eu_origin": not is_eu_origin(garment.origin_country),
    })


def quote_detail(request, pk):
    quote = get_object_or_404(GarmentQuote.objects.select_related("garment", "tariff_line"), pk=pk)
    line = quote.tariff_line
    warnings = []
    if not is_eu_origin(quote.garment.origin_country):
        warnings.append(
            f"Ce vêtement est déclaré fabriqué en {quote.garment.origin_country} : les droits dépendent de "
            "l'origine réelle, pas du pays d'expédition. Ce calcul suppose une origine européenne."
        )
    if line is None:
        warnings.append("Taux saisi à la main : aucune ligne tarifaire n'est associée à ce devis.")
    else:
        if line.specific_duty:
            warnings.append(
                f"La ligne {line.code} comporte aussi un droit spécifique ({line.specific_duty}) qui n'est pas "
                "calculé ici : ajoutez son montant dans « Autres frais »."
            )
        if not line.validated_by_expert:
            warnings.append(
                f"La ligne {line.code} n'est pas validée par l'experte (confiance : "
                f"{line.get_confidence_display().lower()}) : traitez ce résultat comme une estimation."
            )
    return render(request, "customs/quote_detail.html", {
        "quote": quote,
        "breakdown": quote.breakdown,
        "rules": DESTINATIONS[quote.destination],
        "warnings": warnings,
    })


def quote_list(request):
    quotes = GarmentQuote.objects.select_related("garment")
    page, querystring = _paginate(request, quotes)
    return render(request, "customs/quote_list.html", {"page": page, "querystring": querystring})


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
