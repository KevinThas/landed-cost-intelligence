from decimal import Decimal

from django import forms
from django.db import transaction

from .classification import LINE_KO, LINE_OK
from .costing import DESTINATIONS
from .fibres import composition_total_error, parse_composition
from .models import ACCESSORY_CHOICES, ClassificationRule, Garment, GarmentFibre, GarmentQuote, TariffLine


def _percent_field(label, required=False, help_text="", initial=None):
    return forms.DecimalField(
        label=label, required=required, min_value=0, max_value=100, max_digits=5, decimal_places=2,
        help_text=help_text, initial=initial,
    )


def _amount_field(label, required=True, min_value=0, initial=None, help_text=""):
    return forms.DecimalField(
        label=label, required=required, min_value=min_value, max_digits=12, decimal_places=2,
        initial=initial, help_text=help_text,
    )


class QuoteForm(forms.Form):
    tariff_line = forms.ModelChoiceField(
        label="Ligne tarifaire", queryset=TariffLine.objects.none(), required=False,
        empty_label="Aucune : je saisis le taux moi-même",
    )
    duty_rate_pct = _percent_field(
        "Taux de droits (%)", help_text="Laissez vide pour reprendre le droit de la ligne choisie.",
    )
    all_in_minimum_pct = _percent_field(
        "Droit total minimum « tout compris » (%)",
        help_text=(
            "Facultatif. Si renseigné, le droit retenu est le plus élevé entre la ligne et ce minimum "
            "(ex. la règle des 15 % « tout compris » appliquée en 2025 aux produits européens vers les "
            "États-Unis). Règle à vérifier avant usage : elle peut avoir changé."
        ),
    )
    vat_pct = _percent_field("TVA à l'import (%)", required=True)
    quantity = forms.IntegerField(label="Quantité (pièces)", min_value=1)
    unit_price = _amount_field("Prix unitaire d'achat, hors taxes (€)", min_value=Decimal("0.01"))
    freight_total = _amount_field(
        "Transport international + assurance, total (€)", required=False, initial=0,
        help_text="Frais du trajet complet jusqu'au port ou à l'aéroport d'arrivée.",
    )
    other_costs_total = _amount_field(
        "Autres frais, total (€)", required=False, initial=0,
        help_text="Courtier, manutention, frais de dossier, taxe de dédouanement américaine (MPF/HMF)…",
    )

    def __init__(self, *args, destination, matches, **kwargs):
        super().__init__(*args, **kwargs)
        self.destination = destination
        self.matches = {match.line.pk: match for match in matches}
        line_field = self.fields["tariff_line"]
        line_field.queryset = TariffLine.objects.filter(pk__in=self.matches)
        line_field.label_from_instance = self._line_label
        default_vat = DESTINATIONS[destination].default_vat_rate * 100
        self.fields["vat_pct"].initial = default_vat.normalize()
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

    def _line_label(self, line):
        status = self.matches[line.pk].status
        suffix = {LINE_OK: " — condition de fibre remplie", LINE_KO: " — condition de fibre non remplie"}.get(status, "")
        description = line.description if len(line.description) <= 80 else line.description[:77] + "…"
        return f"{line.code} · {line.duty_display} · {description}{suffix}"

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        line = cleaned.get("tariff_line")
        rate_pct = cleaned.get("duty_rate_pct")
        if rate_pct is not None:
            cleaned["duty_rate"] = (rate_pct / 100).quantize(Decimal("0.0001"))
        elif line is None:
            self.add_error("duty_rate_pct", "Choisissez une ligne tarifaire ou saisissez le taux de droits.")
        elif line.ad_valorem_rate is None:
            self.add_error("duty_rate_pct", "Cette ligne n'a pas de droit ad valorem renseigné : saisissez le taux.")
        else:
            cleaned["duty_rate"] = line.ad_valorem_rate
        return cleaned

    def save(self, garment):
        data = self.cleaned_data
        minimum = data.get("all_in_minimum_pct")
        return GarmentQuote.objects.create(
            garment=garment,
            destination=self.destination,
            tariff_line=data.get("tariff_line"),
            duty_rate=data["duty_rate"],
            all_in_minimum_rate=None if minimum is None else (minimum / 100).quantize(Decimal("0.0001")),
            vat_rate=(data["vat_pct"] / 100).quantize(Decimal("0.0001")),
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            freight_total=data.get("freight_total") or Decimal(0),
            other_costs_total=data.get("other_costs_total") or Decimal(0),
        )


MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class ImportForm(forms.Form):
    file = forms.FileField(
        label="Classeur Excel (.xlsx)",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".xlsx"}),
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Envoyez un fichier Excel au format .xlsx.")
        if uploaded.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError("Fichier trop volumineux (5 Mo maximum).")
        return uploaded


class GarmentForm(forms.ModelForm):
    garment_type = forms.ChoiceField(label="Type de vêtement")
    composition = forms.CharField(
        label="Composition du tissu principal",
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "60% coton, 30% soie, 10% viscose"}),
        help_text=(
            "Comme sur l'étiquette. Le total doit faire 100 %. Les boutons, zips et autres "
            "accessoires ne se comptent pas ici : cochez-les plus bas."
        ),
    )
    accessory_materials = forms.MultipleChoiceField(
        label="Accessoires non textiles (boutons, zip, patch…)",
        choices=ACCESSORY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Garment
        fields = ["name", "reference", "garment_type", "origin_country", "composition", "accessory_materials", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        types = ClassificationRule.objects.order_by("garment_type").values_list("garment_type", flat=True).distinct()
        self.fields["garment_type"].choices = [("", "---------")] + [(t, t) for t in types]
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs["class"] = "form-check-input"
            else:
                widget.attrs["class"] = "form-control"

    def clean_composition(self):
        try:
            fibres = parse_composition(self.cleaned_data["composition"])
        except ValueError as error:
            raise forms.ValidationError(str(error))
        error = composition_total_error(fibres)
        if error:
            raise forms.ValidationError(error)
        self.fibres = fibres
        return self.cleaned_data["composition"]

    def save(self, commit=True):
        garment = super().save(commit=False)
        garment.accessory_materials = self.cleaned_data["accessory_materials"]
        if commit:
            with transaction.atomic():
                garment.save()
                GarmentFibre.objects.bulk_create(
                    GarmentFibre(garment=garment, fibre=code, percent=percent) for code, percent in self.fibres
                )
        return garment
