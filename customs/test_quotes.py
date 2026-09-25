from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from . import costing
from .models import Garment, GarmentFibre, GarmentQuote, TariffLine
from .templatetags.customs_extras import pct

BLOUSE = "Chemisier, chemise femme/fille (tissé)"
D = Decimal


class CostingTests(SimpleTestCase):
    def test_us_duty_excludes_freight_and_there_is_no_vat(self):
        b = costing.compute("US", 100, D("50"), D("400"), D("100"), D("0.154"), None, D("0"))
        self.assertEqual((b.goods, b.duty_base, b.duty), (D("5000.00"), D("5000.00"), D("770.00")))
        self.assertEqual((b.landed_total, b.landed_per_unit), (D("6270.00"), D("62.70")))
        self.assertEqual((b.vat, b.cash_needed), (D("0.00"), D("6270.00")))

    def test_china_duty_is_on_cif_and_vat_on_base_plus_duty(self):
        b = costing.compute("CN", 100, D("50"), D("400"), D("100"), D("0.16"), None, D("0.13"))
        self.assertEqual((b.duty_base, b.duty), (D("5400.00"), D("864.00")))
        self.assertEqual((b.landed_total, b.landed_per_unit), (D("6364.00"), D("63.64")))
        self.assertEqual((b.vat_base, b.vat, b.cash_needed), (D("6264.00"), D("814.32"), D("7178.32")))
        self.assertEqual(round(b.uplift, 4), D("0.2728"))

    def test_all_in_minimum_only_applies_when_higher_than_the_line(self):
        low = costing.compute("US", 100, D("50"), D("0"), D("0"), D("0.035"), D("0.15"), D("0"))
        self.assertTrue(low.minimum_applied)
        self.assertEqual((low.effective_rate, low.duty), (D("0.15"), D("750.00")))
        high = costing.compute("US", 100, D("50"), D("0"), D("0"), D("0.154"), D("0.15"), D("0"))
        self.assertFalse(high.minimum_applied)
        self.assertEqual(high.duty, D("770.00"))

    def test_rounding_is_half_up_to_the_cent(self):
        b = costing.compute("US", 3, D("33.33"), D("0"), D("0"), D("0.165"), None, D("0"))
        self.assertEqual((b.goods, b.duty), (D("99.99"), D("16.50")))

    def test_european_origin_detection(self):
        for country in ["France", "  ITALIE ", "Union européenne", "pays-bas"]:
            self.assertTrue(costing.is_eu_origin(country), country)
        for country in ["Chine", "Maroc", "Turquie", "Royaume-Uni", ""]:
            self.assertFalse(costing.is_eu_origin(country), country)

    def test_percent_filter(self):
        self.assertEqual(pct(D("0.154")), "15,4 %")
        self.assertEqual(pct(D("6364") / D("5000") - 1), "27,28 %")
        self.assertEqual(pct(D("0")), "0 %")
        self.assertEqual(pct(D("1")), "100 %")
        self.assertEqual(pct(None), "—")


def make_garment(name="Chemisier test", garment_type=BLOUSE, fibre="coton", origin="France"):
    garment = Garment.objects.create(name=name, garment_type=garment_type, origin_country=origin)
    GarmentFibre.objects.create(garment=garment, fibre=fibre, percent=D("100"))
    return garment


