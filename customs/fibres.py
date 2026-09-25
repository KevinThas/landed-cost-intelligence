import re
import unicodedata
from decimal import Decimal

GROUP_SILK = "soie"
GROUP_WOOL = "laine"
GROUP_COTTON = "coton"
GROUP_OTHER_PLANT = "autres_vegetales"
GROUP_MANMADE = "fibres_chimiques"

# Ordre des chapitres 50 à 55 du système harmonisé : sert à départager une égalité de poids.
GROUP_ORDER = [GROUP_SILK, GROUP_WOOL, GROUP_COTTON, GROUP_OTHER_PLANT, GROUP_MANMADE]

GROUP_CHOICES = [
    (GROUP_SILK, "Soie"),
    (GROUP_WOOL, "Laine ou poils fins"),
    (GROUP_COTTON, "Coton"),
    (GROUP_OTHER_PLANT, "Autres fibres (lin, chanvre, ramie…)"),
    (GROUP_MANMADE, "Fibres synthétiques ou artificielles"),
]
GROUP_LABELS = dict(GROUP_CHOICES)

# (code, libellé, famille, synonymes acceptés à la saisie)
FIBRES = [
    ("coton", "Coton", GROUP_COTTON, ["cotton", "co", "cot"]),
    ("soie", "Soie", GROUP_SILK, ["silk", "se"]),
    ("laine", "Laine", GROUP_WOOL, ["wool", "wo", "laine vierge", "lambswool", "laine d'agneau"]),
    ("cachemire", "Cachemire", GROUP_WOOL, ["cashmere", "ws"]),
    ("alpaga", "Alpaga", GROUP_WOOL, ["alpaca", "wa"]),
    ("mohair", "Mohair", GROUP_WOOL, ["wm"]),
    ("angora", "Angora", GROUP_WOOL, ["wp"]),
    ("lin", "Lin", GROUP_OTHER_PLANT, ["linen", "flax", "li"]),
    ("chanvre", "Chanvre", GROUP_OTHER_PLANT, ["hemp", "ha"]),
    ("ramie", "Ramie", GROUP_OTHER_PLANT, ["ra"]),
    ("viscose", "Viscose", GROUP_MANMADE, ["rayonne", "rayon", "cv", "vi"]),
    ("modal", "Modal", GROUP_MANMADE, ["cmd"]),
    ("lyocell", "Lyocell", GROUP_MANMADE, ["tencel", "cly"]),
    ("acetate", "Acétate", GROUP_MANMADE, ["ace", "ac"]),
    ("cupro", "Cupro", GROUP_MANMADE, ["cup", "cu"]),
    ("polyester", "Polyester", GROUP_MANMADE, ["pes", "pl", "poly"]),
    ("polyamide", "Polyamide", GROUP_MANMADE, ["nylon", "pa", "pam"]),
    ("acrylique", "Acrylique", GROUP_MANMADE, ["acrylic", "pac"]),
    ("elasthanne", "Élasthanne", GROUP_MANMADE, ["elastane", "elasthane", "spandex", "lycra", "ea"]),
    ("polypropylene", "Polypropylène", GROUP_MANMADE, ["pp"]),
]

FIBRE_CHOICES = [(code, label) for code, label, _, _ in FIBRES]
FIBRE_LABELS = dict(FIBRE_CHOICES)
FIBRE_GROUP = {code: group for code, _, group, _ in FIBRES}


def normalize_text(value):
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


_SYNONYMS = {}
for _code, _label, _group, _aliases in FIBRES:
    for _name in [_code, _label, *_aliases]:
        _SYNONYMS[normalize_text(_name)] = _code

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
# Une virgule entre deux chiffres est décimale (62,5 %), sinon c'est un séparateur.
_SEPARATORS = re.compile(r"[;/+\n]+|,(?!\d)|(?<!\d),")


def resolve_fibre(name):
    return _SYNONYMS.get(normalize_text(name))


def parse_composition(text):
    """Transforme « 60% coton, 30% soie, 10% viscose » en [(code_fibre, pourcentage), ...]."""
    segments = [s for s in _SEPARATORS.split(text) if s.strip()]
    if not segments:
        raise ValueError("Saisissez au moins une fibre, par exemple : 60% coton, 40% polyester.")

    fibres = {}
    for segment in segments:
        numbers = _NUMBER.findall(segment)
        if len(numbers) != 1:
            raise ValueError(
                f"« {segment.strip()} » : indiquez un seul pourcentage par fibre, "
                "et séparez les fibres par une virgule."
            )
        percent = Decimal(numbers[0].replace(",", "."))
        name = _NUMBER.sub(" ", segment).replace("%", " ").strip()
        code = resolve_fibre(name)
        if code is None:
            raise ValueError(
                f"Fibre inconnue : « {name} ». Fibres reconnues : "
                + ", ".join(label.lower() for _, label in FIBRE_CHOICES) + "."
            )
        if not 0 < percent <= 100:
            raise ValueError(f"« {segment.strip()} » : le pourcentage doit être compris entre 0 et 100.")
        fibres[code] = fibres.get(code, Decimal(0)) + percent
    return list(fibres.items())
