from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Q

from .fibres import FIBRE_GROUP, GROUP_LABELS, GROUP_ORDER
from .models import ANIMAL_ACCESSORIES, ClassificationRule, CodeMapping, TariffLine

LINE_OK = "ok"
LINE_KO = "ko"
LINE_NONE = "none"


@dataclass
class LineMatch:
    line: TariffLine
    status: str


@dataclass
class Classification:
    totals: dict
    group: str | None
    tied_groups: list
    rule: ClassificationRule | None
    hs6: str
    lines: dict
    mappings: list
    warnings: list = field(default_factory=list)

    @property
    def group_label(self):
        return GROUP_LABELS.get(self.group, "")

    @property
    def hs6_display(self):
        return f"{self.hs6[:4]}.{self.hs6[4:]}" if self.hs6 else ""


def group_totals(fibres):
    totals = {}
    for code, percent in fibres:
        group = FIBRE_GROUP[code]
        totals[group] = totals.get(group, Decimal(0)) + percent
    return totals


def predominant_group(totals):
    """Famille de fibres la plus lourde ; en cas d'égalité, la dernière dans l'ordre de la nomenclature."""
    if not totals:
        return None, []
    top = max(totals.values())
    leaders = [group for group in GROUP_ORDER if totals.get(group) == top]
    return leaders[-1], leaders


def line_status(line, fibres):
    if line.condition_min_pct is None:
        return LINE_NONE
    if line.condition_fibre:
        share = sum((p for code, p in fibres if code == line.condition_fibre), Decimal(0))
    else:
        share = group_totals(fibres).get(line.condition_group, Decimal(0))
    return LINE_OK if share >= line.condition_min_pct else LINE_KO


def classify(garment_type, fibres, accessory_materials=()):
    totals = group_totals(fibres)
    group, tied = predominant_group(totals)
    warnings = []

    if len(tied) > 1:
        names = " et ".join(GROUP_LABELS[g].lower() for g in tied)
        warnings.append(
            f"Égalité de poids entre {names}. La règle retient la fibre placée en dernier "
            f"dans la nomenclature ({GROUP_LABELS[group].lower()}) : à faire valider."
        )

    rule = None
    if group:
        rule = ClassificationRule.objects.filter(garment_type=garment_type, fibre_group=group).first()
        if rule is None:
            warnings.append(
                f"Aucune règle de classement pour « {garment_type} » avec la fibre prédominante "
                f"« {GROUP_LABELS[group].lower()} ». Ajoutez-la dans l'admin (Règles de classement)."
            )

    hs6 = rule.hs6 if rule else ""
    lines = {code: [] for code, _ in TariffLine.Jurisdiction.choices}
    mappings = []
    if hs6:
        for line in TariffLine.objects.filter(hs6=hs6):
            lines[line.jurisdiction].append(LineMatch(line, line_status(line, fibres)))
        line_ids = [m.line.pk for matches in lines.values() for m in matches]
        mappings = list(
            CodeMapping.objects.filter(Q(from_line__in=line_ids) | Q(to_line__in=line_ids))
            .select_related("from_line", "to_line")
        )

    if ANIMAL_ACCESSORIES & set(accessory_materials):
        warnings.append(
            "Le vêtement comporte des parties non textiles d'origine animale (cuir, corne, nacre) : "
            "une mention d'étiquetage peut être obligatoire dans l'UE, et un accessoire important "
            "peut peser sur le classement. À vérifier."
        )

    return Classification(
        totals=totals, group=group, tied_groups=tied, rule=rule,
        hs6=hs6, lines=lines, mappings=mappings, warnings=warnings,
    )
