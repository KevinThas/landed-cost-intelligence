from django import forms

from .models import Calculation


class CalculationForm(forms.ModelForm):
    class Meta:
        model = Calculation
        fields = [
            "category",
            "product_name",
            "fob_unit_price",
            "quantity",
            "freight_cost_total",
            "amazon_referral_pct",
            "amazon_fba_fee_per_unit",
            "target_sale_price",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "product_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optionnel"}),
            "fob_unit_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "freight_cost_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "amazon_referral_pct": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "amazon_fba_fee_per_unit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "target_sale_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
        labels = {
            "category": "Categorie tarifaire",
            "product_name": "Nom du produit",
            "fob_unit_price": "Prix fournisseur (FOB) / unite ($)",
            "quantity": "Quantite",
            "freight_cost_total": "Cout freight total ($)",
            "amazon_referral_pct": "Commission Amazon referral (ex: 0.15 = 15%)",
            "amazon_fba_fee_per_unit": "Frais FBA / unite ($)",
            "target_sale_price": "Prix de vente cible / unite ($, optionnel)",
        }
