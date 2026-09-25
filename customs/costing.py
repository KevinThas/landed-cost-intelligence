from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .fibres import normalize_text

CENT = Decimal("0.01")

EU_ORIGINS = {
    normalize_text(name) for name in [
        "France", "Allemagne", "Italie", "Espagne", "Portugal", "Belgique", "Pays-Bas", "Luxembourg",
        "Irlande", "Grèce", "Autriche", "Pologne", "Roumanie", "Bulgarie", "Hongrie", "République tchèque",
        "Tchéquie", "Slovaquie", "Slovénie", "Croatie", "Danemark", "Suède", "Finlande", "Estonie",
        "Lettonie", "Lituanie", "Chypre", "Malte", "UE", "Union européenne",
    ]
}


def is_eu_origin(country):
    return normalize_text(country) in EU_ORIGINS


@dataclass(frozen=True)
class DestinationRules:
    label: str
    duty_base_includes_freight: bool
    default_vat_rate: Decimal
    basis_note: str


DESTINATIONS = {
    "US": DestinationRules(
        label="États-Unis",
        duty_base_includes_freight=False,
        default_vat_rate=Decimal("0"),
        basis_note=(
            "Aux États-Unis, les droits se calculent sur la valeur de la marchandise, hors transport "
            "international. Il n'y a pas de TVA fédérale à l'import."
        ),
    ),
    "CN": DestinationRules(
        label="Chine",
        duty_base_includes_freight=True,
        default_vat_rate=Decimal("0.13"),
        basis_note=(
            "En Chine, les droits se calculent sur la valeur CIF (marchandise + transport et assurance jusqu'au "
            "port chinois). La TVA à l'import (13 % à ma connaissance, à vérifier) s'applique sur cette base "
            "augmentée des droits."
        ),
    ),
}


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Breakdown:
    goods: Decimal
    freight: Decimal
    other_costs: Decimal
    duty_base: Decimal
    line_rate: Decimal
    effective_rate: Decimal
    minimum_applied: bool
    duty: Decimal
    landed_total: Decimal
    landed_per_unit: Decimal
    uplift: Decimal | None
    vat_base: Decimal
    vat: Decimal
    cash_needed: Decimal


def compute(destination, quantity, unit_price, freight_total, other_costs_total,
            duty_rate, all_in_minimum_rate, vat_rate):
    """Coût d'arrivée (landed cost) et TVA à l'import. Toutes les sommes dans la même devise."""
    rules = DESTINATIONS[destination]
    goods = money(unit_price * quantity)
    freight = money(freight_total)
    other = money(other_costs_total)

    duty_base = goods + freight if rules.duty_base_includes_freight else goods
    minimum_applied = all_in_minimum_rate is not None and all_in_minimum_rate > duty_rate
    effective_rate = all_in_minimum_rate if minimum_applied else duty_rate
    duty = money(duty_base * effective_rate)

    landed_total = goods + freight + other + duty
    vat_base = duty_base + duty
    vat = money(vat_base * vat_rate)
    return Breakdown(
        goods=goods, freight=freight, other_costs=other, duty_base=duty_base,
        line_rate=duty_rate, effective_rate=effective_rate, minimum_applied=minimum_applied,
        duty=duty, landed_total=landed_total, landed_per_unit=money(landed_total / quantity),
        uplift=(landed_total / goods - 1) if goods else None,
        vat_base=vat_base, vat=vat, cash_needed=landed_total + vat,
    )
