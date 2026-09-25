from django.contrib import admin

from .models import ClassificationRule, CodeMapping, Garment, GarmentFibre, TariffLine

TRACEABILITY_FIELDSET = (
    "Fiabilité des données",
    {"fields": ("confidence", "source", "last_verified", "next_review", "validated_by_expert", "notes")},
)


@admin.register(TariffLine)
class TariffLineAdmin(admin.ModelAdmin):
    list_display = (
        "jurisdiction", "code", "short_description", "duty_display",
        "condition_display", "confidence", "validated_by_expert", "last_verified",
    )
    list_filter = ("jurisdiction", "confidence", "validated_by_expert")
    search_fields = ("code", "description", "notes")
    readonly_fields = ("hs6",)
    fieldsets = (
        ("Ligne", {"fields": ("jurisdiction", "code", "hs6", "description")}),
        ("Droits de douane", {"fields": ("ad_valorem_rate", "specific_duty")}),
        (
            "Condition de composition (optionnel)",
            {
                "fields": ("condition_group", "condition_fibre", "condition_min_pct"),
                "description": "Pour les lignes du type « contenant 36 % ou plus de lin ».",
            },
        ),
        TRACEABILITY_FIELDSET,
    )

    @admin.display(description="Description")
    def short_description(self, obj):
        return obj.description if len(obj.description) <= 70 else obj.description[:67] + "…"


@admin.register(CodeMapping)
class CodeMappingAdmin(admin.ModelAdmin):
    list_display = ("from_line", "to_line", "confidence", "validated_by_expert")
    list_filter = ("confidence", "validated_by_expert")
    autocomplete_fields = ("from_line", "to_line")
    fieldsets = (
        ("Correspondance", {"fields": ("from_line", "to_line", "condition_note")}),
        TRACEABILITY_FIELDSET,
    )


@admin.register(ClassificationRule)
class ClassificationRuleAdmin(admin.ModelAdmin):
    list_display = ("garment_type", "fibre_group", "hs6", "confidence", "validated_by_expert")
    list_filter = ("garment_type", "confidence", "validated_by_expert")
    search_fields = ("garment_type", "hs6")
    fieldsets = (
        ("Règle", {"fields": ("garment_type", "fibre_group", "hs6")}),
        TRACEABILITY_FIELDSET,
    )


class GarmentFibreInline(admin.TabularInline):
    model = GarmentFibre
    extra = 3


@admin.register(Garment)
class GarmentAdmin(admin.ModelAdmin):
    list_display = ("name", "reference", "garment_type", "composition_display", "origin_country", "created_at")
    list_filter = ("garment_type", "origin_country")
    search_fields = ("name", "reference")
    inlines = [GarmentFibreInline]
