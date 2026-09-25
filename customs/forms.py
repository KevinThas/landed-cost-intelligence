from decimal import Decimal

from django import forms
from django.db import transaction

from .fibres import parse_composition
from .models import ACCESSORY_CHOICES, ClassificationRule, Garment, GarmentFibre


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
        total = sum((percent for _, percent in fibres), Decimal(0))
        if abs(total - 100) > Decimal("0.01"):
            raise forms.ValidationError(
                f"Le total fait {total.normalize():f} % : il doit faire 100 %. "
                "Les accessoires (boutons, zip…) ne comptent pas dans ce total."
            )
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
