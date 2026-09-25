from decimal import Decimal

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
            "fob_unit_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "freight_cost_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "amazon_referral_pct": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
            "amazon_fba_fee_per_unit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "target_sale_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
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

    def clean_fob_unit_price(self):
        value = self.cleaned_data["fob_unit_price"]
        if value <= 0:
            raise forms.ValidationError("Le prix fournisseur doit être supérieur à 0.")
        return value

    def clean_quantity(self):
        value = self.cleaned_data["quantity"]
        if value < 1:
            raise forms.ValidationError("La quantité doit être d'au moins 1.")
        return value

    def clean_freight_cost_total(self):
        value = self.cleaned_data["freight_cost_total"]
        if value < 0:
            raise forms.ValidationError("Le coût de freight ne peut pas être négatif.")
        return value

    def clean_amazon_fba_fee_per_unit(self):
        value = self.cleaned_data["amazon_fba_fee_per_unit"]
        if value < 0:
            raise forms.ValidationError("Les frais FBA ne peuvent pas être négatifs.")
        return value

    def clean_target_sale_price(self):
        value = self.cleaned_data["target_sale_price"]
        if value is not None and value <= 0:
            raise forms.ValidationError("Le prix de vente cible doit être supérieur à 0 (ou laissé vide).")
        return value

    def clean_amazon_referral_pct(self):
        value = self.cleaned_data["amazon_referral_pct"]
        if value >= 1:
            if value <= 100:
                suggestion = f"{(value / 100).normalize():f}".replace(".", ",")
                raise forms.ValidationError(
                    f"Vous avez saisi {value.normalize():f} : écrivez {suggestion} pour {value.normalize():f} %."
                )
            raise forms.ValidationError("La commission s'écrit sous forme de fraction : 0,15 pour 15 %.")
        if value < Decimal(0):
            raise forms.ValidationError("La commission ne peut pas être négative.")
        return value
