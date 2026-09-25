from django.db import models


class TariffCategory(models.Model):
    """
    La matrice tarifaire - le coeur du produit.
    Une ligne = une categorie de produit avec ses taux de droits de douane.
    Gerée via l'admin Django (pas de front a construire pour ca).
    """

    class Confidence(models.TextChoices):
        VALIDATED = "valide_expert", "Valide par l'experte"
        TO_CHECK = "a_verifier", "A verifier"
        DRAFT = "brouillon", "Brouillon - a confirmer"
        LOW_CONFIDENCE = "faible_confiance", "Brouillon - faible confiance"

    name = models.CharField(
        "Categorie", max_length=200,
        help_text="Ex: Electronique grand public - Enceinte Bluetooth",
    )
    hs_code = models.CharField("Code HS", max_length=20, blank=True)
    origin_country = models.CharField("Pays d'origine", max_length=100, default="Chine")

    mfn_base_rate = models.DecimalField(
        "Taux MFN de base", max_digits=6, decimal_places=4, default=0,
        help_text="Fraction, ex: 0.045 pour 4.5%",
    )
    section_301_rate = models.DecimalField(
        "Taux Section 301", max_digits=6, decimal_places=4, default=0,
        help_text="Fraction, ex: 0.075 pour 7.5%",
    )
    additional_surtax_rate = models.DecimalField(
        "Surtaxe additionnelle", max_digits=6, decimal_places=4, default=0,
        help_text="Ex: surtaxe 'forced labor' en vigueur depuis le 24/07/2026 (~0.125). A revalider regulierement.",
    )

    confidence = models.CharField(
        "Niveau de confiance", max_length=30,
        choices=Confidence.choices, default=Confidence.DRAFT,
    )
    notes = models.TextField("Pieges / notes pratiques", blank=True)
    source = models.CharField("Source", max_length=300, blank=True)

    last_verified = models.DateField("Derniere verification", null=True, blank=True)
    next_review = models.DateField("Prochaine revision", null=True, blank=True)
    validated_by_expert = models.BooleanField("Valide par l'experte", default=False)
    expert_comments = models.TextField("Commentaires de l'experte", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categorie tarifaire"
        verbose_name_plural = "Matrice tarifaire"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.origin_country})"

    @property
    def total_effective_rate(self):
        """Taux total de droits applicable a cette categorie."""
        return self.mfn_base_rate + self.section_301_rate + self.additional_surtax_rate

    @property
    def total_effective_rate_display(self):
        return f"{(self.total_effective_rate * 100).normalize():f}".replace(".", ",") + " %"


class Calculation(models.Model):
    """
    Un calcul de landed cost sauvegarde, base sur une categorie de la matrice.
    """

    category = models.ForeignKey(
        TariffCategory, on_delete=models.PROTECT, related_name="calculations",
        verbose_name="Categorie tarifaire",
    )
    product_name = models.CharField("Nom du produit", max_length=200, blank=True)

    fob_unit_price = models.DecimalField("Prix fournisseur (FOB) / unite", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Quantite")
    freight_cost_total = models.DecimalField("Cout freight total", max_digits=10, decimal_places=2, default=0)

    amazon_referral_pct = models.DecimalField(
        "Commission Amazon (referral)", max_digits=6, decimal_places=4, default=0.15,
        help_text="Fraction, ex: 0.15 pour 15%",
    )
    amazon_fba_fee_per_unit = models.DecimalField(
        "Frais FBA / unite", max_digits=10, decimal_places=2, default=0,
    )
    target_sale_price = models.DecimalField(
        "Prix de vente cible / unite", max_digits=10, decimal_places=2, null=True, blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Calcul"
        verbose_name_plural = "Historique des calculs"
        ordering = ["-created_at"]

    def __str__(self):
        label = self.product_name or self.category.name
        return f"{label} - {self.created_at:%d/%m/%Y}"

    # --- Calculs derives : le moteur de calcul du landed cost ---

    @property
    def product_cost_total(self):
        return self.fob_unit_price * self.quantity

    @property
    def duty_amount(self):
        return self.product_cost_total * self.category.total_effective_rate

    @property
    def landed_cost_total(self):
        return self.product_cost_total + self.freight_cost_total + self.duty_amount

    @property
    def landed_cost_per_unit(self):
        if not self.quantity:
            return 0
        return self.landed_cost_total / self.quantity

    @property
    def breakeven_price(self):
        """Prix de vente minimum pour ne pas perdre d'argent (couvre landed cost + frais FBA + commission)."""
        denominator = 1 - self.amazon_referral_pct
        if denominator <= 0:
            return None
        return (self.landed_cost_per_unit + self.amazon_fba_fee_per_unit) / denominator

    @property
    def margin_per_unit(self):
        if self.target_sale_price is None:
            return None
        referral_fee = self.target_sale_price * self.amazon_referral_pct
        return self.target_sale_price - self.landed_cost_per_unit - self.amazon_fba_fee_per_unit - referral_fee

    @property
    def roi_pct(self):
        margin = self.margin_per_unit
        cost = self.landed_cost_per_unit
        if margin is None or not cost:
            return None
        return (margin / cost) * 100
