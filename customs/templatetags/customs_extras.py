from decimal import ROUND_HALF_UP, Decimal

from django import template

register = template.Library()


@register.filter
def pct(value):
    """0.154 -> « 15,4 % »."""
    if value is None or value == "":
        return "—"
    points = (Decimal(value) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP).normalize()
    return f"{points:f}".replace(".", ",") + " %"
