from decimal import Decimal
from functools import cached_property

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from calculator.models import TariffCategory

from . import costing
from .fibres import FIBRE_CHOICES, FIBRE_LABELS, GROUP_CHOICES

Confidence = TariffCategory.Confidence

ACCESSORY_CHOICES = [
    ("bois", "Bois"),
    ("metal", "Métal"),
    ("plastique", "Plastique"),
    ("cuir", "Cuir / peau"),
    ("corne_nacre", "Corne / nacre / os"),
    ("verre", "Verre"),
    ("autre", "Autre"),
]
ANIMAL_ACCESSORIES = {"cuir", "corne_nacre"}


def digits_only(value):
    return "".join(ch for ch in value if ch.isdigit())


def format_percent(rate):
    return f"{(rate * 100).normalize():f}".replace(".", ",") + " %"


class Verifiable(models.Model):
    """Traçabilité commune : d'où vient la donnée, quand elle a été vérifiée, par qui."""

    confidence = models.CharField(
        "Niveau de confiance", max_length=30,
        choices=Confidence.choices, default=Confidence.DRAFT,
    )
    source = models.CharField("Source", max_length=300, blank=True)
    last_verified = models.DateField("Dernière vérification", null=True, blank=True)
    next_review = models.DateField("Prochaine révision", null=True, blank=True)
    validated_by_expert = models.BooleanField("Validé par l'experte", default=False)
    notes = models.TextField("Notes / pièges pratiques", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TariffLine(Verifiable):
    """Une ligne du tarif douanier d'un pays (code national + droit de douane)."""

    class Jurisdiction(models.TextChoices):
        FR = "FR", "France / UE"
        US = "US", "États-Unis"
        CN = "CN", "Chine"

    jurisdiction = models.CharField("Pays / zone", max_length=2, choices=Jurisdiction.choices)
    code = models.CharField(
        "Code douanier", max_length=20,
        help_text="Tel que publié, ex : 6206.30.30 (USA) ou 6206 30 00 (UE).",
    )
    hs6 = models.CharField("Code HS (6 chiffres)", max_length=6, db_index=True, editable=False)
    description = models.TextField("Description")

    ad_valorem_rate = models.DecimalField(
        "Droit ad valorem", max_digits=6, decimal_places=4, null=True, blank=True,
        help_text="Fraction : 0.165 pour 16,5 %. 0 si « Free ». Vide si non renseigné.",
    )
    specific_duty = models.CharField(
        "Droit spécifique", max_length=80, blank=True,
        help_text="Ex : 49,6 ¢/kg. S'ajoute au droit ad valorem (droit composé).",
    )

    condition_group = models.CharField(
        "Condition : famille de fibres", max_length=20, choices=GROUP_CHOICES, blank=True,
    )
    condition_fibre = models.CharField(
        "Condition : fibre précise", max_length=20, choices=FIBRE_CHOICES, blank=True,
    )
    condition_min_pct = models.DecimalField(
        "Condition : seuil minimum (% en poids)", max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Ex : 36 pour « contenant 36 % ou plus de lin ».",
    )

    class Meta:
        verbose_name = "Ligne tarifaire"
        verbose_name_plural = "Lignes tarifaires"
        ordering = ["jurisdiction", "code"]
        constraints = [
            models.UniqueConstraint(fields=["jurisdiction", "code"], name="unique_line_per_jurisdiction"),
        ]

    def __str__(self):
        return f"{self.get_jurisdiction_display()} {self.code}"

    def clean(self):
        if len(digits_only(self.code)) < 6:
            raise ValidationError({"code": "Le code doit contenir au moins 6 chiffres."})
        if self.condition_group and self.condition_fibre:
            raise ValidationError("Choisissez une famille de fibres ou une fibre précise, pas les deux.")
        has_fibre = bool(self.condition_group or self.condition_fibre)
        if has_fibre != (self.condition_min_pct is not None):
            raise ValidationError("La fibre (ou famille) et le seuil en % vont ensemble : remplissez les deux.")

    def save(self, *args, **kwargs):
        self.hs6 = digits_only(self.code)[:6]
        super().save(*args, **kwargs)

    @property
    def duty_display(self):
        parts = []
        if self.specific_duty:
            parts.append(self.specific_duty)
        if self.ad_valorem_rate is not None:
            parts.append(format_percent(self.ad_valorem_rate))
        return " + ".join(parts) if parts else "—"

    @property
    def condition_display(self):
        if self.condition_min_pct is None:
            return ""
        target = FIBRE_LABELS.get(self.condition_fibre) or dict(GROUP_CHOICES).get(self.condition_group, "")
        return f"≥ {self.condition_min_pct.normalize():f} % de {target.lower()}"


class CodeMapping(Verifiable):
    """Correspondance validée entre deux lignes de pays différents (valable dans les deux sens)."""

    from_line = models.ForeignKey(TariffLine, on_delete=models.CASCADE, related_name="mappings_out")
    to_line = models.ForeignKey(TariffLine, on_delete=models.CASCADE, related_name="mappings_in")
    condition_note = models.TextField(
        "Critère de choix", blank=True,
        help_text="Ce qui départage cette ligne des autres (sexe, fibre, coupe...).",
    )

    class Meta:
        verbose_name = "Correspondance de codes"
        verbose_name_plural = "Correspondances de codes"
        constraints = [
            models.UniqueConstraint(fields=["from_line", "to_line"], name="unique_mapping_pair"),
        ]

    def __str__(self):
        return f"{self.from_line} ↔ {self.to_line}"

    def clean(self):
        if self.from_line_id and self.to_line_id and self.from_line.jurisdiction == self.to_line.jurisdiction:
            raise ValidationError("Une correspondance relie deux pays différents.")


class ClassificationRule(Verifiable):
    """Quel code HS (6 chiffres) pour un type de vêtement et une famille de fibres prédominante."""

    garment_type = models.CharField(
        "Type de vêtement", max_length=120,
        help_text="Ex : Chemisier, chemise femme/fille (tissé).",
    )
    fibre_group = models.CharField("Fibre prédominante", max_length=20, choices=GROUP_CHOICES)
    hs6 = models.CharField("Code HS (6 chiffres)", max_length=6)

    class Meta:
        verbose_name = "Règle de classement"
        verbose_name_plural = "Règles de classement"
        ordering = ["garment_type", "fibre_group"]
        constraints = [
            models.UniqueConstraint(fields=["garment_type", "fibre_group"], name="unique_rule_per_type_group"),
        ]

    def __str__(self):
        return f"{self.garment_type} / {self.get_fibre_group_display()} → {self.hs6}"

    def clean(self):
        if len(digits_only(self.hs6)) != 6:
            raise ValidationError({"hs6": "Le code HS comporte exactement 6 chiffres."})

    def save(self, *args, **kwargs):
        self.hs6 = digits_only(self.hs6)
        super().save(*args, **kwargs)


class Garment(models.Model):
    """Un vêtement saisi pour être classé (composition, accessoires, origine)."""

    reference = models.CharField("Référence / SKU", max_length=100, blank=True)
    name = models.CharField("Nom du vêtement", max_length=200)
    garment_type = models.CharField("Type de vêtement", max_length=120)
    origin_country = models.CharField(
        "Pays de fabrication", max_length=100, default="France",
        help_text="L'origine réelle compte pour les droits, pas le pays d'expédition.",
    )
    accessory_materials = models.JSONField("Accessoires non textiles", default=list, blank=True)
    notes = models.TextField("Notes", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vêtement"
        verbose_name_plural = "Vêtements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.reference})" if self.reference else self.name

    def fibre_pairs(self):
        return [(f.fibre, f.percent) for f in self.fibres.all()]

    @property
    def composition_display(self):
        return ", ".join(
            f"{f.percent.normalize():f} % {FIBRE_LABELS[f.fibre].lower()}" for f in self.fibres.all()
        )


class GarmentFibre(models.Model):
    """Une fibre du tissu principal et son poids en % (le total fait 100 %)."""

    garment = models.ForeignKey(Garment, on_delete=models.CASCADE, related_name="fibres")
    fibre = models.CharField("Fibre", max_length=20, choices=FIBRE_CHOICES)
    percent = models.DecimalField("% en poids", max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = "Fibre"
        verbose_name_plural = "Composition"
        ordering = ["-percent", "fibre"]
        constraints = [
            models.UniqueConstraint(fields=["garment", "fibre"], name="unique_fibre_per_garment"),
        ]

    def __str__(self):
        return f"{self.percent} % {self.get_fibre_display()}"


class GarmentQuote(models.Model):
    """Un calcul de coût d'arrivée (landed cost) d'un vêtement vers un pays destinataire."""

    class Destination(models.TextChoices):
        US = "US", "États-Unis"
        CN = "CN", "Chine"

    garment = models.ForeignKey(Garment, on_delete=models.CASCADE, related_name="quotes")
    destination = models.CharField("Pays destinataire", max_length=2, choices=Destination.choices)
    tariff_line = models.ForeignKey(
        TariffLine, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
        verbose_name="Ligne tarifaire utilisée",
    )
    duty_rate = models.DecimalField("Taux de droits", max_digits=6, decimal_places=4)
    all_in_minimum_rate = models.DecimalField(
        "Droit total minimum tout compris", max_digits=6, decimal_places=4, null=True, blank=True,
    )
    vat_rate = models.DecimalField("TVA à l'import", max_digits=6, decimal_places=4, default=0)

    quantity = models.PositiveIntegerField("Quantité", validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        "Prix unitaire d'achat", max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))],
    )
    freight_total = models.DecimalField(
        "Transport international + assurance", max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    other_costs_total = models.DecimalField(
        "Autres frais", max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Devis de coût d'arrivée"
        verbose_name_plural = "Devis de coût d'arrivée"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.garment} → {self.get_destination_display()} ({self.quantity} pièces)"

    @cached_property
    def breakdown(self):
        return costing.compute(
            self.destination, self.quantity, self.unit_price, self.freight_total, self.other_costs_total,
            self.duty_rate, self.all_in_minimum_rate, self.vat_rate,
        )