class QuoteViewTests(TestCase):
    fixtures = ["customs_starter"]

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user("u", password="not-a-real-password"))
        self.garment = make_garment()

    def url(self, destination):
        return reverse("quote_create", args=[self.garment.pk, destination])

    def data(self, **overrides):
        data = {
            "tariff_line": "", "duty_rate_pct": "", "all_in_minimum_pct": "", "vat_pct": "0",
            "quantity": "100", "unit_price": "50", "freight_total": "400", "other_costs_total": "100",
        }
        data.update(overrides)
        return data

    def test_form_lists_the_lines_of_the_destination_only(self):
        page = self.client.get(self.url("us"))
        self.assertContains(page, "6206.30.30")
        self.assertContains(page, "hors transport international")
        china = self.client.get(self.url("cn"))
        self.assertNotContains(china, "6206.30.30")
        self.assertContains(china, "Aucune ligne tarifaire de Chine")
        self.assertContains(china, "valeur CIF")

    def test_us_quote_takes_the_rate_of_the_chosen_line(self):
        line = TariffLine.objects.get(code="6206.30.30")
        response = self.client.post(self.url("us"), self.data(tariff_line=line.pk))
        quote = GarmentQuote.objects.get()
        self.assertRedirects(response, reverse("quote_detail", args=[quote.pk]))
        self.assertEqual((quote.duty_rate, quote.tariff_line), (line.ad_valorem_rate, line))
        self.assertEqual(quote.breakdown.duty, D("770.00"))

        page = self.client.get(reverse("quote_detail", args=[quote.pk]))
        self.assertContains(page, "770,00 €")
        self.assertContains(page, "62,70 €")
        self.assertContains(page, "6206.30.30")
        self.assertContains(page, "traitez ce résultat comme une estimation")

    def test_china_quote_with_manual_rate_and_vat(self):
        self.client.post(self.url("cn"), self.data(duty_rate_pct="16", vat_pct="13"))
        quote = GarmentQuote.objects.get()
        self.assertEqual((quote.destination, quote.duty_rate, quote.vat_rate), ("CN", D("0.16"), D("0.13")))
        page = self.client.get(reverse("quote_detail", args=[quote.pk]))
        self.assertContains(page, "814,32 €")
        self.assertContains(page, "TVA à l'import")
        self.assertContains(page, "Taux saisi à la main")

    def test_manual_rate_overrides_the_line_and_minimum_is_explained(self):
        line = TariffLine.objects.get(code="6206.30.20")
        self.client.post(self.url("us"), self.data(tariff_line=line.pk, all_in_minimum_pct="15"))
        page = self.client.get(reverse("quote_detail", args=[GarmentQuote.objects.get().pk]))
        self.assertContains(page, "Minimum « tout compris » appliqué")

    def test_rate_is_required_when_no_line_is_chosen(self):
        response = self.client.post(self.url("us"), self.data())
        self.assertContains(response, "Choisissez une ligne tarifaire ou saisissez le taux")
        self.assertEqual(GarmentQuote.objects.count(), 0)

    def test_absurd_amounts_are_refused(self):
        for field, value in [("quantity", "0"), ("unit_price", "0"), ("unit_price", "-5"), ("freight_total", "-1"),
                             ("other_costs_total", "-1"), ("duty_rate_pct", "150"), ("vat_pct", "-1")]:
            self.client.post(self.url("us"), self.data(**{"duty_rate_pct": "10", field: value}))
            self.assertEqual(GarmentQuote.objects.count(), 0, f"{field}={value} aurait dû être refusé")

    def test_freight_and_other_costs_may_be_left_empty(self):
        self.client.post(self.url("us"), self.data(duty_rate_pct="10", freight_total="", other_costs_total=""))
        quote = GarmentQuote.objects.get()
        self.assertEqual((quote.freight_total, quote.other_costs_total), (0, 0))

    def test_non_european_origin_is_warned_everywhere(self):
        garment = make_garment(name="Chemisier chinois", origin="Chine")
        page = self.client.get(reverse("quote_create", args=[garment.pk, "us"]))
        self.assertContains(page, "fabriqué en Chine")
        self.client.post(reverse("quote_create", args=[garment.pk, "us"]), self.data(duty_rate_pct="10"))
        detail = self.client.get(reverse("quote_detail", args=[GarmentQuote.objects.get().pk]))
        self.assertContains(detail, "suppose une origine européenne")

    def test_specific_duty_is_flagged_not_silently_ignored(self):
        garment = make_garment(name="Polyester", fibre="polyester")
        line = TariffLine.objects.get(code="6206.40.25")
        self.client.post(reverse("quote_create", args=[garment.pk, "us"]), self.data(tariff_line=line.pk))
        detail = self.client.get(reverse("quote_detail", args=[GarmentQuote.objects.get().pk]))
        self.assertContains(detail, "droit spécifique")

    def test_garment_without_classification_rule_cannot_be_quoted(self):
        garment = make_garment(name="Manteau", garment_type="Manteau")
        url = reverse("quote_create", args=[garment.pk, "us"])
        self.assertContains(self.client.get(url), "pas de code harmonisé")
        self.client.post(url, self.data(duty_rate_pct="10"))
        self.assertEqual(GarmentQuote.objects.count(), 0)

    def test_unknown_destination_or_garment_is_404(self):
        self.assertEqual(self.client.get(self.url("jp")).status_code, 404)
        self.assertEqual(self.client.get(reverse("quote_create", args=[9999, "us"])).status_code, 404)
        self.assertEqual(self.client.get(reverse("quote_detail", args=[9999])).status_code, 404)

    def test_garment_page_offers_the_calculation_and_lists_previous_quotes(self):
        page = self.client.get(reverse("garment_detail", args=[self.garment.pk]))
        self.assertContains(page, "Calculer vers États-Unis")
        self.assertContains(page, "Calculer vers Chine")
        self.client.post(self.url("us"), self.data(duty_rate_pct="10"))
        self.assertContains(self.client.get(reverse("garment_detail", args=[self.garment.pk])), "€ / pièce")

    def test_quote_list_is_paginated(self):
        for _ in range(30):
            GarmentQuote.objects.create(
                garment=self.garment, destination="US", duty_rate=D("0.1"), quantity=1, unit_price=D("10"),
            )
        first = self.client.get(reverse("quote_list"))
        self.assertEqual(len(first.context["page"].object_list), 25)
        self.assertContains(first, "Page 1 sur 2")
        self.assertEqual(len(self.client.get(reverse("quote_list"), {"page": 2}).context["page"].object_list), 5)

    def test_new_pages_require_login(self):
        self.client.logout()
        for url in [self.url("us"), reverse("quote_list"), reverse("quote_detail", args=[1])]:
            self.assertEqual(self.client.get(url).status_code, 302, url)


