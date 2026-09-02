from django.contrib import admin

from .models import Calculation, TariffCategory


@admin.register(TariffCategory)
class TariffCategoryAdmin(admin.ModelAdmin):
    """
    Interface d'administration de la matrice tarifaire.
    C'est ici que vous (et a terme votre femme) gerez les categories
    et leurs taux, sans avoir besoin d'ecran custom.
    """

    list_display = (
        "name", "hs_code", "origin_country",
        "mfn_base_rate", "section_301_rate", "additional_surtax_rate",
        "total_effective_rate_display", "confidence", "validated_by_expert",
        "last_verified",
    )
    list_filter = ("confidence", "validated_by_expert", "origin_country")
    search_fields = ("name", "hs_code", "notes")
    fieldsets = (
        ("Categorie", {
            "fields": ("name", "hs_code", "origin_country"),
        }),
        ("Taux de droits", {
            "fields": ("mfn_base_rate", "section_301_rate", "additional_surtax_rate"),
        }),
        ("Fiabilite des donnees", {
            "fields": (
                "confidence", "notes", "source",
                "last_verified", "next_review",
                "validated_by_expert", "expert_comments",
            ),
        }),
    )

    @admin.display(description="Taux total effectif")
    def total_effective_rate_display(self, obj):
        return f"{obj.total_effective_rate * 100:.1f}%"


@admin.register(Calculation)
class CalculationAdmin(admin.ModelAdmin):
    list_display = ("product_name", "category", "quantity", "created_at")
    list_filter = ("category",)
    search_fields = ("product_name",)
    readonly_fields = [f.name for f in Calculation._meta.fields]

    def has_add_permission(self, request):
        # L'ajout se fait via le formulaire public, pas depuis l'admin.
        return False