class GarmentSearchTests(TestCase):
    fixtures = ["customs_starter"]

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user("u", password="not-a-real-password"))
        make_garment(name="Chemisier lin marine")
        make_garment(name="Blouse coton blanche")
        tshirt = make_garment(name="T-shirt rayé", garment_type="T-shirt, débardeur, maillot de corps (tricoté)")
        tshirt.reference = "TS-042"
        tshirt.save()

    def names(self, **params):
        response = self.client.get(reverse("garment_list"), params)
        return [g.name for g in response.context["page"].object_list]

    def test_search_by_name_and_reference(self):
        self.assertEqual(self.names(q="lin"), ["Chemisier lin marine"])
        self.assertEqual(self.names(q="TS-042"), ["T-shirt rayé"])
        self.assertEqual(self.names(q="BLOUSE"), ["Blouse coton blanche"])

    def test_filter_by_type_and_combination(self):
        self.assertEqual(self.names(type="T-shirt, débardeur, maillot de corps (tricoté)"), ["T-shirt rayé"])
        self.assertEqual(self.names(q="lin", type=BLOUSE), ["Chemisier lin marine"])
        self.assertEqual(self.names(q="lin", type="T-shirt, débardeur, maillot de corps (tricoté)"), [])

    def test_no_result_message_and_clear_link(self):
        page = self.client.get(reverse("garment_list"), {"q": "introuvable"})
        self.assertContains(page, "Aucun vêtement ne correspond")

    def test_pagination_keeps_the_filter_and_tolerates_bad_page_numbers(self):
        for index in range(30):
            make_garment(name=f"Robe {index:02d}")
        page = self.client.get(reverse("garment_list"), {"q": "Robe"})
        self.assertEqual(len(page.context["page"].object_list), 25)
        self.assertContains(page, "?q=Robe&amp;page=2")
        self.assertEqual(len(self.client.get(reverse("garment_list"), {"q": "Robe", "page": 2}).context["page"].object_list), 5)
        self.assertEqual(self.client.get(reverse("garment_list"), {"page": "abc"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("garment_list"), {"page": "999"}).status_code, 200)
